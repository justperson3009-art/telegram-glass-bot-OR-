"""
Простая проверка: сколько всего записей в JSON
"""
import json

with open(r"C:\Users\user\Desktop\Бот по стеклам\compatibility_display.json", "r", encoding="utf-8") as f:
    data = json.load(f)

compatibility = data["compatibility"]

total_records = 0
total_groups = len(compatibility)
multi_variant = 0

for key, gdata in compatibility.items():
    opts = gdata["options"]
    total_records += len(opts)
    if len(opts) > 1:
        multi_variant += 1

print(f"Групп: {total_groups}")
print(f"Всего записей (options): {total_records}")
print(f"Моделей с несколькими вариантами: {multi_variant}")

# Примеры с большим количеством вариантов
print(f"\n=== ТОП-10 моделей по количеству вариантов ===")
sorted_groups = sorted(compatibility.items(), key=lambda x: len(x[1]["options"]), reverse=True)
for key, gdata in sorted_groups[:10]:
    print(f"\n📱 {key}: {', '.join(gdata['models'])}")
    for opt in gdata["options"]:
        note = f" ({opt.get('note', '')})" if opt.get('note') else ""
        print(f"   {opt['type']:12s} — {opt['price']} BYN{note}")
