# 🃏 Шпаргалка — Telegram Glass Bot

## Быстрый старт

### Компьютер (изменения кода):
```powershell
git add -A
git commit -m "описание"
git push
```

### Сервер (обновление):
```bash
cd /opt/glass-bot && bash deploy.sh
```

---

## Команды бота

| Команда | Описание |
|---|---|
| `/start` | Главное меню с кнопками брендов |
| `/feedback` | Оставить отзыв |
| `/admin` | Админ-панель (только ADMIN_ID) |

---

## Админ-панель (/admin)

📊 Статистика — пользователи, поиски, активность
➕ Добавить группу — новые модели стёкол
🗑 Удалить группу — удалить старые модели
📩 Рассылка — сообщение всем пользователям
👥 Пользователи — список + блокировка
🔥 Популярное — топ запросов за неделю
💾 Бэкапы — создание и просмотр
⚙️ Настройки — партнёрские ссылки

---

## Структура файлов

```
/opt/glass-bot/
├── main.py              # Запуск бота
├── config.py            # Настройки
├── .env                 # Токен + ADMIN_ID
├── compatibility.json   # База стёкол
├── bot.db               # SQLite БД
├── deploy.sh            # Скрипт деплоя
├── logs/                # Логи
└── backups/             # Бэкапы
```

---

## Логи

```bash
# Логи бота
tail -f logs/bot.log

# Ошибки
tail -f logs/errors.log
```

---

## Если бот упал

```bash
# Перезапуск
cd /opt/glass-bot && bash deploy.sh

# Или вручную
pkill -f "python.*main.py"
nohup python3 main.py > logs/bot.log 2>&1 &
```

---

## Бэкапы

```bash
# Посмотреть
ls -la backups/

# Восстановить БД
cp backups/bot_20260407_*.db bot.db

# Восстановить стёкла
cp backups/compatibility_20260407_*.json compatibility.json
```
