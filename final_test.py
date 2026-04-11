"""
Тест дисплеев и АКБ
"""
from utils.search_categories import find_compatible_models_in_category

print("=== ТЕСТИРОВАНИЕ ДИСПЛЕЕВ ===\n")
display_tests = ["Honor 200", "Samsung A55", "iPhone 15"]
for q in display_tests:
    result = find_compatible_models_in_category("display", q)
    print(f"🔎 {q}:")
    if result["found"]:
        opts = result.get("display_options", [])
        phones = result.get("phone_models", [])
        print(f"   📱 Совместимые модели: {', '.join(phones)}")
        print(f"   💡 Варианты ({len(opts)}):")
        for o in opts:
            note = f" ({o.get('note','')})" if o.get('note') else ""
            print(f"      {o['type']:12s} — {o['price']} BYN{note}")
    else:
        print(f"   ❌ Не найдено")
    print()

print("\n=== ТЕСТИРОВАНИЕ АКБ (двусторонний) ===\n")
battery_tests = [
    ("Redmi 9", "модель → маркировка"),
    ("BN56", "маркировка → модель"),
    ("Samsung A54", "модель → маркировка"),
    ("iPhone 11", "модель → маркировка"),
]
for q, desc in battery_tests:
    result = find_compatible_models_in_category("battery", q)
    print(f"🔎 {q} ({desc}):")
    if result["found"]:
        mark = result.get("battery_mark")
        phones = result.get("phone_models", [])
        price = result.get("price")
        stype = result.get("search_type")
        if stype == "phone_to_battery":
            print(f"   🔌 Маркировка: {mark}")
        else:
            print(f"   📱 Устанавливается в: {', '.join(phones)}")
        if price:
            print(f"   💰 {price}")
    else:
        print(f"   ❌ Не найдено")
    print()
