"""
Модуль логирования
"""
import logging
import os
from datetime import datetime

LOG_DIR = os.path.join(os.path.dirname(__file__), "..", "logs")
os.makedirs(LOG_DIR, exist_ok=True)

LOG_FILE = os.path.join(LOG_DIR, f"bot_{datetime.now().strftime('%Y_%m')}.log")
ERROR_LOG = os.path.join(LOG_DIR, "errors.log")

# Основной логгер
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler()
    ]
)

# Отдельный логгер для ошибок
error_logger = logging.getLogger("errors")
error_handler = logging.FileHandler(ERROR_LOG, encoding="utf-8")
error_handler.setLevel(logging.ERROR)
error_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
error_handler.setFormatter(error_formatter)
error_logger.addHandler(error_handler)

logger = logging.getLogger(__name__)


def log_error(error, context=None):
    """Логирование ошибки"""
    msg = f"ERROR: {error}"
    if context:
        msg += f"\nContext: {context}"
    error_logger.error(msg, exc_info=True)


def log_search(user_id, query, found):
    """Логирование поиска"""
    status = "FOUND" if found else "NOT FOUND"
    logger.info(f"Search [{status}] user={user_id} query='{query}'")


def log_broadcast(sent, failed):
    """Логирование рассылки"""
    logger.info(f"Broadcast sent={sent}, failed={failed}")


def log_user_action(user_id, action):
    """Логирование действия пользователя"""
    logger.info(f"User {user_id}: {action}")
