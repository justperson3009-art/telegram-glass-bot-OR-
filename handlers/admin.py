"""
Админ-панель — полностью текстовое меню
"""
from telegram import Update
from telegram.ext import ContextTypes
from config import ADMIN_ID, get_text
from database import (
    get_user_stats, get_all_users, block_user, unblock_user,
    add_broadcast, get_broadcast_stats, get_popular_searches,
    get_setting, set_setting, get_feedback_stats, get_latest_feedback,
    get_helpers, set_user_role, get_user_role, add_subscription,
    get_subscription_stats, is_admin as db_is_admin
)
from utils.search import get_all_groups, add_models_to_group, remove_group
from utils.backup import backup_compatibility_json, backup_database, get_backup_list
from keyboards import (
    get_admin_panel_keyboard, get_add_models_keyboard,
    get_helpers_keyboard, get_admin_keyboard, get_keyboard_by_role
)
from utils.logger import log_broadcast, logger

# FSM состояния админки
WAITING_GROUP_NAME, WAITING_MODELS_LIST, WAITING_BLOCK_USER_ID, WAITING_BROADCAST_TEXT = range(4)
WAITING_ADD_HELPER_ID, WAITING_REMOVE_HELPER_ID = range(4, 6)
WAITING_ADD_GLASS, WAITING_ADD_CASE, WAITING_ADD_DISPLAY, WAITING_ADD_BATTERY, WAITING_ADD_OCA = range(6, 11)


def is_admin(user_id):
    return user_id == ADMIN_ID


async def show_admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Статистика бота"""
    msg = update.message if update.message else getattr(update, 'callback_query', None)
    if not msg:
        return
    send = msg.reply_text if hasattr(msg, 'reply_text') else msg.edit_text

    stats = get_user_stats()
    feedback = get_feedback_stats()
    subs = get_subscription_stats()
    groups = get_all_groups()

    text = (
        f"📊 **Статистика бота:**\n\n"
        f"👥 Активных: **{stats['active']}**\n"
        f"🚫 Заблокированных: **{stats['blocked']}**\n"
        f"🔍 Всего поисков: **{stats['total_searches']}**\n"
        f"📱 Моделей в базе: **{sum(len(m) for m in groups.values())}**\n"
        f"📦 Групп: **{len(groups)}**\n\n"
        f"📈 Активность:\n"
        f"  • Сегодня: **{stats['today_active']}**\n"
        f"  • Неделя: **{stats['week_active']}**\n\n"
        f"✅ Обратная связь:\n"
        f"  • Подошло: **{feedback['positive']}**\n"
        f"  • Не подошло: **{feedback['negative']}**\n"
        f"  • Точность: **{feedback['percent']}%**\n\n"
        f"💳 Подписки:\n"
        f"  • Активных: **{subs['active_subscriptions']}**\n"
        f"  • Бесплатных: **{subs['free_users']}**\n"
    )

    await send(text, reply_markup=get_admin_panel_keyboard(), parse_mode="Markdown")


async def show_subscriptions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Статистика подписок"""
    msg = update.message if update.message else getattr(update, 'callback_query', None)
    if not msg:
        return
    send = msg.reply_text if hasattr(msg, 'reply_text') else msg.edit_text

    subs = get_subscription_stats()
    text = (
        f"💳 **Подписки:**\n\n"
        f"👥 Всего пользователей: **{subs['total_users']}**\n"
        f"✅ Активных подписок: **{subs['active_subscriptions']}**\n"
        f"🆓 Бесплатных: **{subs['free_users']}**\n\n"
    )
    if subs['plans']:
        text += "**По планам:**\n"
        for plan, cnt in subs['plans'].items():
            text += f"  • {plan}: **{cnt}**\n"
    else:
        text += "📭 Подписок пока нет."

    await send(text, reply_markup=get_admin_panel_keyboard(), parse_mode="Markdown")


async def show_add_models(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Меню добавления моделей"""
    msg = update.message if update.message else getattr(update, 'callback_query', None)
    if not msg:
        return
    send = msg.reply_text if hasattr(msg, 'reply_text') else msg.edit_text

    await send("📦 **Добавить модели в базу:**\n\nВыберите категорию:", reply_markup=get_add_models_keyboard(), parse_mode="Markdown")


async def add_glass_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Добавить стёкла"""
    context.user_data["admin_state"] = WAITING_ADD_GLASS
    context.user_data["add_category"] = "glass"
    await update.message.reply_text(
        "🔍 **Добавить стёкла**\n\n"
        "Формат: `название_группы: модель1, модель2, модель3`\n\n"
        "Пример: `samsung_a55_group: Samsung A55, Samsung A55 5G, Samsung A54`\n\n"
        "Или просто список моделей (группа создастся автоматически):\n`iPhone 16, iPhone 16 Pro, iPhone 16 Pro Max`\n\n"
        "⬅️ Назад — вернуться",
        reply_markup=get_add_models_keyboard(),
        parse_mode="Markdown"
    )


async def show_helpers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Меню помощников"""
    msg = update.message if update.message else getattr(update, 'callback_query', None)
    if not msg:
        return
    send = msg.reply_text if hasattr(msg, 'reply_text') else msg.edit_text
    await send("👤 **Управление помощниками:**", reply_markup=get_helpers_keyboard(), parse_mode="Markdown")


async def list_helpers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Список помощников"""
    helpers = get_helpers()
    if not helpers:
        text = "👥 Помощников пока нет."
    else:
        text = "👥 **Помощники:**\n\n"
        for h in helpers:
            name = h.get("first_name") or h.get("username") or f"ID:{h['user_id']}"
            text += f"• {name} (ID: `{h['user_id']}`)\n"

    await update.message.reply_text(text, reply_markup=get_helpers_keyboard(), parse_mode="Markdown")


async def assign_helper(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Назначить помощника"""
    context.user_data["admin_state"] = "helper_add"
    text = (
        "➕ **Назначить помощника**\n\n"
        "Введите ID пользователя или перешлите его сообщение.\n\n"
        "Чтобы узнать ID пользователя:\n"
        "1. Попросите его написать /start\n"
        "2. Введите его числовой ID\n\n"
        "Пример: `5164389862`\n\n"
        "⬅️ Назад — отмена"
    )
    await update.message.reply_text(text, reply_markup=get_helpers_keyboard(), parse_mode="Markdown")


async def remove_helper(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Снять помощника"""
    context.user_data["admin_state"] = "helper_remove"
    await update.message.reply_text("🚫 Введите ID пользователя для снятия с роли помощника:\n\n⬅️ Назад — отмена")


async def show_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Рассылка"""
    context.user_data["admin_state"] = WAITING_BROADCAST_TEXT
    await update.message.reply_text("📩 Введите текст рассылки:\n\n⬅️ Назад — отмена")


async def show_block_unblock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Блокировка/разблокировка"""
    context.user_data["admin_state"] = WAITING_BLOCK_USER_ID
    await update.message.reply_text(
        "🚫 **Блокировка/Разблокировка**\n\n"
        "Формат: `block 123456789` или `unblock 123456789`\n\n"
        "⬅️ Назад — отмена"
    )


async def go_back_to_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Назад в админ-панель"""
    context.user_data["admin_state"] = "admin_panel"
    text = "👑 **Панель администратора**\n\nВыберите действие:"
    await update.message.reply_text(text, reply_markup=get_admin_panel_keyboard(), parse_mode="Markdown")


async def handle_admin_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка ввода в админ-панели"""
    state = context.user_data.get("admin_state")
    user_input = update.message.text.strip()
    user_id = update.effective_user.id

    if user_input == "⬅️ Назад" or user_input == "🏠 В меню":
        if state in (WAITING_ADD_GLASS, WAITING_ADD_CASE, WAITING_ADD_DISPLAY, WAITING_ADD_BATTERY, WAITING_ADD_OCA):
            await show_add_models(update, context)
        elif state in (WAITING_ADD_HELPER_ID, WAITING_REMOVE_HELPER_ID):
            await show_helpers(update, context)
        else:
            await go_back_to_admin(update, context)
        return

    if state == WAITING_ADD_GLASS:
        _handle_add_model(update, context, "glass")
    elif state == WAITING_ADD_CASE:
        _handle_add_model(update, context, "case")
    elif state == WAITING_ADD_DISPLAY:
        _handle_add_model(update, context, "display")
    elif state == WAITING_ADD_BATTERY:
        _handle_add_model(update, context, "battery")
    elif state == WAITING_ADD_OCA:
        _handle_add_model(update, context, "oca")
    elif state == "helper_add":
        try:
            helper_id = int(user_input)
            set_user_role(helper_id, "helper")
            await update.message.reply_text(f"✅ Пользователь `{helper_id}` назначен помощником!", reply_markup=get_helpers_keyboard(), parse_mode="Markdown")
        except ValueError:
            await update.message.reply_text("❌ Введите корректный ID (число).")
    elif state == "helper_remove":
        try:
            helper_id = int(user_input)
            set_user_role(helper_id, "user")
            await update.message.reply_text(f"✅ Пользователь `{helper_id}` снят с роли помощника.", reply_markup=get_helpers_keyboard(), parse_mode="Markdown")
        except ValueError:
            await update.message.reply_text("❌ Введите корректный ID (число).")
    elif state == WAITING_BLOCK_USER_ID:
        parts = user_input.split()
        if len(parts) == 2:
            action, target_id = parts[0], int(parts[1])
            if action == "block":
                block_user(target_id)
                await update.message.reply_text(f"✅ Пользователь `{target_id}` заблокирован.", reply_markup=get_admin_panel_keyboard(), parse_mode="Markdown")
            elif action == "unblock":
                unblock_user(target_id)
                await update.message.reply_text(f"✅ Пользователь `{target_id}` разблокирован.", reply_markup=get_admin_panel_keyboard(), parse_mode="Markdown")
        else:
            await update.message.reply_text("❌ Формат: `block ID` или `unblock ID`")
    elif state == WAITING_BROADCAST_TEXT:
        users = get_all_users(active_only=True)
        sent = failed = 0
        progress = await update.message.reply_text(f"📩 Рассылка... 0/{len(users)}")
        for u in users:
            try:
                await update.message._bot.send_message(chat_id=u["user_id"], text=user_input)
                sent += 1
            except:
                failed += 1
            if (sent + failed) % 10 == 0:
                try:
                    await progress.edit_text(f"📩 Рассылка... {sent + failed}/{len(users)}")
                except:
                    pass
        add_broadcast(user_input, sent, failed)
        log_broadcast(sent, failed)
        await progress.edit_text(f"✅ Рассылка завершена!\n\nОтправлено: {sent}\nОшибок: {failed}", parse_mode="Markdown")
        context.user_data["admin_state"] = "admin_panel"


def _handle_add_model(update, context, category):
    """Обработка добавления моделей"""
    user_input = update.message.text.strip()
    if ":" in user_input:
        group_name, models_str = user_input.split(":", 1)
        models = [m.strip() for m in models_str.split(",")]
    else:
        models = [m.strip() for m in user_input.split(",")]
        group_name = f"{category}_{len(get_all_groups()) + 1}_group"

    add_models_to_group(group_name, models)
    update.message.reply_text(
        f"✅ Добавлено **{len(models)}** моделей в группу `{group_name}`",
        reply_markup=get_add_models_keyboard(),
        parse_mode="Markdown"
    )
    context.user_data["admin_state"] = None


def get_admin_handlers():
    """Возвращает только обработчики без CommandHandler (обрабатывается в main.py)"""
    return []
