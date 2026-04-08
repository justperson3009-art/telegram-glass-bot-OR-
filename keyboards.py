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
        [KeyboardButton(text="⚡ Управление")],
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)


def get_helper_keyboard():
    """Меню помощника"""
    kb = [
        [KeyboardButton(text="🔍 Подбор стёкол")],
        [KeyboardButton(text="📱 Чехлы"), KeyboardButton(text="🖥️ Дисплеи")],
        [KeyboardButton(text="🔋 АКБ"), KeyboardButton(text="🧴 Переклейка")],
        [KeyboardButton(text="👤 Мой статус")],
        [KeyboardButton(text="➕ Добавить в базу")],
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)


def get_admin_panel_keyboard():
    """Меню панели администратора (после нажатия ⚡ Управление)"""
    kb = [
        [KeyboardButton(text="📊 Статистика бота")],
        [KeyboardButton(text="👥 Подписки")],
        [KeyboardButton(text="➕ Добавить модели")],
        [KeyboardButton(text="👤 Помощники")],
        [KeyboardButton(text="📩 Рассылка")],
        [KeyboardButton(text="🚫 Блок/Разблок")],
        [KeyboardButton(text="🏠 В меню")],
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)


def get_add_models_keyboard():
    """Меню добавления моделей"""
    kb = [
        [KeyboardButton(text="🔍 Добавить стёкла")],
        [KeyboardButton(text="📱 Добавить чехлы")],
        [KeyboardButton(text="🖥️ Добавить дисплеи")],
        [KeyboardButton(text="🔋 Добавить АКБ")],
        [KeyboardButton(text="🧴 Добавить переклейку")],
        [KeyboardButton(text="⬅️ Назад")],
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)


def get_helpers_keyboard():
    """Меню управления помощниками"""
    kb = [
        [KeyboardButton(text="👥 Список помощников")],
        [KeyboardButton(text="➕ Назначить помощника")],
        [KeyboardButton(text="🚫 Снять помощника")],
        [KeyboardButton(text="⬅️ Назад")],
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)


def get_keyboard_by_role(role="user"):
    """Вернуть клавиатуру по роли"""
    if role == "admin":
        return get_admin_keyboard()
    elif role == "helper":
        return get_helper_keyboard()
    return get_main_keyboard()


def get_cancel_keyboard():
    """Клавиатура отмены"""
    kb = [
        [KeyboardButton(text="❌ Отмена")],
        [KeyboardButton(text="🏠 В меню")],
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
