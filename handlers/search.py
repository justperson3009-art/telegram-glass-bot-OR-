"""
Обработчик поиска
"""
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from utils.search_categories import find_compatible_models_in_category, get_all_models_count
from database import add_search, increment_user_searches, update_popular_search, get_user_search_history, get_popular_searches, add_feedback, get_model_compatibility
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
            "case": "📱 Чехол",
            "oca": "🧴 Стекло для переклейки"
        }
        category_name = category_names.get(category, "🔍 Стекло")

        # === ФОРМАТ ДЛЯ ДИСПЛЕЕВ (только цена) ===
        if category == "display":
            first_model = result["models"][0]
            if " — " in first_model:
                full_name, price = first_model.rsplit(" — ", 1)
            else:
                full_name = first_model
                price = None

            text = f"**{category_name}**\n\n📱 {user_input} — {price}" if price else f"**{category_name}**\n\n📱 {user_input}"
            text += "\n\n💰 **Цена ориентировочная**"

        # === ФОРМАТ ДЛЯ АКБ (маркировка + совместимость + цена) ===
        elif category == "battery":
            first_model = result["models"][0]
            
            # Парсим формат: "Аккумулятор Redmi 9A/9C (BN56) — 20 BYN"
            battery_mark = "—"  # По умолчанию прочерк
            phone_models = []
            price = None
            
            if " — " in first_model:
                name_part, price_part = first_model.rsplit(" — ", 1)
                price = price_part
                
                # Извлекаем маркировку из скобок
                mark_match = re.search(r'\(([^)]+)\)', name_part)
                if mark_match:
                    battery_mark = mark_match.group(1)  # Например BN56
                
                # Извлекаем модели телефонов (убираем "Аккумулятор " и маркировку)
                phone_part = name_part.replace("Аккумулятор ", "").strip()
                if mark_match:
                    phone_part = phone_part.replace(f"({battery_mark})", "").strip()
                
                # Разбиваем по слэшу
                phone_models = [m.strip() for m in phone_part.split("/") if m.strip()]
            
            # Формируем ответ
            # Показываем искомую модель + маркировку
            text = f"**{category_name}**\n\n"
            
            if battery_mark != "—":
                text += f"🔋 {user_input} — **{battery_mark}**"
            else:
                text += f"🔋 {user_input}"
            
            # Совместимые модели
            if phone_models:
                text += "\n\n✅ **Совместимость:**"
                for model in phone_models:
                    text += f"\n• {model}"
            
            # Цена
            if price:
                text += f"\n\n💰 **{price}**"
            
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

        # Получаем рейтинг совместимости (ТОЛЬКО для стёкол/чехлов/ОКА)
        if category not in ("display", "battery"):
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

        # Кнопки обратной связи
        keyboard = [
            [InlineKeyboardButton("✅ Подошло", callback_data=f"feedback_yes_{user_input}"),
             InlineKeyboardButton("❌ Не подошло", callback_data=f"feedback_no_{user_input}")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")
    else:
        # Не нашли
        text = get_text(lang, "not_found")

        await update.message.reply_text(text, reply_markup=menu_keyboard, parse_mode="Markdown")


async def feedback_yes_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Пользователь подтвердил что стекло подошло"""
    query = update.callback_query
    await query.answer("✅ Спасибо за отзыв!")

    user_input = query.data.replace("feedback_yes_", "")
    matched = query.message.text.split("\n")[0] if "\n" in query.message.text else user_input

    add_feedback(update.effective_user.id, user_input, matched, 1)

    # Убираем кнопки
    keyboard = [[InlineKeyboardButton("✅ Вы подтвердили", callback_data="ignored")]]
    await query.message.edit_reply_markup(reply_markup=InlineKeyboardMarkup(keyboard))


async def feedback_no_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Пользователь сказал что стекло НЕ подошло"""
    query = update.callback_query
    await query.answer("❌ Понял, будем улучшать базу!")

    user_input = query.data.replace("feedback_no_", "")
    matched = query.message.text.split("\n")[0] if "\n" in query.message.text else user_input

    add_feedback(update.effective_user.id, user_input, matched, 0)

    # Убираем кнопки
    keyboard = [[InlineKeyboardButton("❌ Отмечено", callback_data="ignored")]]
    await query.message.edit_reply_markup(reply_markup=InlineKeyboardMarkup(keyboard))


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
