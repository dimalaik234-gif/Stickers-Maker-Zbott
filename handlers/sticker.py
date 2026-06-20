# handlers/sticker.py
import asyncio
from datetime import datetime, timedelta
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, BufferedInputFile, InputSticker
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.exceptions import TelegramBadRequest
import logging

from database import get_user_pack, set_user_pack, get_user_lang
from locales import get_text
from utils.img_processor import process_image

router = Router()
logger = logging.getLogger(__name__)

# Store temporary photo data for callback processing with timestamp
pending_images = {}

# Timeout for pending images
PENDING_TIMEOUT = 600  # 10 minutes


@router.message(F.photo)
async def handle_photo(message: Message):
    """Handle incoming photos."""
    user_id = message.from_user.id
    lang = await get_user_lang(user_id)
    
    logger.info(f"📸 Получено фото от пользователя {user_id}")
    
    file_id = message.photo[-1].file_id
    
    # Store file_id with timestamp
    pending_images[user_id] = (file_id, datetime.now())
    
    # Show processing mode buttons
    builder = InlineKeyboardBuilder()
    builder.button(
        text=get_text(lang, 'mode_remove_bg'),
        callback_data="mode_remove_bg"
    )
    builder.button(
        text=get_text(lang, 'mode_keep_bg'),
        callback_data="mode_keep_bg"
    )
    builder.adjust(1)
    
    await message.answer(
        get_text(lang, 'choose_mode'),
        reply_markup=builder.as_markup()
    )


@router.message(F.document)
async def handle_document(message: Message):
    """Handle incoming documents (images only)."""
    user_id = message.from_user.id
    lang = await get_user_lang(user_id)
    
    # Check if it's an image document
    if not message.document.mime_type or not message.document.mime_type.startswith('image/'):
        await message.answer(get_text(lang, 'send_photo'))
        return
    
    logger.info(f"📄 Получен документ-изображение от пользователя {user_id}")
    
    file_id = message.document.file_id
    
    # Store file_id with timestamp
    pending_images[user_id] = (file_id, datetime.now())
    
    # Show processing mode buttons
    builder = InlineKeyboardBuilder()
    builder.button(
        text=get_text(lang, 'mode_remove_bg'),
        callback_data="mode_remove_bg"
    )
    builder.button(
        text=get_text(lang, 'mode_keep_bg'),
        callback_data="mode_keep_bg"
    )
    builder.adjust(1)
    
    await message.answer(
        get_text(lang, 'choose_mode'),
        reply_markup=builder.as_markup()
    )


@router.callback_query(F.data.startswith("mode_"))
async def process_sticker_mode(callback: CallbackQuery, bot: Bot):
    """Process sticker creation based on selected mode."""
    user_id = callback.from_user.id
    lang = await get_user_lang(user_id)
    
    logger.info(f"🎨 Пользователь {user_id} выбрал режим: {callback.data}")
    
    # Get stored file_id
    pending_data = pending_images.get(user_id)
    if not pending_data:
        await callback.answer(get_text(lang, 'callback_expired'), show_alert=True)
        logger.warning(f"⚠️ Нет pending image для пользователя {user_id}")
        return
    
    file_id, timestamp = pending_data
    
    # Check if not expired
    if datetime.now() - timestamp > timedelta(seconds=PENDING_TIMEOUT):
        del pending_images[user_id]
        await callback.answer(get_text(lang, 'callback_expired'), show_alert=True)
        logger.warning(f"⏰ Истек таймаут для пользователя {user_id}")
        return
    
    # Determine mode
    remove_bg = callback.data == "mode_remove_bg"
    
    # Notify user
    await callback.message.edit_text(get_text(lang, 'processing'))
    
    try:
        # Download image
        logger.info(f"⬇️ Скачивание файла {file_id}")
        file = await bot.get_file(file_id)
        image_bytes = await bot.download_file(file.file_path)
        image_data = image_bytes.read()
        
        logger.info(f"🖼 Обработка изображения (remove_bg={remove_bg})")
        
        # Process image in executor to avoid blocking
        loop = asyncio.get_event_loop()
        processed_buffer = await loop.run_in_executor(
            None,
            process_image,
            image_data,
            remove_bg
        )
        
        logger.info(f"✅ Изображение обработано")
        
        # Get or create sticker pack
        pack_short_name = await get_user_pack(user_id)
        bot_info = await bot.get_me()
        bot_username = bot_info.username
        
        if not pack_short_name:
            # Generate unique pack name
            pack_short_name = f"pack_{user_id}_by_{bot_username}"
            await set_user_pack(user_id, pack_short_name)
            logger.info(f"📦 Создан новый pack_short_name: {pack_short_name}")
        
        # Ensure pack name includes bot username
        if not pack_short_name.endswith(f"_by_{bot_username}"):
            pack_short_name = f"{pack_short_name}_by_{bot_username}"
            await set_user_pack(user_id, pack_short_name)
        
        # Prepare sticker file
        sticker_file = BufferedInputFile(
            processed_buffer.read(),
            filename="sticker.png"
        )
        
        # Create InputSticker object
        input_sticker = InputSticker(
            sticker=sticker_file,
            emoji_list=["😊"],
            format="static"
        )
        
        await callback.message.edit_text(get_text(lang, 'adding_sticker'))
        
        logger.info(f"➕ Добавление стикера в пак {pack_short_name}")
        
        # Try to add to existing pack, create new if doesn't exist
        try:
            await bot.add_sticker_to_set(
                user_id=user_id,
                name=pack_short_name,
                sticker=input_sticker
            )
            logger.info(f"✅ Стикер добавлен в существующий пак")
        except TelegramBadRequest as e:
            error_str = str(e)
            logger.warning(f"⚠️ Ошибка добавления в пак: {error_str}")
            
            if "STICKERSET_INVALID" in error_str or "not found" in error_str.lower() or "STICKER_PACK_NAME_INVALID" in error_str:
                # Create new sticker pack
                pack_title = f"{callback.from_user.first_name}'s Stickers" if lang == 'en' else f"Стикеры {callback.from_user.first_name}"
                
                logger.info(f"🆕 Создание нового стикерпака: {pack_title}")
                
                # Need to recreate the file buffer since it was consumed
                processed_buffer.seek(0)
                sticker_file_new = BufferedInputFile(
                    processed_buffer.read(),
                    filename="sticker.png"
                )
                input_sticker_new = InputSticker(
                    sticker=sticker_file_new,
                    emoji_list=["😊"],
                    format="static"
                )
                
                await bot.create_new_sticker_set(
                    user_id=user_id,
                    name=pack_short_name,
                    title=pack_title,
                    stickers=[input_sticker_new]
                )
                logger.info(f"✅ Новый стикерпак создан")
            else:
                raise
        
        # Send success message with link
        pack_link = f"https://t.me/addstickers/{pack_short_name}"
        await callback.message.edit_text(
            get_text(lang, 'success', link=pack_link)
        )
        
        logger.info(f"🎉 Успех! Ссылка: {pack_link}")
        
        # Clean up
        if user_id in pending_images:
            del pending_images[user_id]
        
    except TelegramBadRequest as e:
        error_message = str(e)
        logger.error(f"❌ Telegram API Error: {error_message}")
        await callback.message.edit_text(
            get_text(lang, 'error_telegram', error=error_message)
        )
    except Exception as e:
        logger.error(f"❌ Неожиданная ошибка: {e}")
        import traceback
        traceback.print_exc()
        await callback.message.edit_text(get_text(lang, 'error_general'))
    
    await callback.answer()
