"""
Главный файл бота — сборка всех модулей
"""
import os
import sys
import signal
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
    feedback_yes_callback, feedback_no_callback, handle_issue_comment, handle_issue_comment_text
)
from handlers import admin as admin_handler
from keyboards import (
    get_keyboard_by_role, get_admin_panel_keyboard
)
from utils.logger import logger, log_error
from utils.backup import backup_compatibility_json, backup_database

PID_FILE = "bot.pid"


def check_single_instance():
    """Проверяет, запущен ли уже другой экземпляр бота"""
    if os.path.exists(PID_FILE):
        try:
            with open(PID_FILE, 'r') as f:
                old_pid = int(f.read().strip())
            # Проверяем, существует ли процесс с этим PID
            if sys.platform == 'win32':
                import ctypes
                PROCESS_QUERY_INFORMATION = 0x0400
                PROCESS_VM_READ = 0x0010
                try:
                    handle = ctypes.windll.kernel32.OpenProcess(PROCESS_QUERY_INFORMATION | PROCESS_VM_READ, False, old_pid)
                    if handle:
                        ctypes.windll.kernel32.CloseHandle(handle)
                        print(f"⚠️ Бот уже запущен с PID {old_pid}")
                        print("Если вы уверены, что бот не запущен, удалите файл bot.pid")
                        sys.exit(1)
                except:
                    # Процесс не существует, удаляем старый PID файл
                    os.remove(PID_FILE)
                    logger.info(f"Удалён старый PID файл (процесс {old_pid} не существует)")
            else:
                os.kill(old_pid, 0)  # Проверяем, существует ли процесс
                print(f"⚠️ Бот уже запущен с PID {old_pid}")
                print("Если вы уверены, что бот не запущен, удалите файл bot.pid")
                sys.exit(1)
        except (ValueError, FileNotFoundError, ProcessLookupError):
            # PID файл повреждён или процесс не существует
            if os.path.exists(PID_FILE):
                os.remove(PID_FILE)
                logger.info("Удалён некорректный PID файл")

    # Записываем текущий PID
    with open(PID_FILE, 'w') as f:
        f.write(str(os.getpid()))
    logger.info(f"Записан PID: {os.getpid()}")


def cleanup_pid_file(signum=None, frame=None):
    """Удаляет PID файл при завершении работы"""
    if os.path.exists(PID_FILE):
        os.remove(PID_FILE)
        logger.info("PID файл удалён при завершении работы")
    sys.exit(0)


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
    app.add_handler(CallbackQueryHandler(handle_issue_comment, pattern="^issue_comment_"))
    app.add_handler(CallbackQueryHandler(history_callback, pattern="^my_history"))
    app.add_handler(CallbackQueryHandler(popular_callback, pattern="^popular_searches"))
    app.add_handler(CallbackQueryHandler(back_to_main_callback, pattern="^back_to_main"))

    # Текстовые сообщения
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_main_message))

    # Обработка ошибок
    app.add_error_handler(error_handler)

    return app


async def handle_main_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Главный обработчик всех текстовых сообщений"""
    user_id = update.effective_user.id
    user_input = update.message.text.strip()
    role = get_user_role(user_id)

    # Сохраняем пользователя
    add_or_update_user(
        user_id=user_id,
        username=update.effective_user.username,
        first_name=update.effective_user.first_name,
        last_name=update.effective_user.last_name,
        language_code=update.effective_user.language_code
    )

    # 1. Кнопка возврата в меню
    if user_input == "🏠 В меню":
        context.user_data.pop("admin_state", None)
        keyboard = get_keyboard_by_role(role)
        await update.message.reply_text("🏠 Главное меню", reply_markup=keyboard)
        return

    # 2. Кнопка назад
    if user_input == "⬅️ Назад":
        state = context.user_data.get("admin_state")
        if state == "admin_panel":
            # Из админ-панели → в главное меню
            context.user_data.pop("admin_state", None)
            keyboard = get_keyboard_by_role(role)
            await update.message.reply_text("🏠 Главное меню", reply_markup=keyboard)
        elif state == "add_models":
            # Из меню добавления → в админ-панель
            context.user_data["admin_state"] = "admin_panel"
            text = "👑 **Панель администратора**\n\nВыберите действие:"
            await update.message.reply_text(text, reply_markup=get_admin_panel_keyboard(), parse_mode="Markdown")
        elif state and state.startswith("add_"):
            # Из конкретного добавления → в меню добавления
            context.user_data["admin_state"] = "add_models"
            await admin_handler.show_add_models(update, context)
        elif state and state.startswith("helper_"):
            await admin_handler.show_helpers(update, context)
        elif state in ("issue_reports", "all_issue_reports", "waiting_issue_resolve"):
            # Из жалоб → в админ-панель
            context.user_data["admin_state"] = "admin_panel"
            text = "👑 **Панель администратора**\n\nВыберите действие:"
            await update.message.reply_text(text, reply_markup=get_admin_panel_keyboard(), parse_mode="Markdown")
        else:
            # По умолчанию → в главное меню
            context.user_data.pop("admin_state", None)
            keyboard = get_keyboard_by_role(role)
            await update.message.reply_text("🏠 Главное меню", reply_markup=keyboard)
        return

    # 3. Скрытый вход в админку
    if user_input == SECRET_ADMIN_WORD:
        await secret_admin_handler(update, context)
        return

    # 4. Проверяем отзыв
    if context.user_data.get("waiting_feedback"):
        await handle_feedback(update, context)
        return

    # 4.1 Проверяем комментарий к жалобе
    if context.user_data.get("waiting_issue_comment"):
        await handle_issue_comment_text(update, context)
        return

    # 5. Проверяем заблокирован ли
    db_user = get_user(user_id)
    if db_user and db_user.get("is_blocked"):
        await update.message.reply_text("⛔ Бот заблокировал вам доступ.")
        return

    # === КНОПКИ КАТЕГОРИЙ (ПЕРЕД АДМИНКОЙ, чтобы работали всегда) ===
    if user_input in ("🔍 Подбор стёкол", "📱 Чехлы", "🖥️ Дисплеи", "🔋 АКБ", "🧴 Переклейка"):
        # Сбрасываем admin_state чтобы не мешал
        context.user_data.pop("admin_state", None)
        await category_button_handler(update, context)
        return

    # === СТАТУС (тоже всегда работает) ===
    if user_input == "👤 Мой статус":
        context.user_data.pop("admin_state", None)
        await status_button_handler(update, context)
        return

    # 6. Проверяем админ-состояние (ввод данных)
    admin_state = context.user_data.get("admin_state")
    if admin_state and admin_state not in ("admin_panel", "add_models", "helpers_menu"):
        await admin_handler.handle_admin_input(update, context)
        return

    # === КНОПКИ АДМИНИСТРАТОРА ===
    if user_input == "⚡ Управление":
        if role == "admin":
            context.user_data["admin_state"] = "admin_panel"
            text = "👑 **Панель администратора**\n\nВыберите действие:"
            await update.message.reply_text(text, reply_markup=get_admin_panel_keyboard(), parse_mode="Markdown")
        return

    if user_input == "📊 Статистика бота":
        await admin_handler.show_admin_stats(update, context)
        return

    if user_input == "👥 Подписки":
        await admin_handler.show_subscriptions(update, context)
        return

    if user_input == "➕ Добавить модели":
        context.user_data["admin_state"] = "add_models"
        await admin_handler.show_add_models(update, context)
        return

    if user_input == "👤 Помощники":
        context.user_data["admin_state"] = "helpers_menu"
        await admin_handler.show_helpers(update, context)
        return

    if user_input == "📩 Рассылка":
        await admin_handler.show_broadcast(update, context)
        return

    if user_input == "🚫 Блок/Разблок":
        await admin_handler.show_block_unblock(update, context)
        return

    if user_input == "⚠️ Неподтверждённые":
        await admin_handler.show_unconfirmed_models(update, context)
        return

    if user_input == "📋 Жалобы":
        await admin_handler.show_issue_reports(update, context)
        return

    if user_input == "👥 Список помощников":
        await admin_handler.list_helpers(update, context)
        return

    if user_input == "➕ Назначить помощника":
        context.user_data["admin_state"] = "helper_add"
        await admin_handler.assign_helper(update, context)
        return

    if user_input == "🚫 Снять помощника":
        context.user_data["admin_state"] = "helper_remove"
        await admin_handler.remove_helper(update, context)
        return

    # Кнопки добавления моделей
    if user_input == "📊 Все жалобы":
        await admin_handler.show_all_issue_reports(update, context)
        return

    # Если в состоянии жалоб — пытаемся разобрать как номер
    admin_state = context.user_data.get("admin_state")
    if admin_state == "issue_reports":
        try:
            num = int(user_input)
            await admin_handler.resolve_issue_handler(update, context)
            return
        except ValueError:
            pass  # Не число — идём дальше

    if user_input == "🔍 Добавить стёкла":
        await admin_handler.add_glass_handler(update, context)
        return

    if user_input == "📱 Добавить чехлы":
        context.user_data["admin_state"] = "add_case"
        context.user_data["add_category"] = "case"
        await admin_handler.add_chelts_handler(update, context)
        return

    if user_input == "🖥️ Добавить дисплеи":
        context.user_data["admin_state"] = "add_display"
        context.user_data["add_category"] = "display"
        await admin_handler.add_display_handler(update, context)
        return

    if user_input == "🔋 Добавить АКБ":
        context.user_data["admin_state"] = "add_battery"
        context.user_data["add_category"] = "battery"
        await admin_handler.add_battery_handler(update, context)
        return

    if user_input == "🧴 Добавить переклейку":
        context.user_data["admin_state"] = "add_oca"
        context.user_data["add_category"] = "oca"
        await admin_handler.add_oca_handler(update, context)
        return

    # === КНОПКА ПОМОЩНИКА ===
    if user_input == "➕ Добавить в базу":
        if role in ("admin", "helper"):
            context.user_data["admin_state"] = "add_models"
            await admin_handler.show_add_models(update, context)
        return

    # === ОБЫЧНЫЙ ПОИСК ===
    try:
        await search_handler(update, context)
    except Exception as e:
        log_error(e, {"user_id": user_id, "query": user_input})
        await update.message.reply_text("❌ Произошла ошибка. Попробуйте ещё раз.")


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
    # Проверяем, запущен ли уже другой экземпляр бота
    check_single_instance()
    
    # Регистрируем обработчики сигналов для корректного завершения
    signal.signal(signal.SIGINT, cleanup_pid_file)
    signal.signal(signal.SIGTERM, cleanup_pid_file)
    
    try:
        backup_compatibility_json()
        backup_database()
        logger.info("Бэкапы созданы при запуске")
    except Exception as e:
        logger.warning(f"Не удалось создать бэкап: {e}")

    app = create_app()
    logger.info("🤖 Бот запущен...")
    print("🤖 Бот запущен...")
    try:
        app.run_polling(drop_pending_updates=True, poll_interval=1.0)
    finally:
        cleanup_pid_file()


if __name__ == "__main__":
    main()
