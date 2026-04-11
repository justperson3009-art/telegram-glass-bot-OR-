"""
Проверка формата compatibility_battery.json
"""
import json

with open(r"C:\Users\user\Desktop\Бот по стеклам\compatibility_battery.json", "r", encoding="utf-8") as f:
    data = json.load(f)

print(f"Тип данных: {type(data)}")
print(f"Ключи: {list(data.keys())[:5]}")
print(f"Есть 'compatibility' ключ: {'compatibility' in data}")

if "compatibility" in data:
    compat = data["compatibility"]
    print(f"Тип compatibility: {type(compat)}")
    first_key = list(compat.keys())[0]
    print(f"Первый ключ: {first_key}")
    print(f"Тип значения: {type(compat[first_key])}")
    print(f"Значение: {compat[first_key]}")
else:
    # Старый формат — данные напрямую
    first_key = list(data.keys())[0]
    print(f"Первый ключ: {first_key}")
    print(f"Тип значения: {type(data[first_key])}")
    print(f"Значение: {data[first_key]}")
