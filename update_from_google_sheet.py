"""
Скрипт импорта данных из Google Sheets
Скачивает прайс, фильтрует по категориям (дисплеи/АКБ/запчасти),
обновляет JSON базы с бэкапом
"""
import csv
import json
import os
import re
import shutil
from datetime import datetime
from io import StringIO
import urllib.request

# === КОНФИГУРАЦИЯ ===

# Ссылка на Google Sheets CSV
GOOGLE_SHEET_CSV_URL = (
    "https://docs.google.com/spreadsheets/d/1Tvz3AXuz7-o8TRyqc8XSHQphfQoBltdU8k0i3E_V5YI"
    "/export?format=csv&gid=1779758987"
)

# Базовая директория проекта
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Файлы баз
DISPLAY_FILE = os.path.join(BASE_DIR, "compatibility_display.json")
BATTERY_FILE = os.path.join(BASE_DIR, "compatibility_battery.json")
PARTS_FILE = os.path.join(BASE_DIR, "compatibility_parts.json")

# Бэкап директория
BACKUP_DIR = os.path.join(BASE_DIR, "backups", "google_sheet_imports")

# Исключаемые бренды запчастей (копии/производители)
EXCLUDED_PARTS_BRANDS = [
    "JCID", "ZERO", "JK", "FOG", "GX", "DD", "OR", "WL", "YG", "TK",
    "Nissin", "Nillkin", "USAMS", "Rock", "Baseus", "P-Flow", "Tatsung",
]

# Ключевые слова для фильтрации категорий
DISPLAY_KEYWORDS = ["дисплей", "display", "lcd", "oled", "экран", "модуль", "touch", "in-cell", "amiced"]
BATTERY_KEYWORDS = ["аккумулятор", "battery", "акб", "батарея", "batt"]

# Валюты
CURRENCY = "BYN"  # Базовая валюта из прайса


def create_backup():
    """Создаёт бэкап текущих JSON баз"""
    os.makedirs(BACKUP_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_folder = os.path.join(BACKUP_DIR, f"backup_{timestamp}")
    os.makedirs(backup_folder, exist_ok=True)

    files_to_backup = {
        "compatibility_display.json": DISPLAY_FILE,
        "compatibility_battery.json": BATTERY_FILE,
        "compatibility_parts.json": PARTS_FILE,
    }

    for filename, filepath in files_to_backup.items():
        if os.path.exists(filepath):
            dest = os.path.join(backup_folder, filename)
            shutil.copy2(filepath, dest)
            print(f"  ✅ Бэкап: {filename}")

    print(f"\n💾 Бэкап создан: {backup_folder}")
    return backup_folder


def download_sheet():
    """Скачивает Google Sheets как CSV"""
    print("⬇️ Скачиваю прайс из Google Sheets...")
    try:
        with urllib.request.urlopen(GOOGLE_SHEET_CSV_URL, timeout=30) as response:
            csv_data = response.read().decode('utf-8-sig')  # utf-8-sig для BOM
        print(f"✅ Скачано: {len(csv_data)} символов")
        return csv_data
    except Exception as e:
        print(f"❌ Ошибка скачивания: {e}")
        return None


def parse_csv(csv_data):
    """Парсит CSV и возвращает список строк"""
    reader = csv.reader(StringIO(csv_data))
    rows = []
    for row in reader:
        if len(row) >= 2:
            name = row[0].strip()
            price = row[1].strip()
            # Пропускаем заголовки и пустые строки
            if name and price and name not in ("Наименование", "наименование"):
                # Проверяем что цена - число
                try:
                    price_value = float(price.replace(",", ".").replace(" ", ""))
                    rows.append({"name": name, "price": price_value})
                except ValueError:
                    continue
    print(f"📊 Найдено товаров: {len(rows)}")
    return rows


def categorize_item(name):
    """Определяет категорию товара по названию"""
    name_lower = name.lower()

    # Проверяем дисплеи
    for keyword in DISPLAY_KEYWORDS:
        if keyword in name_lower:
            return "display"

    # Проверяем аккумуляторы
    for keyword in BATTERY_KEYWORDS:
        if keyword in name_lower:
            return "battery"

    # Всё остальное - запчасти
    return "parts"


def should_exclude_from_parts(name):
    """Проверяет нужно ли исключить товар из запчастей (JCID, ZERO и т.д.)"""
    name_upper = name.upper()
    for brand in EXCLUDED_PARTS_BRANDS:
        # Проверяем бренд в скобках или после тире
        if brand in name_upper:
            return True
    return False


def extract_phone_model(name):
    """Извлекает модель телефона из названия товара"""
    # Убираем префиксы категории
    cleaned = name
    for keyword in DISPLAY_KEYWORDS + BATTERY_KEYWORDS:
        cleaned = re.sub(rf'\b{keyword}\b', '', cleaned, flags=re.IGNORECASE)

    # Убираем лишние символы
    cleaned = cleaned.strip()

    # Паттерны для извлечения моделей
    # Пример: "Дисплей Samsung A53 5G (A536B) - OLED"
    # Пример: "Аккумулятор iPhone 15 Pro (GUKD8)"

    # Если есть артикул в скобках - это маркировка АКБ
    mark_match = re.search(r'\(([A-Z0-9]{3,10})\)', cleaned)
    battery_mark = mark_match.group(1) if mark_match else None

    # Убираем артикул и всё после него
    cleaned = re.sub(r'\s*[—\-]\s*.*$', '', cleaned)
    cleaned = re.sub(r'\s*\(.*?\)', '', cleaned)

    # Убираем типы матриц и бренды копий
    cleaned = re.sub(r'\s*[-(]?\s*(OR|OLED|In-Cell|AMOLED|LCD|DD|GX|JK|FOG|WL|YG|TK|JCID|ZERO|Battery Collection).*?$', '', cleaned, flags=re.IGNORECASE)

    # Разделяем по / для моделей с несколькими вариантами
    models = [m.strip() for m in re.split(r'[/|]', cleaned) if m.strip()]

    return models, battery_mark


def build_display_entry(row):
    """Создаёт запись для базы дисплеев"""
    name = row["name"]
    price = row["price"]

    models, _ = extract_phone_model(name)

    if not models:
        return None

    # Создаём ключ для группировки
    # Используем первую модель как ключ
    key = models[0].lower()

    return {
        "key": key,
        "models": models,
        "price": f"{price:.0f} BYN",
        "type": extract_display_type(name),
    }


def extract_display_type(name):
    """Определяет тип дисплея из названия"""
    name_upper = name.upper()
    if "OLED" in name_upper:
        return "OLED"
    elif "IN-CELL" in name_upper or "IN CELL" in name_upper:
        return "In-Cell"
    elif "AMOLED" in name_upper:
        return "AMOLED"
    else:
        return "OR"  # Оригинал/копия по умолчанию


def build_battery_entry(row):
    """Создаёт запись для базы АКБ"""
    name = row["name"]
    price = row["price"]

    models, battery_mark = extract_phone_model(name)

    if not models and not battery_mark:
        return None

    return {
        "models": models,
        "battery_mark": battery_mark or "Не указана",
        "price": f"{price:.0f} BYN",
    }


def build_parts_entry(row):
    """Создаёт запись для базы запчастей"""
    name = row["name"]
    price = row["price"]

    # Очищаем название от префиксов
    cleaned = name
    for keyword in ["Динамик", "Speaker", "Buzzer", "Задняя крышка", "Back Cover",
                    "Шлейф", "Flex", "Камера", "Camera", "Разъем", "Connector",
                    "Кнопка", "Button", "Микрофон", "Microphone"]:
        cleaned = re.sub(rf'\b{keyword}\b', '', cleaned, flags=re.IGNORECASE)

    cleaned = cleaned.strip()
    # Убираем артикулы и спецификации
    cleaned = re.sub(r'\s*\(.*?\)', '', cleaned).strip()
    cleaned = re.sub(r'\s*[—\-]\s*.*$', '', cleaned).strip()

    if not cleaned:
        return None

    # Извлекаем модели
    models = [m.strip() for m in re.split(r'[/|]', cleaned) if m.strip()]

    if not models:
        models = [cleaned]

    # Определяем категорию запчасти
    category = detect_parts_category(name)

    return {
        "key": models[0].lower(),
        "models": models,
        "price": f"{price:.0f} BYN",
        "category": category,
        "original_name": name,
    }


def detect_parts_category(name):
    """Определяет категорию запчасти"""
    name_lower = name.lower()
    if any(k in name_lower for k in ["динамик", "speaker", "buzzer", "звонок"]):
        return "Динамик"
    elif any(k in name_lower for k in ["задняя крышка", "back cover", "корпус"]):
        return "Задняя крышка"
    elif any(k in name_lower for k in ["шлейф", "flex", "кабель"]):
        return "Шлейф"
    elif any(k in name_lower for k in ["камера", "camera"]):
        return "Камера"
    elif any(k in name_lower for k in ["разъем", "connector", "гнездо"]):
        return "Разъём"
    elif any(k in name_lower for k in ["кнопка", "button", "клавиша"]):
        return "Кнопка"
    elif any(k in name_lower for k in ["микрофон", "microphone", "mic"]):
        return "Микрофон"
    else:
        return "Другое"


def load_existing_json(filepath):
    """Загружает существующий JSON файл"""
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def merge_display_data(new_data, existing_data):
    """Объединяет новые данные дисплеев с существующими"""
    merged = dict(existing_data)

    for entry in new_data:
        key = entry["key"]
        if key in merged:
            # Обновляем цену если изменилась
            merged[key]["price"] = entry["price"]
            # Добавляем новые модели
            for model in entry["models"]:
                if model not in merged[key]["models"]:
                    merged[key]["models"].append(model)
        else:
            merged[key] = {
                "models": entry["models"],
                "price": entry["price"],
                "display_options": [
                    {
                        "type": entry["type"],
                        "price": entry["price"].replace(" BYN", ""),
                        "note": ""
                    }
                ],
                "aliases": [key],
            }

    return merged


def merge_battery_data(new_data, existing_data):
    """Объединяет новые данные АКБ с существующими"""
    merged = dict(existing_data)

    for entry in new_data:
        # Ключ по маркировке батареи
        mark = entry["battery_mark"]
        key = mark.lower()

        if key in merged:
            # Обновляем цену
            merged[key]["price"] = entry["price"]
            # Добавляем новые модели
            for model in entry["models"]:
                if model not in merged[key]["models"]:
                    merged[key]["models"].append(model)
        else:
            merged[key] = {
                "models": entry["models"],
                "battery_mark": mark,
                "price": entry["price"],
                "aliases": [key],
            }

    return merged


def merge_parts_data(new_data, existing_data):
    """Объединяет новые данные запчастей с существующими"""
    merged = dict(existing_data)

    for entry in new_data:
        key = entry["key"]
        if key in merged:
            # Обновляем цену
            merged[key]["price"] = entry["price"]
            # Добавляем новые модели
            for model in entry["models"]:
                if model not in merged[key]["models"]:
                    merged[key]["models"].append(model)
        else:
            merged[key] = {
                "models": entry["models"],
                "price": entry["price"],
                "category": entry["category"],
                "original_name": entry["original_name"],
                "aliases": [key],
            }

    return merged


def save_json(filepath, data):
    """Сохраняет JSON файл"""
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"✅ Сохранено: {filepath}")


def main():
    """Главная функция импорта"""
    print("\n" + "="*60)
    print("📦 ИМПОРТ ИЗ GOOGLE SHEETS")
    print("="*60 + "\n")

    # 1. Создаём бэкап
    print("📦 Создаю бэкап текущих баз...")
    backup_folder = create_backup()

    # 2. Скачиваем прайс
    csv_data = download_sheet()
    if not csv_data:
        print("❌ Не удалось скачать прайс. Отмена.")
        return

    # 3. Парсим CSV
    print("\n🔍 Парсю CSV...")
    items = parse_csv(csv_data)

    # 4. Распределяем по категориям
    print("\n📋 Распределяю по категориям...")
    display_items = []
    battery_items = []
    parts_items = []

    for item in items:
        category = categorize_item(item["name"])

        if category == "display":
            entry = build_display_entry(item)
            if entry:
                display_items.append(entry)
        elif category == "battery":
            entry = build_battery_entry(item)
            if entry:
                battery_items.append(entry)
        elif category == "parts":
            # Исключаем JCID, ZERO и т.д.
            if not should_exclude_from_parts(item["name"]):
                entry = build_parts_entry(item)
                if entry:
                    parts_items.append(entry)

    print(f"\n📊 Результаты фильтрации:")
    print(f"  🖥️ Дисплеи: {len(display_items)}")
    print(f"  🔋 АКБ: {len(battery_items)}")
    print(f"  🔧 Запчасти: {len(parts_items)}")

    # 5. Загружаем существующие данные
    print("\n📂 Загружаю существующие данные...")
    existing_display = load_existing_json(DISPLAY_FILE)
    existing_battery = load_existing_json(BATTERY_FILE)
    existing_parts = load_existing_json(PARTS_FILE)

    # 6. Объединяем данные
    print("\n🔄 Объединяю данные...")
    merged_display = merge_display_data(display_items, existing_display)
    merged_battery = merge_battery_data(battery_items, existing_battery)
    merged_parts = merge_parts_data(parts_items, existing_parts)

    # 7. Сохраняем обновлённые базы
    print("\n💾 Сохраняю обновлённые базы...")
    save_json(DISPLAY_FILE, merged_display)
    save_json(BATTERY_FILE, merged_battery)
    save_json(PARTS_FILE, merged_parts)

    # 8. Итоговая статистика
    print("\n" + "="*60)
    print("✅ ИМПОРТ ЗАВЕРШЁН!")
    print("="*60)
    print(f"\n📊 Итоговая статистика:")
    print(f"  🖥️ Дисплеи: {len(merged_display)} групп")
    print(f"  🔋 АКБ: {len(merged_battery)} групп")
    print(f"  🔧 Запчасти: {len(merged_parts)} групп")
    print(f"\n💾 Бэкап: {backup_folder}")
    print(f"\n⚠️ Не забудьте перезапустить бота!")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
