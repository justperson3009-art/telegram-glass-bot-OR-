"""
Модуль базы данных SQLite
Таблицы: users, search_history, popular_searches, settings
"""
import sqlite3
import os
from datetime import datetime, timedelta

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "bot.db")


def get_connection():
    """Получить подключение к БД"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Инициализация БД (создание таблиц)"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Таблица пользователей
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            language_code TEXT DEFAULT 'ru',
            is_blocked INTEGER DEFAULT 0,
            first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            total_searches INTEGER DEFAULT 0
        )
    """)
    
    # История поисков
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS search_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            query TEXT,
            found INTEGER,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    """)
    
    # Популярные запросы
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS popular_searches (
            query TEXT PRIMARY KEY,
            count INTEGER DEFAULT 1,
            last_searched TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Настройки бота
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)
    
    # Рассылки
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS broadcasts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message TEXT,
            sent_count INTEGER DEFAULT 0,
            failed_count INTEGER DEFAULT 0,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    conn.close()


# === Пользователи ===

def add_or_update_user(user_id, username=None, first_name=None, last_name=None, language_code=None):
    """Добавить или обновить пользователя"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
    exists = cursor.fetchone()
    
    if exists:
        cursor.execute("""
            UPDATE users 
            SET username = ?, first_name = ?, last_name = ?, 
                language_code = COALESCE(?, language_code),
                last_seen = CURRENT_TIMESTAMP
            WHERE user_id = ?
        """, (username, first_name, last_name, language_code, user_id))
    else:
        cursor.execute("""
            INSERT INTO users (user_id, username, first_name, last_name, language_code)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, username, first_name, last_name, language_code))
    
    conn.commit()
    conn.close()


def get_user(user_id):
    """Получить пользователя"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_all_users(active_only=True):
    """Получить всех пользователей"""
    conn = get_connection()
    cursor = conn.cursor()
    
    if active_only:
        cursor.execute("SELECT * FROM users WHERE is_blocked = 0")
    else:
        cursor.execute("SELECT * FROM users")
    
    users = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return users


def get_user_stats():
    """Статистика пользователей"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) as total FROM users WHERE is_blocked = 0")
    active = cursor.fetchone()["total"]
    
    cursor.execute("SELECT COUNT(*) as total FROM users WHERE is_blocked = 1")
    blocked = cursor.fetchone()["total"]
    
    cursor.execute("SELECT COALESCE(SUM(total_searches), 0) as total FROM users")
    total_searches = cursor.fetchone()["total"]
    
    cursor.execute("""
        SELECT COUNT(*) as total FROM users 
        WHERE last_seen >= datetime('now', '-24 hours')
    """)
    today_active = cursor.fetchone()["total"]
    
    cursor.execute("""
        SELECT COUNT(*) as total FROM users 
        WHERE last_seen >= datetime('now', '-7 days')
    """)
    week_active = cursor.fetchone()["total"]
    
    conn.close()
    
    return {
        "active": active,
        "blocked": blocked,
        "total_searches": total_searches,
        "today_active": today_active,
        "week_active": week_active,
    }


def increment_user_searches(user_id):
    """Увеличить счётчик поисков пользователя"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET total_searches = total_searches + 1 WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()


def block_user(user_id):
    """Заблокировать пользователя"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET is_blocked = 1 WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()


def unblock_user(user_id):
    """Разблокировать пользователя"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET is_blocked = 0 WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()


# === История поисков ===

def add_search(user_id, query, found):
    """Записать поиск в историю"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO search_history (user_id, query, found)
        VALUES (?, ?, ?)
    """, (user_id, query, 1 if found else 0))
    
    conn.commit()
    conn.close()


def get_user_search_history(user_id, limit=5):
    """Получить историю поисков пользователя"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT query, found, timestamp 
        FROM search_history 
        WHERE user_id = ? 
        ORDER BY timestamp DESC 
        LIMIT ?
    """, (user_id, limit))
    
    results = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return results


# === Популярные запросы ===

def update_popular_search(query):
    """Обновить счётчик популярного запроса"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO popular_searches (query, count, last_searched)
        VALUES (?, 1, CURRENT_TIMESTAMP)
        ON CONFLICT(query) DO UPDATE SET 
            count = count + 1, 
            last_searched = CURRENT_TIMESTAMP
    """, (query.lower(),))
    
    conn.commit()
    conn.close()


def get_popular_searches(limit=10, days=7):
    """Получить популярные запросы за N дней"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT query, count 
        FROM popular_searches 
        WHERE last_searched >= datetime('now', '-{} days')
        ORDER BY count DESC 
        LIMIT ?
    """.format(days), (limit,))
    
    results = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return results


# === Настройки ===

def get_setting(key, default=None):
    """Получить настройку"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
    row = cursor.fetchone()
    conn.close()
    return row["value"] if row else default


def set_setting(key, value):
    """Сохранить настройку"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO settings (key, value) VALUES (?, ?)
        ON CONFLICT(key) DO UPDATE SET value = ?
    """, (key, str(value), str(value)))
    conn.commit()
    conn.close()


# === Рассылки ===

def add_broadcast(message, sent_count=0, failed_count=0):
    """Записать рассылку"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO broadcasts (message, sent_count, failed_count)
        VALUES (?, ?, ?)
    """, (message, sent_count, failed_count))
    conn.commit()
    conn.close()


def get_broadcast_stats():
    """Статистика последних рассылок"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM broadcasts 
        ORDER BY timestamp DESC 
        LIMIT 5
    """)
    results = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return results


# Инициализация при импорте
init_db()
