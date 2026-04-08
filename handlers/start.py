"""
Обработчики /start и /feedback
"""
from telegram import Update
from telegram.ext import ContextTypes
from database import add_or_update_user, get_user
from config import get_text, ADMIN_ID


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    user = update.effective_user

    # Сохраняем пользователя в БД
    add_or_update_user(
        user_id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        language_code=user.language_code
    )

    lang = user.language_code or "ru"
    context.user_data["lang"] = lang

    # Проверяем не заблокирован ли
    db_user = get_user(user.id)
    if db_user and db_user.get("is_blocked"):
        await update.message.reply_text(get_text(lang, "no_access"))
        return

    text = get_text(lang, "start")
    await update.message.reply_text(text, parse_mode="Markdown")


async def feedback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /feedback"""
    lang = context.user_data.get("lang", "ru")

    context.user_data["waiting_feedback"] = True
    await update.message.reply_text(get_text(lang, "feedback_prompt"))


async def handle_feedback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка текста отзыва"""
    user_input = update.message.text.strip()
    lang = context.user_data.get("lang", "ru")

    # Отправляем админу
    from telegram import Bot
    bot = update.effective_user.get_bot()

    await bot.send_message(
        chat_id=ADMIN_ID,
        text=f"📩 Новый отзыв:\n\n"
             f"👤 От: {update.effective_user.full_name}\n"
             f"📛 Username: @{update.effective_user.username or 'нет'}\n"
             f"🆔 ID: {update.effective_user.id}\n\n"
             f"💬 Сообщение:\n{user_input}"
    )

    await update.message.reply_text(get_text(lang, "feedback_thanks"))
    context.user_data["waiting_feedback"] = False
