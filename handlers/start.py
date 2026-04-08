"""
Обработчики /start и /feedback
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database import add_or_update_user, get_user, set_user_category
from config import get_text, ADMIN_ID, CATEGORIES, SECRET_ADMIN_WORD


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start — показывает категории"""
    user = update.effective_user

    add_or_update_user(
        user_id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        language_code=user.language_code
    )

    lang = user.language_code or "ru"
    context.user_data["lang"] = lang

    db_user = get_user(user.id)
    if db_user and db_user.get("is_blocked"):
        await update.message.reply_text(get_text(lang, "no_access"))
        return

    # Кнопки категорий
    keyboard = []
    row = []
    for key, cat in CATEGORIES.items():
        label = f"{cat['emoji']} {cat['label']}"
        if not cat["active"]:
            label += " 🚧"
        row.append(InlineKeyboardButton(label, callback_data=f"cat_{key}"))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)

    reply_markup = InlineKeyboardMarkup(keyboard)
    text = get_text(lang, "start")

    await update.message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")


async def category_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка выбора категории"""
    query = update.callback_query
    await query.answer()

    category = query.data.replace("cat_", "")
    lang = context.user_data.get("lang", "ru")
    user_id = update.effective_user.id

    cat_info = CATEGORIES.get(category)
    if not cat_info:
        return

    # Сохраняем категорию
    set_user_category(user_id, category)
    context.user_data["category"] = category

    if cat_info["active"]:
        text = f"{cat_info['emoji']} **{cat_info['label']}**\n\n{cat_info['hint']}"
        # Показываем текущую выбранную категорию
        current_row = []
        for key, cat in CATEGORIES.items():
            label = f"{cat['emoji']} {cat['label']}"
            if key == category:
                label += " ✅"
            elif not cat["active"]:
                label += " 🚧"
            current_row.append(InlineKeyboardButton(label, callback_data=f"cat_{key}"))
            if len(current_row) == 2:
                keyboard = [current_row]
                current_row = []
        if current_row:
            keyboard.append(current_row)
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.edit_text(text, reply_markup=reply_markup, parse_mode="Markdown")
    else:
        text = f"{cat_info['emoji']} **{cat_info['label']}**\n\n{cat_info['hint']}"
        await query.message.edit_text(text, parse_mode="Markdown")


async def secret_admin_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Скрытый вход в админку по секретному слову"""
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        return  # Игнорируем для обычных пользователей

    # Переходим в режим админки
    context.user_data["admin_state"] = "panel"

    from handlers.admin import admin_panel
    await admin_panel(update, context)


async def feedback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /feedback"""
    lang = context.user_data.get("lang", "ru")
    context.user_data["waiting_feedback"] = True
    await update.message.reply_text(get_text(lang, "feedback_prompt"))


async def handle_feedback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка текста отзыва"""
    user_input = update.message.text.strip()
    lang = context.user_data.get("lang", "ru")

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
