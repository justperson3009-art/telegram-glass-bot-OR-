"""
Конфигурация бота: тексты, кнопки, настройки
"""
import os
from dotenv import load_dotenv

load_dotenv(override=True)

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не найден в .env файле!")
ADMIN_ID = int(os.getenv("ADMIN_ID", "5164389862"))
PROXY_URL = os.getenv("PROXY_URL")

# === Тексты ===

TEXTS = {
    "ru": {
        "start": (
            "📱 **Привет! Я бот для подбора стёкол.**\n\n"
            "Напишите модель телефона (можно частично),\n"
            "и я скажу все модели, для которых подходит стекло.\n\n"
            "Или выберите бренд кнопками ниже 👇"
        ),
        "feedback_prompt": (
            "✍️ Напишите ваше замечание или предложение.\n\n"
            "Я передам его владельцу бота."
        ),
        "feedback_thanks": "✅ Спасибо! Ваше сообщение отправлено администратору.",
        "not_found": (
            "❌ Модель не найдена в базе.\n\n"
            "Попробуйте ввести название по-другому или напишите /feedback если вы считаете что это ошибка."
        ),
        "found_exact": "🔎 **Стекло от {query} подходит для всех этих моделей:**",
        "found_similar": "🔍 **Возможно вы имели в виду {matched_model}?** Стекло подходит для:",
        "popular_searches": "🔥 **Популярные запросы за неделю:**",
        "search_history": "📜 **Ваши последние поиски:**",
        "no_history": "📭 У вас пока нет поисков.",
        "admin_only": "❌ У вас нет доступа к этой команде.",
        "admin_panel": "🔧 **Админ-панель:**",
        "broadcast_sent": "✅ Рассылка отправлена!\n\nОтправлено: {sent}\nОшибок: {failed}",
        "group_added": "✅ Группа **{name}** добавлена!\nМоделей: {count}",
        "group_deleted": "✅ Группа **{name}** удалена.",
        "group_not_found": "❌ Группа не найдена.",
        "no_access": "⛔ Бот заблокировал вам доступ.",
    },
    "en": {
        "start": (
            "📱 **Hi! I'm a glass finder bot.**\n\n"
            "Type a phone model (partial is ok),\n"
            "and I'll show all compatible models.\n\n"
            "Or choose a brand from buttons below 👇"
        ),
        "feedback_prompt": "✍️ Write your feedback or suggestion.",
        "feedback_thanks": "✅ Thanks! Your message sent to admin.",
        "not_found": "❌ Model not found in database.",
        "found_exact": "🔎 **Glass from {query} fits these models:**",
        "found_similar": "🔍 **Did you mean {matched_model}?** Glass fits:",
        "popular_searches": "🔥 **Popular searches this week:**",
        "search_history": "📜 **Your recent searches:**",
        "no_history": "📭 No searches yet.",
        "admin_only": "❌ No access to this command.",
        "admin_panel": "🔧 **Admin Panel:**",
        "broadcast_sent": "✅ Broadcast sent!\n\nSent: {sent}\nFailed: {failed}",
        "group_added": "✅ Group **{name}** added!\nModels: {count}",
        "group_deleted": "✅ Group **{name}** deleted.",
        "group_not_found": "❌ Group not found.",
        "no_access": "⛔ Bot blocked your access.",
    },
    "ar": {
        "start": (
            "📱 **مرحباً! أنا بوت البحث عن واقيات الشاشة.**\n\n"
            "اكتب موديل الهاتف (جزئي مقبول)،\n"
            "وسأعرض لك جميع الموديلات المتوافقة.\n\n"
            "أو اختر العلامة من الأزرار أدناه 👇"
        ),
        "feedback_prompt": "✍️ اكتب ملاحظاتك أو اقتراحاتك.",
        "feedback_thanks": "✅ شكراً! تم إرسال رسالتك للمسؤول.",
        "not_found": "❌ الموديل غير موجود في قاعدة البيانات.",
        "found_exact": "🔎 **واقي {query} يناسب هذه الموديلات:**",
        "found_similar": "🔍 **هل تقصد {matched_model}?** waقي يناسب:",
        "popular_searches": "🔥 **البحث الشائع هذا الأسبوع:**",
        "search_history": "📜 **عمليات البحث الأخيرة:**",
        "no_history": "📭 لا توجد عمليات بحث بعد.",
        "admin_only": "❌ لا يمكنك الوصول لهذا الأمر.",
        "admin_panel": "🔧 **لوحة المسؤول:**",
        "broadcast_sent": "✅ تم الإرسال!\n\nأُرسل: {sent}\nفشل: {failed}",
        "group_added": "✅ تمت إضافة مجموعة **{name}**!\nموديلات: {count}",
        "group_deleted": "✅ تم حذف مجموعة **{name}**.",
        "group_not_found": "❌ المجموعة غير موجودة.",
        "no_access": "⛔ البوت حظر وصولك.",
    },
}


def get_text(lang, key, **kwargs):
    """Получить текст на языке"""
    text = TEXTS.get(lang, TEXTS["ru"]).get(key, TEXTS["ru"].get(key, key))
    if kwargs:
        text = text.format(**kwargs)
    return text


# === Партнёрские ссылки (можно настроить) ===
PARTNER_LINKS = {
    "default": "🛒 Купить стекло: [ссылка на магазин](https://example.com)",
    "apple": "🛒 Купить стекло для iPhone: [ссылка](https://example.com/iphone)",
    "samsung": "🛒 Купить стекло для Samsung: [ссылка](https://example.com/samsung)",
    "xiaomi": "🛒 Купить стекло для Xiaomi: [ссылка](https://example.com/xiaomi)",
}


def get_partner_link(brand):
    """Получить партнёрскую ссылку для бренда"""
    brand_lower = brand.lower()
    if "iphone" in brand_lower or "apple" in brand_lower:
        return PARTNER_LINKS.get("apple", PARTNER_LINKS["default"])
    elif "samsung" in brand_lower:
        return PARTNER_LINKS.get("samsung", PARTNER_LINKS["default"])
    elif "xiaomi" in brand_lower or "redmi" in brand_lower or "poco" in brand_lower:
        return PARTNER_LINKS.get("xiaomi", PARTNER_LINKS["default"])
    return PARTNER_LINKS["default"]


# === Бренды для кнопок ===
BRANDS = {
    "🍎 Apple": ["iPhone", "Apple"],
    "🔵 Samsung": ["Samsung", "Galaxy"],
    "🟠 Xiaomi": ["Xiaomi", "Redmi", "POCO", "Mi"],
    "🔴 Tecno": ["Tecno"],
    "🟣 Infinix": ["Infinix"],
    "🔵 Realme": ["Realme"],
    "🟢 OPPO": ["OPPO"],
    "🟡 Vivo": ["Vivo"],
    "⚫ Google": ["Google Pixel"],
    "⚪ Motorola": ["Moto", "Motorola"],
    "🔵 Huawei": ["Huawei"],
    "🔴 Honor": ["Honor"],
}
