# 🚀 Инструкция по деплою на сервер

## 📋 Рабочий процесс

```
[Твой компьютер]          [GitHub]              [Сервер]
      │                      │                      │
      ├── git push ─────────>│                      │
      │                      │                      │
      │                      │<── git pull ───────── │
      │                      │                      │
      │                      │── bash deploy.sh ──> │
      │                      │                      │
      │                      │<── бот запущен!      │
```

---

## 🏗 Первый деплой (настройка сервера)

### Шаг 1: Подключись к серверу
```bash
ssh user@your-server-ip
```

### Шаг 2: Создай директорию и клонируй репозиторий
```bash
sudo mkdir -p /opt/glass-bot
sudo chown $USER:$USER /opt/glass-bot
cd /opt/glass-bot
git clone https://github.com/justperson3009-art/telegram-glass-bot-OR-.git .
```

### Шаг 3: Создай .env файл
```bash
nano .env
```

Вставь:
```
BOT_TOKEN=твой_токен_от_BotFather
ADMIN_ID=5164389862
```

### Шаг 4: Установи зависимости
```bash
pip3 install -r requirements.txt
```

### Шаг 5: Создай директории для логов и бэкапов
```bash
mkdir -p logs backups
```

### Шаг 6: Сделай скрипт деплоя исполняемым
```bash
chmod +x deploy.sh
```

### Шаг 7: Запусти бота
```bash
bash deploy.sh
```

### Шаг 8: Проверь что бот работает
```bash
tail -f logs/bot.log
```

---

## 🔄 Обычное обновление (после изменений кода)

### На компьютере:
```powershell
git add -A
git commit -m "описание изменений"
git push
```

### На сервере:
```bash
cd /opt/glass-bot
bash deploy.sh
```

**Всё!** Скрипт сам:
- ✅ Создаст бэкап
- ✅ Обновит код из Git
- ✅ Установит новые зависимости
- ✅ Перезапустит бота
- ✅ Проверит что всё работает

---

## 📋 Команды на сервере

| Команда | Описание |
|---|---|
| `bash deploy.sh` | Обновить и перезапустить бота |
| `tail -f logs/bot.log` | Смотреть логи бота |
| `tail -f logs/errors.log` | Смотреть ошибки |
| `ls backups/` | Список бэкапов |
| `pkill -f "python.*main.py"` | Остановить бота |
| `nohup python3 main.py > logs/bot.log 2>&1 &` | Запустить бота вручную |

---

## 🔧 Screen (если нужна сессия)

Если `nohup` не работает — используй `screen`:

```bash
# Создать сессию
screen -S glass-bot

# Запустить бота
python3 main.py

# Отключиться (Ctrl+A, затем D)

# Посмотреть сессии
screen -ls

# Подключиться обратно
screen -r glass-bot

# Удалить сессию
screen -S glass-bot -X quit
```

---

## 🛡 Безопасность

- `.env` и `*.db` **не** попадают в Git
- Бэкапы создаются автоматически перед каждым деплоем
- Логи хранятся в папке `logs/`
- Старые бэкапы удаляются через 7 дней

---

## ⚠️ Если что-то пошло не так

### Бот не запускается:
```bash
# Проверь логи
tail -f logs/bot.log
tail -f logs/errors.log

# Проверь .env
cat .env

# Проверь зависимости
pip3 list | grep telegram
```

### Откатить изменения:
```bash
# Посмотреть коммиты
git log --oneline

# Откатиться на предыдущий
git reset --hard HEAD~1

# Перезапустить
bash deploy.sh
```

### Восстановить из бэкапа:
```bash
# Посмотреть бэкапы
ls -la backups/

# Восстановить БД
cp backups/bot_20260407_123456.db bot.db

# Восстановить базу стёкол
cp backups/compatibility_20260407_123456.json compatibility.json
```
