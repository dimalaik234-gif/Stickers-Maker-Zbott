# handlers/common.py
from aiogram import Router, F
from aiogram.filters import Command, CommandStart, StateFilter
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database import (
    get_user_lang, set_user_lang, get_user_packs, 
    get_current_pack, set_current_pack, create_sticker_pack,
    get_pack_by_name
)
from locales import get_text
import re

router = Router()


class PackCreation(StatesGroup):
    waiting_for_name = State()
    waiting_for_title = State()
    waiting_for_type = State()


@router.message(CommandStart())
async def cmd_start(message: Message):
    """Handle /start command."""
    user_id = message.from_user.id
    lang = await get_user_lang(user_id)
    
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


@router.message(Command("language", "lang"))
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


@router.message(Command("packs"))
async def cmd_packs(message: Message):
    """Show user's sticker packs."""
    user_id = message.from_user.id
    lang = await get_user_lang(user_id)
    
    packs = await get_user_packs(user_id)
    current_pack = await get_current_pack(user_id)
    
    if not packs:
        await message.answer(get_text(lang, 'no_packs'))
        return
    
    text = get_text(lang, 'your_packs')
    builder = InlineKeyboardBuilder()
    
    for pack in packs:
        pack_id, pack_name, pack_title, pack_type, created_at = pack
        
        emoji = "🎭" if pack_type == "emoji" else "📱"
        type_text = get_text(lang, f'pack_type_{pack_type}')
        link = f"https://t.me/addstickers/{pack_name}"
        active = "✅" if current_pack and current_pack[0] == pack_id else "⬜"
        
        text += get_text(lang, 'pack_item', 
                        emoji=emoji, 
                        title=pack_title, 
                        type=type_text,
                        link=link,
                        active=active)
        
        builder.button(
            text=f"{emoji} {pack_title}",
            callback_data=f"select_pack_{pack_id}"
        )
    
    builder.adjust(1)
    
    await message.answer(text, reply_markup=builder.as_markup())


@router.callback_query(F.data.startswith("select_pack_"))
async def select_pack(callback: CallbackQuery):
    """Select active pack."""
    user_id = callback.from_user.id
    lang = await get_user_lang(user_id)
    
    pack_id = int(callback.data.split("_")[2])
    
    packs = await get_user_packs(user_id)
    selected_pack = next((p for p in packs if p[0] == pack_id), None)
    
    if selected_pack:
        await set_current_pack(user_id, pack_id)
        await callback.answer(
            get_text(lang, 'current_pack_set', title=selected_pack[2]),
            show_alert=True
        )
    
    await callback.message.delete()


@router.message(Command("newpack"))
async def cmd_newpack(message: Message, state: FSMContext):
    """Start creating a new sticker pack."""
    user_id = message.from_user.id
    lang = await get_user_lang(user_id)
    
    await state.set_state(PackCreation.waiting_for_name)
    await message.answer(get_text(lang, 'create_pack_name'))


@router.message(PackCreation.waiting_for_name)
async def process_pack_name(message: Message, state: FSMContext, bot):
    """Process pack name input."""
    user_id = message.from_user.id
    lang = await get_user_lang(user_id)
    
    pack_name = message.text.strip().lower()
    
    # Validate pack name
    if not re.match(r'^[a-z0-9_]+$', pack_name):
        await message.answer(get_text(lang, 'pack_name_invalid'))
        return
    
    # Add bot username
    bot_info = await bot.get_me()
    full_pack_name = f"{pack_name}_by_{bot_info.username}"
    
    # Check if exists
    existing = await get_pack_by_name(user_id, full_pack_name)
    if existing:
        await message.answer(get_text(lang, 'pack_exists'))
        return
    
    await state.update_data(pack_name=full_pack_name)
    await state.set_state(PackCreation.waiting_for_title)
    await message.answer(get_text(lang, 'create_pack_title'))


@router.message(PackCreation.waiting_for_title)
async def process_pack_title(message: Message, state: FSMContext):
    """Process pack title input."""
    user_id = message.from_user.id
    lang = await get_user_lang(user_id)
    
    pack_title = message.text.strip()
    
    if len(pack_title) < 1 or len(pack_title) > 64:
        await message.answer("❌ Название должно быть от 1 до 64 символов")
        return
    
    await state.update_data(pack_title=pack_title)
    
    # Choose pack type
    builder = InlineKeyboardBuilder()
    builder.button(
        text=get_text(lang, 'pack_type_btn_regular'),
        callback_data="packtype_regular"
    )
    builder.button(
        text=get_text(lang, 'pack_type_btn_emoji'),
        callback_data="packtype_emoji"
    )
    builder.adjust(1)
    
    await state.set_state(PackCreation.waiting_for_type)
    await message.answer(
        get_text(lang, 'choose_pack_type'),
        reply_markup=builder.as_markup()
    )


@router.callback_query(F.data.startswith("packtype_"), PackCreation.waiting_for_type)
async def process_pack_type(callback: CallbackQuery, state: FSMContext):
    """Process pack type selection."""
    user_id = callback.from_user.id
    lang = await get_user_lang(user_id)
    
    pack_type = callback.data.split("_")[1]
    
    data = await state.get_data()
    pack_name = data['pack_name']
    pack_title = data['pack_title']
    
    # Create pack record in database
    await create_sticker_pack(user_id, pack_name, pack_title, pack_type)
    
    link = f"https://t.me/addstickers/{pack_name}"
    
    await callback.message.edit_text(
        get_text(lang, 'pack_created_success', title=pack_title, link=link)
    )
    
    await state.clear()
    await callback.answer()


# Catch-all handlers
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


@router.message(F.text.startswith('/'))
async def handle_unknown_command(message: Message):
    """Handle unknown commands."""
    user_id = message.from_user.id
    lang = await get_user_lang(user_id)
    
    await message.answer(get_text(lang, 'unknown_command'))


@router.message()
async def handle_any_message(message: Message):
    """Handle any other message type."""
    user_id = message.from_user.id
    lang = await get_user_lang(user_id)
    
    await message.answer(get_text(lang, 'send_photo'))
