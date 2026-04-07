"""
Модуль нечёткого поиска с исправлением опечаток
"""
import json
import os
import re

COMPATIBILITY_FILE = os.path.join(os.path.dirname(__file__), "..", "compatibility.json")


def load_compatibility_data():
    """Загружает базу совместимости стёкол"""
    with open(COMPATIBILITY_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_compatibility_data(data):
    """Сохраняет базу совместимости стёкол"""
    with open(COMPATIBILITY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def levenshtein_distance(s1, s2):
    """Расстояние Левенштейна (сколько символов нужно заменить)"""
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
    
    if len(s2) == 0:
        return len(s1)
    
    prev_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        curr_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = prev_row[j + 1] + 1
            deletions = curr_row[j] + 1
            substitutions = prev_row[j] + (c1 != c2)
            curr_row.append(min(insertions, deletions, substitutions))
        prev_row = curr_row
    
    return prev_row[-1]


def normalize_text(text):
    """Нормализация текста: убираем регистр, лишние пробелы"""
    text = text.lower().strip()
    text = re.sub(r'\s+', ' ', text)
    return text


def find_compatible_models(user_input, compatibility_groups=None):
    """
    Умный поиск с нечётким совпадением.
    
    1. Сначала точное совпадение
    2. Потом нечёткое (допускает опечатки)
    3. Возвращает группу моделей + степень совпадения
    """
    if compatibility_groups is None:
        compatibility_groups = load_compatibility_data()
    
    user_normalized = normalize_text(user_input)
    
    # === Шаг 1: Точное совпадение ===
    for group in compatibility_groups.values():
        for model in group:
            if user_normalized in model.lower():
                return {
                    "found": True,
                    "models": group,
                    "exact_match": True,
                    "matched_model": model,
                    "confidence": 1.0
                }
    
    # === Шаг 2: Нечёткое совпадение (допускает 1-2 ошибки) ===
    best_match = None
    best_score = 0
    
    for group in compatibility_groups.values():
        for model in group:
            model_normalized = normalize_text(model)
            
            # Расстояние Левенштейна
            distance = levenshtein_distance(user_normalized, model_normalized)
            max_len = max(len(user_normalized), len(model_normalized))
            
            if max_len == 0:
                continue
            
            similarity = 1 - (distance / max_len)
            
            # Если совпадение > 70% — считаем найденным
            if similarity > 0.7 and similarity > best_score:
                best_score = similarity
                best_match = {
                    "found": True,
                    "models": group,
                    "exact_match": False,
                    "matched_model": model,
                    "confidence": similarity
                }
    
    # Если нашли нечёткое совпадение
    if best_match:
        return best_match
    
    # === Шаг 3: Проверка по ключевым словам ===
    # Например "айфон 15" → "iphone 15"
    keywords = user_normalized.split()
    
    for group in compatibility_groups.values():
        for model in group:
            model_lower = model.lower()
            matches = sum(1 for kw in keywords if kw in model_lower or _translate_keyword(kw) in model_lower)
            
            if matches == len(keywords):
                return {
                    "found": True,
                    "models": group,
                    "exact_match": False,
                    "matched_model": model,
                    "confidence": 0.8,
                    "keyword_match": True
                }
    
    return {"found": False}


def _translate_keyword(keyword):
    """Перевод популярных ключевых слов"""
    translations = {
        "айфон": "iphone",
        "самсунг": "samsung",
        "сяоми": "xiaomi",
        "редми": "redmi",
        "поко": "poco",
        "реалми": "realme",
        "хоноу": "honor",
        "хонор": "honor",
        "текно": "tecno",
        "инфиникс": "infinix",
        "галaxи": "galaxy",
        "галакси": "galaxy",
        "про": "pro",
        "плюс": "plus",
        "мини": "mini",
        "ультра": "ultra",
        "супер": "super",
    }
    return translations.get(keyword, keyword)


def get_suggestions(query, compatibility_groups=None, limit=5):
    """Получить подсказки для ввода"""
    if compatibility_groups is None:
        compatibility_groups = load_compatibility_data()
    
    query_normalized = normalize_text(query)
    suggestions = []
    
    for group in compatibility_groups.values():
        for model in group:
            if query_normalized in model.lower():
                suggestions.append(model)
                if len(suggestions) >= limit:
                    return suggestions
    
    # Если мало — добавляем нечёткие
    if len(suggestions) < limit:
        for group in compatibility_groups.values():
            for model in group:
                if model not in suggestions:
                    distance = levenshtein_distance(query_normalized, normalize_text(model))
                    if distance <= 3:
                        suggestions.append(model)
                        if len(suggestions) >= limit:
                            return suggestions
    
    return suggestions


def get_all_models_list(compatibility_groups=None):
    """Получить плоский список всех моделей"""
    if compatibility_groups is None:
        compatibility_groups = load_compatibility_data()
    
    models = []
    for group in compatibility_groups.values():
        models.extend(group)
    
    return sorted(set(models))


def get_all_brands(compatibility_groups=None):
    """Получить список брендов"""
    if compatibility_groups is None:
        compatibility_groups = load_compatibility_data()
    
    brands = set()
    for group in compatibility_groups.values():
        for model in group:
            # Извлекаем бренд (первое слово)
            brand = model.split()[0]
            brands.add(brand)
    
    return sorted(brands)


def add_models_to_group(group_name, models):
    """Добавить новую группу моделей"""
    data = load_compatibility_data()
    data[group_name] = models
    save_compatibility_data(data)
    return data


def remove_group(group_name):
    """Удалить группу моделей"""
    data = load_compatibility_data()
    if group_name in data:
        del data[group_name]
        save_compatibility_data(data)
        return True
    return False


def get_all_groups():
    """Возвращает все группы моделей"""
    return load_compatibility_data()
