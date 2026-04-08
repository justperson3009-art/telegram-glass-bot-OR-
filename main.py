"""
Главный файл бота — сборка всех модулей
"""
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from telegram.request import HTTPXRequest

from config import BOT_TOKEN, PROXY_URL, SECRET_ADMIN_WORD
from database import init_db, add_or_update_user, get_user, get_user_category
from handlers.start import start_handler, feedback_handler, handle_feedback, category_callback, back_to_cats_callback, show_menu_callback, secret_admin_handler
from handlers.search import (
    search_handler,
    history_callback, popular_callback, back_to_main_callback,
    feedback_yes_callback, feedback_no_callback
)
from handlers.admin import get_admin_handlers
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
    
    # Инициализация БД
    init_db()
    
    # Команды
    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(CommandHandler("feedback", feedback_handler))

    # Категории (inline callback)
    app.add_handler(CallbackQueryHandler(category_callback, pattern="^cat_"))
    app.add_handler(CallbackQueryHandler(back_to_cats_callback, pattern="^back_to_cats$"))
    app.add_handler(CallbackQueryHandler(show_menu_callback, pattern="^show_menu$"))

    # Админ-панель (убираем /admin — только скрытый вход)
    for handler in get_admin_handlers():
        app.add_handler(handler)

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

    # Сохраняем пользователя
    add_or_update_user(
        user_id=user_id,
        username=update.effective_user.username,
        first_name=update.effective_user.first_name,
        last_name=update.effective_user.last_name,
        language_code=update.effective_user.language_code
    )

    # Скрытый вход в админку
    if user_input == SECRET_ADMIN_WORD:
        await secret_admin_handler(update, context)
        return

    # Проверяем не заблокирован ли
    db_user = get_user(user_id)
    if db_user and db_user.get("is_blocked"):
        await update.message.reply_text("⛔ Бот заблокировал вам доступ.")
        return

    # Проверяем не ждём ли мы отзыв
    if context.user_data.get("waiting_feedback"):
        await handle_feedback(update, context)
        return

    # Проверяем не в админ-панели ли мы
    if context.user_data.get("admin_state") is not None:
        from handlers.admin import handle_admin_input
        await handle_admin_input(update, context)
        return

    # Обычный поиск
    try:
        await search_handler(update, context)
    except Exception as e:
        log_error(e, {"user_id": user_id, "query": update.message.text})
        await update.message.reply_text("❌ Произошла ошибка. Попробуйте ещё раз.")


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка ошибок"""
    error = context.error
    log_error(error, {"update": str(update)})
    
    # Уведомляем админа
    from config import ADMIN_ID
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
    # Бэкап при запуске
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
