"""Все inline-клавиатуры бота."""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

# ============================ ОСНОВНЫЕ МЕНЮ ============================

def main_menu() -> InlineKeyboardMarkup:
    """Главное меню."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🎨 Создать стикер", callback_data="create"),
    )
    builder.row(
        InlineKeyboardButton(text="🖼 Мои стикеры", callback_data="gallery"),
        InlineKeyboardButton(text="📦 Мои паки", callback_data="packs"),
    )
    builder.row(
        InlineKeyboardButton(text="🎭 Шаблоны", callback_data="templates"),
        InlineKeyboardButton(text="⚙️ Настройки", callback_data="settings"),
    )
    builder.row(
        InlineKeyboardButton(text="ℹ️ Помощь", callback_data="help"),
        InlineKeyboardButton(text="📊 Статистика", callback_data="stats"),
    )
    return builder.as_markup()


def back_to_main() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Главное меню", callback_data="back_main")]
    ])


# ============================ МЕНЮ РЕДАКТОРА ============================

def editor_menu() -> InlineKeyboardMarkup:
    """Меню редактора после загрузки изображения."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✂️ Форма", callback_data="shape"),
        InlineKeyboardButton(text="🔄 Повернуть", callback_data="rotate"),
        InlineKeyboardButton(text="🪞 Отразить", callback_data="flip"),
    )
    builder.row(
        InlineKeyboardButton(text="🎨 Фильтры", callback_data="filters"),
        InlineKeyboardButton(text="🎛 Цветокоррекция", callback_data="color"),
    )
    builder.row(
        InlineKeyboardButton(text="✏️ Текст", callback_data="text"),
        InlineKeyboardButton(text="😄 Эмодзи", callback_data="emoji"),
    )
    builder.row(
        InlineKeyboardButton(text="🎭 Эффекты", callback_data="effects"),
        InlineKeyboardButton(text="🌟 Паттерны", callback_data="patterns"),
    )
    builder.row(
        InlineKeyboardButton(text="🔁 Сброс", callback_data="reset"),
        InlineKeyboardButton(text="💾 Сохранить", callback_data="save"),
        InlineKeyboardButton(text="✅ Готово", callback_data="done"),
    )
    return builder.as_markup()


# ============================ ПОДМЕНЮ ============================

def shape_menu() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="⭕ Круг", callback_data="shape_circle"),
        InlineKeyboardButton(text="🔲 Квадрат", callback_data="shape_square"),
    )
    builder.row(
        InlineKeyboardButton(text="🔳 Скруглённый", callback_data="shape_rounded"),
        InlineKeyboardButton(text="🔷 Ромб", callback_data="shape_diamond"),
    )
    builder.row(
        InlineKeyboardButton(text="⬡ Шестиугольник", callback_data="shape_hexagon"),
        InlineKeyboardButton(text="⭐ Звезда", callback_data="shape_star"),
    )
    builder.row(InlineKeyboardButton(text="⬅️ Назад", callback_data="back_editor"))
    return builder.as_markup()


def rotate_menu() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="↺ 90°", callback_data="rot_90"),
        InlineKeyboardButton(text="↻ 90°", callback_data="rot_-90"),
        InlineKeyboardButton(text="↕ 180°", callback_data="rot_180"),
    )
    builder.row(
        InlineKeyboardButton(text="🔀 15°", callback_data="rot_15"),
        InlineKeyboardButton(text="🔀 30°", callback_data="rot_30"),
        InlineKeyboardButton(text="🔀 45°", callback_data="rot_45"),
    )
    builder.row(
        InlineKeyboardButton(text="🎲 Случайно", callback_data="rot_random"),
    )
    builder.row(InlineKeyboardButton(text="⬅️ Назад", callback_data="back_editor"))
    return builder.as_markup()


def flip_menu() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="↔ Горизонтально", callback_data="flip_h"),
        InlineKeyboardButton(text="↕ Вертикально", callback_data="flip_v"),
    )
    builder.row(InlineKeyboardButton(text="⬅️ Назад", callback_data="back_editor"))
    return builder.as_markup()


def filters_menu() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="⬛ Ч/Б", callback_data="f_grayscale"),
        InlineKeyboardButton(text="🟫 Сепия", callback_data="f_sepia"),
        InlineKeyboardButton(text="🌈 Инверсия", callback_data="f_invert"),
    )
    builder.row(
        InlineKeyboardButton(text="🎯 Постеризация", callback_data="f_posterize"),
        InlineKeyboardButton(text="☀️ Соляризация", callback_data="f_solarize"),
        InlineKeyboardButton(text="⬛ Порог", callback_data="f_threshold"),
    )
    builder.row(
        InlineKeyboardButton(text="✏️ Карандаш", callback_data="f_edge"),
        InlineKeyboardButton(text="🗿 Тиснение", callback_data="f_emboss"),
        InlineKeyboardButton(text="〰️ Контур", callback_data="f_contour"),
    )
    builder.row(
        InlineKeyboardButton(text="🔮 Размытие", callback_data="f_blur"),
        InlineKeyboardButton(text="✨ Резкость", callback_data="f_sharpen"),
    )
    builder.row(
        InlineKeyboardButton(text="🌸 Пастель", callback_data="f_pastel"),
        InlineKeyboardButton(text="📷 Винтаж", callback_data="f_vintage"),
        InlineKeyboardButton(text="❄️ Холод", callback_data="f_cool"),
    )
    builder.row(InlineKeyboardButton(text="⬅️ Назад", callback_data="back_editor"))
    return builder.as_markup()


def color_adjust_menu() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🔅 Яркость −", callback_data="c_bright_dn"),
        InlineKeyboardButton(text="🔆 Яркость +", callback_data="c_bright_up"),
    )
    builder.row(
        InlineKeyboardButton(text="◽ Контраст −", callback_data="c_contrast_dn"),
        InlineKeyboardButton(text="◾ Контраст +", callback_data="c_contrast_up"),
    )
    builder.row(
        InlineKeyboardButton(text="🤍 Насыщ. −", callback_data="c_sat_dn"),
        InlineKeyboardButton(text="💜 Насыщ. +", callback_data="c_sat_up"),
    )
    builder.row(
        InlineKeyboardButton(text="⬜ Резкость −", callback_data="c_sharp_dn"),
        InlineKeyboardButton(text="⬛ Резкость +", callback_data="c_sharp_up"),
    )
    builder.row(InlineKeyboardButton(text="⬅️ Назад", callback_data="back_editor"))
    return builder.as_markup()


def text_menu() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📝 Ввести текст", callback_data="t_input"),
        InlineKeyboardButton(text="🗑 Убрать текст", callback_data="t_clear"),
    )
    builder.row(
        InlineKeyboardButton(text="🎨 Цвет", callback_data="t_color"),
        InlineKeyboardButton(text="🖌 Цвет обводки", callback_data="t_stroke_color"),
    )
    builder.row(
        InlineKeyboardButton(text="📏 Размер шрифта", callback_data="t_size"),
        InlineKeyboardButton(text="📍 Позиция", callback_data="t_position"),
    )
    builder.row(
        InlineKeyboardButton(text="🔠 Стиль шрифта", callback_data="t_font"),
        InlineKeyboardButton(text="📐 Толщина обводки", callback_data="t_stroke_width"),
    )
    builder.row(InlineKeyboardButton(text="⬅️ Назад", callback_data="back_editor"))
    return builder.as_markup()


def text_color_menu() -> InlineKeyboardMarkup:
    return _color_picker(prefix="tc", back_to="back_text")


def text_stroke_color_menu() -> InlineKeyboardMarkup:
    return _color_picker(prefix="tsc", back_to="back_text")


def outline_color_menu() -> InlineKeyboardMarkup:
    return _color_picker(prefix="oc", back_to="back_effects")


def border_color_menu() -> InlineKeyboardMarkup:
    return _color_picker(prefix="bc", back_to="back_effects")


def _color_picker(prefix: str, back_to: str = "back_editor") -> InlineKeyboardMarkup:
    """Универсальная палитра цветов."""
    colors = [
        ("⬛", "#000000"), ("⬜", "#FFFFFF"), ("🟥", "#FF0000"),
        ("🟧", "#FFA500"), ("🟨", "#FFFF00"), ("🟩", "#00FF00"),
        ("🟦", "#0000FF"), ("🟪", "#800080"), ("🟫", "#8B4513"),
        ("🩷", "#FFC0CB"), ("🤎", "#964B00"), ("💗", "#FF69B4"),
        ("💎", "#00CED1"), ("🍀", "#228B22"), ("🌸", "#FFB7C5"),
        ("🌙", "#191970"),
    ]
    builder = InlineKeyboardBuilder()
    for i in range(0, len(colors), 4):
        row = [
            InlineKeyboardButton(text=emoji, callback_data=f"{prefix}_{hex_}")
            for emoji, hex_ in colors[i:i + 4]
        ]
        builder.row(*row)
    builder.row(InlineKeyboardButton(text="⬅️ Назад", callback_data=back_to))
    return builder.as_markup()


def text_position_menu() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="⬆️ Сверху", callback_data="tp_top"),
        InlineKeyboardButton(text="⏬ Снизу", callback_data="tp_bottom"),
    )
    builder.row(
        InlineKeyboardButton(text="⏺ Центр", callback_data="tp_center"),
    )
    builder.row(
        InlineKeyboardButton(text="↖ Верх-лево", callback_data="tp_tl"),
        InlineKeyboardButton(text="↗ Верх-право", callback_data="tp_tr"),
    )
    builder.row(
        InlineKeyboardButton(text="↙ Низ-лево", callback_data="tp_bl"),
        InlineKeyboardButton(text="↘ Низ-право", callback_data="tp_br"),
    )
    builder.row(InlineKeyboardButton(text="⬅️ Назад", callback_data="back_text"))
    return builder.as_markup()


def text_size_menu() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🔠 30", callback_data="ts_30"),
        InlineKeyboardButton(text="🔡 50", callback_data="ts_50"),
        InlineKeyboardButton(text="🅰️ 70", callback_data="ts_70"),
    )
    builder.row(
        InlineKeyboardButton(text="🆎 100", callback_data="ts_100"),
        InlineKeyboardButton(text="🆑 140", callback_data="ts_140"),
    )
    builder.row(InlineKeyboardButton(text="⬅️ Назад", callback_data="back_text"))
    return builder.as_markup()


def text_font_menu() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🔤 Обычный", callback_data="tf_default"),
        InlineKeyboardButton(text="🔠 Жирный", callback_data="tf_bold"),
    )
    builder.row(
        InlineKeyboardButton(text="📜 Курсив", callback_data="tf_italic"),
        InlineKeyboardButton(text="💬 Комик", callback_data="tf_comic"),
    )
    builder.row(
        InlineKeyboardButton(text="⌨️ Моно", callback_data="tf_mono"),
    )
    builder.row(InlineKeyboardButton(text="⬅️ Назад", callback_data="back_text"))
    return builder.as_markup()


def text_stroke_width_menu() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="0", callback_data="tsw_0"),
        InlineKeyboardButton(text="2", callback_data="tsw_2"),
        InlineKeyboardButton(text="4", callback_data="tsw_4"),
    )
    builder.row(
        InlineKeyboardButton(text="6", callback_data="tsw_6"),
        InlineKeyboardButton(text="8", callback_data="tsw_8"),
        InlineKeyboardButton(text="12", callback_data="tsw_12"),
    )
    builder.row(InlineKeyboardButton(text="⬅️ Назад", callback_data="back_text"))
    return builder.as_markup()


def emoji_menu(emojis: list[str]) -> InlineKeyboardMarkup:
    """Сетка эмодзи."""
    builder = InlineKeyboardBuilder()
    # По 5 эмодзи в строке, используем индекс как callback
    for i in range(0, len(emojis), 5):
        row = [
            InlineKeyboardButton(text=e, callback_data=f"e_{i + j}")
            for j, e in enumerate(emojis[i:i + 5])
        ]
        builder.row(*row)
    builder.row(
        InlineKeyboardButton(text="📍 Позиция", callback_data="e_position"),
        InlineKeyboardButton(text="🔍 Размер", callback_data="e_size"),
    )
    builder.row(InlineKeyboardButton(text="🗑 Убрать эмодзи", callback_data="e_clear"))
    builder.row(InlineKeyboardButton(text="⬅️ Назад", callback_data="back_editor"))
    return builder.as_markup()


def emoji_position_menu() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="↖", callback_data="ep_tl"),
        InlineKeyboardButton(text="⬆", callback_data="ep_tr"),
        InlineKeyboardButton(text="⏺", callback_data="ep_center"),
    )
    builder.row(
        InlineKeyboardButton(text="↙", callback_data="ep_bl"),
        InlineKeyboardButton(text="⏬", callback_data="ep_br"),
    )
    builder.row(InlineKeyboardButton(text="⬅️ Назад", callback_data="back_emoji"))
    return builder.as_markup()


def emoji_size_menu() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🔸 60", callback_data="es_60"),
        InlineKeyboardButton(text="🔹 90", callback_data="es_90"),
        InlineKeyboardButton(text="🔶 120", callback_data="es_120"),
    )
    builder.row(
        InlineKeyboardButton(text="🟠 160", callback_data="es_160"),
        InlineKeyboardButton(text="🔴 200", callback_data="es_200"),
    )
    builder.row(InlineKeyboardButton(text="⬅️ Назад", callback_data="back_emoji"))
    return builder.as_markup()


def effects_menu() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="⭕ Обводка", callback_data="ef_outline"),
        InlineKeyboardButton(text="🖼 Рамка", callback_data="ef_border"),
    )
    builder.row(
        InlineKeyboardButton(text="🌫 Тень", callback_data="ef_shadow"),
        InlineKeyboardButton(text="✨ Свечение", callback_data="ef_glow"),
    )
    builder.row(
        InlineKeyboardButton(text="🎨 Цвет обводки", callback_data="ef_oc"),
        InlineKeyboardButton(text="📏 Толщина", callback_data="ef_ow"),
    )
    builder.row(
        InlineKeyboardButton(text="🎨 Цвет рамки", callback_data="ef_bc"),
        InlineKeyboardButton(text="📏 Толщина рамки", callback_data="ef_bw"),
    )
    builder.row(InlineKeyboardButton(text="⬅️ Назад", callback_data="back_editor"))
    return builder.as_markup()


def outline_width_menu() -> InlineKeyboardMarkup:
    return _width_picker("ow", back_to="back_effects")


def border_width_menu() -> InlineKeyboardMarkup:
    return _width_picker("bw", back_to="back_effects")


def _width_picker(prefix: str, back_to: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="2", callback_data=f"{prefix}_2"),
        InlineKeyboardButton(text="4", callback_data=f"{prefix}_4"),
        InlineKeyboardButton(text="6", callback_data=f"{prefix}_6"),
    )
    builder.row(
        InlineKeyboardButton(text="10", callback_data=f"{prefix}_10"),
        InlineKeyboardButton(text="15", callback_data=f"{prefix}_15"),
        InlineKeyboardButton(text="20", callback_data=f"{prefix}_20"),
    )
    builder.row(
        InlineKeyboardButton(text="30", callback_data=f"{prefix}_30"),
        InlineKeyboardButton(text="40", callback_data=f"{prefix}_40"),
    )
    builder.row(InlineKeyboardButton(text="⬅️ Назад", callback_data=back_to))
    return builder.as_markup()


def patterns_menu() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="⚫ Точки", callback_data="p_dots"),
        InlineKeyboardButton(text="➖ Полосы", callback_data="p_stripes"),
    )
    builder.row(
        InlineKeyboardButton(text="⭐ Звёзды", callback_data="p_stars"),
        InlineKeyboardButton(text="❤️ Сердца", callback_data="p_hearts"),
    )
    builder.row(
        InlineKeyboardButton(text="✦ Искры", callback_data="p_sparkles"),
        InlineKeyboardButton(text="▦ Сетка", callback_data="p_grid"),
    )
    builder.row(
        InlineKeyboardButton(text="🗑 Убрать паттерн", callback_data="p_clear"),
    )
    builder.row(InlineKeyboardButton(text="⬅️ Назад", callback_data="back_editor"))
    return builder.as_markup()


# ============================ ШАБЛОНЫ ============================

def templates_menu() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🐱 Кот", callback_data="tpl_cat"),
        InlineKeyboardButton(text="🐶 Пёс", callback_data="tpl_dog"),
    )
    builder.row(
        InlineKeyboardButton(text="💖 Сердце", callback_data="tpl_heart"),
        InlineKeyboardButton(text="⭐ Звезда", callback_data="tpl_star"),
    )
    builder.row(
        InlineKeyboardButton(text="🔥 Огонь", callback_data="tpl_fire"),
        InlineKeyboardButton(text="✨ Сияние", callback_data="tpl_shine"),
    )
    builder.row(
        InlineKeyboardButton(text="🎲 Случайный", callback_data="tpl_random"),
    )
    builder.row(InlineKeyboardButton(text="⬅️ Главное меню", callback_data="back_main"))
    return builder.as_markup()


# ============================ НАСТРОЙКИ ============================

def settings_menu() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🎨 Цвет обводки", callback_data="set_oc"),
        InlineKeyboardButton(text="📏 Толщина", callback_data="set_ow"),
    )
    builder.row(
        InlineKeyboardButton(text="🔠 Шрифт", callback_data="set_font"),
        InlineKeyboardButton(text="💧 Водяной знак", callback_data="set_wm"),
    )
    builder.row(
        InlineKeyboardButton(text="🗑 Сброс настроек", callback_data="set_reset"),
    )
    builder.row(InlineKeyboardButton(text="⬅️ Главное меню", callback_data="back_main"))
    return builder.as_markup()


def settings_outline_width() -> InlineKeyboardMarkup:
    return _width_picker("setow", back_to="settings")


# ============================ ГАЛЕРЕЯ ============================

def gallery_menu(stickers: list, page: int = 0, per_page: int = 10, total: int = 0) -> InlineKeyboardMarkup:
    """Меню галереи со списком стикеров и пагинацией."""
    builder = InlineKeyboardBuilder()
    for sid, _path, _emoji, _pack, created in stickers:
        date_str = created[:16] if created else ""
        builder.row(
            InlineKeyboardButton(
                text=f"🖼 #{sid} • {date_str}",
                callback_data=f"view_{sid}",
            )
        )

    # Пагинация
    max_page = max(0, (total - 1) // per_page)
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton(text="⬅️", callback_data=f"page_{page - 1}"))
    nav.append(InlineKeyboardButton(text=f"📄 {page + 1}/{max_page + 1}", callback_data="noop"))
    if page < max_page:
        nav.append(InlineKeyboardButton(text="➡️", callback_data=f"page_{page + 1}"))
    if nav:
        builder.row(*nav)

    builder.row(InlineKeyboardButton(text="⬅️ Главное меню", callback_data="back_main"))
    return builder.as_markup()


def sticker_actions(sticker_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📥 Скачать .webp", callback_data=f"dl_{sticker_id}"),
    )
    builder.row(
        InlineKeyboardButton(text="😄 Сменить эмодзи", callback_data=f"ch_emoji_{sticker_id}"),
        InlineKeyboardButton(text="📦 В пак", callback_data=f"to_pack_{sticker_id}"),
    )
    builder.row(
        InlineKeyboardButton(text="⭐ В избранное", callback_data=f"fav_{sticker_id}"),
        InlineKeyboardButton(text="🗑 Удалить", callback_data=f"del_{sticker_id}"),
    )
    builder.row(InlineKeyboardButton(text="⬅️ К галерее", callback_data="gallery"))
    return builder.as_markup()


# ============================ ПАКИ СТИКЕРОВ ============================

def packs_menu() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="➕ Создать новый пак", callback_data="new_pack"),
    )
    builder.row(
        InlineKeyboardButton(text="📥 Инструкция по добавлению в Telegram", callback_data="pack_help"),
    )
    builder.row(InlineKeyboardButton(text="⬅️ Главное меню", callback_data="back_main"))
    return builder.as_markup()


def confirm_yes_no(action: str) -> InlineKeyboardMarkup:
    """Универсальное подтверждение."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Да", callback_data=f"yes_{action}"),
            InlineKeyboardButton(text="❌ Нет", callback_data=f"no_{action}"),
        ]
    ])
