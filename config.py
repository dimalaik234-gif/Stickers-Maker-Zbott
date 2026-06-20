# config.py
import os
import sys

# Bothost.ru передает токен через переменную окружения TOKEN или BOT_TOKEN
BOT_TOKEN = os.getenv("TOKEN") or os.getenv("BOT_TOKEN") or os.getenv("TELEGRAM_TOKEN")

# Если токен все еще не найден, попробуйте прочитать из файла
if not BOT_TOKEN:
    try:
        # Bothost.ru может хранить токен в файле /app/token.txt
        with open('/app/token.txt', 'r') as f:
            BOT_TOKEN = f.read().strip()
    except:
        pass

# Если токен все еще не найден, попробуйте из аргументов командной строки
if not BOT_TOKEN and len(sys.argv) > 1:
    BOT_TOKEN = sys.argv[1]

# Финальная проверка
if not BOT_TOKEN or BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
    print("=" * 60)
    print("❌ ОШИБКА: BOT_TOKEN не установлен!")
    print("=" * 60)
    print("\n📝 Инструкция для Bothost.ru:\n")
    print("1. Откройте настройки бота на bothost.ru")
    print("2. Найдите раздел 'Переменные окружения' или 'Environment Variables'")
    print("3. Добавьте переменную:")
    print("   Имя:  TOKEN")
    print("   Значение: ваш_токен_от_@BotFather")
    print("\n4. Или добавьте токен в поле 'Токен бота' в настройках")
    print("=" * 60)
    
    # Не падаем сразу, даем возможность увидеть инструкцию
    BOT_TOKEN = ""

DATABASE_PATH = "bot_database.db"
MAX_STICKER_SIZE = 512
