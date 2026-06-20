# config.py
import os

# КРИТИЧЕСКИ ВАЖНО: Проверьте, что токен правильный!
BOT_TOKEN = os.getenv("BOT_TOKEN", "")

if not BOT_TOKEN or BOT_TOKEN == "8908476972:AAEMCMHpIFutJhX6U4nHbJq2VUHQmHHMH_I":
    raise ValueError("❌ BOT_TOKEN не установлен! Задайте переменную окружения BOT_TOKEN")

DATABASE_PATH = "bot_database.db"
MAX_STICKER_SIZE = 512
