"""
Обработчик поиска с inline-кнопками брендов
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from utils.search import find_compatible_models, get_all_brands, get_suggestions
from database import add_search, increment_user_searches, update_popular_search, get_user_search_history, get_popular_searches
from config import get_text, get_partner_link, BRANDS


async def search_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик поиска совместимых моделей"""
    user_input = update.message.text.strip()
    user_id = update.effective_user.id
    lang = update.effective_user.language_code or "ru"
    
    # Сохраняем язык пользователя
    context.user_data["lang"] = lang
    
    # Ищем
    result = find_compatible_models(user_input)
    
    # Записываем в БД
    add_search(user_id, user_input, result["found"])
    increment_user_searches(user_id)
    if result["found"]:
        update_popular_search(user_input)
    
    if result["found"]:
        # Нашли!
        if result.get("exact_match"):
            text = get_text(lang, "found_exact", query=user_input)
        else:
            text = get_text(lang, "found_similar", 
                          matched_model=result["matched_model"])
        
        text += "\n\n"
        for model in result["models"]:
            text += f"• {model}\n"
        
        # Добавляем партнёрскую ссылку
        text += f"\n{get_partner_link(user_input)}"
        
        # Кнопки
        keyboard = [
            [InlineKeyboardButton("📜 История поисков", callback_data="my_history")],
            [InlineKeyboardButton("🔥 Популярное", callback_data="popular_searches")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")
    else:
        # Не нашли
        text = get_text(lang, "not_found")
        
        # Подсказки
        suggestions = get_suggestions(user_input, limit=5)
        if suggestions:
            text += "\n\n💡 **Попробуйте:**\n"
            for s in suggestions[:3]:
                text += f"• {s}\n"
        
        await update.message.reply_text(text, parse_mode="Markdown")


async def show_brands(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать кнопки брендов"""
    lang = context.user_data.get("lang", "ru")
    
    keyboard = []
    row = []
    for brand_text in BRANDS.keys():
        row.append(InlineKeyboardButton(brand_text, callback_data=f"brand_{brand_text}"))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    text = get_text(lang, "start")
    
    if update.message:
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")
    else:
        await update.callback_query.message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")


async def brand_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка выбора бренда"""
    query = update.callback_query
    await query.answer()
    
    brand_data = query.data.replace("brand_", "")
    lang = context.user_data.get("lang", "ru")
    
    # Ищем модели этого бренда
    suggestions = get_suggestions(brand_data, limit=20)
    
    if not suggestions:
        await query.message.reply_text(f"❌ Модели {brand_data} не найдены.")
        return
    
    # Группируем по 3 в ряд
    keyboard = []
    row = []
    for model in suggestions[:15]:
        row.append(InlineKeyboardButton(model[:25], callback_data=f"select_{model}"))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    
    # Кнопка назад
    keyboard.append([InlineKeyboardButton("🔙 Назад к брендам", callback_data="back_to_brands")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.edit_text(f"📱 **Выберите модель {brand_data}:**", reply_markup=reply_markup, parse_mode="Markdown")


async def select_model_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка выбора модели"""
    query = update.callback_query
    await query.answer()
    
    model = query.data.replace("select_", "")
    lang = context.user_data.get("lang", "ru")
    user_id = update.effective_user.id
    
    # Ищем совместимые
    result = find_compatible_models(model)
    
    # Записываем в БД
    add_search(user_id, model, result["found"])
    increment_user_searches(user_id)
    update_popular_search(model)
    
    if result["found"]:
        text = get_text(lang, "found_exact", query=model) + "\n\n"
        for m in result["models"]:
            text += f"• {m}\n"
        
        text += f"\n{get_partner_link(model)}"
        
        keyboard = [[InlineKeyboardButton("🔙 Назад к брендам", callback_data="back_to_brands")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.message.edit_text(text, reply_markup=reply_markup, parse_mode="Markdown")
    else:
        await query.message.reply_text(get_text(lang, "not_found"), parse_mode="Markdown")


async def back_to_brands_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Кнопка назад к брендам"""
    query = update.callback_query
    await query.answer()
    await show_brands(update, context)


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
    await show_brands(update, context)
