"""
Добавление недостающих моделей Redmi в базу стёкол
"""
import json

with open('compatibility_glass.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Модели которые нужно добавить
new_models = {
    "redmi_9a_group": [
        "Redmi 9A",
        "Redmi 9C",
        "Redmi 9AT"
    ],
    "redmi_10a_group": [
        "Redmi 10A",
        "Redmi 10C"
    ],
    "redmi_note9_group": [
        "Redmi Note 9",
        "Redmi Note 9S",
        "Redmi Note 9 Pro"
    ],
    "redmi_note10_group": [
        "Redmi Note 10",
        "Redmi Note 10S",
        "Redmi Note 10 Pro"
    ],
    "redmi_note11_group": [
        "Redmi Note 11",
        "Redmi Note 11S",
        "Redmi Note 11 Pro"
    ],
    "redmi_note12_group": [
        "Redmi Note 12",
        "Redmi Note 12 Pro",
        "Redmi Note 12 4G"
    ],
    "redmi_note13_group": [
        "Redmi Note 13",
        "Redmi Note 13 Pro"
    ],
    "redmi_12_group": [
        "Redmi 12",
        "Redmi 12 5G",
        "Redmi 12C"
    ],
    "redmi_13_group": [
        "Redmi 13",
        "Redmi 13C"
    ]
}

# Добавляем новые группы
added = 0
for group_name, models in new_models.items():
    if group_name not in data:
        data[group_name] = models
        added += 1
        print(f"✅ Добавлена группа: {group_name}")
        for m in models:
            print(f"   • {m}")

print(f"\n📊 Итого добавлено групп: {added}")
print(f"📱 Всего моделей в базе: {sum(len(m) for m in data.values())}")

# Сохраняем
with open('compatibility_glass.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print("\n💾 Сохранено!")
