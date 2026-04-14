# Автообновление прайса 1-го числа каждого месяца

## Настройка на сервере (Linux)

### 1. Загрузи обновлённый код на сервер:

```bash
cd /opt/glass-bot
git pull origin main
```

### 2. Сделай скрипт исполняемым:

```bash
chmod +x /opt/glass-bot/auto_update_monthly.sh
```

### 3. Создай лог-файл:

```bash
mkdir -p /opt/glass-bot/logs
touch /opt/glass-bot/logs/auto_update.log
```

### 4. Добавь задание в cron:

```bash
crontab -e
```

Добавь строку в конец файла:

```
0 3 1 * * /opt/glass-bot/auto_update_monthly.sh
```

Это запустит обновление **каждое 1-е число в 3:00 утра**.

### 5. Проверь что cron работает:

```bash
crontab -l
```

Должно показать твоё задание.

---

## Тестовый запуск (вручную):

```bash
cd /opt/glass-bot
./auto_update_monthly.sh
```

После этого проверь лог:

```bash
tail -50 /opt/glass-bot/logs/auto_update.log
```

---

## Что делает скрипт:

1. ✅ Обновляет курсы валют (API НБРБ)
2. ✅ Скачивает прайс из Google Sheets
3. ✅ Фильтрует: дисплеи / АКБ / запчасти
4. ✅ Создаёт бэкап текущих баз
5. ✅ Обновляет JSON файлы
6. ✅ Перезапускает бота
7. ✅ Логирует результат

---

## Просмотр логов:

```bash
# Последние 50 строк
tail -50 /opt/glass-bot/logs/auto_update.log

# Все логи за сегодня
grep "$(date '+%Y-%m-%d')" /opt/glass-bot/logs/auto_update.log

# Логи за конкретное число
grep "2026-04-01" /opt/glass-bot/logs/auto_update.log
```

---

## Если нужно обновить чаще:

### Раз в неделю (каждое воскресенье в 3:00):
```
0 3 * * 0 /opt/glass-bot/auto_update_monthly.sh
```

### Раз в 2 недели (понедельник в 3:00):
```
0 3 */14 * 1 /opt/glass-bot/auto_update_monthly.sh
```

### Каждое утро в 3:00:
```
0 3 * * * /opt/glass-bot/auto_update_monthly.sh
```
