#!/bin/bash
# Скрипт автоматического обновления прайса 1-го числа каждого месяца
# Запускать через cron: 0 3 1 * * /opt/glass-bot/auto_update_monthly.sh

set -e

LOG_FILE="/opt/glass-bot/logs/auto_update.log"
BOT_DIR="/opt/glass-bot"

echo "========================================" >> "$LOG_FILE"
echo "$(date '+%Y-%m-%d %H:%M:%S') - НАЧАЛО АВТООБНОВЛЕНИЯ" >> "$LOG_FILE"
echo "========================================" >> "$LOG_FILE"

cd "$BOT_DIR"

# Обновляем курсы валют
echo "$(date '+%Y-%m-%d %H:%M:%S') - Обновляю курсы валют..." >> "$LOG_FILE"
python3 update_currency_rates.py >> "$LOG_FILE" 2>&1

# Обновляем прайс из Google Sheets
echo "$(date '+%Y-%m-%d %H:%M:%S') - Обновляю прайс из Google Sheets..." >> "$LOG_FILE"
python3 update_from_google_sheet.py >> "$LOG_FILE" 2>&1

# Перезапускаем бота
echo "$(date '+%Y-%m-%d %H:%M:%S') - Перезапускаю бота..." >> "$LOG_FILE"
sudo systemctl restart glass-bot >> "$LOG_FILE" 2>&1

# Проверяем статус
if sudo systemctl is-active --quiet glass-bot; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') - ✅ Бот успешно перезапущен" >> "$LOG_FILE"
else
    echo "$(date '+%Y-%m-%d %H:%M:%S') - ❌ ОШИБКА: бот не запустился!" >> "$LOG_FILE"
fi

echo "$(date '+%Y-%m-%d %H:%M:%S') - АВТООБНОВЛЕНИЕ ЗАВЕРШЕНО" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"
