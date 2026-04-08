"""
Модуль автобэкапов
"""
import os
import shutil
import json
from datetime import datetime

BACKUP_DIR = os.path.join(os.path.dirname(__file__), "..", "backups")
os.makedirs(BACKUP_DIR, exist_ok=True)

CATEGORY_FILES = [
    "compatibility_glass.json",
    "compatibility_case.json",
    "compatibility_display.json",
    "compatibility_battery.json",
    "compatibility_oca.json",
]


def backup_compatibility_json():
    """Бэкап всех файлов категорий"""
    backups = []
    for filename in CATEGORY_FILES:
        source = os.path.join(os.path.dirname(__file__), "..", filename)
        if not os.path.exists(source):
            continue
        timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
        backup_path = os.path.join(BACKUP_DIR, f"{filename.replace('.json', '')}_{timestamp}.json")
        shutil.copy2(source, backup_path)
        backups.append(backup_path)
    return backups


def backup_database():
    """Бэкап БД"""
    source = os.path.join(os.path.dirname(__file__), "..", "bot.db")
    if not os.path.exists(source):
        return None

    timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
    backup_path = os.path.join(BACKUP_DIR, f"bot_{timestamp}.db")

    shutil.copy2(source, backup_path)
    return backup_path


def cleanup_old_backups(keep_days=7):
    """Удалить старые бэкапы"""
    if not os.path.exists(BACKUP_DIR):
        return

    cutoff = datetime.now()
    for filename in os.listdir(BACKUP_DIR):
        filepath = os.path.join(BACKUP_DIR, filename)
        file_time = datetime.fromtimestamp(os.path.getmtime(filepath))

        if file_time < cutoff.replace(day=cutoff.day - keep_days):
            os.remove(filepath)


def get_backup_list():
    """Получить список бэкапов"""
    if not os.path.exists(BACKUP_DIR):
        return []

    backups = []
    for filename in sorted(os.listdir(BACKUP_DIR)):
        filepath = os.path.join(BACKUP_DIR, filename)
        size = os.path.getsize(filepath)
        mtime = datetime.fromtimestamp(os.path.getmtime(filepath))

        backups.append({
            "name": filename,
            "path": filepath,
            "size": f"{size / 1024:.1f} KB",
            "date": mtime.strftime("%Y-%m-%d %H:%M")
        })

    return backups
