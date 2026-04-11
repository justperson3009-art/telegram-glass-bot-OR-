# Проверка
pm = "a54 5g"
user = "samsung a54"
user_words = user.split()  # ['samsung', 'a54']
pm_words = pm.split()  # ['a54', '5g']

for uw in user_words:
    check1 = uw in pm
    check2 = any(uw in pw for pw in pm_words)
    print(f"'{uw}' in '{pm}': {check1}")
    print(f"'{uw}' in any pm_word: {check2}")
    print(f"  pm_words: {pm_words}")

# Проблема: 'samsung' НЕ содержится в 'a54 5g' и НЕ содержится ни в одном pm_word
