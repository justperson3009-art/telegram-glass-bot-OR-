"""
Модуль работы с файлами категорий
Каждая категория — отдельный JSON файл
"""
import json
import os
import re
from datetime import datetime

BASE_DIR = os.path.join(os.path.dirname(__file__), "..")

# Маппинг категорий на файлы
CATEGORY_FILES = {
    "glass": "compatibility_glass.json",
    "case": "compatibility_case.json",
    "display": "compatibility_display.json",
    "battery": "compatibility_battery.json",
    "oca": "compatibility_oca.json",
}


def get_category_file(category):
    """Получить путь к файлу категории"""
    return os.path.join(BASE_DIR, CATEGORY_FILES.get(category, "compatibility_glass.json"))


def load_category(category):
    """Загрузить данные категории"""
    filepath = get_category_file(category)
    if not os.path.exists(filepath):
        return {}
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # Для дисплеев и АКБ новый формат с поисковым индексом
    if category in ("display", "battery") and isinstance(data, dict) and "compatibility" in data:
        return data  # Возвращаем как есть {compatibility: {...}, search_index: {...}}
    
    return data


def save_category(category, data):
    """Сохранить данные категории"""
    filepath = get_category_file(category)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def load_all_categories():
    """Загрузить все категории в один dict"""
    combined = {}
    for cat in CATEGORY_FILES:
        data = load_category(cat)
        combined.update(data)
    return combined


def add_models_to_category(category, group_name, models):
    """Добавить группу моделей в категорию"""
    data = load_category(category)
    data[group_name] = models
    save_category(category, data)
    return data


def remove_group_from_category(category, group_name):
    """Удалить группу из категории"""
    data = load_category(category)
    if group_name in data:
        del data[group_name]
        save_category(category, data)
        return True
    return False


def get_all_groups_in_category(category):
    """Получить все группы в категории"""
    return load_category(category)


def get_all_models_count():
    """Посчитать общее количество моделей"""
    total = 0
    for cat in CATEGORY_FILES:
        data = load_category(cat)
        total += sum(len(m) for m in data.values())
    return total


def get_groups_count():
    """Посчитать общее количество групп"""
    total = 0
    for cat in CATEGORY_FILES:
        data = load_category(cat)
        total += len(data)
    return total


def get_category_stats():
    """Статистика по всем категориям"""
    stats = {}
    for cat, filename in CATEGORY_FILES.items():
        data = load_category(cat)
        stats[cat] = {
            "file": filename,
            "groups": len(data),
            "models": sum(len(m) for m in data.values()),
        }
    return stats


# === НЕЧЁТКИЙ ПОИСК (для любой категории) ===

def levenshtein_distance(s1, s2):
    """Расстояние Левенштейна"""
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
    if len(s2) == 0:
        return len(s1)
    prev_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        curr_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = prev_row[j + 1] + 1
            deletions = curr_row[j] + 1
            substitutions = prev_row[j] + (c1 != c2)
            curr_row.append(min(insertions, deletions, substitutions))
        prev_row = curr_row
    return prev_row[-1]


def normalize_text(text):
    """Нормализация текста"""
    text = text.lower().strip()
    text = re.sub(r'\s+', ' ', text)
    return text


def _translate_keyword(keyword):
    """Перевод популярных ключевых слов"""
    translations = {
        "айфон": "iphone",
        "самсунг": "samsung",
        "сяоми": "xiaomi",
        "редми": "redmi",
        "поко": "poco",
        "реалми": "realme",
        "хоноу": "honor",
        "хонор": "honor",
        "текно": "tecno",
        "инфиникс": "infinix",
        "галакси": "galaxy",
        "про": "pro",
        "плюс": "plus",
        "мини": "mini",
        "ультра": "ultra",
    }
    return translations.get(keyword, keyword)


# === АЛИАСЫ ДЛЯ ОБЛЕГЧЁННОГО ПОИСКА ===

def generate_model_aliases(model_name):
    """
    Генерирует все варианты написания модели для поиска.
    Пример: 'Samsung Galaxy A32 5G' →
      'samsung galaxy a32 5g', 'samsung a32 5g', 'galaxy a32 5g',
      'samsung a32', 'galaxy a32', 'a32 5g', 'a32'
    """
    normalized = normalize_text(model_name)
    words = normalized.split()

    aliases = set()
    aliases.add(normalized)  # Полное название

    # Слова которые можно убирать при поиске
    skip_words = {"galaxy", "the", "and", "для"}

    # Генерируем все подпоследовательности слов (от 2 слов и более)
    for i in range(len(words)):
        for j in range(i + 1, len(words) + 1):
            sub = " ".join(words[i:j])
            aliases.add(sub)
            # Без skip_words
            filtered = [w for w in words[i:j] if w not in skip_words]
            if filtered and len(filtered) >= 1:
                aliases.add(" ".join(filtered))

    # Отдельно — только номер модели (A32, A55, 15 Pro и т.д.)
    number_pattern = re.search(r'([A-Z]?\d+[A-Z]?(?:\s*Pro\s*Max|Plus|Pro|Lite|SE|FE)?(?:\s*5G)?)', model_name, re.IGNORECASE)
    if number_pattern:
        aliases.add(number_pattern.group(1).lower().strip())

    return list(aliases)


def build_search_index(category):
    """Строит поисковый индекс с алиасами для категории"""
    data = load_category(category)
    index = {}

    for group_name, models in data.items():
        for model in models:
            aliases = generate_model_aliases(model)
            for alias in aliases:
                if alias not in index:
                    index[alias] = []
                index[alias].append(model)

    return index


def find_compatible_models_in_category(category, user_input):
    """Поиск моделей в конкретной категории с алиасами"""
    data = load_category(category)
    user_normalized = normalize_text(user_input)

    # === СПЕЦИАЛЬНЫЙ ПОИСК ДЛЯ АКБ (по маркировке ИЛИ модели телефона) ===
    if category == "battery":
        # Для battery data = {compatibility: {...}, search_index: {...}}
        compatibility_data = data.get("compatibility", {}) if isinstance(data, dict) and "compatibility" in data else data
        battery_mark_result = _find_battery_by_mark(compatibility_data, user_input)
        if battery_mark_result["found"]:
            return battery_mark_result
        # Если не нашли через специальный поиск - идём дальше через обычный поиск
        return _find_in_compatibility_data(compatibility_data, user_input, user_normalized)

    # === СПЕЦИАЛЬНЫЙ ПОИСК ДЛЯ ДИСПЛЕЕВ (по модели телефона) ===
    if category == "display":
        # Для display data = {compatibility: {...}, search_index: {...}}
        compatibility_data = data.get("compatibility", {}) if isinstance(data, dict) and "compatibility" in data else data
        display_result = _find_display_by_phone(compatibility_data, user_input)
        if display_result["found"]:
            return display_result
        # Если не нашли — обычный поиск
        return _find_in_compatibility_data(compatibility_data, user_input, user_normalized)

    # Для остальных категорий — обычный поиск
    return _find_in_compatibility_data(data, user_input, user_normalized)


def _find_in_compatibility_data(data, user_input, user_normalized):
    """Обычный поиск в данных совместимости"""
    # Шаг 1: Точное совпадение (оригинал)
    for group in data.values():
        for model in group:
            if user_normalized in model.lower():
                return {
                    "found": True,
                    "models": group,
                    "exact_match": True,
                    "matched_model": model,
                    "confidence": 1.0
                }

    # Шаг 2: Поиск по алиасам
    index = build_search_index_for_data(data)
    if user_normalized in index:
        matched_model = index[user_normalized][0]
        # Находим группу с этой моделью
        for group in data.values():
            if matched_model in group:
                return {
                    "found": True,
                    "models": group,
                    "exact_match": True,
                    "matched_model": matched_model,
                    "confidence": 0.95,
                    "alias_match": True
                }

    # Шаг 3: Умное совпадение по ключевым словам + номер модели
    keywords = user_normalized.split()
    
    # Если запрос содержит номер модели (например "redmi 10")
    number_match = re.search(r'\b(\d+[A-Za-z]?)\b', user_normalized)
    if number_match and len(keywords) >= 1:
        model_number = number_match.group(1)
        # Ищем модели где есть бренд И точный номер
        for group in data.values():
            for model in group:
                model_lower = model.lower()
                # Проверяем что номер модели есть в названии
                if model_number in model_lower:
                    # И бренд тоже совпадает
                    brand_match = any(
                        _translate_keyword(kw) in model_lower or kw in model_lower 
                        for kw in keywords 
                        if kw != model_number
                    )
                    if brand_match or len(keywords) == 1:
                        return {
                            "found": True,
                            "models": group,
                            "exact_match": True,
                            "matched_model": model,
                            "confidence": 0.92,
                            "number_match": True
                        }

    # Шаг 4: Ключевые слова (частичное совпадение по 2+ словам)
    if len(keywords) >= 2:
        for group in data.values():
            for model in group:
                model_lower = model.lower()
                matches = sum(1 for kw in keywords if kw in model_lower or _translate_keyword(kw) in model_lower)
                if matches == len(keywords):
                    return {
                        "found": True,
                        "models": group,
                        "exact_match": True,
                        "matched_model": model,
                        "confidence": 0.9,
                        "keyword_match": True
                    }

    # Шаг 5: Нечёткое совпадение (Levenshtein) - СНИЖАЕМ порог до 0.75
    best_match = None
    best_score = 0

    for group in data.values():
        for model in group:
            model_normalized = normalize_text(model)
            distance = levenshtein_distance(user_normalized, model_normalized)
            max_len = max(len(user_normalized), len(model_normalized))
            if max_len == 0:
                continue
            similarity = 1 - (distance / max_len)
            # ПОВЫСИЛИ порог с 0.7 до 0.75 чтобы избежать ложных совпадений
            if similarity > 0.75 and similarity > best_score:
                best_score = similarity
                best_match = {
                    "found": True,
                    "models": group,
                    "exact_match": False,
                    "matched_model": model,
                    "confidence": similarity
                }

    if best_match:
        return best_match

    return {"found": False}


def build_search_index_for_data(data):
    """Строит поисковый индекс для произвольных данных"""
    index = {}
    for group_name, models in data.items():
        for model in models:
            aliases = generate_model_aliases(model)
            for alias in aliases:
                if alias not in index:
                    index[alias] = []
                index[alias].append(model)
    return index

def normalize_model_name(name):
    """Нормализует название: убирает лишние пробелы, приводит к нижнему регистру"""
    return " ".join(name.strip().lower().split())


def save_category(category, data):
    """Атомарное сохранение (предотвращает битые JSON файлы)"""
    filepath = get_category_file(category)
    tmp_path = filepath + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    os.replace(tmp_path, filepath)  # Атомарная замена на POSIX/Windows


def add_models_smart(category, raw_models_str):
    """
    Умное добавление моделей:
    1. Чистит и нормализует ввод
    2. Убирает дубли внутри ввода
    3. Проверяет глобальные дубли во всех категориях
    4. Создаёт уникальную группу
    5. Атомарно сохраняет
    """
    # 1. Парсим и чистим
    models = [normalize_model_name(m) for m in raw_models_str.split(",") if m.strip()]
    # Убираем дубли внутри ввода (сохраняем порядок)
    unique_input = list(dict.fromkeys(models))

    if not unique_input:
        return {"added": 0, "skipped": 0, "group": None, "error": "❌ Пустой список"}

    # 2. Проверяем глобальные дубли (во всех категориях)
    all_data = load_all_categories()
    existing_global = {normalize_model_name(m) for group in all_data.values() for m in group}

    new_models = []
    skipped = 0
    for m in unique_input:
        if m in existing_global:
            skipped += 1
        else:
            new_models.append(m)

    if not new_models:
        return {"added": 0, "skipped": len(unique_input), "group": None, "msg": "Все модели уже есть в базе"}

    # 3. Создаём уникальную группу (timestamp предотвращает конфликты имён)
    cat_data = load_category(category)
    timestamp = int(datetime.now().timestamp())
    group_name = f"auto_{category}_{len(cat_data) + 1}_{timestamp}"

    # 4. Сохраняем атомарно
    cat_data[group_name] = new_models
    save_category(category, cat_data)

    return {"added": len(new_models), "skipped": skipped, "group": group_name, "models": new_models}


# === ПОИСК АКБ ПО МАРКИРОВКЕ ИЛИ МОДЕЛИ ТЕЛЕФОНА ===

def _find_battery_by_mark(data, user_input):
    """
    Ищем АКБ:
    1. По маркировке (BN56, BM41 и т.д.)
    2. По модели телефона (Redmi 9A, Samsung A55 и т.д.)
    Формат записи: "Аккумулятор Redmi 9A/9C (BN56) — 20 BYN"
    """
    user_normalized = normalize_text(user_input)
    
    # === ШАГ 1: Поиск по маркировке (BN56) ===
    for group_name, models in data.items():
        for model in models:
            mark_match = re.search(r'\(([^)]+)\)', model)
            if mark_match:
                battery_mark = mark_match.group(1).lower().strip()
                if user_normalized == battery_mark or user_normalized in battery_mark or battery_mark in user_normalized:
                    return {
                        "found": True,
                        "models": models,
                        "exact_match": True,
                        "matched_model": model,
                        "confidence": 1.0,
                        "mark_match": True
                    }
    
    # === ШАГ 2: Поиск по модели телефона ===
    # Извлекаем названия телефонов из записей
    for group_name, models in data.items():
        for model in models:
            # Убираем "Аккумулятор " и маркировку в скобках
            phone_part = model.replace("Аккумулятор ", "").strip()
            mark_match = re.search(r'\(([^)]+)\)', phone_part)
            if mark_match:
                phone_part = phone_part.replace(f"({mark_match.group(1)})", "").strip()
            # Убираем цену
            if " — " in phone_part:
                phone_part = phone_part.rsplit(" — ", 1)[0].strip()
            
            # Разбиваем по слэшу - получаем отдельные модели
            phone_models = [m.strip().lower() for m in phone_part.split("/") if m.strip()]
            
            # Проверяем точное совпадение
            for pm in phone_models:
                if user_normalized == pm or user_normalized in pm or pm in user_normalized:
                    return {
                        "found": True,
                        "models": models,
                        "exact_match": True,
                        "matched_model": model,
                        "confidence": 0.98,
                        "phone_match": True
                    }

    return {"found": False}


# === ПОИСК ДИСПЛЕЕВ ПО МОДЕЛИ ТЕЛЕФОНА ===

def _find_display_by_phone(data, user_input):
    """
    Ищем дисплей по модели телефона — возвращаем ВСЕ варианты (OR/OLED/In-Cell/Стандарт)
    Формат записи: {"models": [...], "options": [{"type": "...", "price": ..., "full_name": "..."}]}
    """
    user_normalized = normalize_text(user_input)
    user_words = user_normalized.split()

    # === ШАГ 1: ТОЧНОЕ совпадение по модели телефона — собираем ВСЕ группы ===
    all_matching_groups = []

    for group_name, group_data in data.items():
        phone_models = group_data.get("models", [])
        options = group_data.get("options", [])
        
        for pm in phone_models:
            pm_lower = pm.lower()
            
            is_match = False
            is_exact_eq = False

            if user_normalized == pm_lower:
                is_match = True
                is_exact_eq = True
            elif user_normalized in pm_lower:
                # Проверяем границы (mi 9 НЕ должно находить mi 9t)
                idx = pm_lower.find(user_normalized)
                end_idx = idx + len(user_normalized)
                if end_idx >= len(pm_lower) or pm_lower[end_idx] in ' /-+()':
                    if idx == 0 or pm_lower[idx-1] in ' /-+(':
                        is_match = True

            if is_match:
                # Считаем score для приоритета
                if is_exact_eq:
                    score = 1000 + len(phone_models)
                else:
                    len_diff = abs(len(pm_lower) - len(user_normalized))
                    if pm_lower.endswith(user_normalized):
                        bonus = 3
                    else:
                        bonus = 0
                    score = bonus + (len(phone_models) * 0.1) - len_diff
                
                all_matching_groups.append((group_name, group_data, score, is_exact_eq))
                break  # Одна группа добавлена один раз

    if all_matching_groups:
        # Разделяем exact_eq и exact_in
        eq_matches = [(gn, gd, s, ie) for gn, gd, s, ie in all_matching_groups if ie]
        in_matches = [(gn, gd, s, ie) for gn, gd, s, ie in all_matching_groups if not ie]

        # Выбираем лучшую группу
        if eq_matches:
            best_gn, best_gd, best_score, _ = max(eq_matches, key=lambda x: x[2])
        else:
            best_gn, best_gd, best_score, _ = max(in_matches, key=lambda x: x[2])

        # Возвращаем лучшую группу со ВСМИ вариантами
        return {
            "found": True,
            "models": [f"{opt['type']} — {opt['price']} BYN" for opt in best_gd["options"]],
            "display_options": best_gd["options"],  # Все варианты
            "phone_models": best_gd["models"],  # Совместимые модели телефонов
            "exact_match": True,
            "matched_model": best_gn,
            "confidence": 1.0,
            "phone_match": True,
            "all_matching_groups": all_matching_groups  # Для отладки
        }

    # === ШАГ 2: Все слова запроса содержатся в модели (brand + model number) ===
    if len(user_words) >= 1:
        for group_name, group_data in data.items():
            phone_models = group_data.get("models", [])
            
            for pm in phone_models:
                pm_lower = pm.lower()
                pm_words = pm_lower.split()
                if all(w in pm_words for w in user_words):
                    return {
                        "found": True,
                        "models": [f"{opt['type']} — {opt['price']} BYN" for opt in group_data["options"]],
                        "display_options": group_data["options"],
                        "phone_models": group_data["models"],
                        "exact_match": True,
                        "matched_model": group_name,
                        "confidence": 0.95,
                        "phone_match": True
                    }

    # === ШАГ 3: Частичное совпадение (номер модели + бренд) ===
    number_match = re.search(r'([A-Z]?\d+[A-Z]?(?:\s*Pro\s*Max|Plus|Pro|Lite|SE|FE)?(?:\s*5G)?)', user_normalized, re.IGNORECASE)
    if number_match:
        model_number = number_match.group(1).lower().strip()
        best_match = None
        best_score = 0
        for group_name, group_data in data.items():
            phone_models = group_data.get("models", [])
            
            for pm in phone_models:
                pm_lower = pm.lower()
                if model_number in pm_lower:
                    brand_words = [w for w in user_words if w != model_number]
                    brand_match = all(any(bw in pm_lower for pm_word in pm_lower.split() if pm_word != model_number) for bw in brand_words)
                    if brand_match or not brand_words:
                        score = len(pm_lower)
                        if score > best_score:
                            best_score = score
                            best_match = {
                                "found": True,
                                "models": [f"{opt['type']} — {opt['price']} BYN" for opt in group_data["options"]],
                                "display_options": group_data["options"],
                                "phone_models": group_data["models"],
                                "exact_match": True,
                                "matched_model": group_name,
                                "confidence": 0.9,
                                "number_match": True
                            }
        if best_match:
            return best_match

    return {"found": False}
