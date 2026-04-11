"""
Отладка Samsung A54 и iPhone 11
"""
import json, re

with open(r"C:\Users\user\Desktop\Бот по стеклам\compatibility_battery.json", "r", encoding="utf-8") as f:
    data = json.load(f)

compatibility = data["compatibility"]

# Samsung A54
for key, models in compatibility.items():
    for model in models:
        if "a54" in model.lower():
            print(f"НАЙДЕНО: {model}")
            all_marks = re.findall(r'\(([^)]+)\)', model)
            print(f"  Скобки: {all_marks}")
            phone_part = model.replace("Аккумулятор ", "").strip()
            phone_part_clean = re.sub(r'\s*\([^)]+\)', '', phone_part).strip()
            if " — " in phone_part_clean:
                phone_part_clean = phone_part_clean.rsplit(" — ", 1)[0].strip()
            print(f"  Телефоны: {phone_part_clean}")
            phone_models = [m.strip().lower() for m in phone_part_clean.split("/") if m.strip()]
            print(f"  Модели: {phone_models}")
            
            # Проверяем "samsung a54"
            user = "samsung a54"
            for pm in phone_models:
                if user == pm or user in pm:
                    print(f"  ✅ MATCH: {pm}")
                else:
                    print(f"  ❌ NO MATCH: '{user}' vs '{pm}'")
            print()

# iPhone 11
for key, models in compatibility.items():
    for model in models:
        if "iphone 11" in model.lower() and "pro" not in model.lower():
            print(f"НАЙДЕНО: {model}")
            all_marks = re.findall(r'\(([^)]+)\)', model)
            print(f"  Скобки: {all_marks}")
            phone_part = model.replace("Аккумулятор ", "").strip()
            phone_part_clean = re.sub(r'\s*\([^)]+\)', '', phone_part).strip()
            if " — " in phone_part_clean:
                phone_part_clean = phone_part_clean.rsplit(" — ", 1)[0].strip()
            print(f"  Телефоны: {phone_part_clean}")
            phone_models = [m.strip().lower() for m in phone_part_clean.split("/") if m.strip()]
            print(f"  Модели: {phone_models}")
            
            user = "iphone 11"
            for pm in phone_models:
                if user == pm or user in pm:
                    print(f"  ✅ MATCH: {pm}")
                else:
                    print(f"  ❌ NO MATCH: '{user}' vs '{pm}'")
