"""
Добавление недостающих моделей в базу дисплеев
"""
import json

with open('compatibility_display.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

compatibility = data.get("compatibility", {})
search_index = data.get("search_index", {})

# Модели которые нужно добавить
new_displays = {
    "redmi_9a_display": [
        "Redmi 9A - In-Cell (черная рама) — 35 BYN"
    ],
    "redmi_9c_display": [
        "Redmi 9C - In-Cell (черная рама) — 38 BYN"
    ],
    "redmi_10a_display": [
        "Redmi 10A - In-Cell (черная рама) — 40 BYN"
    ],
    "redmi_10c_display": [
        "Redmi 10C - In-Cell (черная рама) — 42 BYN"
    ],
    "redmi_10_display": [
        "Redmi 10 - In-Cell (черная рама) — 55 BYN",
        "Redmi 10 - OR (оригинал) — 120 BYN"
    ],
    "redmi_note9_display": [
        "Redmi Note 9 - In-Cell (черная рама) — 45 BYN",
        "Redmi Note 9S - In-Cell (черная рама) — 48 BYN",
        "Redmi Note 9 Pro - In-Cell (черная рама) — 52 BYN"
    ],
    "redmi_note10_display": [
        "Redmi Note 10 - OLED — 65 BYN",
        "Redmi Note 10S - In-Cell — 48 BYN",
        "Redmi Note 10 Pro - OLED — 85 BYN"
    ],
    "redmi_note11_display": [
        "Redmi Note 11 - In-Cell — 45 BYN",
        "Redmi Note 11S - In-Cell — 48 BYN",
        "Redmi Note 11 Pro - AMOLED — 75 BYN"
    ],
    "redmi_note12_display": [
        "Redmi Note 12 4G - In-Cell (премиум) (черная рама) — 77 BYN",
        "Redmi Note 12 4G - In-Cell (черая рама) — 48 BYN"
    ],
    "redmi_note13_display": [
        "Redmi Note 13 - In-Cell — 55 BYN",
        "Redmi Note 13 Pro - AMOLED — 95 BYN"
    ],
    "redmi_12_display": [
        "Redmi 12 - In-Cell — 50 BYN",
        "Redmi 12 5G - In-Cell — 65 BYN",
        "Redmi 12C - In-Cell — 42 BYN"
    ],
    "redmi_13_display": [
        "Redmi 13 - In-Cell — 55 BYN",
        "Redmi 13C - In-Cell — 45 BYN"
    ]
}

# Добавляем новые группы
added = 0
for group_name, models in new_displays.items():
    if group_name not in compatibility:
        compatibility[group_name] = models
        added += 1
        print(f"✅ Добавлена группа: {group_name}")
        for m in models:
            print(f"   • {m}")

print(f"\n📊 Итого добавлено групп: {added}")
print(f"📱 Всего моделей в базе: {sum(len(m) for m in compatibility.values())}")

# Сохраняем
data["compatibility"] = compatibility
with open('compatibility_display.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print("\n💾 Сохранено!")
