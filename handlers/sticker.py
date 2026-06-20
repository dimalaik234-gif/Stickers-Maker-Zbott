# handlers/sticker.py
import asyncio
from datetime import datetime, timedelta
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, BufferedInputFile, InputSticker
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.exceptions import TelegramBadRequest
from aiogram.enums import StickerFormat
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import logging

from database import get_current_pack, get_user_lang
from locales import get_text
from utils.img_processor import process_image

router = Router()
logger = logging.getLogger(__name__)


class StickerCreation(StatesGroup):
    waiting_for_mode = State()
    waiting_for_emoji = State()


# Store temporary data
pending_stickers = {}

# Popular emojis
POPULAR_EMOJIS = ["😊", "😂", "❤️", "👍", "🔥", "✨", "🎉", "😎", "🤔", "😍", "🥰", "😭", "💀", "🙏", "👌"]


@router.message(F.photo)
async def handle_photo(message: Message, state: FSMContext):
    """Handle incoming photos."""
    user_id = message.from_user.id
    lang = await get_user_lang(user_id)
    
    # Check if user has active pack
    current_pack = await get_current_pack(user_id)
    if not current_pack:
        await message.answer(get_text(lang, 'no_active_pack'))
        return
    
    logger.info(f"📸 Получено фото от пользователя {user_id}")
    
    file_id = message.photo[-1].file_id
    
    # Store file_id
    await state.update_data(file_id=file_id, timestamp=datetime.now())
    
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
    
    await state.set_state(StickerCreation.waiting_for_mode)
    await message.answer(
        get_text(lang, 'choose_mode'),
        reply_markup=builder.as_markup()
    )


@router.message(F.document)
async def handle_document(message: Message, state: FSMContext):
    """Handle incoming documents (images only)."""
    user_id = message.from_user.id
    lang = await get_user_lang(user_id)
    
    # Check if user has active pack
    current_pack = await get_current_pack(user_id)
    if not current_pack:
        await message.answer(get_text(lang, 'no_active_pack'))
        return
    
    # Check if it's an image document
    if not message.document.mime_type or not message.document.mime_type.startswith('image/'):
        await message.answer(get_text(lang, 'send_photo'))
        return
    
    logger.info(f"📄 Получен документ-изображение от пользователя {user_id}")
    
    file_id = message.document.file_id
    
    # Store file_id
    await state.update_data(file_id=file_id, timestamp=datetime.now())
    
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
    
    await state.set_state(StickerCreation.waiting_for_mode)
    await message.answer(
        get_text(lang, 'choose_mode'),
        reply_markup=builder.as_markup()
    )


@router.callback_query(F.data.startswith("mode_"), StickerCreation.waiting_for_mode)
async def process_mode_selection(callback: CallbackQuery, state: FSMContext, bot: Bot):
    """Process mode selection and show emoji picker."""
    user_id = callback.from_user.id
    lang = await get_user_lang(user_id)
    
    remove_bg = callback.data == "mode_remove_bg"
    
    data = await state.get_data()
    file_id = data.get('file_id')
    
    if not file_id:
        await callback.answer(get_text(lang, 'callback_expired'), show_alert=True)
        return
    
    # Process image
    await callback.message.edit_text(get_text(lang, 'processing'))
    
    try:
        # Download and process image
        file = await bot.get_file(file_id)
        image_bytes = await bot.download_file(file.file_path)
        image_data = image_bytes.read()
        
        loop = asyncio.get_event_loop()
        processed_buffer = await loop.run_in_executor(
            None,
            process_image,
            image_data,
            remove_bg
        )
        
        # Store processed image
        await state.update_data(processed_image=processed_buffer.getvalue(), remove_bg=remove_bg)
        
        # Show emoji picker
        builder = InlineKeyboardBuilder()
        for emoji in POPULAR_EMOJIS:
            builder.button(text=emoji, callback_data=f"emoji_{emoji}")
        
        builder.button(text=get_text(lang, 'custom_emoji_input'), callback_data="emoji_custom")
        builder.adjust(5)
        
        await state.set_state(StickerCreation.waiting_for_emoji)
        await callback.message.edit_text(
            get_text(lang, 'choose_emoji'),
            reply_markup=builder.as_markup()
        )
        
    except Exception as e:
        logger.error(f"❌ Ошибка обработки: {e}")
        await callback.message.edit_text(get_text(lang, 'error_general'))
        await state.clear()
    
    await callback.answer()


@router.callback_query(F.data.startswith("emoji_"), StickerCreation.waiting_for_emoji)
async def process_emoji_selection(callback: CallbackQuery, state: FSMContext, bot: Bot):
    """Process emoji selection and add sticker."""
    user_id = callback.from_user.id
    lang = await get_user_lang(user_id)
    
    if callback.data == "emoji_custom":
        await callback.message.edit_text(get_text(lang, 'custom_emoji_input'))
        await callback.answer()
        return
    
    emoji = callback.data.split("_", 1)[1]
    
    await add_sticker_to_pack(callback.message, state, bot, user_id, lang, emoji)
    await callback.answer()


@router.message(StickerCreation.waiting_for_emoji)
async def process_custom_emoji(message: Message, state: FSMContext, bot: Bot):
    """Process custom emoji text input."""
    user_id = message.from_user.id
    lang = await get_user_lang(user_id)
    
    emoji = message.text.strip()
    
    # Simple emoji validation
    if len(emoji) > 10:
        await message.answer("❌ Слишком длинный текст. Отправь только эмодзи.")
        return
    
    await add_sticker_to_pack(message, state, bot, user_id, lang, emoji)


async def add_sticker_to_pack(message, state: FSMContext, bot: Bot, user_id: int, lang: str, emoji: str):
    """Add sticker to pack with given emoji."""
    data = await state.get_data()
    processed_image = data.get('processed_image')
    
    if not processed_image:
        await message.answer(get_text(lang, 'error_general'))
        await state.clear()
        return
    
    current_pack = await get_current_pack(user_id)
    if not current_pack:
        await message.answer(get_text(lang, 'no_active_pack'))
        await state.clear()
        return
    
    pack_id, pack_name, pack_title, pack_type = current_pack
    
    # Determine sticker format based on pack type
    if pack_type == "emoji":
        sticker_format = StickerFormat.STATIC  # Custom emoji still uses static format
    else:
        sticker_format = StickerFormat.STATIC
    
    try:
        status_msg = await message.answer(get_text(lang, 'adding_sticker'))
        
        # Prepare sticker
        sticker_file = BufferedInputFile(processed_image, filename="sticker.png")
        input_sticker = InputSticker(
            sticker=sticker_file,
            emoji_list=[emoji],
            format="static"
        )
        
        # Try to add to existing pack
        try:
            await bot.add_sticker_to_set(
                user_id=user_id,
                name=pack_name,
                sticker=input_sticker
            )
            logger.info(f"✅ Стикер добавлен в пак {pack_name}")
        except TelegramBadRequest as e:
            if "STICKERSET_INVALID" in str(e) or "not found" in str(e).lower():
                # Create new pack
                sticker_file_new = BufferedInputFile(processed_image, filename="sticker.png")
                input_sticker_new = InputSticker(
                    sticker=sticker_file_new,
                    emoji_list=[emoji],
                    format="static"
                )
                
                await bot.create_new_sticker_set(
                    user_id=user_id,
                    name=pack_name,
                    title=pack_title,
                    stickers=[input_sticker_new],
                    sticker_format=sticker_format
                )
                logger.info(f"✅ Создан новый пак {pack_name}")
            else:
                raise
        
        # Send success
        pack_link = f"https://t.me/addstickers/{pack_name}"
        await status_msg.edit_text(
            get_text(lang, 'success', link=pack_link)
        )
        
    except Exception as e:
        logger.error(f"❌ Ошибка добавления стикера: {e}")
        import traceback
        traceback.print_exc()
        await message.answer(get_text(lang, 'error_general'))
    
    await state.clear()
