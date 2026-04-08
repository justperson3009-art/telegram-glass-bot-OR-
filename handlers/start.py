"""
Обработчики /start, категории и /feedback
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database import add_or_update_user, get_user, set_user_category, get_user_role
from config import get_text, ADMIN_ID, CATEGORIES, SECRET_ADMIN_WORD
from keyboards import get_keyboard_by_role


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start — показывает текстовое меню"""
    user = update.effective_user

    add_or_update_user(
        user_id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        language_code=user.language_code
    )

    # ADMIN_ID автоматически получает роль admin
    if user.id == ADMIN_ID:
        from database import set_user_role
        set_user_role(user.id, "admin")

    lang = user.language_code or "ru"
    context.user_data["lang"] = lang
    context.user_data["category"] = "glass"
    set_user_category(user.id, "glass")

    role = get_user_role(user.id)
    keyboard = get_keyboard_by_role(role)
    text = get_text(lang, "start")

    await update.message.reply_text(text, reply_markup=keyboard, parse_mode="Markdown")


async def category_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка нажатия текстовой кнопки категории"""
    user_input = update.message.text.strip()
    user_id = update.effective_user.id

    category_map = {
        "🔍 Подбор стёкол": "glass",
        "📱 Чехлы": "case",
        "🖥️ Дисплеи": "display",
        "🔋 АКБ": "battery",
        "🧴 Переклейка": "oca",
    }

    category = category_map.get(user_input)
    if not category:
        return

    context.user_data["category"] = category
    set_user_category(user_id, category)

    cat_info = CATEGORIES.get(category)
    if not cat_info:
        return

    role = get_user_role(user_id)
    keyboard = get_keyboard_by_role(role)

    if cat_info["active"]:
        text = f"{cat_info['emoji']} **{cat_info['label']}**\n\n{cat_info['hint']}"
        await update.message.reply_text(text, reply_markup=keyboard, parse_mode="Markdown")
    else:
        text = f"{cat_info['emoji']} **{cat_info['label']}**\n\n{cat_info['hint']}"
        await update.message.reply_text(text, reply_markup=keyboard, parse_mode="Markdown")


async def status_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка кнопки 👤 Мой статус"""
    user_id = update.effective_user.id

    from database import get_user, get_subscription
    db_user = get_user(user_id)

    if not db_user:
        text = "⚠️ Вы ещё не зарегистрированы в системе."
    else:
        total = db_user.get("total_searches", 0)
        category = db_user.get("active_category", "glass")
        cat_info = CATEGORIES.get(category, {})
        cat_label = cat_info.get("label", category)
        role = db_user.get("role", "user")
        role_names = {"admin": "👑 Админ", "helper": "🔧 Помощник", "user": "👤 Пользователь"}
        role_name = role_names.get(role, role)

        sub = get_subscription(user_id)
        sub_text = "Бесплатный"
        if sub and sub.get("is_active"):
            sub_text = f"{sub.get('plan', 'free').upper()} (до {sub.get('expires_at', '?')[:10]})"

        text = (
            f"👤 **Ваш статус:**\n\n"
            f"🎭 Роль: **{role_name}**\n"
            f"📊 Всего поисков: **{total}**\n"
            f"📂 Категория: **{cat_label}**\n"
            f"💳 Подписка: **{sub_text}**\n"
            f"🆔 ID: `{user_id}`"
        )

    role = get_user_role(user_id)
    keyboard = get_keyboard_by_role(role)

    await update.message.reply_text(text, reply_markup=keyboard, parse_mode="Markdown")


async def secret_admin_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Скрытый вход в админку по секретному слову"""
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        return

    context.user_data["admin_state"] = "admin_panel"

    from database import set_user_role
    set_user_role(user_id, "admin")

    from keyboards import get_admin_keyboard
    text = (
        "👑 **Панель администратора**\n\n"
        "Выберите действие:"
    )
    from keyboards import get_admin_panel_keyboard
    await update.message.reply_text(text, reply_markup=get_admin_panel_keyboard(), parse_mode="Markdown")


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
