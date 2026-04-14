"""
Админ-панель — полностью текстовое меню
"""
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
from config import ADMIN_ID, get_text
from database import (
    get_user_stats, get_all_users, block_user, unblock_user,
    add_broadcast, get_broadcast_stats, get_popular_searches,
    get_setting, set_setting, get_feedback_stats, get_latest_feedback,
    get_helpers, set_user_role, get_user_role, add_subscription,
    get_subscription_stats, is_admin as db_is_admin, get_unconfirmed_models,
    get_pending_issue_reports, get_all_issue_reports, resolve_issue_report,
    get_issue_reports_stats
)
from utils.search import get_all_groups, add_models_to_group, remove_group
from utils.search_categories import add_models_smart, load_category, get_category_stats
from utils.backup import backup_compatibility_json, backup_database, get_backup_list
from keyboards import (
    get_admin_panel_keyboard, get_helpers_keyboard, get_keyboard_by_role
)
from utils.logger import log_broadcast, logger

# FSM состояния админки
WAITING_GROUP_NAME, WAITING_MODELS_LIST, WAITING_BLOCK_USER_ID, WAITING_BROADCAST_TEXT = range(4)
WAITING_ADD_HELPER_ID, WAITING_REMOVE_HELPER_ID = range(4, 6)
WAITING_ADD_GLASS, WAITING_ADD_CASE, WAITING_ADD_DISPLAY, WAITING_ADD_BATTERY, WAITING_ADD_OCA = range(6, 11)
WAITING_ISSUE_RESOLVE = 11


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
    cat_stats = get_category_stats()

    text = (
        f"📊 **Статистика бота:**\n\n"
        f"👥 Активных: **{stats['active']}**\n"
        f"🚫 Заблокированных: **{stats['blocked']}**\n"
        f"🔍 Всего поисков: **{stats['total_searches']}**\n"
        f"📱 Моделей в базе: **{sum(len(m) for m in groups.values())}**\n"
        f"📦 Групп: **{len(groups)}**\n\n"
        f"📂 **Файлы категорий:**\n"
        f"  • 🔍 Стёкла: **{cat_stats['glass']['models']}** моделей\n"
        f"  • 🔧 Запчасти: **{cat_stats.get('parts', {'models': 0})['models']}** моделей\n"
        f"  • 🖥️ Дисплеи: **{cat_stats['display']['models']}** моделей\n"
        f"  • 🔋 АКБ: **{cat_stats['battery']['models']}** моделей\n\n"
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

    # Создаём клавиатуру с кнопкой "Назад"
    kb = [
        [KeyboardButton(text="🔍 Добавить стёкла")],
        [KeyboardButton(text="📱 Добавить чехлы")],
        [KeyboardButton(text="🖥️ Добавить дисплеи")],
        [KeyboardButton(text="🔋 Добавить АКБ")],
        [KeyboardButton(text="🧴 Добавить переклейку")],
        [KeyboardButton(text="⬅️ Назад")],
    ]
    await send("📦 **Добавить модели в базу:**\n\nВыберите категорию:", reply_markup=ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True), parse_mode="Markdown")


from telegram import KeyboardButton
from telegram import ReplyKeyboardMarkup


async def add_glass_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Добавить стёкла"""
    context.user_data["admin_state"] = "add_glass"
    context.user_data["add_category"] = "glass"
    await _send_simple_add_prompt(update, "🔍 Стёкла")

async def add_chelts_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Добавить чехлы"""
    context.user_data["admin_state"] = "add_case"
    context.user_data["add_category"] = "case"
    await _send_simple_add_prompt(update, "📱 Чехлы")

async def add_display_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Добавить дисплеи"""
    context.user_data["admin_state"] = "add_display"
    context.user_data["add_category"] = "display"
    await _send_simple_add_prompt(update, "🖥️ Дисплеи")

async def add_battery_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Добавить АКБ"""
    context.user_data["admin_state"] = "add_battery"
    context.user_data["add_category"] = "battery"
    await _send_simple_add_prompt(update, "🔋 АКБ")

async def add_parts_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Добавить запчасти"""
    context.user_data["admin_state"] = "add_parts"
    context.user_data["add_category"] = "parts"
    await _send_simple_add_prompt(update, "🔧 Запчасти")

async def update_from_google_sheet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обновить прайс из Google Sheets"""
    import subprocess
    import sys
    import os

    msg = update.message

    await msg.reply_text(
        "🔄 **Обновляю прайс из Google Sheets...**\n\n"
        "⏳ Это может занять несколько минут...\n"
        "📦 Буду создан бэкап текущих баз.",
        parse_mode="Markdown"
    )

    try:
        # Определяем директив скрипта автоматически
        script_dir = os.path.dirname(os.path.abspath(__file__))
        base_dir = os.path.join(script_dir, "..")  # Поднимаемся на уровень вверх

        # Запускаем скрипт импорта
        result = subprocess.run(
            [sys.executable, "update_from_google_sheet.py"],
            capture_output=True,
            text=True,
            timeout=300,  # 5 минут таймаут
            cwd=base_dir
        )

        output = result.stdout
        error = result.stderr

        if result.returncode == 0:
            # Формируем отчёт
            text = "✅ **Обновление завершено!**\n\n"

            # Парсим вывод
            if "Дисплеи:" in output:
                for line in output.split("\n"):
                    if "Дисплеи:" in line or "АКБ:" in line or "Запчасти:" in line:
                        text += line.strip() + "\n"

            text += "\n💾 Бэкап создан в папке `backups/`\n\n"
            text += "🔄 **Перезапускаю бота...**\n"
            text += "⏳ Подождите 10-15 секунд..."

            await msg.reply_text(text, parse_mode="Markdown")

            # Перезапускаем бота через systemd
            try:
                subprocess.run(
                    ["sudo", "systemctl", "restart", "glass-bot"],
                    capture_output=True,
                    timeout=30
                )
                await msg.reply_text(
                    "✅ **Бот перезапущен!**\n\n"
                    "Теперь можно пользоваться поиском в категории **🔧 Запчасти**.\n"
                    "Дисплеи и АКБ также обновлены!",
                    parse_mode="Markdown"
                )
            except Exception as restart_err:
                await msg.reply_text(
                    "⚠️ **Бот обновил данные, но требует ручного перезапуска!**\n\n"
                    "Выполни на сервере:\n"
                    "```bash\nsudo systemctl restart glass-bot\n```",
                    parse_mode="Markdown"
                )
        else:
            await msg.reply_text(
                f"❌ **Ошибка обновления:**\n\n```\n{error}\n```",
                parse_mode="Markdown"
            )

    except subprocess.TimeoutExpired:
        await msg.reply_text(
            "❌ **Таймаут!** Обновление заняло слишком много времени.\n"
            "Проверьте интернет-соединение и попробуйте снова."
        )
    except Exception as e:
        await msg.reply_text(
            f"❌ **Ошибка:**\n\n`{e}`",
            parse_mode="Markdown"
        )

async def add_oca_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Добавить переклейку"""
    context.user_data["admin_state"] = "add_oca"
    context.user_data["add_category"] = "oca"
    await _send_simple_add_prompt(update, "🧴 Переклейка")


async def _send_simple_add_prompt(update: Update, category_name: str):
    """Отправить упрощённое сообщение для добавления моделей"""
    kb = [
        [KeyboardButton(text="🔍 Добавить стёкла")],
        [KeyboardButton(text="🖥️ Добавить дисплеи"), KeyboardButton(text="🔋 Добавить АКБ")],
        [KeyboardButton(text="🔧 Добавить запчасти")],
        [KeyboardButton(text="⬅️ Назад")],
    ]
    await update.message.reply_text(
        f"{category_name}\n\n"
        f"✍️ **Просто перечисли модели через запятую:**\n"
        f"например: `iPhone 16, iPhone 16 Pro, iPhone 16 Pro Max`\n\n"
        f"⚡ Бот сам создаст группу и уберёт дубли.\n\n"
        f"⬅️ Назад — вернуться",
        reply_markup=ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True),
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


async def show_unconfirmed_models(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать модели с низкой совместимостью"""
    msg = update.message if update.message else getattr(update, 'callback_query', None)
    if not msg:
        return
    send = msg.reply_text if hasattr(msg, 'reply_text') else msg.edit_text

    unconfirmed = get_unconfirmed_models()
    if not unconfirmed:
        text = "✅ **Все модели подтверждены!**\n\nНет моделей с низким рейтингом."
    else:
        text = "⚠️ **Модели с низкой совместимостью:**\n\n"
        for m in unconfirmed:
            text += f"• `{m['model']}` — **{m['percent']}%** ({m['positive']}✅ / {m['negative']}❌)\n"
        text += "\n💡 Эти модели могут быть неверно определены."

    kb = [
        [KeyboardButton(text="📊 Статистика бота")],
        [KeyboardButton(text="⬅️ Назад")],
    ]
    await send(text, reply_markup=ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True), parse_mode="Markdown")


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

    # Обрабатываем Назад и В меню ПЕРВЫМ
    if user_input == "⬅️ Назад":
        if state and (state.startswith("add_") or state == "add_models"):
            # Из добавления моделей → в админ-панель
            context.user_data["admin_state"] = "admin_panel"
            text = "👑 **Панель администратора**\n\nВыберите действие:"
            await update.message.reply_text(text, reply_markup=get_admin_panel_keyboard(), parse_mode="Markdown")
        elif state and state.startswith("helper_"):
            # Из помощников → в меню помощников
            context.user_data["admin_state"] = "helpers_menu"
            await show_helpers(update, context)
        elif state and state == WAITING_BROADCAST_TEXT:
            # Из рассылки → в админ-панель
            context.user_data["admin_state"] = "admin_panel"
            text = "👑 **Панель администратора**\n\nВыберите действие:"
            await update.message.reply_text(text, reply_markup=get_admin_panel_keyboard(), parse_mode="Markdown")
        elif state and state == WAITING_BLOCK_USER_ID:
            # Из блокировки → в админ-панель
            context.user_data["admin_state"] = "admin_panel"
            text = "👑 **Панель администратора**\n\nВыберите действие:"
            await update.message.reply_text(text, reply_markup=get_admin_panel_keyboard(), parse_mode="Markdown")
        else:
            await go_back_to_admin(update, context)
        return

    if user_input == "🏠 В меню":
        context.user_data.pop("admin_state", None)
        from keyboards import get_keyboard_by_role
        from database import get_user_role
        role = get_user_role(user_id)
        await update.message.reply_text("🏠 Главное меню", reply_markup=get_keyboard_by_role(role))
        return

    if state and state.startswith("add_") and state not in ("add_models", "admin_panel", "helpers_menu", "helper_add", "helper_remove"):
        # Обрабатываем ввод моделей
        _handle_add_model_smart(update, context, state.replace("add_", ""))
        return
    elif state == "helper_add":
        try:
            helper_id = int(user_input)
            set_user_role(helper_id, "helper")
            await update.message.reply_text(f"✅ Пользователь `{helper_id}` назначен помощником!", reply_markup=get_helpers_keyboard(), parse_mode="Markdown")
            context.user_data["admin_state"] = "helpers_menu"  # Сбрасываем состояние в меню помощников
        except ValueError:
            await update.message.reply_text("❌ Введите корректный ID (число).")
    elif state == "helper_remove":
        try:
            helper_id = int(user_input)
            set_user_role(helper_id, "user")
            await update.message.reply_text(f"✅ Пользователь `{helper_id}` снят с роли помощника.", reply_markup=get_helpers_keyboard(), parse_mode="Markdown")
            context.user_data["admin_state"] = "helpers_menu"  # Сбрасываем состояние в меню помощников
        except ValueError:
            await update.message.reply_text("❌ Введите корректный ID (число).")
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


def _handle_add_model_smart(update, context, category):
    """Умная обработка добавления моделей через запятую"""
    user_input = update.message.text.strip()
    result = add_models_smart(category, user_input)

    kb = [
        [KeyboardButton(text="🔍 Добавить стёкла")],
        [KeyboardButton(text="📱 Добавить чехлы")],
        [KeyboardButton(text="🖥️ Добавить дисплеи")],
        [KeyboardButton(text="🔋 Добавить АКБ")],
        [KeyboardButton(text="🧴 Добавить переклейку")],
        [KeyboardButton(text="⬅️ Назад")],
    ]

    if result.get("error"):
        update.message.reply_text(result["error"], reply_markup=ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True))
    elif result.get("msg"):
        update.message.reply_text(f"ℹ️ {result['msg']}", reply_markup=ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True))
    else:
        text = (
            f"✅ **Успешно добавлено!**\n\n"
            f"📦 Категория: `{category}`\n"
            f"📂 Группа: `{result['group']}`\n"
            f"➕ Добавлено: **{result['added']}**\n"
            f"⏭️ Пропущено дублей: **{result['skipped']}**\n\n"
            f"📝 Модели:\n" + "\n".join([f"• {m}" for m in result["models"][:10]])
        )
        if len(result["models"]) > 10:
            text += f"\n... и ещё {len(result['models']) - 10}"
        update.message.reply_text(text, reply_markup=ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True), parse_mode="Markdown")
    context.user_data["admin_state"] = "add_models"


# === ЖАЛОБЫ ===

async def show_issue_reports(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать необработанные жалобы"""
    msg = update.message if update.message else getattr(update, 'callback_query', None)
    if not msg:
        return
    send = msg.reply_text if hasattr(msg, 'reply_text') else msg.edit_text

    context.user_data["admin_state"] = "issue_reports"

    stats = get_issue_reports_stats()
    reports = get_pending_issue_reports(limit=10)

    text = f"📋 **Жалобы пользователей**\n\n"
    text += f"⏳ Ожидает: **{stats['pending']}**\n"
    text += f"✅ Решено: **{stats['resolved']}**\n"
    text += f"📊 Всего: **{stats['total']}**\n\n"

    if not reports:
        text += "🎉 Нет необработанных жалоб!"
    else:
        for i, r in enumerate(reports, 1):
            cat_emoji = {"glass": "🔍", "display": "🖥️", "battery": "🔋", "case": "📱", "oca": "🧴"}.get(r["category"], "📋")
            text += (
                f"**{i}.** {cat_emoji} {r['category']} — {r['query']}\n"
                f"   👤 @{r.get('username') or r.get('first_name') or 'N/A'}\n"
                f"   💬 {r['comment'][:80]}\n"
                f"   🕐 {r['timestamp']}\n\n"
            )

        text += "💡 **Напишите номер жалобы** чтобы обработать её."

    kb = [
        [KeyboardButton(text="📊 Все жалобы")],
        [KeyboardButton(text="⬅️ Назад")],
    ]
    await send(text, reply_markup=ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True), parse_mode="Markdown")


async def show_all_issue_reports(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать все жалобы"""
    msg = update.message
    send = msg.reply_text

    context.user_data["admin_state"] = "all_issue_reports"

    reports = get_all_issue_reports(limit=20)

    if not reports:
        text = "📭 Жалоб нет."
    else:
        text = "📋 **Все жалобы (последние 20):**\n\n"
        for i, r in enumerate(reports, 1):
            status_emoji = "✅" if r["status"] == "resolved" else "⏳"
            cat_emoji = {"glass": "🔍", "display": "🖥️", "battery": "🔋", "case": "📱", "oca": "🧴"}.get(r["category"], "📋")
            text += (
                f"**{i}.** {status_emoji} {cat_emoji} {r['category']} — {r['query']}\n"
                f"   👤 @{r.get('username') or r.get('first_name') or 'N/A'}\n"
                f"   💬 {r['comment'][:80]}\n"
                f"   🕐 {r['timestamp']}\n\n"
            )

    kb = [[KeyboardButton(text="⬅️ Назад")]]
    await send(text, reply_markup=ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True), parse_mode="Markdown")


async def resolve_issue_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка жалобы по номеру"""
    msg = update.message
    text_input = msg.text.strip()

    try:
        report_num = int(text_input)
    except ValueError:
        await msg.reply_text("❌ Напишите номер жалобы (число).")
        return

    reports = get_pending_issue_reports(limit=20)
    if report_num < 1 or report_num > len(reports):
        await msg.reply_text(f"❌ Жалобы с номером {report_num} не найдено.")
        return

    report = reports[report_num - 1]
    report_id = report["id"]

    # Отмечаем как решённую
    resolve_issue_report(report_id, admin_response="Обработано администратором")

    cat_emoji = {"glass": "🔍", "display": "🖥️", "battery": "🔋", "case": "📱", "oca": "🧴"}.get(report["category"], "📋")

    await msg.reply_text(
        f"✅ **Жалоба #{report_num} обработана!**\n\n"
        f"{cat_emoji} Категория: {report['category']}\n"
        f"🔎 Запрос: {report['query']}\n"
        f"👤 Пользователь: @{report.get('username') or report.get('first_name') or 'N/A'}\n"
        f"💬 Комментарий: {report['comment']}\n\n"
        "Жалоба отмечена как решённая.",
        parse_mode="Markdown"
    )

    # Показываем обновлённый список
    await show_issue_reports(update, context)


def get_admin_handlers():
    """Возвращает только обработчики без CommandHandler (обрабатывается в main.py)"""
    return []
