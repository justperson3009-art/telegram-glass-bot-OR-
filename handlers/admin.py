"""
Полная админ-панель с рассылкой, статистикой, управлением
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ConversationHandler
from config import ADMIN_ID, get_text
from database import (
    get_user_stats, get_all_users, block_user, unblock_user,
    add_broadcast, get_broadcast_stats, get_popular_searches,
    get_setting, set_setting, get_feedback_stats, get_latest_feedback
)
from utils.search import get_all_groups, add_models_to_group, remove_group
from utils.backup import backup_compatibility_json, backup_database, get_backup_list, cleanup_old_backups
from utils.logger import log_broadcast, logger
from keyboards import get_admin_keyboard
import asyncio

# Состояния FSM
WAITING_GROUP_NAME, WAITING_MODELS_LIST, WAITING_GROUP_TO_DELETE, WAITING_BROADCAST, WAITING_BLOCK_USER = range(5)


def is_admin(user_id):
    """Проверяет что пользователь — админ"""
    return user_id == ADMIN_ID


async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Главное меню админ-панели — текстовое меню"""
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ У вас нет доступа к этой команде.")
        return

    text = (
        "🔧 **Админ-панель:**\n\n"
        "Выберите действие кнопками ниже или напишите команду:\n\n"
        "📊 Статистика\n"
        "✅ Обратная связь\n"
        "➕ Добавить группу\n"
        "🗑 Удалить группу\n"
        "📩 Рассылка\n"
        "👥 Пользователи\n"
        "🔥 Популярное\n"
        "💾 Бэкапы\n"
        "⚙️ Настройки"
    )

    await update.message.reply_text(text, reply_markup=get_admin_keyboard(), parse_mode="Markdown")


async def admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка кнопок админ-панели"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data == "admin_stats":
        await show_stats(query)
    elif data == "admin_feedback":
        await show_feedback(query)
    elif data == "admin_add_group":
        await query.message.reply_text("📝 Введите название для новой группы (например: samsung_a55_group):")
        context.user_data["admin_state"] = WAITING_GROUP_NAME
    elif data == "admin_delete_group":
        groups = get_all_groups()
        text = "🗑 Доступные группы для удаления:\n\n"
        for i, group_name in enumerate(list(groups.keys())[:20], 1):
            text += f"{i}. `{group_name}`\n"
        if len(groups) > 20:
            text += f"... и ещё {len(groups) - 20}\n"
        text += "\nВведите название группы для удаления:"
        await query.message.reply_text(text, parse_mode="Markdown")
        context.user_data["admin_state"] = WAITING_GROUP_TO_DELETE
    elif data == "admin_broadcast":
        await query.message.reply_text("📩 Введите текст для рассылки всем пользователям бота:")
        context.user_data["admin_state"] = WAITING_BROADCAST
    elif data == "admin_users":
        await show_users(query)
    elif data == "admin_popular":
        await show_popular(query)
    elif data == "admin_backups":
        await show_backups(query)
    elif data == "admin_settings":
        await show_settings(query)


async def show_stats(query):
    """Показывает статистику бота"""
    stats = get_user_stats()
    groups = get_all_groups()
    total_models = sum(len(models) for models in groups.values())
    feedback = get_feedback_stats()

    text = (
        f"📊 **Статистика бота:**\n\n"
        f"👥 Активных пользователей: **{stats['active']}**\n"
        f"🚫 Заблокированных: **{stats['blocked']}**\n"
        f"📱 Всего моделей в базе: **{total_models}**\n"
        f"📦 Групп совместимости: **{len(groups)}**\n"
        f"🔍 Всего поисков: **{stats['total_searches']}**\n\n"
        f"📈 Активность:\n"
        f"  • Сегодня: **{stats['today_active']}**\n"
        f"  • За неделю: **{stats['week_active']}**\n\n"
        f"✅ **Обратная связь:**\n"
        f"  • Подошло: **{feedback['positive']}**\n"
        f"  • Не подошло: **{feedback['negative']}**\n"
        f"  • Точность: **{feedback['percent']}%**\n"
    )

    await query.message.reply_text(text, parse_mode="Markdown")


async def show_feedback(query):
    """Показывает отзывы пользователей"""
    stats = get_feedback_stats()
    latest = get_latest_feedback(limit=15)

    text = (
        f"✅ **Обратная связь:**\n\n"
        f"📊 Всего отзывов: **{stats['total']}**\n"
        f"✅ Подошло: **{stats['positive']}** ({stats['percent']}%)\n"
        f"❌ Не подошло: **{stats['negative']}**\n\n"
    )

    if latest:
        text += "**Последние отзывы:**\n\n"
        for f in latest[:10]:
            emoji = "✅" if f["rating"] == 1 else "❌"
            name = f["first_name"] or f["username"] or "Аноним"
            text += f"{emoji} {name}: `{f['query']}` → `{f['matched_model'][:25]}`\n"

    keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="admin_back")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")


async def show_users(query):
    """Показывает список пользователей"""
    users = get_all_users(active_only=True)
    
    if not users:
        text = "👥 Пользователей пока нет."
    else:
        text = f"👥 **Пользователи ({len(users)}):**\n\n"
        for u in users[:10]:
            name = u["first_name"] or u["username"] or "Аноним"
            text += f"• {name} (ID: `{u['user_id']}`) — {u['total_searches']} поисков\n"
        
        if len(users) > 10:
            text += f"\n... и ещё {len(users) - 10}"
    
    keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="admin_back")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")


async def show_popular(query):
    """Показывает популярные запросы"""
    popular = get_popular_searches(limit=15, days=7)
    
    if not popular:
        text = "🔥 Пока нет популярных запросов."
    else:
        text = "🔥 **Популярные запросы за неделю:**\n\n"
        for i, p in enumerate(popular, 1):
            text += f"{i}. `{p['query']}` — {p['count']} раз\n"
    
    keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="admin_back")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")


async def show_backups(query):
    """Показывает бэкапы"""
    backups = get_backup_list()
    
    if not backups:
        text = "💾 Бэкапов пока нет."
    else:
        text = "💾 **Бэкапы:**\n\n"
        for b in backups[-10:]:
            text += f"• `{b['name']}` ({b['size']}) — {b['date']}\n"
    
    # Кнопки
    keyboard = [
        [InlineKeyboardButton("💾 Создать бэкап", callback_data="admin_create_backup")],
        [InlineKeyboardButton("🔙 Назад", callback_data="admin_back")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")


async def show_settings(query):
    """Показывает настройки"""
    partner_link = get_setting("partner_link", "не установлена")
    
    text = (
        f"⚙️ **Настройки бота:**\n\n"
        f"🔗 Партнёрская ссылка: `{partner_link}`\n\n"
        f"Чтобы изменить ссылку, отправьте:\n"
        f"`/set_partner https://example.com`"
    )
    
    keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="admin_back")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")


async def handle_admin_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка ввода в админ-панели"""
    state = context.user_data.get("admin_state")
    user_input = update.message.text.strip()
    
    if state == WAITING_GROUP_NAME:
        context.user_data["new_group_name"] = user_input
        context.user_data["admin_state"] = WAITING_MODELS_LIST
        await update.message.reply_text(
            f"✅ Группа: {user_input}\n\n"
            f"Теперь введите модели через запятую:\n"
            f"например: Samsung A55, Samsung A55 5G, Samsung A55 Pro"
        )
    
    elif state == WAITING_MODELS_LIST:
        group_name = context.user_data.get("new_group_name")
        models = [m.strip() for m in user_input.split(",")]
        
        add_models_to_group(group_name, models)
        
        await update.message.reply_text(
            f"✅ Группа **{group_name}** добавлена!\n"
            f"Моделей: {len(models)}\n\n"
            f"Используйте /admin чтобы вернуться в меню.",
            parse_mode="Markdown"
        )
        context.user_data["admin_state"] = None
    
    elif state == WAITING_GROUP_TO_DELETE:
        if remove_group(user_input):
            await update.message.reply_text(f"✅ Группа **{user_input}** удалена.", parse_mode="Markdown")
        else:
            await update.message.reply_text(f"❌ Группа {user_input} не найдена.")
        context.user_data["admin_state"] = None
    
    elif state == WAITING_BROADCAST:
        # Рассылка
        users = get_all_users(active_only=True)
        sent = 0
        failed = 0
        
        progress_msg = await update.message.reply_text(f"📩 Рассылка... 0/{len(users)}")
        
        for user in users:
            try:
                await update.message._bot.send_message(
                    chat_id=user["user_id"],
                    text=user_input
                )
                sent += 1
            except Exception as e:
                failed += 1
                logger.error(f"Broadcast failed for user {user['user_id']}: {e}")
            
            # Обновляем прогресс каждые 10
            if (sent + failed) % 10 == 0:
                await progress_msg.edit_text(f"📩 Рассылка... {sent + failed}/{len(users)}")
        
        # Записываем в БД
        add_broadcast(user_input, sent, failed)
        log_broadcast(sent, failed)
        
        await progress_msg.edit_text(
            f"✅ Рассылка завершена!\n\n"
            f"Отправлено: {sent}\n"
            f"Ошибок: {failed}",
            parse_mode="Markdown"
        )
        context.user_data["admin_state"] = None


async def create_backup_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Создание бэкапа"""
    query = update.callback_query
    await query.answer()
    
    compat_backup = backup_compatibility_json()
    db_backup = backup_database()
    
    text = "✅ Бэкапы созданы:\n\n"
    if compat_backup:
        text += f"📦 Compatibility: `{os.path.basename(compat_backup)}`\n"
    if db_backup:
        text += f"🗄 База данных: `{os.path.basename(db_backup)}`\n"
    
    # Чистим старые
    cleanup_old_backups(keep_days=7)
    
    keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="admin_backups")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")


async def admin_back_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Кнопка назад в админке — возвращаем в главное меню админа"""
    query = update.callback_query
    await query.answer()

    # Возвращаем текстовое меню админа
    await query.message.reply_text("🔧 **Админ-панель:**", reply_markup=get_admin_keyboard(), parse_mode="Markdown")


def get_admin_handlers():
    """Возвращает обработчики админ-панели (без MessageHandler!)"""
    return [
        CommandHandler("admin", admin_panel),
        CallbackQueryHandler(admin_callback, pattern="^admin_"),
        CallbackQueryHandler(create_backup_callback, pattern="^admin_create_backup"),
        CallbackQueryHandler(admin_back_callback, pattern="^admin_back$"),
    ]
