"""Конфигурация бота."""
import os
from pathlib import Path
from dotenv import load_dotenv

# Загружаем .env файл
load_dotenv()

# Базовые директории
BASE_DIR = Path(__file__).parent.resolve()
DATA_DIR = BASE_DIR / "data"
TEMP_DIR = DATA_DIR / "temp"
STICKERS_DIR = DATA_DIR / "stickers"
FONTS_DIR = DATA_DIR / "fonts"

# Создаём директории, если их нет
for d in (DATA_DIR, TEMP_DIR, STICKERS_DIR, FONTS_DIR):
    d.mkdir(parents=True, exist_ok=True)

# Telegram
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0") or "0")

# Пути
DATABASE_PATH = os.getenv("DATABASE_PATH", str(DATA_DIR / "bot.db"))
TEMP_DIR = Path(os.getenv("TEMP_DIR", str(TEMP_DIR)))
STICKERS_DIR = Path(os.getenv("STICKERS_DIR", str(STICKERS_DIR)))
FONTS_DIR = Path(os.getenv("FONTS_DIR", str(FONTS_DIR)))

# Создаём директории (повторно, с учётом переменных окружения)
for d in (TEMP_DIR, STICKERS_DIR, FONTS_DIR):
    d.mkdir(parents=True, exist_ok=True)

# Лимиты Telegram для стикеров
STICKER_SIZE = int(os.getenv("STICKER_SIZE", "512"))
MAX_STICKER_BYTES = int(os.getenv("MAX_STICKER_BYTES", "500000"))

# Дефолтные настройки пользователей
DEFAULT_SETTINGS = {
    "outline_color": "#000000",
    "outline_width": 5,
    "watermark_text": "",
    "default_font": "bold",
    "default_position": "bottom",
}
