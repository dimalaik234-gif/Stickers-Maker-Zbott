# handlers/common.py
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database import get_user_lang, set_user_lang
from locales import get_text

router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message):
    """Handle /start command."""
    user_id = message.from_user.id
    lang = await get_user_lang(user_id)
    
    # Show language selection for new users
    builder = InlineKeyboardBuilder()
    builder.button(text="🇷🇺 Русский", callback_data="lang_ru")
    builder.button(text="🇬🇧 English", callback_data="lang_en")
    builder.adjust(2)
    
    await message.answer(
        get_text(lang, 'welcome'),
        reply_markup=builder.as_markup()
    )


@router.message(Command("help"))
async def cmd_help(message: Message):
    """Handle /help command."""
    user_id = message.from_user.id
    lang = await get_user_lang(user_id)
    
    await message.answer(get_text(lang, 'help'))


@router.message(Command("language"))
async def cmd_language(message: Message):
    """Handle /language command."""
    user_id = message.from_user.id
    lang = await get_user_lang(user_id)
    
    builder = InlineKeyboardBuilder()
    builder.button(text="🇷🇺 Русский", callback_data="lang_ru")
    builder.button(text="🇬🇧 English", callback_data="lang_en")
    builder.adjust(2)
    
    await message.answer(
        get_text(lang, 'choose_language'),
        reply_markup=builder.as_markup()
    )


@router.callback_query(F.data.startswith("lang_"))
async def process_language_selection(callback: CallbackQuery):
    """Handle language selection callback."""
    user_id = callback.from_user.id
    selected_lang = callback.data.split("_")[1]
    
    await set_user_lang(user_id, selected_lang)
    
    await callback.message.edit_text(
        get_text(selected_lang, 'language_changed')
    )
    
    await callback.answer()


# ===== НОВЫЕ ОБРАБОТЧИКИ =====

@router.message(F.text & ~F.text.startswith('/'))
async def handle_text_message(message: Message):
    """Handle all text messages that are not commands."""
    user_id = message.from_user.id
    lang = await get_user_lang(user_id)
    
    await message.answer(get_text(lang, 'send_photo'))


@router.message(F.sticker)
async def handle_sticker(message: Message):
    """Handle stickers sent to bot."""
    user_id = message.from_user.id
    lang = await get_user_lang(user_id)
    
    await message.answer(get_text(lang, 'send_photo'))


@router.message(F.video | F.video_note | F.voice | F.audio | F.animation)
async def handle_media(message: Message):
    """Handle video, voice, audio, and animations."""
    user_id = message.from_user.id
    lang = await get_user_lang(user_id)
    
    await message.answer(get_text(lang, 'send_photo'))


@router.callback_query()
async def handle_unknown_callback(callback: CallbackQuery):
    """Handle unknown or outdated callbacks."""
    user_id = callback.from_user.id
    lang = await get_user_lang(user_id)
    
    await callback.answer(
        get_text(lang, 'callback_expired'),
        show_alert=True
    )
