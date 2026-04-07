#!/bin/bash
# =============================================
# 📝 Скрипт настройки .env на сервере
# Запускать ОДИН РАЗ при первом деплое
# =============================================

echo "📝 Создаю .env файл..."
echo ""
echo "ВВЕДИ ТОКЕН БОТА (получи у @BotFather):"
read BOT_TOKEN
echo ""
echo "ВВЕДИ ADMIN_ID (получи у @userinfobot):"
read ADMIN_ID
echo ""

cat > .env << ENVOF
# Токен бота
BOT_TOKEN=${BOT_TOKEN}

# ID администратора
ADMIN_ID=${ADMIN_ID}
ENVOF

echo "✅ .env файл создан!"
echo ""
echo "Проверь:"
cat .env
