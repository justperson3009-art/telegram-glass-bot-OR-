#!/usr/bin/env python3
"""
Парсер каталога дисплеев с topset-minsk.by
Структура: Название товара, Артикул, Цена (красным), Наличие
Запуск: python scripts/parse_displays_topset.py
"""
import requests
import json
import time
import re
from bs4 import BeautifulSoup
from datetime import datetime

BASE_URL = "https://topset-minsk.by"
CATALOG_URL = f"{BASE_URL}/zapchasti-dlya-telefonov/displei-modulya"
OUTPUT_FILE = "prices_display.json"
COMPATIBILITY_FILE = "compatibility_display.json"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}


def extract_model_from_title(title):
    """
    Извлекаем модель телефона из названия дисплея.
    Примеры:
    'Дисплейный модуль LTN для Samsung Galaxy A32 5G (A326) черный' → 'Samsung Galaxy A32 5G'
    'Дисплейный модуль для iPhone 15 черный' → 'iPhone 15'
    'Дисплейный модуль LTN для Xiaomi Redmi Note 12 черный' → 'Xiaomi Redmi Note 12'
    """
    # Убираем скобки с артикулами
    clean = re.sub(r"\([A-Za-z0-9\s\-]+\)", "", title)

    # Ищем известные бренды
    brands = [
        "iPhone", "iPad", "iPod",
        "Samsung", "Galaxy",
        "Xiaomi", "Redmi", "POCO", "Poco", "Mi",
        "Huawei", "Honor",
        "Tecno", "Infinix",
        "Realme",
        "OPPO", "Oppo",
        "Vivo",
        "OnePlus",
        "Motorola", "Moto",
        "Nokia",
        "Sony",
        "LG",
        "Meizu",
        "ZTE",
        "Lenovo",
        "Asus",
        "Blackview",
        "Ulefone",
        "Doogee",
        "Oukitel",
        "Cubot",
        "Umidigi",
        "Apple",
    ]

    for brand in brands:
        if brand.lower() in clean.lower():
            idx = clean.lower().index(brand.lower())
            rest = clean[idx:].strip()

            # Берём всё до слова "черный", "белый", "синий", "зеленый" и т.д.
            color_stop = re.search(r"\s+(черный|белый|синий|зеленый|красный|розовый|золотой|серый|желтый|фиолетовый|серебристый|черн|бел|син|зел|красн|розов|золот|сер|желт|фиол|серебр)", rest, re.IGNORECASE)
            if color_stop:
                rest = rest[:color_stop.start()].strip()

            # Убираем слова-мусор
            rest = re.sub(r"\s+(для|модуль|дисплей|дисплейный|оригинал|копия|LTN|OEM)\b", " ", rest, flags=re.IGNORECASE)
            rest = re.sub(r"\s+", " ", rest).strip()

            if len(rest) > 3:
                return rest

    return None


def parse_products(html, page_num):
    """Распарсить продукты со страницы каталога"""
    soup = BeautifulSoup(html, "html.parser")
    products = []

    # Ищем карточки товаров — каталог битрикс обычно использует такой шаблон
    items = soup.find_all("div", class_="catalog-item")
    if not items:
        # Пробуем другие варианты
        items = soup.find_all("div", class_=re.compile(r"item|product|good"))
    if not items:
        # Если не нашли div, ищем ссылки на товары
        items = soup.find_all("a", href=re.compile(r"/catalog/"))

    print(f"    Найдено элементов: {len(items)}")

    for item in items:
        try:
            # Название — обычно в <a> с классом catalog-section-name или в <h3>
            title_tag = item.find("a", class_=re.compile(r"name|title|section"))
            if not title_tag:
                title_tag = item.find("h3") or item.find("h4")
            if not title_tag:
                title_tag = item.find("a")

            if not title_tag:
                continue

            title = title_tag.get_text(strip=True)
            if not title or len(title) < 10:
                continue

            # Цена — ищем элемент с ценой (обычно span с class="price" или div)
            price_tag = item.find("span", class_=re.compile(r"price|cost"))
            if not price_tag:
                # Пробуем найти цену в любом месте карточки
                all_prices = item.find_all(string=re.compile(r"\d+\.\d+"))
                if all_prices:
                    price_tag = all_prices[0]

            price = None
            if price_tag:
                price_text = price_tag.get_text(strip=True) if hasattr(price_tag, 'get_text') else str(price_tag)
                price_match = re.search(r"(\d+(?:[.,]\d+)?)\s*(?:BYN|руб|Br|р\.)", price_text, re.IGNORECASE)
                if price_match:
                    price = float(price_match.group(1).replace(",", "."))

            # Извлекаем модель телефона из названия
            model = extract_model_from_title(title)

            if model:
                products.append({
                    "full_name": title,
                    "model": model,
                    "price": price,
                    "note": "Цена ориентировочная",
                    "source": "topset-minsk.by",
                })

        except Exception as e:
            print(f"    ❌ Ошибка парсинга товара: {e}")
            continue

    return products


def get_page(session, url, page_num):
    """Получить страницу каталога"""
    # Для Битрикс пагинация: ?PAGEN_1=2 или /page/2/
    if page_num > 1:
        url = f"{url}/?PAGEN_1={page_num}"

    try:
        resp = session.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        return resp.text
    except Exception as e:
        print(f"  ❌ Ошибка загрузки страницы {page_num}: {e}")
        return None


def parse_all_pages():
    """Спарсить все страницы каталога"""
    session = requests.Session()
    session.headers.update(HEADERS)

    all_products = []

    # Сначала получаем первую страницу чтобы узнать сколько всего страниц
    print("📄 Загрузка первой страницы...")
    html = get_page(session, CATALOG_URL, 1)
    if not html:
        print("❌ Не удалось загрузить первую страницу!")
        return []

    products = parse_products(html, 1)
    all_products.extend(products)
    print(f"  ✅ Страница 1: {len(products)} товаров")

    # Ищем пагинацию — сколько всего страниц
    soup = BeautifulSoup(html, "html.parser")
    pagination = soup.find("div", class_=re.compile(r"pagination|nav-pages|pager"))
    total_pages = 1
    if pagination:
        page_links = pagination.find_all("a")
        for link in page_links:
            try:
                page_num = int(link.get_text(strip=True))
                if page_num > total_pages:
                    total_pages = page_num
            except:
                pass

    # Если не нашли пагинацию — пробуем 94 страницы (по скриншотам)
    if total_pages == 1:
        total_pages = 94
        print(f"  ⚠️ Не удалось определить кол-во страниц, пробую 94...")
    else:
        print(f"  📊 Найдено страниц: {total_pages}")

    # Собираем остальные страницы
    for page in range(2, total_pages + 1):
        print(f"  📄 Страница {page}/{total_pages}...")
        html = get_page(session, CATALOG_URL, page)
        if html:
            products = parse_products(html, page)
            all_products.extend(products)
            print(f"    ✅ Найдено: {len(products)} товаров")

        # Пауза чтобы не забанили
        time.sleep(1.5)

        # Промежуточное сохранение каждые 10 страниц
        if page % 10 == 0:
            save_intermediate(all_products, page)

    print(f"\n📊 Всего спарсено: {len(all_products)} товаров")
    return all_products


def save_intermediate(products, page):
    """Промежуточное сохранение"""
    tmp_file = f"prices_display_page_{page}.json"
    with open(tmp_file, "w", encoding="utf-8") as f:
        json.dump(products, f, indent=2, ensure_ascii=False)
    print(f"  💾 Промежуточное сохранение: {tmp_file} ({len(products)} товаров)")


def process_and_save(products):
    """Обработать и сохранить результаты"""
    print("\n🔄 Обработка данных...")

    # Убираем дубли по модели (берём первый найденный)
    seen = {}
    for p in products:
        key = p["model"].lower().strip()
        if key not in seen:
            seen[key] = p
        else:
            # Если у нового есть цена а у старого нет — берём новый
            if p["price"] and not seen[key]["price"]:
                seen[key] = p

    unique_products = list(seen.values())

    # Сортируем по названию
    unique_products.sort(key=lambda x: x["model"])

    # Сохраняем цены
    prices_data = {
        "last_updated": datetime.now().isoformat(),
        "source": "topset-minsk.by",
        "currency": "BYN",
        "note": "Цена ориентировочная, может отличаться",
        "total_models": len(unique_products),
        "products": {
            p["model"].lower().strip(): {
                "name": p["model"],
                "price": p["price"],
                "note": "Цена ориентировочная",
            }
            for p in unique_products
        }
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(prices_data, f, indent=2, ensure_ascii=False)
    print(f"✅ Цены сохранены: {OUTPUT_FILE}")

    # Формируем совместимость для дисплеев
    compat_data = {}
    for p in unique_products:
        model_key = p["model"].lower().strip().replace(" ", "_").replace("/", "_")
        group_name = f"display_{model_key}"
        compat_data[group_name] = [p["model"]]

    with open(COMPATIBILITY_FILE, "w", encoding="utf-8") as f:
        json.dump(compat_data, f, indent=2, ensure_ascii=False)
    print(f"✅ Совместимость сохранена: {COMPATIBILITY_FILE}")

    # Статистика
    with_prices = sum(1 for p in unique_products if p["price"])
    without_prices = len(unique_products) - with_prices
    print(f"\n📈 Статистика:")
    print(f"   Уникальных моделей: {len(unique_products)}")
    print(f"   С ценой: {with_prices}")
    print(f"   Без цены: {without_prices}")


if __name__ == "__main__":
    print("=" * 60)
    print("📱 Парсер каталога дисплеев topset-minsk.by")
    print("=" * 60)

    products = parse_all_pages()
    if products:
        process_and_save(products)
        print("\n✅ Готово!")
        print(f"📁 Файлы созданы:")
        print(f"   • {OUTPUT_FILE}")
        print(f"   • {COMPATIBILITY_FILE}")
    else:
        print("\n❌ Не удалось спарсить товары. Проверьте URL.")
