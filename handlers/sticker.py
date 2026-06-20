# handlers/sticker.py
import asyncio
from datetime import datetime, timedelta
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, BufferedInputFile, InputSticker
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.exceptions import TelegramBadRequest

from database import get_user_pack, set_user_pack, get_user_lang
from locales import get_text
from utils.img_processor import process_image

router = Router()

# Store temporary photo data for callback processing with timestamp
pending_images = {}

# Cleanup task interval (seconds)
CLEANUP_INTERVAL = 300  # 5 minutes
PENDING_TIMEOUT = 600  # 10 minutes


async def cleanup_pending_images():
    """Periodically clean up old pending images."""
    while True:
        await asyncio.sleep(CLEANUP_INTERVAL)
        current_time = datetime.now()
        expired_users = [
            user_id for user_id, (_, timestamp) in pending_images.items()
            if current_time - timestamp > timedelta(seconds=PENDING_TIMEOUT)
        ]
        for user_id in expired_users:
            del pending_images[user_id]
        if expired_users:
            print(f"🧹 Очищено {len(expired_users)} устаревших изображений")


@router.message(F.photo | F.document)
async def handle_image(message: Message):
    """Handle incoming photos or documents."""
    user_id = message.from_user.id
    lang = await get_user_lang(user_id)
    
    # Determine file to download
    if message.photo:
        file_id = message.photo[-1].file_id
    elif message.document and message.document.mime_type and message.document.mime_type.startswith('image/'):
        file_id = message.document.file_id
    else:
        await message.answer(get_text(lang, 'send_photo'))
        return
    
    # Store file_id with timestamp for callback processing
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
    
    # Get stored file_id
    pending_data = pending_images.get(user_id)
    if not pending_data:
        await callback.answer(get_text(lang, 'callback_expired'), show_alert=True)
        return
    
    file_id, timestamp = pending_data
    
    # Check if not expired
    if datetime.now() - timestamp > timedelta(seconds=PENDING_TIMEOUT):
        del pending_images[user_id]
        await callback.answer(get_text(lang, 'callback_expired'), show_alert=True)
        return
    
    # Determine mode
    remove_bg = callback.data == "mode_remove_bg"
    
    # Notify user
    await callback.message.edit_text(get_text(lang, 'processing'))
    
    try:
        # Download image
        file = await bot.get_file(file_id)
        image_bytes = await bot.download_file(file.file_path)
        image_data = image_bytes.read()
        
        # Process image in executor to avoid blocking
        loop = asyncio.get_event_loop()
        processed_buffer = await loop.run_in_executor(
            None,
            process_image,
            image_data,
            remove_bg
        )
        
        # Get or create sticker pack
        pack_short_name = await get_user_pack(user_id)
        bot_info = await bot.get_me()
        bot_username = bot_info.username
        
        if not pack_short_name:
            # Generate unique pack name
            pack_short_name = f"pack_{user_id}_by_{bot_username}"
            await set_user_pack(user_id, pack_short_name)
        
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
        
        # Try to add to existing pack, create new if doesn't exist
        try:
            await bot.add_sticker_to_set(
                user_id=user_id,
                name=pack_short_name,
                sticker=input_sticker
            )
        except TelegramBadRequest as e:
            if "STICKERSET_INVALID" in str(e) or "not found" in str(e).lower():
                # Create new sticker pack
                pack_title = f"{callback.from_user.first_name}'s Stickers" if lang == 'en' else f"Стикеры {callback.from_user.first_name}"
                
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
            else:
                raise
        
        # Send success message with link
        pack_link = f"https://t.me/addstickers/{pack_short_name}"
        await callback.message.edit_text(
            get_text(lang, 'success', link=pack_link)
        )
        
        # Clean up
        if user_id in pending_images:
            del pending_images[user_id]
        
    except TelegramBadRequest as e:
        await callback.message.edit_text(
            get_text(lang, 'error_telegram', error=str(e))
        )
        print(f"❌ Telegram API Error: {e}")
    except Exception as e:
        print(f"❌ Error processing sticker: {e}")
        import traceback
        traceback.print_exc()
        await callback.message.edit_text(get_text(lang, 'error_general'))
    
    await callback.answer()


# Start cleanup task
asyncio.create_task(cleanup_pending_images())
