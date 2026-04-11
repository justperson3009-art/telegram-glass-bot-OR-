"""
Проверка — сколько типов в каждой группе
"""
import json

with open(r"C:\Users\user\Desktop\Бот по стеклам\compatibility_display.json", "r", encoding="utf-8") as f:
    data = json.load(f)

compatibility = data["compatibility"]

# Сколько групп имеют несколько вариантов
multi_option_groups = {k: v for k, v in compatibility.items() if len(v["options"]) > 1}

print(f"Всего групп: {len(compatibility)}")
print(f"Групп с несколькими вариантами: {len(multi_option_groups)}")

# Примеры
if multi_option_groups:
    print("\n=== ПРИМЕРЫ (первые 20) ===")
    count = 0
    for key, gdata in multi_option_groups.items():
        if count >= 20:
            break
        print(f"\n📱 {key}:")
        print(f"   Модели: {', '.join(gdata['models'])}")
        for opt in gdata['options']:
            note = f" ({opt.get('note', '')})" if opt.get('note') else ""
            print(f"   {opt['type']:12s} — {opt['price']} BYN{note}")
        count += 1
else:
    print("\nНЕТ групп с несколькими вариантами! Проблема в группировке.")
    
    # Ищем модели которые должны иметь несколько вариантов
    # Например Honor 200
    for key, gdata in compatibility.items():
        if "honor_200" in key and "pro" not in key:
            print(f"\n📱 {key}:")
            print(f"   Модели: {', '.join(gdata['models'])}")
            for opt in gdata['options']:
                print(f"   {opt['type']:12s} — {opt['price']} BYN")
