"""
Главный файл бота — сборка всех модулей
"""
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from telegram.request import HTTPXRequest

from config import BOT_TOKEN, PROXY_URL, SECRET_ADMIN_WORD, ADMIN_ID
from database import init_db, add_or_update_user, get_user, get_user_role, set_user_role
from handlers.start import (
    start_handler, feedback_handler, handle_feedback,
    category_button_handler, status_button_handler, secret_admin_handler
)
from handlers.search import (
    search_handler,
    history_callback, popular_callback, back_to_main_callback,
    feedback_yes_callback, feedback_no_callback
)
from handlers import admin as admin_handler
from keyboards import (
    get_keyboard_by_role, get_admin_panel_keyboard, get_add_models_keyboard,
    get_helpers_keyboard
)
from utils.logger import logger, log_error
from utils.backup import backup_compatibility_json, backup_database
import asyncio


def create_app():
    """Создаёт и настраивает приложение бота"""
    request = HTTPXRequest(
        connection_pool_size=8,
        connect_timeout=60,
        read_timeout=60,
        write_timeout=60,
        pool_timeout=60,
    )

    app = ApplicationBuilder().token(BOT_TOKEN).request(request).build()

    init_db()

    # Команды
    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(CommandHandler("feedback", feedback_handler))

    # Inline callbacks
    app.add_handler(CallbackQueryHandler(feedback_yes_callback, pattern="^feedback_yes_"))
    app.add_handler(CallbackQueryHandler(feedback_no_callback, pattern="^feedback_no_"))
    app.add_handler(CallbackQueryHandler(history_callback, pattern="^my_history"))
    app.add_handler(CallbackQueryHandler(popular_callback, pattern="^popular_searches"))
    app.add_handler(CallbackQueryHandler(back_to_main_callback, pattern="^back_to_main"))

    # Основной обработчик сообщений
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_main_message))

    # Обработка ошибок
    app.add_error_handler(error_handler)

    return app


async def handle_main_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Главный обработчик всех текстовых сообщений"""
    user_id = update.effective_user.id
    user_input = update.message.text.strip()

    add_or_update_user(
        user_id=user_id,
        username=update.effective_user.username,
        first_name=update.effective_user.first_name,
        last_name=update.effective_user.last_name,
        language_code=update.effective_user.language_code
    )

    role = get_user_role(user_id)

    # === ПРОВЕРКА КНОПОК В ПЕРВУЮ ОЧЕРЕДЬ ===

    # Кнопка возврата в меню
    if user_input == "🏠 В меню":
        context.user_data["admin_state"] = None
        keyboard = get_keyboard_by_role(role)
        await update.message.reply_text("🏠 Главное меню", reply_markup=keyboard)
        return

    # Кнопка назад
    if user_input == "⬅️ Назад":
        state = context.user_data.get("admin_state")
        if state in ("add_models", "add_glass", "add_case", "add_display", "add_battery", "add_oca"):
            await admin_handler.show_add_models(update, context)
        elif state in ("helpers_menu", "add_helper", "remove_helper"):
            await admin_handler.show_helpers(update, context)
        else:
            await admin_handler.go_back_to_admin(update, context)
        return

    # Кнопки админ-панели
    if user_input == "📊 Статистика бота":
        await admin_handler.show_admin_stats(update, context)
        return

    if user_input == "👥 Подписки":
        await admin_handler.show_subscriptions(update, context)
        return

    if user_input == "➕ Добавить модели":
        await admin_handler.show_add_models(update, context)
        return

    if user_input == "👤 Помощники":
        await admin_handler.show_helpers(update, context)
        return

    if user_input == "📩 Рассылка":
        await admin_handler.show_broadcast(update, context)
        return

    if user_input == "🚫 Блок/Разблок":
        await admin_handler.show_block_unblock(update, context)
        return

    # Кнопки помощников
    if user_input == "👥 Список помощников":
        await admin_handler.list_helpers(update, context)
        return

    if user_input == "➕ Назначить помощника":
        await admin_handler.assign_helper(update, context)
        return

    if user_input == "🚫 Снять помощника":
        await admin_handler.remove_helper(update, context)
        return

    # Кнопки добавления моделей
    if user_input == "🔍 Добавить стёкла":
        await admin_handler.add_glass_handler(update, context)
        return

    if user_input == "📱 Добавить чехлы":
        context.user_data["admin_state"] = "add_case"
        context.user_data["add_category"] = "case"
        await update.message.reply_text(
            "📱 **Добавить чехлы**\n\nФормат: `группа: модель1, модель2`\n\n⬅️ Назад",
            reply_markup=get_add_models_keyboard(), parse_mode="Markdown"
        )
        return

    if user_input == "🖥️ Добавить дисплеи":
        context.user_data["admin_state"] = "add_display"
        context.user_data["add_category"] = "display"
        await update.message.reply_text(
            "🖥️ **Добавить дисплеи**\n\nФормат: `группа: модель1, модель2`\n\n⬅️ Назад",
            reply_markup=get_add_models_keyboard(), parse_mode="Markdown"
        )
        return

    if user_input == "🔋 Добавить АКБ":
        context.user_data["admin_state"] = "add_battery"
        context.user_data["add_category"] = "battery"
        await update.message.reply_text(
            "🔋 **Добавить АКБ**\n\nФормат: `группа: модель1, модель2`\n\n⬅️ Назад",
            reply_markup=get_add_models_keyboard(), parse_mode="Markdown"
        )
        return

    if user_input == "🧴 Добавить переклейку":
        context.user_data["admin_state"] = "add_oca"
        context.user_data["add_category"] = "oca"
        await update.message.reply_text(
            "🧴 **Добавить переклейку**\n\nФормат: `группа: модель1, модель2`\n\n⬅️ Назад",
            reply_markup=get_add_models_keyboard(), parse_mode="Markdown"
        )
        return

    # Управление (админ)
    if user_input == "⚡ Управление":
        if role == "admin":
            context.user_data["admin_state"] = "admin_panel"
            text = "👑 **Панель администратора**\n\nВыберите действие:"
            await update.message.reply_text(text, reply_markup=get_admin_panel_keyboard(), parse_mode="Markdown")
        return

    # Добавить в базу (помощник)
    if user_input == "➕ Добавить в базу":
        if role in ("admin", "helper"):
            await admin_handler.show_add_models(update, context)
        return

    # Скрытый вход в админку
    if user_input == SECRET_ADMIN_WORD:
        await secret_admin_handler(update, context)
        return

    # Проверяем не ждём ли мы отзыв
    if context.user_data.get("waiting_feedback"):
        await handle_feedback(update, context)
        return

    # Проверяем админ-состояние (ввод данных: группы, модели, ID)
    if context.user_data.get("admin_state") is not None:
        await admin_handler.handle_admin_input(update, context)
        return

    # Проверяем не заблокирован ли
    db_user = get_user(user_id)
    if db_user and db_user.get("is_blocked"):
        await update.message.reply_text("⛔ Бот заблокировал вам доступ.")
        return

    # Проверяем текстовые кнопки категорий
    category_buttons = ["🔍 Подбор стёкол", "📱 Чехлы", "🖥️ Дисплеи", "🔋 АКБ", "🧴 Переклейка"]
    if user_input in category_buttons:
        await category_button_handler(update, context)
        return

    if user_input == "👤 Мой статус":
        await status_button_handler(update, context)
        return

    # Обычный поиск
    try:
        await search_handler(update, context)
    except Exception as e:
        log_error(e, {"user_id": user_id, "query": user_input})
        await update.message.reply_text("❌ Произошла ошибка. Попробуйте ещё раз.")


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка ошибок"""
    error = context.error
    log_error(error, {"update": str(update)})
    try:
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"⚠️ **Ошибка в боте:**\n\n`{error}`",
            parse_mode="Markdown"
        )
    except:
        pass


def main():
    """Запуск бота"""
    try:
        backup_compatibility_json()
        backup_database()
        logger.info("Бэкапы созданы при запуске")
    except Exception as e:
        logger.warning(f"Не удалось создать бэкап: {e}")

    app = create_app()
    logger.info("🤖 Бот запущен...")
    print("🤖 Бот запущен...")
    app.run_polling(drop_pending_updates=True, poll_interval=1.0)


if __name__ == "__main__":
    main()
