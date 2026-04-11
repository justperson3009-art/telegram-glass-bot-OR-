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
    
    # Пользователи
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
            total_searches INTEGER DEFAULT 0,
            active_category TEXT DEFAULT 'glass',
            role TEXT DEFAULT 'user'
        )
    """)

    # Миграция — добавляем колонки если их нет
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN active_category TEXT DEFAULT 'glass'")
        conn.commit()
    except:
        pass
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'user'")
        conn.commit()
    except:
        pass

    # Подписки
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS subscriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            plan TEXT DEFAULT 'free',
            is_active INTEGER DEFAULT 1,
            expires_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
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

    # Обратная связь (подошло/не подошло)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            query TEXT,
            matched_model TEXT,
            rating INTEGER,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    """)

    # Жалобы — что не подошло с комментарием
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS issue_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            category TEXT,
            query TEXT,
            matched_model TEXT,
            comment TEXT,
            status TEXT DEFAULT 'pending',
            admin_response TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    """)
    conn.commit()
    
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


def set_user_category(user_id, category):
    """Установить активную категорию пользователя"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET active_category = ? WHERE user_id = ?", (category, user_id))
    conn.commit()
    conn.close()


def get_user_category(user_id):
    """Получить активную категорию пользователя"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT active_category FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return row["active_category"] if row else "glass"


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


# === Обратная связь ===

def add_feedback(user_id, query, matched_model, rating):
    """Добавить отзыв: rating=1 (подошло), rating=0 (не подошло)"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO feedback (user_id, query, matched_model, rating)
        VALUES (?, ?, ?, ?)
    """, (user_id, query, matched_model, rating))
    conn.commit()
    conn.close()


def get_model_compatibility(model_name):
    """Получить рейтинг совместимости модели (в %)"""
    conn = get_connection()
    cursor = conn.cursor()

    # Ищем все отзывы по этой модели (частичное совпадение)
    cursor.execute("""
        SELECT rating, COUNT(*) as cnt
        FROM feedback
        WHERE matched_model LIKE ?
        GROUP BY rating
    """, (f"%{model_name}%",))

    results = {row["rating"]: row["cnt"] for row in cursor.fetchall()}
    conn.close()

    positive = results.get(1, 0)
    negative = results.get(0, 0)
    total = positive + negative

    if total == 0:
        return {"percent": None, "positive": 0, "negative": 0, "total": 0, "status": "unknown"}

    percent = round((positive / total) * 100, 1)

    if percent >= 80:
        status = "confirmed"
    elif percent >= 50:
        status = "partial"
    else:
        status = "unconfirmed"

    return {
        "percent": percent,
        "positive": positive,
        "negative": negative,
        "total": total,
        "status": status
    }


def get_unconfirmed_models():
    """Получить модели с низким рейтингом (<50%)"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT matched_model, 
               SUM(CASE WHEN rating = 1 THEN 1 ELSE 0 END) as positive,
               SUM(CASE WHEN rating = 0 THEN 1 ELSE 0 END) as negative,
               COUNT(*) as total
        FROM feedback
        GROUP BY matched_model
        HAVING total >= 3
        ORDER BY CAST(SUM(CASE WHEN rating = 1 THEN 1 ELSE 0 END) AS FLOAT) / COUNT(*) ASC
        LIMIT 20
    """)

    results = []
    for row in cursor.fetchall():
        percent = round((row["positive"] / row["total"]) * 100, 1) if row["total"] > 0 else 0
        if percent < 50:
            results.append({
                "model": row["matched_model"],
                "percent": percent,
                "positive": row["positive"],
                "negative": row["negative"],
                "total": row["total"]
            })

    conn.close()
    return results


def get_feedback_stats():
    """Статистика обратной связи"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) as total FROM feedback WHERE rating = 1")
    positive = cursor.fetchone()["total"]

    cursor.execute("SELECT COUNT(*) as total FROM feedback WHERE rating = 0")
    negative = cursor.fetchone()["total"]

    total = positive + negative
    percent = round((positive / total * 100), 1) if total > 0 else 0

    conn.close()
    return {
        "positive": positive,
        "negative": negative,
        "total": total,
        "percent": percent
    }


def get_latest_feedback(limit=20):
    """Последние отзывы"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT f.query, f.matched_model, f.rating, f.timestamp,
               u.first_name, u.username
        FROM feedback f
        LEFT JOIN users u ON f.user_id = u.user_id
        ORDER BY f.timestamp DESC
        LIMIT ?
    """, (limit,))
    results = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return results


# === Роли и помощники ===

def get_user_role(user_id):
    """Получить роль пользователя: admin, helper, user"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT role FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return row["role"] if row else "user"


def set_user_role(user_id, role):
    """Установить роль пользователя"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET role = ? WHERE user_id = ?", (role, user_id))
    conn.commit()
    conn.close()


def get_helpers():
    """Получить список помощников"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE role = 'helper' ORDER BY first_seen DESC")
    results = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return results


def is_admin(user_id):
    """Проверить что пользователь — админ"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT role FROM users WHERE user_id = ? AND is_blocked = 0", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return row and row["role"] == "admin"


def is_helper(user_id):
    """Проверить что пользователь — помощник"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT role FROM users WHERE user_id = ? AND is_blocked = 0", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return row and row["role"] in ("admin", "helper")


# === Подписки ===

def add_subscription(user_id, plan="free", days=30):
    """Добавить/обновить подписку"""
    from datetime import datetime, timedelta
    conn = get_connection()
    cursor = conn.cursor()
    expires = (datetime.now() + timedelta(days=days)).isoformat()
    cursor.execute("""
        INSERT INTO subscriptions (user_id, plan, is_active, expires_at)
        VALUES (?, ?, 1, ?)
        ON CONFLICT DO NOTHING
    """, (user_id, plan, expires))
    conn.commit()
    conn.close()


def get_subscription(user_id):
    """Получить подписку пользователя"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM subscriptions 
        WHERE user_id = ? AND is_active = 1
        ORDER BY created_at DESC LIMIT 1
    """, (user_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_subscription_stats():
    """Статистика подписок"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) as total FROM users WHERE is_blocked = 0")
    total_users = cursor.fetchone()["total"]

    cursor.execute("SELECT COUNT(DISTINCT user_id) as total FROM subscriptions WHERE is_active = 1")
    active_subs = cursor.fetchone()["total"]

    cursor.execute("SELECT plan, COUNT(*) as cnt FROM subscriptions WHERE is_active = 1 GROUP BY plan")
    plans = {row["plan"]: row["cnt"] for row in cursor.fetchall()}

    conn.close()
    return {
        "total_users": total_users,
        "active_subscriptions": active_subs,
        "free_users": total_users - active_subs,
        "plans": plans
    }


# === ЖАЛОБЫ (что не подошло) ===

def add_issue_report(user_id, category, query, matched_model, comment):
    """Добавить жалобу — что не подошло"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO issue_reports (user_id, category, query, matched_model, comment, status)
        VALUES (?, ?, ?, ?, ?, 'pending')
    """, (user_id, category, query, matched_model, comment))
    conn.commit()
    conn.close()


def get_pending_issue_reports(limit=20):
    """Получить необработанные жалобы"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT r.*, u.first_name, u.username
        FROM issue_reports r
        LEFT JOIN users u ON r.user_id = u.user_id
        WHERE r.status = 'pending'
        ORDER BY r.timestamp DESC
        LIMIT ?
    """, (limit,))
    results = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return results


def get_all_issue_reports(limit=50):
    """Получить все жалобы"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT r.*, u.first_name, u.username
        FROM issue_reports r
        LEFT JOIN users u ON r.user_id = u.user_id
        ORDER BY r.timestamp DESC
        LIMIT ?
    """, (limit,))
    results = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return results


def resolve_issue_report(report_id, admin_response=""):
    """Обработать жалобу — отметить как решённую"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE issue_reports SET status = 'resolved', admin_response = ?
        WHERE id = ?
    """, (admin_response, report_id))
    conn.commit()
    conn.close()


def get_issue_reports_stats():
    """Статистика жалоб"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) as total FROM issue_reports")
    total = cursor.fetchone()["total"]

    cursor.execute("SELECT COUNT(*) as total FROM issue_reports WHERE status = 'pending'")
    pending = cursor.fetchone()["total"]

    cursor.execute("SELECT COUNT(*) as total FROM issue_reports WHERE status = 'resolved'")
    resolved = cursor.fetchone()["total"]

    conn.close()
    return {
        "total": total,
        "pending": pending,
        "resolved": resolved
    }
