"""
Отладка поиска
"""
from utils.search_categories import find_compatible_models_in_category

for q in ["Samsung A54", "iPhone 11"]:
    result = find_compatible_models_in_category("battery", q)
    print(f"🔎 {q}:")
    print(f"  found: {result['found']}")
    print(f"  battery_mark: {result.get('battery_mark')}")
    print(f"  phone_models: {result.get('phone_models')}")
    print(f"  price: {result.get('price')}")
    print(f"  search_type: {result.get('search_type')}")
    print()
