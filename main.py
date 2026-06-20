# main.py
import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config import BOT_TOKEN
from database import init_db
from handlers import common, sticker


async def main():
    """Main entry point for the bot."""
    # Configure logging with more details
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    logger = logging.getLogger(__name__)
    
    logger.info("🗄️  Инициализация базы данных...")
    try:
        await init_db()
        logger.info("✅ База данных готова")
    except Exception as e:
        logger.error(f"❌ Ошибка инициализации БД: {e}")
        return
    
    logger.info("🤖 Создание экземпляра бота...")
    try:
        bot = Bot(
            token=BOT_TOKEN,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML)
        )
        dp = Dispatcher()
    except Exception as e:
        logger.error(f"❌ Ошибка создания бота: {e}")
        return
    
    logger.info("📡 Регистрация обработчиков...")
    # ВАЖНО: порядок имеет значение - common должен быть ПОСЛЕДНИМ
    dp.include_router(sticker.router)
    dp.include_router(common.router)
    logger.info("✅ Все обработчики зарегистрированы")
    
    logger.info("🚀 Запуск long polling...")
    logger.info("✨ Бот работает! Нажмите Ctrl+C для остановки")
    
    try:
        await dp.start_polling(
            bot,
            allowed_updates=dp.resolve_used_update_types(),
            drop_pending_updates=True  # Пропустить старые обновления при запуске
        )
    except Exception as e:
        logger.error(f"❌ Ошибка во время polling: {e}")
    finally:
        logger.info("🛑 Остановка бота...")
        await bot.session.close()
        logger.info("👋 Бот остановлен")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Остановка по Ctrl+C")
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
