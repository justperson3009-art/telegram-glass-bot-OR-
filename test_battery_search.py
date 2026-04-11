"""
Тест поиска АКБ
"""
from utils.search_categories import find_compatible_models_in_category

test_queries = [
    "Redmi 9",
    "iPhone 11",
    "Samsung A54",
]

print("=== ТЕСТИРОВАНИЕ ПОИСКА АКБ ===\n")

for query in test_queries:
    print(f"🔎 Запрос: {query}")
    try:
        result = find_compatible_models_in_category("battery", query)
        if result["found"]:
            print(f"   ✅ Нашли: {result['models'][:3]}...")
        else:
            print(f"   ❌ Не нашли")
    except Exception as e:
        print(f"   💥 ОШИБКА: {e}")
        import traceback
        traceback.print_exc()
    print()
