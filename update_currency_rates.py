"""
Скрипт обновления курса валют из API НБРБ (Национальный банк Республики Беларусь)
Обновляет курсы USD и RUB относительно BYN
"""
import json
import os
import urllib.request
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CURRENCY_RATES_FILE = os.path.join(BASE_DIR, "currency_rates.json")

# API НБРБ
# Получаем курсы валют в формате XML/JSON
# USD: 431, RUB: 460 (коды валют НБРБ)
NBRB_API_URL = "https://www.nbrb.by/api/exrates/rates"


def load_existing_rates():
    """Загружает существующие курсы"""
    if os.path.exists(CURRENCY_RATES_FILE):
        with open(CURRENCY_RATES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {
        "last_updated": None,
        "rates": {
            "USD": {"rate": None, "date": None},
            "RUB": {"rate": None, "date": None},
        }
    }


def fetch_nbrb_rates():
    """Скачивает курсы валют с API НБРБ"""
    print("⬇️ Скачиваю курсы валют с НБРБ...")
    try:
        # Скачиваем курсы USD (431) и RUB (460)
        usd_url = f"{NBRB_API_URL}/431?period=1"
        rub_url = f"{NBRB_API_URL}/460?period=1"

        def fetch_json(url):
            with urllib.request.urlopen(url, timeout=10) as response:
                data = response.read().decode('utf-8')
                return json.loads(data)

        usd_data = fetch_json(usd_url)
        rub_data = fetch_json(rub_url)

        # Извлекаем курсы (Cur_OfficialRate - официальный курс)
        usd_rate = usd_data.get("Cur_OfficialRate")
        rub_rate = rub_data.get("Cur_OfficialRate")

        # Даты обновления
        usd_date = usd_data.get("Date", "")
        rub_date = rub_data.get("Date", "")

        print(f"  ✅ USD: {usd_rate} BYN (на {usd_date})")
        print(f"  ✅ RUB: {rub_rate} BYN (на {rub_date})")

        return {
            "USD": {"rate": usd_rate, "date": usd_date},
            "RUB": {"rate": rub_rate, "date": rub_date},
        }

    except Exception as e:
        print(f"❌ Ошибка загрузки курсов: {e}")
        return None


def update_rates_file():
    """Обновляет файл курсов валют"""
    print("\n" + "="*60)
    print("💱 ОБНОВЛЕНИЕ КУРСОВ ВАЛЮТ")
    print("="*60 + "\n")

    # Загружаем существующие курсы
    existing = load_existing_rates()

    # Скачиваем новые курсы
    new_rates = fetch_nbrb_rates()
    if not new_rates:
        print("❌ Не удалось получить курсы. Отмена.")
        return

    # Обновляем данные
    updated_data = {
        "last_updated": datetime.now().isoformat(),
        "rates": {
            "USD": new_rates["USD"],
            "RUB": new_rates["RUB"],
        }
    }

    # Сохраняем
    with open(CURRENCY_RATES_FILE, 'w', encoding='utf-8') as f:
        json.dump(updated_data, f, ensure_ascii=False, indent=2)

    print(f"\n💾 Сохранено: {CURRENCY_RATES_FILE}")
    print(f"📅 Обновлено: {updated_data['last_updated']}")
    print("\n✅ ОБНОВЛЕНИЕ КУРСОВ ЗАВЕРШЁНО!")
    print("="*60 + "\n")

    return updated_data


def get_rates():
    """Возвращает текущие курсы валют"""
    if os.path.exists(CURRENCY_RATES_FILE):
        with open(CURRENCY_RATES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None


def convert_price(price_byn, target_currency):
    """Конвертирует цену из BYN в целевую валюту"""
    if target_currency == "BYN":
        return f"{price_byn:.2f} BYN"

    rates_data = get_rates()
    if not rates_data:
        return f"{price_byn:.2f} BYN"  # Если нет курсов, показываем BYN

    if target_currency == "USD":
        usd_rate = rates_data["rates"]["USD"]["rate"]
        if usd_rate:
            price_usd = price_byn / usd_rate
            return f"${price_usd:.2f}"
    elif target_currency == "RUB":
        rub_rate = rates_data["rates"]["RUB"]["rate"]
        if rub_rate:
            price_rub = price_byn / rub_rate
            return f"{price_rub:.2f} ₽"

    return f"{price_byn:.2f} BYN"


if __name__ == "__main__":
    update_rates_file()
