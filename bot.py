"""
Главный файл Telegram-бота для создания стикеров.

Запуск:
    python bot.py

Перед запуском:
    1. Скопируйте .env.example в .env и впишите BOT_TOKEN.
    2. Установите зависимости: pip install -r requirements.txt
"""
from __future__ import annotations

import asyncio
import logging
import os
import random
import re
import shutil
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Optional

from aiogram import Bot, Dispatcher, F, Router, types
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    BufferedInputFile,
    CallbackQuery,
    ContentType,
    FSInputFile,
    InlineKeyboardMarkup,
    Message,
)
from PIL import Image

import keyboards as kb
from config import (
    BOT_TOKEN,
    STICKERS_DIR,
    TEMP_DIR,
    ADMIN_ID,
)
from database import Database
from image_processor import (
    STICKER_SIZE,
    MAX_STICKER_BYTES,
    POPULAR_EMOJIS,
    add_border,
    add_drop_shadow,
    add_emoji,
    add_glow,
    add_outline,
    add_pattern,
    add_text,
    add_watermark,
    adjust_brightness,
    adjust_contrast,
    adjust_saturation,
    adjust_sharpness,
    crop_circle,
    crop_diamond,
    crop_hexagon,
    crop_rounded,
    crop_star,
    filter_blur,
    filter_contour,
    filter_cool,
    filter_duotone,
    filter_edge,
    filter_emboss,
    filter_grayscale,
    filter_invert,
    filter_pastel,
    filter_posterize,
    filter_sepia,
    filter_sharpen,
    filter_solarize,
    filter_threshold,
    filter_vintage,
    flip_h as flip_horizontal,
    flip_v as flip_vertical,
    generate_template,
    get_font,
    hex_to_rgba,
    optimize_for_telegram,
    resize_to_sticker,
    rotate,
    save_sticker,
)
from aiogram.client.default import DefaultBotProperties

# ============================ ЛОГИРОВАНИЕ ============================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("sticker_bot")


# ============================ FSM ============================

class StickerFSM(StatesGroup):
    """Состояния для создания стикера."""
    waiting_image = State()          # ожидаем фото/документ
    editing = State()                # в редакторе
    waiting_text = State()           # ввод текста
    waiting_watermark = State()      # ввод водяного знака
    waiting_pack_name = State()      # имя нового пака
    waiting_sticker_emoji = State()  # смена эмодзи у готового стикера


# ============================ ИНИЦИАЛИЗАЦИЯ ============================

bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML),
)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
router = Router()
dp.include_router(router)
db = Database()


# ============================ ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ============================

def user_temp_path(user_id: int) -> str:
    """Путь к текущему редактируемому файлу пользователя."""
    return str(TEMP_DIR / f"{user_id}_current.webp")


def user_original_path(user_id: int) -> str:
    """Путь к оригиналу (для сброса)."""
    return str(TEMP_DIR / f"{user_id}_original.webp")


async def save_state_image(state: FSMContext, image: Image.Image, user_id: int) -> str:
    """Сохранить PIL Image в state и на диск."""
    path = user_temp_path(user_id)
    image = image.convert("RGBA")
    image.save(path, "WEBP", quality=90, method=6)
    await state.update_data(image_path=path)
    return path


async def load_state_image(state: FSMContext) -> Optional[Image.Image]:
    """Загрузить PIL Image из state."""
    data = await state.get_data()
    path = data.get("image_path")
    if path and os.path.exists(path):
        return Image.open(path)
    return None


async def update_preview(
    target: Message | CallbackQuery,
    state: FSMContext,
    caption: str | None = None,
    reply_markup: InlineKeyboardMarkup | None = None,
) -> bool:
    """
    Обновить превью стикера в сообщении. Если edit_media не сработал —
    отправляем новое сообщение.
    Возвращает True если edit удался.
    """
    img = await load_state_image(state)
    if img is None:
        if isinstance(target, CallbackQuery):
            await target.message.answer(
                "❌ Изображение не найдено. Начните заново: /create",
            )
        else:
            await target.answer(
                "❌ Изображение не найдено. Начните заново: /create",
            )
        return False

    user_id = target.from_user.id if isinstance(target, CallbackQuery) else target.from_user.id
    path = user_temp_path(user_id)
    img.convert("RGBA").save(path, "WEBP", quality=90, method=6)
    input_file = FSInputFile(path, filename="sticker.webp")

    media = types.InputMediaPhoto(media=input_file, caption=caption)

    try:
        if isinstance(target, CallbackQuery):
            await target.message.edit_media(media=media, reply_markup=reply_markup)
        else:
            await target.edit_media(media=media, reply_markup=reply_markup)
        return True
    except Exception:
        try:
            if isinstance(target, CallbackQuery):
                await target.message.answer_photo(
                    photo=input_file, caption=caption, reply_markup=reply_markup,
                )
            else:
                await target.answer_photo(
                    photo=input_file, caption=caption, reply_markup=reply_markup,
                )
        except Exception as e:
            logger.exception("Не удалось отправить превью: %s", e)
        return False


async def increment_edits(user_id: int) -> None:
    """Инкрементировать счётчик правок."""
    try:
        await db.increment_stat(user_id, "total_edits")
    except Exception:
        pass


async def reset_to_original(state: FSMContext, user_id: int) -> Optional[Image.Image]:
    """Сбросить изображение к оригиналу."""
    orig = user_original_path(user_id)
    if not os.path.exists(orig):
        return None
    img = Image.open(orig)
    await save_state_image(state, img, user_id)
    return img


# ============================ /start И /help ============================

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await db.upsert_user(
        message.from_user.id,
        message.from_user.username or "",
        message.from_user.first_name or "",
    )
    await message.answer(
        f"👋 <b>Привет, {message.from_user.first_name or 'друг'}!</b>\n\n"
        "Я — бот для создания <b>стикеров</b> с кучей настроек.\n\n"
        "🎨 Создавай стикеры из любых фото\n"
        "✂️ Вырезай в любую форму\n"
        "🎭 Применяй фильтры и эффекты\n"
        "✏️ Добавляй текст и эмодзи\n"
        "📦 Сохраняй в свою коллекцию\n\n"
        "Отправь мне фото, чтобы начать, или выбери действие:",
        reply_markup=kb.main_menu(),
    )


@router.message(Command("help"))
@router.callback_query(F.data == "help")
async def cmd_help(event: Message | CallbackQuery):
    text = (
        "ℹ️ <b>Как пользоваться ботом</b>\n\n"
        "<b>1.</b> Нажми «🎨 Создать стикер» или отправь фото.\n"
        "<b>2.</b> Выбери форму, фильтры, добавь текст/эмодзи.\n"
        "<b>3.</b> Нажми «✅ Готово» — стикер сохранится в галерею.\n\n"
        "<b>Доступные функции:</b>\n"
        "✂️ Формы: круг, квадрат, скруглённый, ромб, шестиугольник, звезда\n"
        "🔄 Поворот на любой угол + отражение\n"
        "🎨 12+ фильтров: ч/б, сепия, инверсия, винтаж и т.д.\n"
        "🎛 Цветокоррекция: яркость, контраст, насыщенность\n"
        "✏️ Текст с настройкой шрифта, цвета, обводки, позиции\n"
        "😄 Эмодзи-наложение с выбором позиции и размера\n"
        "🎭 Эффекты: обводка, рамка, тень, свечение\n"
        "🌟 Паттерны: точки, полосы, звёзды, сердца\n"
        "💧 Водяной знак\n\n"
        "<b>Команды:</b>\n"
        "/start — главное меню\n"
        "/create — создать стикер\n"
        "/gallery — мои стикеры\n"
        "/cancel — отмена текущего действия"
    )
    if isinstance(event, CallbackQuery):
        await event.message.edit_text(text, reply_markup=kb.back_to_main())
        await event.answer()
    else:
        await event.answer(text, reply_markup=kb.main_menu())


@router.message(Command("cancel"))
@router.message(F.text.casefold() == "отмена")
async def cmd_cancel(message: Message, state: FSMContext):
    current = await state.get_state()
    if current is None:
        await message.answer("Нет активного действия.", reply_markup=kb.main_menu())
        return
    await state.clear()
    await message.answer("❌ Действие отменено.", reply_markup=kb.main_menu())


# ============================ МЕНЮ ============================

@router.callback_query(F.data == "back_main")
async def back_to_main(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    try:
        await callback.message.edit_text(
            "🏠 <b>Главное меню</b>\n\nВыбери действие:",
            reply_markup=kb.main_menu(),
        )
    except Exception:
        await callback.message.answer(
            "🏠 <b>Главное меню</b>\n\nВыбери действие:",
            reply_markup=kb.main_menu(),
        )
    await callback.answer()


@router.callback_query(F.data == "back_editor")
async def back_to_editor(callback: CallbackQuery, state: FSMContext):
    img = await load_state_image(state)
    if img is None:
        await back_to_main(callback, state)
        return
    await update_preview(callback, state, caption="🎨 <b>Редактор стикера</b>", reply_markup=kb.editor_menu())
    await callback.answer()


@router.callback_query(F.data == "back_text")
async def back_to_text(callback: CallbackQuery, state: FSMContext):
    await update_preview(callback, state, caption="✏️ <b>Настройки текста</b>", reply_markup=kb.text_menu())
    await callback.answer()


@router.callback_query(F.data == "back_emoji")
async def back_to_emoji(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    emojis = data.get("emoji_list", POPULAR_EMOJIS)
    await update_preview(callback, state, caption="😄 <b>Эмодзи</b>", reply_markup=kb.emoji_menu(emojis))
    await callback.answer()


@router.callback_query(F.data == "back_effects")
async def back_to_effects(callback: CallbackQuery, state: FSMContext):
    await update_preview(callback, state, caption="🎭 <b>Эффекты</b>", reply_markup=kb.effects_menu())
    await callback.answer()


# ============================ СОЗДАНИЕ СТИКЕРА ============================

@router.callback_query(F.data == "create")
@router.message(Command("create"))
async def cmd_create(event: Message | CallbackQuery, state: FSMContext):
    await state.clear()
    await state.set_state(StickerFSM.waiting_image)
    text = (
        "📸 <b>Отправь мне изображение</b>\n\n"
        "Можно отправить:\n"
        "• 📷 Фото (как сжатое превью)\n"
        "• 📄 Документ (оригинальное качество)\n\n"
        "<i>Лучше отправлять как документ, чтобы сохранить качество.</i>"
    )
    if isinstance(event, CallbackQuery):
        try:
            await event.message.edit_text(text)
        except Exception:
            await event.message.answer(text)
        await event.answer()
    else:
        await event.answer(text)


@router.message(StateFilter(StickerFSM.waiting_image), F.photo | F.document)
async def receive_image(message: Message, state: FSMContext):
    """Получаем фото или документ."""
    await db.upsert_user(
        message.from_user.id,
        message.from_user.username or "",
        message.from_user.first_name or "",
    )

    # Определяем источник файла
    if message.photo:
        # Берём самое большое фото
        source = message.photo[-1].file_id
    elif message.document:
        # Проверяем, что это изображение
        mime = message.document.mime_type or ""
        if not mime.startswith("image/"):
            await message.answer("❌ Это не изображение. Отправь фото или картинку.")
            return
        source = message.document.file_id
    else:
        return

    try:
        file = await bot.get_file(source)
        file_bytes = BytesIO()
        await bot.download_file(file.file_path, file_bytes)
        file_bytes.seek(0)
        img = Image.open(file_bytes).convert("RGBA")
    except Exception as e:
        logger.exception("Ошибка загрузки: %s", e)
        await message.answer("❌ Не удалось загрузить изображение. Попробуй ещё раз.")
        return

    # Сохраняем и оригинал (для сброса), и текущее состояние
    user_id = message.from_user.id
    original = resize_to_sticker(img)
    original.save(user_original_path(user_id), "WEBP", quality=92, method=6)
    await save_state_image(state, original, user_id)

    await state.update_data(
        original_path=user_original_path(user_id),
        emoji_list=POPULAR_EMOJIS,
    )
    await state.set_state(StickerFSM.editing)

    await message.answer_photo(
        photo=FSInputFile(user_original_path(user_id), filename="sticker.webp"),
        caption=(
            "✅ <b>Изображение загружено!</b>\n\n"
            "Используй кнопки ниже, чтобы настроить стикер:"
        ),
        reply_markup=kb.editor_menu(),
    )


@router.message(StateFilter(StickerFSM.editing))
async def catch_non_image_in_editing(message: Message):
    await message.answer(
        "📸 Сейчас я жду нажатия кнопок. Чтобы загрузить новое фото — нажми «🔁 Сброс» или /cancel.",
    )


# ============================ ОПЕРАЦИИ РЕДАКТОРА ============================

@router.callback_query(StateFilter(StickerFSM.editing), F.data.startswith("shape_"))
async def apply_shape(callback: CallbackQuery, state: FSMContext):
    shape = callback.data[6:]
    img = await load_state_image(state)
    if img is None:
        return await callback.answer("❌ Нет изображения", show_alert=True)

    # Берём ОРИГИНАЛ для чистого результата (но сохраняем оригинал)
    data = await state.get_data()
    orig_path = data.get("original_path")
    if orig_path and os.path.exists(orig_path):
        img = Image.open(orig_path)

    if shape == "circle":
        img = crop_circle(img)
    elif shape == "square":
        img = resize_to_sticker(img)
    elif shape == "rounded":
        img = crop_rounded(img)
    elif shape == "diamond":
        img = crop_diamond(img)
    elif shape == "hexagon":
        img = crop_hexagon(img)
    elif shape == "star":
        img = crop_star(img)

    await save_state_image(state, img, callback.from_user.id)
    await increment_edits(callback.from_user.id)
    await update_preview(callback, state, caption="✂️ <b>Форма применена!</b>", reply_markup=kb.editor_menu())
    await callback.answer("✅ Форма применена")


@router.callback_query(StateFilter(StickerFSM.editing), F.data == "shape")
async def menu_shape(callback: CallbackQuery, state: FSMContext):
    await update_preview(callback, state, caption="✂️ <b>Выбери форму:</b>", reply_markup=kb.shape_menu())
    await callback.answer()


@router.callback_query(StateFilter(StickerFSM.editing), F.data.startswith("rot_"))
async def apply_rotation(callback: CallbackQuery, state: FSMContext):
    val = callback.data[4:]
    img = await load_state_image(state)
    if img is None:
        return await callback.answer("❌ Нет изображения", show_alert=True)

    if val == "random":
        angle = random.choice([15, 30, 45, -15, -30, 75, 90, -90])
    else:
        angle = float(val)

    img = rotate(img, angle)
    await save_state_image(state, img, callback.from_user.id)
    await increment_edits(callback.from_user.id)
    await update_preview(callback, state, caption=f"🔄 Поворот на {angle}°", reply_markup=kb.editor_menu())
    await callback.answer(f"✅ Поворот {angle}°")


@router.callback_query(StateFilter(StickerFSM.editing), F.data == "rotate")
async def menu_rotate(callback: CallbackQuery, state: FSMContext):
    await update_preview(callback, state, caption="🔄 <b>Выбери угол поворота:</b>", reply_markup=kb.rotate_menu())
    await callback.answer()


@router.callback_query(StateFilter(StickerFSM.editing), F.data.startswith("flip_"))
async def apply_flip(callback: CallbackQuery, state: FSMContext):
    img = await load_state_image(state)
    if img is None:
        return await callback.answer("❌ Нет изображения", show_alert=True)

    if callback.data == "flip_h":
        img = flip_horizontal(img)
    elif callback.data == "flip_v":
        img = flip_vertical(img)

    await save_state_image(state, img, callback.from_user.id)
    await increment_edits(callback.from_user.id)
    await update_preview(callback, state, caption="🪞 Отражение применено", reply_markup=kb.editor_menu())
    await callback.answer("✅ Готово")


@router.callback_query(StateFilter(StickerFSM.editing), F.data == "flip")
async def menu_flip(callback: CallbackQuery, state: FSMContext):
    await update_preview(callback, state, caption="🪞 <b>Отражение:</b>", reply_markup=kb.flip_menu())
    await callback.answer()


# ---------- ФИЛЬТРЫ ----------

@router.callback_query(StateFilter(StickerFSM.editing), F.data.startswith("f_"))
async def apply_filter(callback: CallbackQuery, state: FSMContext):
    f = callback.data[2:]
    img = await load_state_image(state)
    if img is None:
        return await callback.answer("❌ Нет изображения", show_alert=True)

    filter_map = {
        "grayscale": filter_grayscale,
        "sepia": filter_sepia,
        "invert": filter_invert,
        "posterize": filter_posterize,
        "solarize": filter_solarize,
        "threshold": filter_threshold,
        "edge": filter_edge,
        "emboss": filter_emboss,
        "contour": filter_contour,
        "blur": lambda i: filter_blur(i, radius=5),
        "sharpen": filter_sharpen,
        "pastel": filter_pastel,
        "vintage": filter_vintage,
        "cool": filter_cool,
    }
    fn = filter_map.get(f)
    if not fn:
        return await callback.answer("❌ Неизвестный фильтр")
    img = fn(img)
    await save_state_image(state, img, callback.from_user.id)
    await increment_edits(callback.from_user.id)
    await update_preview(callback, state, caption=f"🎨 Фильтр «{f}» применён", reply_markup=kb.editor_menu())
    await callback.answer("✅ Готово")


@router.callback_query(StateFilter(StickerFSM.editing), F.data == "filters")
async def menu_filters(callback: CallbackQuery, state: FSMContext):
    await update_preview(callback, state, caption="🎨 <b>Выбери фильтр:</b>", reply_markup=kb.filters_menu())
    await callback.answer()


# ---------- ЦВЕТОКОРРЕКЦИЯ ----------

@router.callback_query(StateFilter(StickerFSM.editing), F.data.startswith("c_"))
async def adjust_color(callback: CallbackQuery, state: FSMContext):
    op = callback.data[2:]
    img = await load_state_image(state)
    if img is None:
        return await callback.answer("❌ Нет изображения", show_alert=True)

    STEP = 0.2
    data = await state.get_data()
    color_state = data.get("color_state", {
        "brightness": 1.0, "contrast": 1.0, "saturation": 1.0, "sharpness": 1.0,
    })

    if op == "bright_up":
        color_state["brightness"] = min(3.0, color_state["brightness"] + STEP)
        img = adjust_brightness(img, color_state["brightness"])
    elif op == "bright_dn":
        color_state["brightness"] = max(0.1, color_state["brightness"] - STEP)
        img = adjust_brightness(img, color_state["brightness"])
    elif op == "contrast_up":
        color_state["contrast"] = min(3.0, color_state["contrast"] + STEP)
        img = adjust_contrast(img, color_state["contrast"])
    elif op == "contrast_dn":
        color_state["contrast"] = max(0.1, color_state["contrast"] - STEP)
        img = adjust_contrast(img, color_state["contrast"])
    elif op == "sat_up":
        color_state["saturation"] = min(3.0, color_state["saturation"] + STEP)
        img = adjust_saturation(img, color_state["saturation"])
    elif op == "sat_dn":
        color_state["saturation"] = max(0.0, color_state["saturation"] - STEP)
        img = adjust_saturation(img, color_state["saturation"])
    elif op == "sharp_up":
        color_state["sharpness"] = min(3.0, color_state["sharpness"] + STEP)
        img = adjust_sharpness(img, color_state["sharpness"])
    elif op == "sharp_dn":
        color_state["sharpness"] = max(0.0, color_state["sharpness"] - STEP)
        img = adjust_sharpness(img, color_state["sharpness"])
    else:
        return await callback.answer("❌ ?")

    await save_state_image(state, img, callback.from_user.id)
    await state.update_data(color_state=color_state)
    await increment_edits(callback.from_user.id)
    await update_preview(callback, state, caption=f"🎛 {op}", reply_markup=kb.editor_menu())
    await callback.answer("✅")


@router.callback_query(StateFilter(StickerFSM.editing), F.data == "color")
async def menu_color(callback: CallbackQuery, state: FSMContext):
    await update_preview(callback, state, caption="🎛 <b>Цветокоррекция</b>\n\nНажимай кнопки — параметр меняется с шагом 0.2", reply_markup=kb.color_adjust_menu())
    await callback.answer()


# ---------- ТЕКСТ ----------

TEXT_DEFAULTS = {
    "text": "Hello!",
    "font_size": 50,
    "color": "#FFFFFF",
    "stroke_color": "#000000",
    "stroke_width": 4,
    "position": "bottom",
    "font": "bold",
}


@router.callback_query(StateFilter(StickerFSM.editing), F.data == "text")
async def menu_text(callback: CallbackQuery, state: FSMContext):
    await update_preview(callback, state, caption="✏️ <b>Настройки текста</b>", reply_markup=kb.text_menu())
    await callback.answer()


@router.callback_query(StateFilter(StickerFSM.editing), F.data == "t_input")
async def text_input_prompt(callback: CallbackQuery, state: FSMContext):
    await state.set_state(StickerFSM.waiting_text)
    try:
        await callback.message.edit_caption(
            caption="✏️ <b>Введи текст для стикера:</b>\n\nМаксимум 60 символов.",
        )
    except Exception:
        await callback.message.answer("✏️ Введи текст для стикера (макс. 60 символов):")
    await callback.answer()


@router.message(StateFilter(StickerFSM.waiting_text), F.text)
async def text_input_received(message: Message, state: FSMContext):
    text = message.text.strip()[:60]
    if not text:
        await message.answer("Текст пустой. Попробуй ещё раз или /cancel")
        return
    await state.update_data(text=text)
    await state.set_state(StickerFSM.editing)

    img = await load_state_image(state)
    if img is None:
        await message.answer("❌ Изображение потеряно", reply_markup=kb.main_menu())
        return

    data = await state.get_data()
    td = {**TEXT_DEFAULTS, **data.get("text_settings", {}), "text": text}

    img = add_text(
        img,
        text=td["text"],
        font_size=td["font_size"],
        color=hex_to_rgba(td["color"]),
        position=td["position"],
        stroke_width=td["stroke_width"],
        stroke_color=hex_to_rgba(td["stroke_color"]),
        font_name=td["font"],
    )
    await save_state_image(state, img, message.from_user.id)
    await increment_edits(message.from_user.id)

    await message.answer_photo(
        photo=FSInputFile(user_temp_path(message.from_user.id), filename="s.webp"),
        caption=f"✏️ Текст «{text}» добавлен",
        reply_markup=kb.editor_menu(),
    )


@router.callback_query(StateFilter(StickerFSM.editing), F.data == "t_clear")
async def text_clear(callback: CallbackQuery, state: FSMContext):
    """Убрать текст — сброс к оригиналу и применение прочих эффектов не сбрасываем,
    но проще всего восстановить оригинал и применить последний известный набор.
    Для простоты — восстанавливаем оригинал."""
    img = await reset_to_original(state, callback.from_user.id)
    if img is None:
        return await callback.answer("❌ Нет оригинала", show_alert=True)
    await update_preview(callback, state, caption="🗑 Текст убран (изображение сброшено к оригиналу)", reply_markup=kb.editor_menu())
    await callback.answer("✅ Текст убран")


@router.callback_query(StateFilter(StickerFSM.editing), F.data.startswith("tc_"))
async def set_text_color(callback: CallbackQuery, state: FSMContext):
    hex_ = callback.data[3:]
    await state.update_data(text_color=hex_)
    await callback.answer(f"✅ Цвет текста: {hex_}")


@router.callback_query(StateFilter(StickerFSM.editing), F.data.startswith("tsc_"))
async def set_text_stroke_color(callback: CallbackQuery, state: FSMContext):
    hex_ = callback.data[4:]
    await state.update_data(text_stroke_color=hex_)
    await callback.answer(f"✅ Цвет обводки текста: {hex_}")


@router.callback_query(StateFilter(StickerFSM.editing), F.data.startswith("ts_"))
async def set_text_size(callback: CallbackQuery, state: FSMContext):
    size = int(callback.data[3:])
    await state.update_data(text_size=size)
    await callback.answer(f"✅ Размер: {size}")


@router.callback_query(StateFilter(StickerFSM.editing), F.data.startswith("tsw_"))
async def set_text_stroke_width(callback: CallbackQuery, state: FSMContext):
    w = int(callback.data[4:])
    await state.update_data(text_stroke_width=w)
    await callback.answer(f"✅ Толщина обводки: {w}")


@router.callback_query(StateFilter(StickerFSM.editing), F.data.startswith("tp_"))
async def set_text_position(callback: CallbackQuery, state: FSMContext):
    pos = callback.data[3:]
    pos_map = {"top": "top", "bottom": "bottom", "center": "center",
               "tl": "top-left", "tr": "top-right", "bl": "bottom-left", "br": "bottom-right"}
    p = pos_map.get(pos, "bottom")
    await state.update_data(text_position=p)
    await callback.answer(f"✅ Позиция: {p}")


@router.callback_query(StateFilter(StickerFSM.editing), F.data.startswith("tf_"))
async def set_text_font(callback: CallbackQuery, state: FSMContext):
    font = callback.data[3:]
    await state.update_data(text_font=font)
    await callback.answer(f"✅ Шрифт: {font}")


@router.callback_query(StateFilter(StickerFSM.editing), F.data == "t_color")
async def menu_text_color(callback: CallbackQuery, state: FSMContext):
    await update_preview(callback, state, caption="🎨 <b>Цвет текста</b>", reply_markup=kb.text_color_menu())
    await callback.answer()


@router.callback_query(StateFilter(StickerFSM.editing), F.data == "t_stroke_color")
async def menu_text_stroke_color(callback: CallbackQuery, state: FSMContext):
    await update_preview(callback, state, caption="🖌 <b>Цвет обводки текста</b>", reply_markup=kb.text_stroke_color_menu())
    await callback.answer()


@router.callback_query(StateFilter(StickerFSM.editing), F.data == "t_size")
async def menu_text_size(callback: CallbackQuery, state: FSMContext):
    await update_preview(callback, state, caption="📏 <b>Размер шрифта</b>", reply_markup=kb.text_size_menu())
    await callback.answer()


@router.callback_query(StateFilter(StickerFSM.editing), F.data == "t_position")
async def menu_text_position(callback: CallbackQuery, state: FSMContext):
    await update_preview(callback, state, caption="📍 <b>Позиция текста</b>", reply_markup=kb.text_position_menu())
    await callback.answer()


@router.callback_query(StateFilter(StickerFSM.editing), F.data == "t_font")
async def menu_text_font(callback: CallbackQuery, state: FSMContext):
    await update_preview(callback, state, caption="🔠 <b>Стиль шрифта</b>", reply_markup=kb.text_font_menu())
    await callback.answer()


@router.callback_query(StateFilter(StickerFSM.editing), F.data == "t_stroke_width")
async def menu_text_stroke_width(callback: CallbackQuery, state: FSMContext):
    await update_preview(callback, state, caption="📐 <b>Толщина обводки текста</b>", reply_markup=kb.text_stroke_width_menu())
    await callback.answer()


# ---------- ЭМОДЗИ ----------

@router.callback_query(StateFilter(StickerFSM.editing), F.data == "emoji")
async def menu_emoji(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    emojis = data.get("emoji_list", POPULAR_EMOJIS)
    await update_preview(callback, state, caption="😄 <b>Выбери эмодзи для наложения:</b>", reply_markup=kb.emoji_menu(emojis))
    await callback.answer()


@router.callback_query(StateFilter(StickerFSM.editing), F.data.regexp(r"^e_\d+$"))
async def apply_emoji(callback: CallbackQuery, state: FSMContext):
    idx = int(callback.data[2:])
    data = await state.get_data()
    emojis = data.get("emoji_list", POPULAR_EMOJIS)
    if idx >= len(emojis):
        return await callback.answer("❌", show_alert=True)
    emoji_char = emojis[idx]

    img = await load_state_image(state)
    if img is None:
        return await callback.answer("❌ Нет изображения", show_alert=True)

    pos = data.get("emoji_position", "top-right")
    size = data.get("emoji_size", 120)
    img = add_emoji(img, emoji_char, size=size, position=pos)
    await save_state_image(state, img, callback.from_user.id)
    await increment_edits(callback.from_user.id)
    await state.update_data(last_emoji=emoji_char)
    await update_preview(callback, state, caption=f"😄 Эмодзи {emoji_char} добавлено", reply_markup=kb.editor_menu())
    await callback.answer("✅")


@router.callback_query(StateFilter(StickerFSM.editing), F.data == "e_position")
async def menu_emoji_position(callback: CallbackQuery, state: FSMContext):
    await update_preview(callback, state, caption="📍 <b>Позиция эмодзи</b>", reply_markup=kb.emoji_position_menu())
    await callback.answer()


@router.callback_query(StateFilter(StickerFSM.editing), F.data == "e_size")
async def menu_emoji_size(callback: CallbackQuery, state: FSMContext):
    await update_preview(callback, state, caption="🔍 <b>Размер эмодзи</b>", reply_markup=kb.emoji_size_menu())
    await callback.answer()


@router.callback_query(StateFilter(StickerFSM.editing), F.data.startswith("ep_"))
async def set_emoji_position(callback: CallbackQuery, state: FSMContext):
    p = callback.data[3:]
    pos_map = {"tl": "top-left", "tr": "top-right", "bl": "bottom-left",
               "br": "bottom-right", "center": "center"}
    pos = pos_map.get(p, "top-right")
    await state.update_data(emoji_position=pos)
    await callback.answer(f"✅ Позиция: {pos}")


@router.callback_query(StateFilter(StickerFSM.editing), F.data.startswith("es_"))
async def set_emoji_size(callback: CallbackQuery, state: FSMContext):
    s = int(callback.data[3:])
    await state.update_data(emoji_size=s)
    await callback.answer(f"✅ Размер: {s}")


@router.callback_query(StateFilter(StickerFSM.editing), F.data == "e_clear")
async def emoji_clear(callback: CallbackQuery, state: FSMContext):
    img = await reset_to_original(state, callback.from_user.id)
    if img is None:
        return await callback.answer("❌", show_alert=True)
    await update_preview(callback, state, caption="🗑 Эмодзи убрано (изображение сброшено)", reply_markup=kb.editor_menu())
    await callback.answer("✅")


# ---------- ЭФФЕКТЫ ----------

@router.callback_query(StateFilter(StickerFSM.editing), F.data == "effects")
async def menu_effects(callback: CallbackQuery, state: FSMContext):
    await update_preview(callback, state, caption="🎭 <b>Эффекты</b>", reply_markup=kb.effects_menu())
    await callback.answer()


@router.callback_query(StateFilter(StickerFSM.editing), F.data == "ef_outline")
async def apply_outline(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    color = hex_to_rgba(data.get("outline_color", "#000000"))
    width = int(data.get("outline_width", 6))
    img = await load_state_image(state)
    if img is None:
        return await callback.answer("❌", show_alert=True)
    img = add_outline(img, color=color, width=width)
    await save_state_image(state, img, callback.from_user.id)
    await increment_edits(callback.from_user.id)
    await update_preview(callback, state, caption=f"⭕ Обводка {width}px применена", reply_markup=kb.editor_menu())
    await callback.answer("✅")


@router.callback_query(StateFilter(StickerFSM.editing), F.data == "ef_border")
async def apply_border(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    color = hex_to_rgba(data.get("border_color", "#000000"))
    width = int(data.get("border_width", 10))
    img = await load_state_image(state)
    if img is None:
        return await callback.answer("❌", show_alert=True)
    img = add_border(img, color=color, width=width)
    await save_state_image(state, img, callback.from_user.id)
    await increment_edits(callback.from_user.id)
    await update_preview(callback, state, caption=f"🖼 Рамка {width}px применена", reply_markup=kb.editor_menu())
    await callback.answer("✅")


@router.callback_query(StateFilter(StickerFSM.editing), F.data == "ef_shadow")
async def apply_shadow(callback: CallbackQuery, state: FSMContext):
    img = await load_state_image(state)
    if img is None:
        return await callback.answer("❌", show_alert=True)
    img = add_drop_shadow(img, offset=(8, 8), color=(0, 0, 0, 180), blur_radius=12)
    await save_state_image(state, img, callback.from_user.id)
    await increment_edits(callback.from_user.id)
    await update_preview(callback, state, caption="🌫 Тень добавлена", reply_markup=kb.editor_menu())
    await callback.answer("✅")


@router.callback_query(StateFilter(StickerFSM.editing), F.data == "ef_glow")
async def apply_glow(callback: CallbackQuery, state: FSMContext):
    img = await load_state_image(state)
    if img is None:
        return await callback.answer("❌", show_alert=True)
    img = add_glow(img, color=(255, 220, 100, 220), radius=20)
    await save_state_image(state, img, callback.from_user.id)
    await increment_edits(callback.from_user.id)
    await update_preview(callback, state, caption="✨ Свечение добавлено", reply_markup=kb.editor_menu())
    await callback.answer("✅")


@router.callback_query(StateFilter(StickerFSM.editing), F.data == "ef_oc")
async def menu_outline_color(callback: CallbackQuery, state: FSMContext):
    await update_preview(callback, state, caption="🎨 <b>Цвет обводки</b>", reply_markup=kb.outline_color_menu())
    await callback.answer()


@router.callback_query(StateFilter(StickerFSM.editing), F.data.startswith("oc_"))
async def set_outline_color(callback: CallbackQuery, state: FSMContext):
    hex_ = callback.data[3:]
    await state.update_data(outline_color=hex_)
    await callback.answer(f"✅ Цвет обводки: {hex_}")


@router.callback_query(StateFilter(StickerFSM.editing), F.data == "ef_ow")
async def menu_outline_width(callback: CallbackQuery, state: FSMContext):
    await update_preview(callback, state, caption="📏 <b>Толщина обводки</b>", reply_markup=kb.outline_width_menu())
    await callback.answer()


@router.callback_query(StateFilter(StickerFSM.editing), F.data.startswith("ow_"))
async def set_outline_width(callback: CallbackQuery, state: FSMContext):
    w = int(callback.data[3:])
    await state.update_data(outline_width=w)
    await callback.answer(f"✅ Толщина обводки: {w}")


@router.callback_query(StateFilter(StickerFSM.editing), F.data == "ef_bc")
async def menu_border_color(callback: CallbackQuery, state: FSMContext):
    await update_preview(callback, state, caption="🎨 <b>Цвет рамки</b>", reply_markup=kb.border_color_menu())
    await callback.answer()


@router.callback_query(StateFilter(StickerFSM.editing), F.data.startswith("bc_"))
async def set_border_color(callback: CallbackQuery, state: FSMContext):
    hex_ = callback.data[3:]
    await state.update_data(border_color=hex_)
    await callback.answer(f"✅ Цвет рамки: {hex_}")


@router.callback_query(StateFilter(StickerFSM.editing), F.data == "ef_bw")
async def menu_border_width(callback: CallbackQuery, state: FSMContext):
    await update_preview(callback, state, caption="📏 <b>Толщина рамки</b>", reply_markup=kb.border_width_menu())
    await callback.answer()


@router.callback_query(StateFilter(StickerFSM.editing), F.data.startswith("bw_"))
async def set_border_width(callback: CallbackQuery, state: FSMContext):
    w = int(callback.data[3:])
    await state.update_data(border_width=w)
    await callback.answer(f"✅ Толщина рамки: {w}")


# ---------- ПАТТЕРНЫ ----------

@router.callback_query(StateFilter(StickerFSM.editing), F.data == "patterns")
async def menu_patterns(callback: CallbackQuery, state: FSMContext):
    await update_preview(callback, state, caption="🌟 <b>Узоры</b>", reply_markup=kb.patterns_menu())
    await callback.answer()


@router.callback_query(StateFilter(StickerFSM.editing), F.data.startswith("p_"))
async def apply_pattern(callback: CallbackQuery, state: FSMContext):
    p = callback.data[2:]
    img = await load_state_image(state)
    if img is None:
        return await callback.answer("❌", show_alert=True)
    if p == "clear":
        img2 = await reset_to_original(state, callback.from_user.id)
        if img2 is None:
            return await callback.answer("❌", show_alert=True)
        await update_preview(callback, state, caption="🗑 Узор убран", reply_markup=kb.editor_menu())
        await callback.answer("✅")
        return
    img = add_pattern(img, p)
    await save_state_image(state, img, callback.from_user.id)
    await increment_edits(callback.from_user.id)
    await update_preview(callback, state, caption=f"🌟 Узор «{p}» применён", reply_markup=kb.editor_menu())
    await callback.answer("✅")


# ---------- СБРОС И СОХРАНЕНИЕ ----------

@router.callback_query(StateFilter(StickerFSM.editing), F.data == "reset")
async def reset_image(callback: CallbackQuery, state: FSMContext):
    img = await reset_to_original(state, callback.from_user.id)
    if img is None:
        return await callback.answer("❌ Нет оригинала", show_alert=True)
    await update_preview(callback, state, caption="🔁 Сброшено к оригиналу", reply_markup=kb.editor_menu())
    await callback.answer("✅ Сброшено")


@router.callback_query(StateFilter(StickerFSM.editing), F.data == "done")
async def done_editing(callback: CallbackQuery, state: FSMContext):
    """Финал редактирования — отправить пользователю результат и сохранить в галерею."""
    img = await load_state_image(state)
    if img is None:
        return await callback.answer("❌", show_alert=True)

    user_id = callback.from_user.id

    # Сохранить в постоянное хранилище
    user_dir = STICKERS_DIR / str(user_id)
    user_dir.mkdir(parents=True, exist_ok=True)

    # Следующий номер
    existing = list(user_dir.glob("*.webp"))
    next_num = len(existing) + 1
    final_path = str(user_dir / f"sticker_{next_num:04d}.webp")
    save_sticker(img, final_path, quality=90)
    optimize_for_telegram(final_path)

    # Сохранить в БД
    sticker_id = await db.add_sticker(
        user_id=user_id,
        file_path=final_path,
        emoji="😀",
        pack_name=None,
    )

    try:
        await callback.message.edit_caption(
            caption=(
                f"🎉 <b>Стикер #{sticker_id} готов!</b>\n\n"
                "Сохранён в твоей галерее. Скачай его как .webp — "
                "и добавь в свой пак стикеров через @Stickers."
            ),
        )
    except Exception:
        pass

    # Отправить файл
    await callback.message.answer_document(
        document=FSInputFile(final_path, filename=f"sticker_{sticker_id}.webp"),
        caption=(
            f"🎉 <b>Стикер #{sticker_id}</b>\n\n"
            "📥 Скачай и добавь в свой пак стикеров через @Stickers.\n"
            "🖼 Все твои стикеры — в «Мои стикеры»."
        ),
    )

    await callback.message.answer(
        "Что дальше?",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🎨 Создать ещё", callback_data="create")],
            [InlineKeyboardButton(text="🖼 В галерею", callback_data="gallery")],
            [InlineKeyboardButton(text="🏠 В меню", callback_data="back_main")],
        ]),
    )
    await state.clear()
    await callback.answer()


@router.callback_query(StateFilter(StickerFSM.editing), F.data == "save")
async def save_only(callback: CallbackQuery, state: FSMContext):
    """Только сохранить (промежуточное сохранение в галерею)."""
    img = await load_state_image(state)
    if img is None:
        return await callback.answer("❌", show_alert=True)

    user_id = callback.from_user.id
    user_dir = STICKERS_DIR / str(user_id)
    user_dir.mkdir(parents=True, exist_ok=True)
    existing = list(user_dir.glob("*.webp"))
    final_path = str(user_dir / f"sticker_{len(existing) + 1:04d}.webp")
    save_sticker(img, final_path, quality=90)
    optimize_for_telegram(final_path)
    await db.add_sticker(user_id, final_path, "😀", None)
    await callback.answer("💾 Сохранено в галерею", show_alert=False)


# ============================ ШАБЛОНЫ ============================

@router.callback_query(F.data == "templates")
async def menu_templates(callback: CallbackQuery, state: FSMContext):
    try:
        await callback.message.edit_text(
            "🎭 <b>Шаблоны</b>\n\nВыбери готовый стикер для редактирования:",
            reply_markup=kb.templates_menu(),
        )
    except Exception:
        await callback.message.answer(
            "🎭 <b>Шаблоны</b>",
            reply_markup=kb.templates_menu(),
        )
    await callback.answer()


@router.callback_query(F.data.startswith("tpl_"))
async def apply_template(callback: CallbackQuery, state: FSMContext):
    name = callback.data[4:]
    img = generate_template(name)
    if img is None:
        return await callback.answer("❌ Шаблон не найден", show_alert=True)

    user_id = callback.from_user.id
    # Сохранить как оригинал
    img.save(user_original_path(user_id), "WEBP", quality=92, method=6)
    await save_state_image(state, img, user_id)
    await state.update_data(original_path=user_original_path(user_id), emoji_list=POPULAR_EMOJIS)
    await state.set_state(StickerFSM.editing)
    await increment_edits(user_id)

    await update_preview(
        callback, state,
        caption=f"🎭 Шаблон «{name}» загружен. Можешь редактировать:",
        reply_markup=kb.editor_menu(),
    )
    await callback.answer("✅ Шаблон загружен")


# ============================ НАСТРОЙКИ ============================

@router.callback_query(F.data == "settings")
async def menu_settings(callback: CallbackQuery):
    try:
        await callback.message.edit_text(
            "⚙️ <b>Настройки</b>\n\nНастрой значения по умолчанию:",
            reply_markup=kb.settings_menu(),
        )
    except Exception:
        await callback.message.answer("⚙️ <b>Настройки</b>", reply_markup=kb.settings_menu())
    await callback.answer()


@router.callback_query(F.data == "set_oc")
async def settings_outline_color(callback: CallbackQuery):
    await callback.message.edit_text(
        "🎨 <b>Цвет обводки по умолчанию</b>",
        reply_markup=kb.outline_color_menu(),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("setoc_"))
async def settings_set_outline_color(callback: CallbackQuery):
    hex_ = callback.data[6:]
    await db.update_setting(callback.from_user.id, "outline_color", hex_)
    await callback.answer(f"✅ Цвет: {hex_}", show_alert=True)
    await menu_settings.callback(callback) if False else None
    try:
        await callback.message.edit_text(
            "⚙️ <b>Настройки</b>",
            reply_markup=kb.settings_menu(),
        )
    except Exception:
        pass


@router.callback_query(F.data == "set_ow")
async def settings_outline_width(callback: CallbackQuery):
    await callback.message.edit_text(
        "📏 <b>Толщина обводки по умолчанию</b>",
        reply_markup=kb.settings_outline_width(),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("setow_"))
async def settings_set_outline_width(callback: CallbackQuery):
    w = int(callback.data[6:])
    await db.update_setting(callback.from_user.id, "outline_width", w)
    await callback.answer(f"✅ Толщина: {w}", show_alert=True)
    try:
        await callback.message.edit_text(
            "⚙️ <b>Настройки</b>",
            reply_markup=kb.settings_menu(),
        )
    except Exception:
        pass


@router.callback_query(F.data == "set_font")
async def settings_font(callback: CallbackQuery):
    try:
        await callback.message.edit_text(
            "🔠 <b>Шрифт по умолчанию</b>",
            reply_markup=kb.text_font_menu(),
        )
    except Exception:
        pass
    await callback.answer()


@router.callback_query(F.data.startswith("setf_"))
async def settings_set_font(callback: CallbackQuery):
    font = callback.data[5:]
    await db.update_setting(callback.from_user.id, "default_font", font)
    await callback.answer(f"✅ Шрифт: {font}", show_alert=True)
    try:
        await callback.message.edit_text(
            "⚙️ <b>Настройки</b>",
            reply_markup=kb.settings_menu(),
        )
    except Exception:
        pass


@router.callback_query(F.data == "set_wm")
async def settings_watermark_prompt(callback: CallbackQuery, state: FSMContext):
    await state.set_state(StickerFSM.waiting_watermark)
    await callback.message.answer(
        "💧 <b>Введи водяной знак</b>\n\n"
        "Отправь текст — он будет автоматически добавляться на все стикеры.\n"
        "Или отправь «-» чтобы отключить.",
    )
    await callback.answer()


@router.message(StateFilter(StickerFSM.waiting_watermark), F.text)
async def settings_watermark_received(message: Message, state: FSMContext):
    text = message.text.strip()
    val = "" if text == "-" else text[:40]
    await db.update_setting(message.from_user.id, "watermark_text", val)
    await state.clear()
    if val:
        await message.answer(f"✅ Водяной знак: «{val}»", reply_markup=kb.settings_menu())
    else:
        await message.answer("✅ Водяной знак отключён", reply_markup=kb.settings_menu())


@router.callback_query(F.data == "set_reset")
async def settings_reset(callback: CallbackQuery):
    await db.update_setting(callback.from_user.id, "outline_color", "#000000")
    await db.update_setting(callback.from_user.id, "outline_width", 5)
    await db.update_setting(callback.from_user.id, "watermark_text", "")
    await db.update_setting(callback.from_user.id, "default_font", "bold")
    await callback.answer("✅ Настройки сброшены", show_alert=True)
    try:
        await callback.message.edit_text(
            "⚙️ <b>Настройки</b>\n\n(сброшены к значениям по умолчанию)",
            reply_markup=kb.settings_menu(),
        )
    except Exception:
        pass


# ============================ СТАТИСТИКА ============================

@router.callback_query(F.data == "stats")
@router.message(Command("stats"))
async def show_stats(event: Message | CallbackQuery):
    user_id = event.from_user.id
    stats = await db.get_stats(user_id)
    total = stats["sticker_count"]
    edits = stats["total_edits"]
    user = await db.get_user(user_id)
    created = user[3] if user else None

    text = (
        "📊 <b>Твоя статистика</b>\n\n"
        f"🎨 Стикеров создано: <b>{total}</b>\n"
        f"🛠 Правок сделано: <b>{edits}</b>\n"
        f"📅 С нами с: <b>{created[:10] if created else '—'}</b>\n"
    )
    if isinstance(event, CallbackQuery):
        try:
            await event.message.edit_text(text, reply_markup=kb.back_to_main())
        except Exception:
            await event.message.answer(text, reply_markup=kb.back_to_main())
        await event.answer()
    else:
        await event.answer(text, reply_markup=kb.main_menu())


# ============================ ГАЛЕРЕЯ ============================

PER_PAGE = 10


@router.callback_query(F.data == "gallery")
@router.message(Command("gallery"))
async def show_gallery(event: Message | CallbackQuery, state: FSMContext, page: int = 0):
    user_id = event.from_user.id
    total = await db.count_stickers(user_id)
    if total == 0:
        text = "🖼 <b>Галерея пуста</b>\n\nСоздай свой первый стикер через «🎨 Создать стикер»!"
        if isinstance(event, CallbackQuery):
            try:
                await event.message.edit_text(text, reply_markup=kb.back_to_main())
            except Exception:
                await event.message.answer(text, reply_markup=kb.back_to_main())
            await event.answer()
        else:
            await event.answer(text, reply_markup=kb.main_menu())
        return

    stickers = await db.get_stickers(user_id, limit=PER_PAGE, offset=page * PER_PAGE)
    text = f"🖼 <b>Галерея</b> • {total} стикеров\n\nСтраница {page + 1}"
    if isinstance(event, CallbackQuery):
        try:
            await event.message.edit_text(text, reply_markup=kb.gallery_menu(stickers, page, PER_PAGE, total))
        except Exception:
            await event.message.answer(text, reply_markup=kb.gallery_menu(stickers, page, PER_PAGE, total))
        await event.answer()
    else:
        await event.answer(text, reply_markup=kb.gallery_menu(stickers, page, PER_PAGE, total))


@router.callback_query(F.data.startswith("page_"))
async def gallery_page(callback: CallbackQuery, state: FSMContext):
    page = int(callback.data[5:])
    await show_gallery(callback, state, page=page)


@router.callback_query(F.data == "noop")
async def noop(callback: CallbackQuery):
    await callback.answer()


@router.callback_query(F.data.startswith("view_"))
async def view_sticker(callback: CallbackQuery):
    sticker_id = int(callback.data[5:])
    user_id = callback.from_user.id
    sticker = await db.get_sticker(sticker_id, user_id)
    if not sticker:
        return await callback.answer("❌ Стикер не найден", show_alert=True)

    _, file_path, emoji, pack_name, created = sticker
    if not os.path.exists(file_path):
        return await callback.answer("❌ Файл не найден", show_alert=True)

    text = (
        f"🖼 <b>Стикер #{sticker_id}</b>\n\n"
        f"😄 Эмодзи: {emoji}\n"
        f"📅 Создан: {created[:16]}\n"
        f"📦 Пак: {pack_name or '—'}\n"
    )

    try:
        await callback.message.delete()
    except Exception:
        pass
    await callback.message.answer_photo(
        photo=FSInputFile(file_path, filename=f"sticker_{sticker_id}.webp"),
        caption=text,
        reply_markup=kb.sticker_actions(sticker_id),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("dl_"))
async def download_sticker(callback: CallbackQuery):
    sticker_id = int(callback.data[3:])
    sticker = await db.get_sticker(sticker_id, callback.from_user.id)
    if not sticker or not os.path.exists(sticker[1]):
        return await callback.answer("❌", show_alert=True)
    await callback.message.answer_document(
        document=FSInputFile(sticker[1], filename=f"sticker_{sticker_id}.webp"),
        caption=f"📥 Стикер #{sticker_id}",
    )
    await callback.answer("✅ Отправлено")


@router.callback_query(F.data.startswith("del_"))
async def delete_sticker(callback: CallbackQuery):
    sticker_id = int(callback.data[4:])
    file_path = await db.delete_sticker(sticker_id, callback.from_user.id)
    if not file_path:
        return await callback.answer("❌", show_alert=True)
    try:
        os.remove(file_path)
    except OSError:
        pass
    await callback.answer("🗑 Удалён", show_alert=True)
    await show_gallery(callback, FSMContext, page=0) if False else None
    # Простое обновление — переход в галерею
    try:
        await callback.message.edit_caption(caption="🗑 Стикер удалён")
    except Exception:
        pass


@router.callback_query(F.data.startswith("ch_emoji_"))
async def change_emoji_prompt(callback: CallbackQuery, state: FSMContext):
    sticker_id = int(callback.data.split("_")[2])
    await state.set_state(StickerFSM.waiting_sticker_emoji)
    await state.update_data(edit_sticker_id=sticker_id)
    await callback.message.answer("😄 Отправь один эмодзи для этого стикера:")
    await callback.answer()


@router.message(StateFilter(StickerFSM.waiting_sticker_emoji), F.text)
async def change_emoji_received(message: Message, state: FSMContext):
    data = await state.get_data()
    sid = data.get("edit_sticker_id")
    text = message.text.strip()
    if not text or len(text) > 8:
        await message.answer("Отправь один эмодзи (или короткий текст до 8 символов).")
        return
    ok = await db.update_sticker_emoji(sid, message.from_user.id, text)
    await state.clear()
    await message.answer(f"{'✅' if ok else '❌'} Эмодзи: {text}")


@router.callback_query(F.data.startswith("fav_"))
async def fav_sticker(callback: CallbackQuery):
    sid = int(callback.data[4:])
    new_state = await db.toggle_favorite(callback.from_user.id, sid)
    await callback.answer("⭐ В избранном" if new_state else "💫 Убрано", show_alert=False)


@router.callback_query(F.data.startswith("to_pack_"))
async def to_pack(callback: CallbackQuery, state: FSMContext):
    sid = int(callback.data.split("_")[2])
    await state.update_data(pack_sticker_id=sid)
    await state.set_state(StickerFSM.waiting_pack_name)
    await callback.message.answer(
        "📦 <b>Введи имя пака</b>\n\n"
        "Имя должно заканчиваться на <code>_by_&lt;bot_username&gt;</code>.\n"
        "Используй только латиницу, цифры и _.\n"
        "Например: <code>my_pack_by_mystickerbot</code>",
    )
    await callback.answer()


@router.message(StateFilter(StickerFSM.waiting_pack_name), F.text)
async def pack_name_received(message: Message, state: FSMContext):
    name = re.sub(r"[^A-Za-z0-9_]", "", message.text.strip())
    if len(name) < 3:
        await message.answer("❌ Имя слишком короткое")
        return
    data = await state.get_data()
    sid = data.get("pack_sticker_id")
    if sid:
        await db.update_sticker_pack(sid, message.from_user.id, name)
    await state.clear()
    await message.answer(
        f"✅ Стикер #{sid} привязан к паку <b>{name}</b>.\n\n"
        "<i>Для реального добавления в Telegram-пак бот должен иметь "
        "права на управление стикерами (выдаётся через @BotFather).</i>",
        reply_markup=kb.back_to_main(),
    )


# ============================ ПАКИ ============================

@router.callback_query(F.data == "packs")
async def packs_menu(callback: CallbackQuery):
    try:
        await callback.message.edit_text(
            "📦 <b>Паки стикеров</b>\n\n"
            "Здесь ты можешь группировать стикеры в Telegram-паки.\n\n"
            "⚠️ <b>Важно:</b> для добавления стикеров в Telegram-пак "
            "бот должен быть создан через @BotFather как sticker-бот.\n"
            "Тогда становятся доступны методы createNewStickerSet и addStickerToSet.",
            reply_markup=kb.packs_menu(),
        )
    except Exception:
        await callback.message.answer("📦 <b>Паки стикеров</b>", reply_markup=kb.packs_menu())
    await callback.answer()


@router.callback_query(F.data == "new_pack")
async def new_pack(callback: CallbackQuery, state: FSMContext):
    await state.set_state(StickerFSM.waiting_pack_name)
    await callback.message.answer(
        "📦 <b>Создание нового пака</b>\n\n"
        "Введи имя пака (должно заканчиваться на <code>_by_&lt;username&gt;</code>):",
    )
    await callback.answer()


@router.callback_query(F.data == "pack_help")
async def pack_help(callback: CallbackQuery):
    text = (
        "📥 <b>Как добавить стикер в Telegram</b>\n\n"
        "<b>Способ 1 — через @Stickers (рекомендуется):</b>\n"
        "1. Скачай свой .webp стикер (через «📥 Скачать»).\n"
        "2. Открой @Stickers → /newpack.\n"
        "3. Загрузи файл и привяжи эмодзи.\n\n"
        "<b>Способ 2 — программный:</b>\n"
        "Через Telegram Bot API методы:\n"
        "• createNewStickerSet\n"
        "• addStickerToSet\n"
        "Бот должен быть sticker-ботом (см. @BotFather → /setdescription).\n\n"
        "<b>Требования Telegram к стикерам:</b>\n"
        "• Формат: .webp или .png\n"
        "• Размер: 512×512 px\n"
        "• Вес: ≤ 500 КБ"
    )
    await callback.message.answer(text, reply_markup=kb.back_to_main())
    await callback.answer()


# ============================ ЗАПУСК ============================

async def on_startup():
    await db.init()
    logger.info("База данных инициализирована")
    if ADMIN_ID:
        try:
            await bot.send_message(ADMIN_ID, "🟢 Бот запущен")
        except Exception:
            pass


async def main():
    await on_startup()
    logger.info("Бот стартует...")
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен вручную")
