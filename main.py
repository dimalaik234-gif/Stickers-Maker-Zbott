# main.py
import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from database import init_db
from handlers import common, sticker


async def main():
    """Main entry point for the bot."""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    logger = logging.getLogger(__name__)
    
    # Import here to avoid circular import and allow config to print instructions
    from config import BOT_TOKEN
    
    # Финальная проверка токена
    if not BOT_TOKEN:
        logger.error("❌ Невозможно запустить бота без токена!")
        logger.error("📖 См. инструкцию выше")
        return
    
    logger.info("🔑 Токен загружен успешно")
    logger.info(f"🔑 Токен начинается с: {BOT_TOKEN[:10]}...")
    
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
        
        # Проверка токена
        bot_info = await bot.get_me()
        logger.info(f"✅ Бот подключен: @{bot_info.username} (ID: {bot_info.id})")
        
        dp = Dispatcher()
    except Exception as e:
        logger.error(f"❌ Ошибка создания бота: {e}")
        logger.error(f"❌ Проверьте правильность токена!")
        return
    
    logger.info("📡 Регистрация обработчиков...")
    
    # Правильный порядок роутеров
    dp.include_router(sticker.router)
    dp.include_router(common.router)
    
    logger.info("✅ Все обработчики зарегистрированы")
    
    logger.info("🚀 Запуск long polling...")
    logger.info("✨ Бот работает! Нажмите Ctrl+C для остановки")
    
    try:
        await dp.start_polling(
            bot,
            allowed_updates=dp.resolve_used_update_types(),
            drop_pending_updates=True
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
        import traceback
        traceback.print_exc()
