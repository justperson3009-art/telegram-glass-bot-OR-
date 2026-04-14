"""
Обработчик поиска
"""
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from utils.search_categories import find_compatible_models_in_category, get_all_models_count
from database import add_search, increment_user_searches, update_popular_search, get_user_search_history, get_popular_searches, add_feedback, get_model_compatibility, add_issue_report
from config import get_text, get_partner_link
from keyboards import get_keyboard_by_role
from database import get_user_role


async def search_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик поиска совместимых моделей"""
    user_input = update.message.text.strip()
    user_id = update.effective_user.id
    lang = update.effective_user.language_code or "ru"

    context.user_data["lang"] = lang

    # Определяем категорию
    category = context.user_data.get("category", "glass")
    
    # Логируем категорию для отладки
    print(f"[DEBUG] Поиск в категории: {category}, запрос: {user_input}")

    # Ищем в выбранной категории
    result = find_compatible_models_in_category(category, user_input)

    # Записываем в БД
    add_search(user_id, user_input, result["found"])
    increment_user_searches(user_id)
    if result["found"]:
        update_popular_search(user_input)

    # Клавиатура возврата в меню
    role = get_user_role(user_id)
    menu_keyboard = get_keyboard_by_role(role)

    if result["found"]:
        # Нашли!
        # Формируем заголовок в зависимости от категории
        category_names = {
            "glass": "🔍 Стекло",
            "display": "🖥️ Дисплей",
            "battery": "🔋 Аккумулятор",
            "parts": "🔧 Запчасть",
        }
        category_name = category_names.get(category, "🔍 Стекло")

        # === ФОРМАТ ДЛЯ ДИСПЛЕЕВ (ВСЕ варианты: копия/OLED/оригинал + цены) ===
        if category == "display":
            # Проверяем есть ли display_options (новый формат)
            display_options = result.get("display_options")
            phone_models_list = result.get("phone_models", [])

            if display_options:
                # НОВЫЙ ФОРМАТ — показываем все варианты
                text = f"**🖥️ Дисплеи для {user_input}**\n\n"

                if phone_models_list:
                    text += f"📱 **Совместимые модели:**\n"
                    for model in phone_models_list:
                        text += f"• {model}\n"
                    text += "\n"

                text += f"💡 **Доступные варианты:**\n\n"

                for i, opt in enumerate(display_options, 1):
                    dtype = opt["type"]
                    price = opt["price"]
                    note = opt.get("note", "")

                    # Определяем эмодзи по типу
                    type_emoji = {
                        "OR": "🅾️",
                        "OLED": "🔵",
                        "In-Cell": "🟢",
                        "Стандарт": "⚪",
                        "AMOLED": "🟣",
                    }.get(dtype, "📱")

                    # Красивое название типа
                    type_names = {
                        "OR": "Оригинал",
                        "OLED": "OLED копия",
                        "In-Cell": "In-Cell копия",
                        "Стандарт": "Стандарт копия",
                        "AMOLED": "AMOLED копия",
                    }
                    type_name = type_names.get(dtype, dtype)

                    text += f"{type_emoji} **{i}. {type_name}** — {price} BYN\n"
                    if note:
                        text += f"   _{note}_\n"
                    text += "\n"

                text += "💰 _Цены ориентировочные_"
            else:
                # СТАРЫЙ ФОРМАТ (обратная совместимость)
                first_model = result["models"][0]
                price = None
                display_name = first_model

                if " — " in first_model:
                    name_part, price_part = first_model.rsplit(" — ", 1)
                    price = price_part
                else:
                    name_part = first_model

                name_part = name_part.replace("Дисплей ", "").replace("Аккумулятор ", "").strip()
                name_clean = re.sub(r'\s*-\s*(In-Cell|OR|OLED|DD).*?$', '', name_part, flags=re.IGNORECASE).strip()
                name_clean = re.sub(r'\s*\(.*?\)', '', name_clean).strip()
                phone_models_list = [m.strip() for m in name_clean.split("/") if m.strip()]

                text = f"**{category_name}**\n\n"
                if price:
                    text += f"📱 {user_input} — {price}"
                else:
                    text += f"📱 {user_input}"

                if phone_models_list:
                    text += "\n\n✅ **Совместимость:**"
                    for model in phone_models_list:
                        text += f"\n• {model}"

                text += "\n\n💰 **Цена ориентировочная**"

        # === ФОРМАТ ДЛЯ АКБ (маркировка + модель, БЕЗ совместимости) ===
        elif category == "battery":
            # Проверяем новый формат (двусторонний поиск)
            battery_mark = result.get("battery_mark")
            phone_models_list = result.get("phone_models", [])
            price = result.get("price")
            search_type = result.get("search_type")

            if search_type == "phone_to_battery":
                # Запрос по модели телефона → показываем маркировку
                text = f"**🔋 Аккумулятор для {user_input}**\n\n"
                if battery_mark:
                    text += f"🔌 **Маркировка батареи:** {battery_mark}"
                else:
                    text += f"🔌 **Маркировка:** не указана"
                if price:
                    text += f"\n\n💰 **{price}**"
                text += "\n\n💰 _Цена ориентировочная_"
            elif search_type == "mark_to_phone":
                # Запрос по маркировке → показываем модели телефонов
                text = f"**🔋 Батарея {battery_mark}**\n\n"
                text += f"📱 **Устанавливается в:**\n"
                for model in phone_models_list:
                    text += f"• {model}\n"
                if price:
                    text += f"\n💰 **{price}**"
                text += "\n\n💰 _Цена ориентировочная_"
            else:
                # СТАРЫЙ ФОРМАТ (обратная совместимость)
                if not result.get("models"):
                    await update.message.reply_text("❌ АКБ не найдены в базе. Попробуйте другую модель.")
                    return
                
                first_model = result["models"][0]
                battery_mark_old = "—"
                phone_models_old = []
                price_old = None

                if " — " in first_model:
                    name_part, price_part = first_model.rsplit(" — ", 1)
                    price_old = price_part
                    mark_match = re.search(r'\(([^)]+)\)', name_part)
                    if mark_match:
                        battery_mark_old = mark_match.group(1)
                    phone_part = name_part.replace("Аккумулятор ", "").strip()
                    if mark_match:
                        phone_part = phone_part.replace(f"({battery_mark_old})", "").strip()
                    phone_models_old = [m.strip() for m in phone_part.split("/") if m.strip()]

                text = f"**{category_name}**\n\n"
                if battery_mark_old != "—":
                    text += f"🔋 {user_input} — **{battery_mark_old}**"
                else:
                    text += f"🔋 {user_input}"

                if phone_models_old:
                    text += "\n\n✅ **Совместимость:**"
                    for model in phone_models_old:
                        text += f"\n• {model}"

                if price_old:
                    text += f"\n\n💰 **{price_old}**"

                text += "\n\n💰 **Цена ориентировочная**"

        # === ФОРМАТ ДЛЯ СТЁКОЛ, ЧЕХЛОВ, ОКА ===
        else:
            if result.get("exact_match"):
                text = f"🔎 **{category_name} от {user_input} подходит для всех этих моделей:**"
            else:
                text = f"🔍 **Возможно вы имели в виду {result['matched_model']}?** {category_name} подходит для:"

            text += "\n\n"

            for model in result["models"]:
                clean_model = model.replace(" (цена ориентировочная)", "").strip()
                text += f"• {clean_model}\n"

        # Получаем рейтинг совместимости (ТОЛЬКО для стёкол/запчастей)
        if category in ("glass", "parts"):
            compat = get_model_compatibility(result["matched_model"])
            if compat["percent"] is not None:
                if compat["status"] == "confirmed":
                    emoji = "✅"
                    label = "Подтверждено"
                elif compat["status"] == "partial":
                    emoji = "⚠️"
                    label = "Совместимо"
                else:
                    emoji = "❌"
                    label = "Не подтверждено"

                text += f"\n\n{emoji} **Совместимость: {compat['percent']}%** ({label})\n"
                text += f"👍 Подошло: {compat['positive']} | 👎 Не подошло: {compat['negative']}"

        # Кнопки обратной связи — передаём категорию
        keyboard = [
            [InlineKeyboardButton("✅ Подошло", callback_data=f"feedback_yes_{category}_{user_input}"),
             InlineKeyboardButton("❌ Не подошло", callback_data=f"feedback_no_{category}_{user_input}")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")
    else:
        # Не нашли
        text = get_text(lang, "not_found")

        await update.message.reply_text(text, reply_markup=menu_keyboard, parse_mode="Markdown")


async def feedback_yes_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Пользователь подтвердил что подошло"""
    query = update.callback_query
    await query.answer("✅ Спасибо за отзыв!")

    # Парсим: feedback_yes_CATEGORY_QUERY
    data = query.data.replace("feedback_yes_", "", 1)
    # Первый _ разделяет категорию и запрос
    parts = data.split("_", 1)
    if len(parts) == 2:
        category, user_input = parts
    else:
        category = "glass"
        user_input = data

    add_feedback(update.effective_user.id, user_input, "", 1)

    # Убираем кнопки
    keyboard = [[InlineKeyboardButton("✅ Вы подтвердили", callback_data="ignored")]]
    await query.message.edit_reply_markup(reply_markup=InlineKeyboardMarkup(keyboard))


async def feedback_no_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Пользователь сказал что НЕ подошло — запрашиваем комментарий"""
    query = update.callback_query

    # Парсим: feedback_no_CATEGORY_QUERY
    data = query.data.replace("feedback_no_", "", 1)
    parts = data.split("_", 1)
    if len(parts) == 2:
        category, user_input = parts
    else:
        category = "glass"
        user_input = data

    # Сохраняем данные для комментария
    context.user_data["issue_category"] = category
    context.user_data["issue_query"] = user_input
    context.user_data["issue_matched"] = query.message.text.split("\n")[0] if "\n" in query.message.text else user_input
    context.user_data["waiting_issue_comment"] = True

    # Обновляем сообщение с просьбой написать комментарий
    text = (
        "❌ **Понял, будем улучшать базу!**\n\n"
        "📝 **Напишите что именно не подошло:**\n"
        "— Неправильная модель?\n"
        "— Неверная цена?\n"
        "— Другая проблема?\n\n"
        "Опишите подробно — администратор обработает вашу жалобу."
    )

    # Убираем кнопки
    await query.message.edit_text(text, parse_mode="Markdown")
    await query.answer()


async def handle_issue_comment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка inline кнопки 'Отправить комментарий'"""
    query = update.callback_query
    await query.answer("✍️ Напишите ваш комментарий в чат!")

    category = context.user_data.get("issue_category", "glass")
    issue_query = context.user_data.get("issue_query", "")

    # Убираем состояние ожидания
    context.user_data.pop("waiting_issue_comment", None)

    # Подсказка
    text = "✍️ **Напишите ваш комментарий в чат.**\n\nИли нажмите /start для возврата в меню."
    await query.message.reply_text(text, parse_mode="Markdown")


async def handle_issue_comment_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка текстового комментария к жалобе"""
    user_id = update.effective_user.id
    comment = update.message.text.strip()

    category = context.user_data.get("issue_category", "glass")
    issue_query = context.user_data.get("issue_query", "")
    issue_matched = context.user_data.get("issue_matched", "")

    # Сохраняем жалобу в БД
    add_issue_report(user_id, category, issue_query, issue_matched, comment)

    # Сбрасываем состояние
    context.user_data.pop("waiting_issue_comment", None)
    context.user_data.pop("issue_category", None)
    context.user_data.pop("issue_query", None)
    context.user_data.pop("issue_matched", None)

    # Также записываем как feedback=0
    add_feedback(user_id, issue_query, issue_matched, 0)

    # Подтверждение
    category_names = {
        "glass": "🔍 Стёкла",
        "display": "🖥️ Дисплеи",
        "battery": "🔋 АКБ",
        "parts": "🔧 Запчасти"
    }
    cat_label = category_names.get(category, category)

    await update.message.reply_text(
        f"✅ **Жалоба отправлена!**\n\n"
        f"📂 Категория: {cat_label}\n"
        f"🔎 Запрос: {issue_query}\n"
        f"💬 Комментарий: {comment}\n\n"
        "Администратор обработает вашу жалобу. Спасибо!"
    )

    # Уведомление админу
    from config import ADMIN_ID
    try:
        await update.message.bot.send_message(
            chat_id=ADMIN_ID,
            text=(
                f"⚠️ **Новая жалоба!**\n\n"
                f"👤 Пользователь: {update.effective_user.first_name} (@{update.effective_user.username})\n"
                f"📂 Категория: {cat_label}\n"
                f"🔎 Запрос: {issue_query}\n"
                f"🎯 Найдено: {issue_matched}\n"
                f"💬 Комментарий: {comment}"
            ),
            parse_mode="Markdown"
        )
    except:
        pass


async def history_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать историю поисков"""
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    lang = context.user_data.get("lang", "ru")

    history = get_user_search_history(user_id, limit=5)

    if not history:
        text = get_text(lang, "no_history")
    else:
        text = get_text(lang, "search_history") + "\n\n"
        for i, h in enumerate(history, 1):
            status = "✅" if h["found"] else "❌"
            text += f"{i}. {status} {h['query']} ({h['timestamp'][-8:-3]})\n"

    keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.message.edit_text(text, reply_markup=reply_markup, parse_mode="Markdown")


async def popular_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать популярные запросы"""
    query = update.callback_query
    await query.answer()

    lang = context.user_data.get("lang", "ru")
    popular = get_popular_searches(limit=10, days=7)

    if not popular:
        text = "📭 Пока нет популярных запросов."
    else:
        text = get_text(lang, "popular_searches") + "\n\n"
        for i, p in enumerate(popular, 1):
            text += f"{i}. 🔥 {p['query']} ({p['count']})\n"

    keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.message.edit_text(text, reply_markup=reply_markup, parse_mode="Markdown")


async def back_to_main_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Кнопка назад к главному меню"""
    query = update.callback_query
    await query.answer()

    lang = context.user_data.get("lang", "ru")
    text = get_text(lang, "start")
    await query.message.reply_text(text, parse_mode="Markdown")
