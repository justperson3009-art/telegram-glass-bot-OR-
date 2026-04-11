"""
Проверка записей АКБ для конкретных моделей
"""
import json

with open(r"C:\Users\user\Desktop\Бот по стеклам\compatibility_battery.json", "r", encoding="utf-8") as f:
    data = json.load(f)

compatibility = data["compatibility"]

# Ищем Samsung A54 и iPhone 11
for key, models in compatibility.items():
    for model in models:
        model_lower = model.lower()
        if "a54" in model_lower or "iphone 11" in model_lower:
            print(f"{key}: {model}")
