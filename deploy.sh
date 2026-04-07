#!/bin/bash
# =============================================
# 🚀 Скрипт деплоя бота на сервер
# Запускать на сервере: bash deploy.sh
# =============================================

set -e  # Остановка при ошибке

echo "🚀 Начинаю деплой..."

# 1. Переход в директорию бота
cd /opt/glass-bot || { echo "❌ Папка /opt/glass-bot не найдена!"; exit 1; }

# 2. Бэкап перед обновлением
echo "💾 Создаю бэкап..."
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
cp bot.db "backups/bot_${TIMESTAMP}.db" 2>/dev/null || true
cp compatibility.json "backups/compatibility_${TIMESTAMP}.json" 2>/dev/null || true
echo "✅ Бэкап создан"

# 3. Обновление кода
echo "📦 Обновляю код из Git..."
git pull origin main
echo "✅ Код обновлён"

# 4. Установка зависимостей
echo "📚 Устанавливаю зависимости..."
pip3 install --break-system-packages -r requirements.txt --quiet
echo "✅ Зависимости установлены"

# 5. Остановка ТОЛЬКО этого бота (по PID файлу)
echo "⏹️ Останавливаю glass-bot..."
if [ -f glass-bot.pid ]; then
    OLD_PID=$(cat glass-bot.pid)
    kill $OLD_PID 2>/dev/null || true
    sleep 2
fi
# Дополнительная проверка - убить только процесс с нашим путем
pkill -f "python.*glass-bot.*main.py" 2>/dev/null || true
sleep 1
echo "✅ Бот остановлен"

# 6. Запуск НОВОГО бота
echo "▶️ Запускаю glass-bot..."
nohup python3 /opt/glass-bot/main.py > /opt/glass-bot/logs/bot.log 2>&1 &
BOT_PID=$!
echo $BOT_PID > glass-bot.pid
echo "✅ Бот запущен (PID: $BOT_PID)"

# 7. Проверка
sleep 3
if ps -p $BOT_PID > /dev/null 2>&1; then
    echo ""
    echo "✅ ДЕПЛОЙ ЗАВЕРШЁН УСПЕШНО!"
    echo "🤖 Бот работает (PID: $BOT_PID)"
    echo "📜 Логи: tail -f logs/bot.log"
else
    echo ""
    echo "❌ ВНИМАНИЕ! Бот не запустился!"
    echo "📜 Проверь логи: tail -f logs/bot.log"
    exit 1
fi
