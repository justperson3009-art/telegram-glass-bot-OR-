"""
Тест поиска дисплеев с несколькими вариантами
"""
from utils.search_categories import find_compatible_models_in_category

test_queries = [
    "Honor 200",
    "Google Pixel 7",
    "Huawei Honor 200 Pro",
    "Samsung A55",
    "iPhone 15",
    "Redmi Note 12",
]

print("=== ТЕСТИРОВАНИЕ ПОИСКА ДИСПЛЕЕВ ===\n")

for query in test_queries:
    print(f"🔎 Запрос: {query}")
    result = find_compatible_models_in_category("display", query)
    
    if result["found"]:
        display_options = result.get("display_options")
        phone_models = result.get("phone_models", [])
        
        if display_options:
            print(f"   📱 Модели: {', '.join(phone_models)}")
            print(f"   💡 Варианты ({len(display_options)} шт):")
            for opt in display_options:
                note = f" ({opt.get('note', '')})" if opt.get('note') else ""
                print(f"      {opt['type']:12s} — {opt['price']} BYN{note}")
        else:
            print(f"   ✅ Нашли: {result['models']}")
    else:
        print(f"   ❌ Не нашли")
    print()
