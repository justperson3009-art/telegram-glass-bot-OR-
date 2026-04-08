"""
Модуль работы с файлами категорий
Каждая категория — отдельный JSON файл
"""
import json
import os
import re

BASE_DIR = os.path.join(os.path.dirname(__file__), "..")

# Маппинг категорий на файлы
CATEGORY_FILES = {
    "glass": "compatibility_glass.json",
    "case": "compatibility_case.json",
    "display": "compatibility_display.json",
    "battery": "compatibility_battery.json",
    "oca": "compatibility_oca.json",
}


def get_category_file(category):
    """Получить путь к файлу категории"""
    return os.path.join(BASE_DIR, CATEGORY_FILES.get(category, "compatibility_glass.json"))


def load_category(category):
    """Загрузить данные категории"""
    filepath = get_category_file(category)
    if not os.path.exists(filepath):
        return {}
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def save_category(category, data):
    """Сохранить данные категории"""
    filepath = get_category_file(category)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def load_all_categories():
    """Загрузить все категории в один dict"""
    combined = {}
    for cat in CATEGORY_FILES:
        data = load_category(cat)
        combined.update(data)
    return combined


def add_models_to_category(category, group_name, models):
    """Добавить группу моделей в категорию"""
    data = load_category(category)
    data[group_name] = models
    save_category(category, data)
    return data


def remove_group_from_category(category, group_name):
    """Удалить группу из категории"""
    data = load_category(category)
    if group_name in data:
        del data[group_name]
        save_category(category, data)
        return True
    return False


def get_all_groups_in_category(category):
    """Получить все группы в категории"""
    return load_category(category)


def get_all_models_count():
    """Посчитать общее количество моделей"""
    total = 0
    for cat in CATEGORY_FILES:
        data = load_category(cat)
        total += sum(len(m) for m in data.values())
    return total


def get_groups_count():
    """Посчитать общее количество групп"""
    total = 0
    for cat in CATEGORY_FILES:
        data = load_category(cat)
        total += len(data)
    return total


def get_category_stats():
    """Статистика по всем категориям"""
    stats = {}
    for cat, filename in CATEGORY_FILES.items():
        data = load_category(cat)
        stats[cat] = {
            "file": filename,
            "groups": len(data),
            "models": sum(len(m) for m in data.values()),
        }
    return stats


# === НЕЧЁТКИЙ ПОИСК (для любой категории) ===

def levenshtein_distance(s1, s2):
    """Расстояние Левенштейна"""
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
    """Нормализация текста"""
    text = text.lower().strip()
    text = re.sub(r'\s+', ' ', text)
    return text


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
        "галакси": "galaxy",
        "про": "pro",
        "плюс": "plus",
        "мини": "mini",
        "ультра": "ultra",
    }
    return translations.get(keyword, keyword)


def find_compatible_models_in_category(category, user_input):
    """Поиск моделей в конкретной категории"""
    data = load_category(category)
    user_normalized = normalize_text(user_input)

    # Шаг 1: Точное совпадение
    for group in data.values():
        for model in group:
            if user_normalized in model.lower():
                return {
                    "found": True,
                    "models": group,
                    "exact_match": True,
                    "matched_model": model,
                    "confidence": 1.0
                }

    # Шаг 2: Ключевые слова
    keywords = user_normalized.split()
    if len(keywords) >= 2:
        for group in data.values():
            for model in group:
                model_lower = model.lower()
                matches = sum(1 for kw in keywords if kw in model_lower or _translate_keyword(kw) in model_lower)
                if matches == len(keywords):
                    return {
                        "found": True,
                        "models": group,
                        "exact_match": True,
                        "matched_model": model,
                        "confidence": 0.95,
                        "keyword_match": True
                    }

    # Шаг 3: Нечёткое совпадение
    best_match = None
    best_score = 0

    for group in data.values():
        for model in group:
            model_normalized = normalize_text(model)
            distance = levenshtein_distance(user_normalized, model_normalized)
            max_len = max(len(user_normalized), len(model_normalized))
            if max_len == 0:
                continue
            similarity = 1 - (distance / max_len)
            if similarity > 0.7 and similarity > best_score:
                best_score = similarity
                best_match = {
                    "found": True,
                    "models": group,
                    "exact_match": False,
                    "matched_model": model,
                    "confidence": similarity
                }

    if best_match:
        return best_match

    return {"found": False}
