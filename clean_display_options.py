"""
Очистка вариантов — объединяем одинаковые типы с разными рамами
Оставляем лучший вариант (обычно самый дорогой OR = с рамой)
"""
import json

input_path = r"C:\Users\user\Desktop\Бот по стеклам\compatibility_display.json"

with open(input_path, "r", encoding="utf-8") as f:
    data = json.load(f)

compatibility = data["compatibility"]

# Для каждой группы — объединяем варианты по типу
for group_key, group_data in compatibility.items():
    options = group_data["options"]
    
    # Группируем по типу
    by_type = {}
    for opt in options:
        dtype = opt["type"]
        if dtype not in by_type:
            by_type[dtype] = []
        by_type[dtype].append(opt)
    
    # Для каждого типа оставляем один вариант
    # Если несколько — берём с максимальной ценой (это обычно полная версия)
    cleaned_options = []
    for dtype, opts in by_type.items():
        if len(opts) == 1:
            cleaned_options.append(opts[0])
        else:
            # Берём самый дорогой (полная версия с рамой)
            best = max(opts, key=lambda x: x["price"] if x["price"] else 0)
            # Но показываем что есть другие варианты
            if dtype == "OR":
                best["note"] = f"Есть варианты с разными рамами (от {min(o['price'] for o in opts if o['price'])} до {max(o['price'] for o in opts if o['price'])} BYN)"
            cleaned_options.append(best)
    
    group_data["options"] = cleaned_options

# Сохраняем
with open(input_path, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print(f"✅ Очищено! Теперь в каждой группе по 1 варианту на тип")

# Считаем статистику
type_counts = {}
for group_key, group_data in compatibility.items():
    for opt in group_data["options"]:
        t = opt["type"]
        type_counts[t] = type_counts.get(t, 0) + 1

print(f"\nРаспределение типов:")
for t, cnt in sorted(type_counts.items(), key=lambda x: -x[1]):
    print(f"  {t}: {cnt}")

# Примеры
print("\n=== ПРИМЕРЫ ===")
count = 0
for key, data in list(compatibility.items())[:20]:
    if len(data["options"]) > 1:
        print(f"\n📱 {key}:")
        print(f"   Модели: {', '.join(data['models'])}")
        for opt in data['options']:
            note = f" ({opt.get('note', '')})" if opt.get('note') else ""
            print(f"   {opt['type']:12s} — {opt['price']} BYN{note}")
        count += 1
        if count >= 10:
            break
