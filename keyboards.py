"""
Клавиатуры бота (ReplyKeyboardMarkup — кнопки в строке ввода)
"""
from telegram import KeyboardButton, ReplyKeyboardMarkup


def get_main_keyboard():
    """Главное меню пользователя"""
    kb = [
        [KeyboardButton(text="🔍 Подбор стёкол")],
        [KeyboardButton(text="📱 Чехлы"), KeyboardButton(text="🖥️ Дисплеи")],
        [KeyboardButton(text="🔋 АКБ"), KeyboardButton(text="🧴 Переклейка")],
        [KeyboardButton(text="👤 Мой статус")],
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)


def get_admin_keyboard():
    """Меню администратора"""
    kb = [
        [KeyboardButton(text="🔍 Подбор стёкол")],
        [KeyboardButton(text="📱 Чехлы"), KeyboardButton(text="🖥️ Дисплеи")],
        [KeyboardButton(text="🔋 АКБ"), KeyboardButton(text="🧴 Переклейка")],
        [KeyboardButton(text="👤 Мой статус")],
        [KeyboardButton(text="🔧 Админ-панель")],
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)


def get_keyboard_by_role(is_admin=False):
    """Вернуть клавиатуру по роли"""
    if is_admin:
        return get_admin_keyboard()
    return get_main_keyboard()


def get_cancel_keyboard():
    """Клавиатура отмены"""
    kb = [
        [KeyboardButton(text="❌ Отмена")],
        [KeyboardButton(text="🏠 В меню")],
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
