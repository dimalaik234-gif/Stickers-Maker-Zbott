"""
Модуль обработки изображений для стикеров.

Содержит все эффекты: фильтры, текст, эмодзи, рамки, тени, повороты, паттерны.
Все функции возвращают RGBA-изображение размером STICKER_SIZE x STICKER_SIZE
(для соответствия требованиям Telegram).
"""
from __future__ import annotations
import os
import math
import random
from pathlib import Path
from typing import Tuple, Optional

from PIL import (
    Image, ImageDraw, ImageFont, ImageFilter, ImageOps,
    ImageEnhance, ImageChops,
)

from config import STICKER_SIZE, MAX_STICKER_BYTES, FONTS_DIR

# ============================ ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ============================

def hex_to_rgba(hex_color: str, alpha: int = 255) -> Tuple[int, int, int, int]:
    """Преобразовать #RRGGBB в (R, G, B, A). Поддерживает короткую форму #RGB."""
    s = hex_color.lstrip("#")
    if len(s) == 3:
        s = "".join(c * 2 for c in s)
    if len(s) != 6:
        return (0, 0, 0, alpha)
    return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16), alpha)


def resize_to_sticker(image: Image.Image) -> Image.Image:
    """
    Подогнать изображение под 512×512 с сохранением пропорций.
    Прозрачный фон, центрирование.
    """
    image = image.convert("RGBA")
    ratio = min(STICKER_SIZE / image.width, STICKER_SIZE / image.height)
    new_size = (max(1, int(image.width * ratio)), max(1, int(image.height * ratio)))
    image = image.resize(new_size, Image.LANCZOS)

    canvas = Image.new("RGBA", (STICKER_SIZE, STICKER_SIZE), (0, 0, 0, 0))
    offset = ((STICKER_SIZE - image.width) // 2, (STICKER_SIZE - image.height) // 2)
    canvas.paste(image, offset, image)
    return canvas


def get_font(size: int, font_name: str = "bold") -> ImageFont.FreeTypeFont:
    """
    Загрузить шрифт. Сначала пробуем локальные шрифты из FONTS_DIR,
    затем системные. Если ничего не нашли — дефолтный.
    """
    candidates: list[Path] = []

    # 1. Локальные шрифты (можно положить свои .ttf в data/fonts)
    local_map = {
        "default": ["Roboto-Regular.ttf", "arial.ttf"],
        "bold": ["Roboto-Bold.ttf", "arialbd.ttf", "DejaVuSans-Bold.ttf"],
        "italic": ["Roboto-Italic.ttf", "ariali.ttf"],
        "comic": ["ComicSansMS.ttf", "ComicNeue-Bold.ttf"],
        "mono": ["RobotoMono-Regular.ttf"],
    }
    for name in local_map.get(font_name, local_map["default"]):
        candidates.append(FONTS_DIR / name)

    # 2. Системные шрифты Linux
    system_map = {
        "default": [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        ],
        "bold": [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        ],
        "italic": [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Oblique.ttf",
        ],
        "comic": [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        ],
        "mono": [
            "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
        ],
    }
    for p in system_map.get(font_name, system_map["default"]):
        candidates.append(Path(p))

    for path in candidates:
        if path.exists():
            try:
                return ImageFont.truetype(str(path), size)
            except Exception:
                continue

    # В крайнем случае — дефолтный растровый шрифт (не масштабируется)
    return ImageFont.load_default()


# ============================ ФОРМЫ / КРОП ============================

def crop_circle(image: Image.Image) -> Image.Image:
    """Вырезать в круг."""
    image = image.convert("RGBA")
    image = resize_to_sticker(image)
    mask = Image.new("L", (STICKER_SIZE, STICKER_SIZE), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, STICKER_SIZE, STICKER_SIZE), fill=255)
    out = Image.new("RGBA", (STICKER_SIZE, STICKER_SIZE), (0, 0, 0, 0))
    out.paste(image, (0, 0), mask)
    return out


def crop_rounded(image: Image.Image, radius: int = 60) -> Image.Image:
    """Прямоугольник со скруглёнными углами."""
    image = image.convert("RGBA")
    image = resize_to_sticker(image)
    mask = Image.new("L", (STICKER_SIZE, STICKER_SIZE), 0)
    ImageDraw.Draw(mask).rounded_rectangle(
        (0, 0, STICKER_SIZE - 1, STICKER_SIZE - 1),
        radius=radius, fill=255,
    )
    out = Image.new("RGBA", (STICKER_SIZE, STICKER_SIZE), (0, 0, 0, 0))
    out.paste(image, (0, 0), mask)
    return out


def crop_diamond(image: Image.Image) -> Image.Image:
    """Ромбовидная маска."""
    image = image.convert("RGBA")
    image = resize_to_sticker(image)
    mask = Image.new("L", (STICKER_SIZE, STICKER_SIZE), 0)
    draw = ImageDraw.Draw(mask)
    draw.polygon([
        (STICKER_SIZE // 2, 0),
        (STICKER_SIZE, STICKER_SIZE // 2),
        (STICKER_SIZE // 2, STICKER_SIZE),
        (0, STICKER_SIZE // 2),
    ], fill=255)
    out = Image.new("RGBA", (STICKER_SIZE, STICKER_SIZE), (0, 0, 0, 0))
    out.paste(image, (0, 0), mask)
    return out


def crop_hexagon(image: Image.Image) -> Image.Image:
    """Шестиугольная маска."""
    image = image.convert("RGBA")
    image = resize_to_sticker(image)
    cx, cy = STICKER_SIZE // 2, STICKER_SIZE // 2
    r = STICKER_SIZE // 2
    points = []
    for i in range(6):
        a = math.radians(60 * i - 30)
        points.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    mask = Image.new("L", (STICKER_SIZE, STICKER_SIZE), 0)
    ImageDraw.Draw(mask).polygon(points, fill=255)
    out = Image.new("RGBA", (STICKER_SIZE, STICKER_SIZE), (0, 0, 0, 0))
    out.paste(image, (0, 0), mask)
    return out


def crop_star(image: Image.Image) -> Image.Image:
    """Звезда (5 конечностей)."""
    image = image.convert("RGBA")
    image = resize_to_sticker(image)
    cx, cy = STICKER_SIZE // 2, STICKER_SIZE // 2
    r_out = STICKER_SIZE // 2
    r_in = r_out * 0.45
    points = []
    for i in range(10):
        r = r_out if i % 2 == 0 else r_in
        a = math.radians(36 * i - 90)
        points.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    mask = Image.new("L", (STICKER_SIZE, STICKER_SIZE), 0)
    ImageDraw.Draw(mask).polygon(points, fill=255)
    out = Image.new("RGBA", (STICKER_SIZE, STICKER_SIZE), (0, 0, 0, 0))
    out.paste(image, (0, 0), mask)
    return out


# ============================ ТРАНСФОРМАЦИИ ============================

def rotate(image: Image.Image, angle: float) -> Image.Image:
    """Повернуть на произвольный угол с expand=True (без обрезки углов)."""
    image = image.convert("RGBA")
    rotated = image.rotate(-angle, resample=Image.BICUBIC, expand=True)
    return resize_to_sticker(rotated)


def flip_h(image: Image.Image) -> Image.Image:
    return resize_to_sticker(ImageOps.mirror(image.convert("RGBA")))


def flip_v(image: Image.Image) -> Image.Image:
    return resize_to_sticker(ImageOps.flip(image.convert("RGBA")))


# ============================ ФИЛЬТРЫ ============================

def filter_grayscale(image: Image.Image) -> Image.Image:
    return resize_to_sticker(ImageOps.grayscale(image.convert("RGBA")).convert("RGBA"))


def filter_sepia(image: Image.Image) -> Image.Image:
    """Сепия — имитация через colorize поверх grayscale."""
    gray = ImageOps.grayscale(image.convert("RGBA"))
    sepia = ImageOps.colorize(gray, "#704214", "#C0A062").convert("RGBA")
    return resize_to_sticker(sepia)


def filter_invert(image: Image.Image) -> Image.Image:
    r, g, b, a = image.convert("RGBA").split()
    inv = ImageOps.invert(Image.merge("RGB", (r, g, b)))
    return resize_to_sticker(Image.merge("RGBA", (*inv.split(), a)))


def filter_posterize(image: Image.Image, bits: int = 3) -> Image.Image:
    """Снижение количества цветов (постеризация). Работает с RGB, сохраняет альфу."""
    image = image.convert("RGBA")
    r, g, b, a = image.split()
    rgb = Image.merge("RGB", (r, g, b))
    out_rgb = ImageOps.posterize(rgb, bits)
    return resize_to_sticker(Image.merge("RGBA", (*out_rgb.split(), a)))


def filter_solarize(image: Image.Image, threshold: int = 128) -> Image.Image:
    """Соляризация. Работает с RGB, сохраняет альфу."""
    image = image.convert("RGBA")
    r, g, b, a = image.split()
    rgb = Image.merge("RGB", (r, g, b))
    out_rgb = ImageOps.solarize(rgb, threshold)
    return resize_to_sticker(Image.merge("RGBA", (*out_rgb.split(), a)))


def filter_threshold(image: Image.Image, threshold: int = 128) -> Image.Image:
    gray = image.convert("L")
    bw = gray.point(lambda x: 255 if x > threshold else 0, "1")
    return resize_to_sticker(bw.convert("RGBA"))


def filter_edge(image: Image.Image) -> Image.Image:
    """Выделение границ (похоже на карандашный набросок)."""
    img = image.convert("L")
    edges = img.filter(ImageFilter.FIND_EDGES)
    return resize_to_sticker(edges.convert("RGBA"))


def filter_emboss(image: Image.Image) -> Image.Image:
    return resize_to_sticker(image.convert("RGBA").filter(ImageFilter.EMBOSS))


def filter_contour(image: Image.Image) -> Image.Image:
    return resize_to_sticker(image.convert("RGBA").filter(ImageFilter.CONTOUR))


def filter_blur(image: Image.Image, radius: int = 4) -> Image.Image:
    return resize_to_sticker(image.convert("RGBA").filter(ImageFilter.GaussianBlur(radius)))


def filter_sharpen(image: Image.Image) -> Image.Image:
    return resize_to_sticker(image.convert("RGBA").filter(ImageFilter.SHARPEN))


def filter_pastel(image: Image.Image) -> Image.Image:
    """Мягкий пастельный эффект: светлее, контраст ниже, насыщенность ниже."""
    img = image.convert("RGBA")
    img = ImageEnhance.Brightness(img).enhance(1.15)
    img = ImageEnhance.Contrast(img).enhance(0.85)
    img = ImageEnhance.Color(img).enhance(0.65)
    return resize_to_sticker(img)


def filter_vintage(image: Image.Image) -> Image.Image:
    """Тёплый винтажный тон."""
    img = image.convert("RGBA")
    r, g, b, a = img.split()
    gray = ImageOps.grayscale(img)
    colored = ImageOps.colorize(gray, "#704214", "#C0A062")
    return resize_to_sticker(Image.merge("RGBA", (*colored.split(), a)))


def filter_cool(image: Image.Image) -> Image.Image:
    img = image.convert("RGBA")
    r, g, b, a = img.split()
    gray = ImageOps.grayscale(img)
    colored = ImageOps.colorize(gray, "#0a1a3a", "#aaccff")
    return resize_to_sticker(Image.merge("RGBA", (*colored.split(), a)))


def filter_duotone(image: Image.Image, dark="#1a1a3a", light="#ffcc66") -> Image.Image:
    img = image.convert("RGBA")
    r, g, b, a = img.split()
    gray = ImageOps.grayscale(img)
    colored = ImageOps.colorize(gray, dark, light)
    return resize_to_sticker(Image.merge("RGBA", (*colored.split(), a)))


def adjust_brightness(image: Image.Image, factor: float) -> Image.Image:
    return resize_to_sticker(ImageEnhance.Brightness(image.convert("RGBA")).enhance(factor))


def adjust_contrast(image: Image.Image, factor: float) -> Image.Image:
    return resize_to_sticker(ImageEnhance.Contrast(image.convert("RGBA")).enhance(factor))


def adjust_saturation(image: Image.Image, factor: float) -> Image.Image:
    return resize_to_sticker(ImageEnhance.Color(image.convert("RGBA")).enhance(factor))


def adjust_sharpness(image: Image.Image, factor: float) -> Image.Image:
    return resize_to_sticker(ImageEnhance.Sharpness(image.convert("RGBA")).enhance(factor))


# ============================ ТЕКСТ ============================

def _text_position_coords(
    draw: ImageDraw.ImageDraw, text: str, font, position: str, canvas_size: int, margin: int
) -> Tuple[int, int, int, int]:
    """Получить координаты текста по имени позиции. Возвращает (x, y, w, h)."""
    bbox = draw.textbbox((0, 0), text, font=font)
    w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]

    pos = position
    if pos == "top":
        return (canvas_size // 2 - w // 2, margin, w, h)
    if pos == "bottom":
        return (canvas_size // 2 - w // 2, canvas_size - h - margin, w, h)
    if pos == "center":
        return (canvas_size // 2 - w // 2, canvas_size // 2 - h // 2, w, h)
    if pos == "top-left":
        return (margin, margin, w, h)
    if pos == "top-right":
        return (canvas_size - w - margin, margin, w, h)
    if pos == "bottom-left":
        return (margin, canvas_size - h - margin, w, h)
    if pos == "bottom-right":
        return (canvas_size - w - margin, canvas_size - h - margin, w, h)
    # default = bottom
    return (canvas_size // 2 - w // 2, canvas_size - h - margin, w, h)


def add_text(
    image: Image.Image,
    text: str,
    font_size: int = 50,
    color: Tuple[int, int, int, int] = (255, 255, 255, 255),
    bg_color: Optional[Tuple[int, int, int, int]] = None,
    position: str = "bottom",
    stroke_width: int = 3,
    stroke_color: Tuple[int, int, int, int] = (0, 0, 0, 255),
    font_name: str = "bold",
    auto_size: bool = True,
) -> Image.Image:
    """
    Добавить текст. Если auto_size=True, шрифт автоматически уменьшается,
    чтобы текст влез в стикер.
    """
    image = resize_to_sticker(image.convert("RGBA"))
    font = get_font(font_size, font_name)
    draw = ImageDraw.Draw(image)

    # Подгоняем размер, чтобы текст не вылезал за края
    if auto_size:
        max_w = STICKER_SIZE - 40
        while font_size > 12:
            tmp = get_font(font_size, font_name)
            bbox = draw.textbbox((0, 0), text, font=tmp)
            if (bbox[2] - bbox[0]) <= max_w:
                font = tmp
                break
            font_size -= 4

    x, y, w, h = _text_position_coords(draw, text, font, position, STICKER_SIZE, 20)

    if bg_color is not None:
        pad = 8
        draw.rectangle([x - pad, y - pad, x + w + pad, y + h + pad], fill=bg_color)

    draw.text(
        (x, y), text, font=font, fill=color,
        stroke_width=stroke_width, stroke_fill=stroke_color,
    )
    return image


# ============================ ЭМОДЗИ ============================

# Стандартный набор эмодзи для быстрого доступа
POPULAR_EMOJIS = [
    "😀", "😃", "😄", "😁", "😆", "😅", "🤣", "😂", "🙂", "🙃",
    "😉", "😊", "😇", "🥰", "😍", "🤩", "😘", "😗", "😚", "😙",
    "😋", "😛", "😜", "🤪", "😝", "🤑", "🤗", "🤭", "🤫", "🤔",
    "🤐", "🤨", "😐", "😑", "😶", "😏", "😒", "🙄", "😬", "🤥",
    "😌", "😔", "😪", "🤤", "😴", "😷", "🤒", "🤕", "🤢", "🤮",
    "🥵", "🥶", "😎", "🤓", "🧐", "😕", "😟", "🙁", "☹️", "😮",
    "😯", "😲", "😳", "🥺", "😦", "😧", "😨", "😰", "😥", "😢",
    "😭", "😱", "😖", "😣", "😞", "😓", "😩", "😫", "🥱", "😤",
    "😡", "😠", "🤬", "😈", "👿", "💀", "☠️", "💩", "🤡", "👹",
    "👺", "👻", "👽", "👾", "🤖", "😺", "😸", "😹", "😻", "😼",
    "😽", "🙀", "😿", "😾", "❤️", "🧡", "💛", "💚", "💙", "💜",
    "🖤", "🤍", "🤎", "💔", "❣️", "💕", "💞", "💓", "💗", "💖",
    "💘", "💝", "💟", "☮️", "✝️", "☪️", "🕉️", "☸️", "✡️", "🔯",
    "🕎", "☯️", "☦️", "🛐", "⛎", "♈", "♉", "♊", "♋", "♌",
    "👍", "👎", "👏", "🙌", "👐", "🤲", "🤝", "🙏", "✍️", "💅",
    "🤳", "💪", "🦾", "🦿", "🦵", "🦶", "👂", "🦻", "👃", "🧠",
    "🔥", "✨", "⭐", "🌟", "💫", "⚡", "☀️", "🌈", "☁️", "❄️",
]

# Шрифты с цветными эмодзи
EMOJI_FONTS = [
    "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf",
    "/usr/share/fonts/truetype/seguiemj/seguiemj.ttf",
    "/usr/share/fonts/truetype/noto-emoji/NotoColorEmoji.ttf",
    "/Library/Fonts/Apple Color Emoji.ttc",
    str(FONTS_DIR / "NotoColorEmoji.ttf"),
]


def _get_emoji_font(size: int):
    for p in EMOJI_FONTS:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                continue
    return get_font(size, "bold")


def add_emoji(
    image: Image.Image,
    emoji_char: str,
    size: int = 120,
    position: str = "top-right",
    opacity: float = 1.0,
) -> Image.Image:
    """Наложить эмодзи на стикер."""
    image = resize_to_sticker(image.convert("RGBA"))
    overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    font = _get_emoji_font(size)
    bbox = draw.textbbox((0, 0), emoji_char, font=font)
    w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    margin = 20

    pos_map = {
        "top-left": (margin, margin),
        "top-right": (image.width - w - margin, margin),
        "bottom-left": (margin, image.height - h - margin),
        "bottom-right": (image.width - w - margin, image.height - h - margin),
        "center": ((image.width - w) // 2, (image.height - h) // 2),
    }
    x, y = pos_map.get(position, pos_map["top-right"])

    try:
        draw.text((x, y), emoji_char, font=font, embedded_color=True)
    except TypeError:
        # Старые версии Pillow без embedded_color
        draw.text((x, y), emoji_char, font=font, fill=(255, 255, 255, 255))

    if opacity < 1.0:
        alpha = overlay.split()[3].point(lambda p: int(p * opacity))
        overlay.putalpha(alpha)

    return Image.alpha_composite(image, overlay)


# ============================ ЭФФЕКТЫ (рамки, тени, обводки) ============================

def add_border(
    image: Image.Image, color=(0, 0, 0, 255), width: int = 10
) -> Image.Image:
    """Прямоугольная рамка вокруг изображения."""
    image = image.convert("RGBA")
    bordered = Image.new(
        "RGBA",
        (image.width + width * 2, image.height + width * 2),
        color,
    )
    bordered.paste(image, (width, width), image)
    return resize_to_sticker(bordered)


def add_outline(
    image: Image.Image, color=(0, 0, 0, 255), width: int = 6
) -> Image.Image:
    """Обводка по силуэту (дилатация альфа-канала)."""
    image = image.convert("RGBA")
    alpha = image.split()[3]

    outline_alpha = alpha.copy()
    for _ in range(max(1, width)):
        outline_alpha = outline_alpha.filter(ImageFilter.MaxFilter(3))

    outline = Image.new("RGBA", image.size, color)
    outline.putalpha(outline_alpha)

    # Накладываем оригинал поверх
    combined = Image.alpha_composite(outline, image)
    return resize_to_sticker(combined)


def add_drop_shadow(
    image: Image.Image,
    offset=(8, 8),
    color=(0, 0, 0, 180),
    blur_radius: int = 12,
) -> Image.Image:
    """Тень с заданным смещением и размытием."""
    image = image.convert("RGBA")

    # Размер холста с запасом под смещение и размытие
    pad = blur_radius * 2 + max(abs(offset[0]), abs(offset[1]))
    canvas_size = (image.width + pad * 2, image.height + pad * 2)
    canvas = Image.new("RGBA", canvas_size, (0, 0, 0, 0))

    # Генерируем тень из альфа-канала
    shadow = Image.new("RGBA", image.size, color)
    shadow.putalpha(image.split()[3])
    shadow = shadow.filter(ImageFilter.GaussianBlur(blur_radius))

    sx = pad + offset[0]
    sy = pad + offset[1]
    canvas.paste(shadow, (sx, sy), shadow)

    # Оригинал по центру
    ox = pad - min(offset[0], 0)
    oy = pad - min(offset[1], 0)
    canvas.paste(image, (ox, oy), image)

    return resize_to_sticker(canvas)


def add_glow(
    image: Image.Image,
    color=(255, 255, 0, 200),
    radius: int = 20,
) -> Image.Image:
    """Свечение вокруг объекта."""
    image = image.convert("RGBA")

    glow_size = (image.width + radius * 4, image.height + radius * 4)
    canvas = Image.new("RGBA", glow_size, (0, 0, 0, 0))

    glow_layer = Image.new("RGBA", image.size, color)
    glow_layer.putalpha(image.split()[3])
    glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(radius))

    offset = (radius * 2, radius * 2)
    canvas.paste(glow_layer, offset, glow_layer)
    canvas.paste(image, offset, image)

    return resize_to_sticker(canvas)


# ============================ ПАТТЕРНЫ / ОВЕРЛЕИ ============================

def add_pattern(
    image: Image.Image, pattern: str, color=(255, 255, 255, 120), density: int = 30
) -> Image.Image:
    """Добавить узор поверх изображения."""
    image = resize_to_sticker(image.convert("RGBA"))
    overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    font = get_font(int(density * 0.7), "bold")

    if pattern == "dots":
        for x in range(0, image.width, density):
            for y in range(0, image.height, density):
                r = max(2, density // 8)
                draw.ellipse((x - r, y - r, x + r, y + r), fill=color)
    elif pattern == "stripes":
        for x in range(0, image.width, density // 2):
            draw.rectangle((x, 0, x + max(2, density // 4), image.height), fill=color)
    elif pattern == "stars":
        for x in range(0, image.width, density * 2):
            for y in range(0, image.height, density * 2):
                draw.text((x, y), "★", fill=color, font=font)
    elif pattern == "hearts":
        for x in range(0, image.width, density * 2):
            for y in range(0, image.height, density * 2):
                draw.text((x, y), "♥", fill=color, font=font)
    elif pattern == "sparkles":
        for x in range(0, image.width, density * 2):
            for y in range(0, image.height, density * 2):
                draw.text((x, y), "✦", fill=color, font=font)
    elif pattern == "grid":
        for x in range(0, image.width, density):
            draw.line((x, 0, x, image.height), fill=color, width=1)
        for y in range(0, image.height, density):
            draw.line((0, y, image.width, y), fill=color, width=1)

    return Image.alpha_composite(image, overlay)


# ============================ ВОДЯНОЙ ЗНАК ============================

def add_watermark(image: Image.Image, text: str, opacity: int = 90) -> Image.Image:
    """Диагональный повторяющийся водяной знак."""
    image = resize_to_sticker(image.convert("RGBA"))

    overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    font = get_font(40, "bold")

    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    step_x, step_y = tw + 30, th + 30

    for y in range(-th, image.height, step_y):
        for x in range(-tw, image.width, step_x):
            draw.text((x, y), text, font=font, fill=(255, 255, 255, opacity))

    overlay = overlay.rotate(-30, resample=Image.BICUBIC, expand=False)
    return Image.alpha_composite(image, overlay)


# ============================ КОЛЛАЖИ ============================

def make_collage(images: list[Image.Image], layout: str = "grid", spacing: int = 10) -> Image.Image:
    """Собрать коллаж из нескольких изображений."""
    if not images:
        return resize_to_sticker(Image.new("RGBA", (STICKER_SIZE, STICKER_SIZE), (0, 0, 0, 0)))

    images = [resize_to_sticker(img.convert("RGBA")) for img in images]

    if layout == "horizontal":
        w = sum(i.width for i in images) + spacing * (len(images) - 1)
        h = max(i.height for i in images)
        canvas = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        x = 0
        for i in images:
            canvas.paste(i, (x, (h - i.height) // 2), i)
            x += i.width + spacing
    elif layout == "vertical":
        w = max(i.width for i in images)
        h = sum(i.height for i in images) + spacing * (len(images) - 1)
        canvas = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        y = 0
        for i in images:
            canvas.paste(i, ((w - i.width) // 2, y), i)
            y += i.height + spacing
    else:  # grid
        n = len(images)
        cols = math.ceil(math.sqrt(n))
        rows = math.ceil(n / cols)
        cell = max(80, STICKER_SIZE // max(cols, rows))
        small = [i.resize((cell, cell), Image.LANCZOS) for i in images]
        w = cols * cell + spacing * (cols + 1)
        h = rows * cell + spacing * (rows + 1)
        canvas = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        for idx, im in enumerate(small):
            r, c = idx // cols, idx % cols
            x = spacing + c * (cell + spacing)
            y = spacing + r * (cell + spacing)
            canvas.paste(im, (x, y), im)

    return resize_to_sticker(canvas)


# ============================ СОХРАНЕНИЕ И ОПТИМИЗАЦИЯ ============================

def save_sticker(image: Image.Image, path: str, quality: int = 90) -> str:
    """Сохранить стикер в формате WebP (оптимально для Telegram)."""
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    image = image.convert("RGBA")
    image.save(path, "WEBP", quality=quality, method=6, lossless=False)
    return path


def optimize_for_telegram(path: str, max_bytes: int = MAX_STICKER_BYTES) -> str:
    """Если файл слишком большой — уменьшаем качество до прохождения лимита."""
    if os.path.getsize(path) <= max_bytes:
        return path

    img = Image.open(path).convert("RGBA")
    for q in (85, 80, 75, 70, 65, 60, 55, 50, 45, 40):
        img.save(path, "WEBP", quality=q, method=6)
        if os.path.getsize(path) <= max_bytes:
            return path
    return path


# ============================ ГЕНЕРАЦИЯ ШАБЛОНОВ ============================

def template_heart(color: str = "#ff3366") -> Image.Image:
    img = Image.new("RGBA", (STICKER_SIZE, STICKER_SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    c = hex_to_rgba(color)
    cx, cy = STICKER_SIZE // 2, STICKER_SIZE // 2
    r = 90
    # Две окружности + треугольник = сердце
    draw.ellipse((cx - r * 2 + r, cy - r, cx + r, cy + r), fill=c)
    draw.ellipse((cx, cy - r, cx + r * 2, cy + r), fill=c)
    draw.polygon([
        (cx - r, cy + r // 2),
        (cx + r, cy + r // 2),
        (cx, cy + r * 2),
    ], fill=c)
    return resize_to_sticker(img)


def template_star(color: str = "#ffcc00") -> Image.Image:
    img = Image.new("RGBA", (STICKER_SIZE, STICKER_SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    cx, cy = STICKER_SIZE // 2, STICKER_SIZE // 2
    r_out, r_in = 200, 90
    points = []
    for i in range(10):
        r = r_out if i % 2 == 0 else r_in
        a = math.radians(36 * i - 90)
        points.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    draw.polygon(points, fill=hex_to_rgba(color))
    return resize_to_sticker(img)


def template_fire() -> Image.Image:
    img = Image.new("RGBA", (STICKER_SIZE, STICKER_SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    cx, cy = STICKER_SIZE // 2, STICKER_SIZE // 2 + 40
    # Внешний контур (оранжевый)
    points_out = [
        (cx, cy - 180), (cx + 60, cy - 100), (cx + 30, cy - 80),
        (cx + 100, cy), (cx + 50, cy + 80), (cx + 120, cy + 160),
        (cx, cy + 220), (cx - 120, cy + 160), (cx - 50, cy + 80),
        (cx - 100, cy), (cx - 30, cy - 80), (cx - 60, cy - 100),
    ]
    draw.polygon(points_out, fill=(255, 100, 0, 255))
    # Средний контур (жёлтый)
    points_mid = [
        (cx, cy - 130), (cx + 40, cy - 60), (cx + 20, cy - 40),
        (cx + 70, cy + 20), (cx, cy + 110), (cx - 70, cy + 20),
        (cx - 20, cy - 40), (cx - 40, cy - 60),
    ]
    draw.polygon(points_mid, fill=(255, 200, 0, 255))
    # Ядро (белое)
    points_in = [
        (cx, cy - 50), (cx + 25, cy), (cx, cy + 60), (cx - 25, cy),
    ]
    draw.polygon(points_in, fill=(255, 255, 200, 255))
    return resize_to_sticker(img)


def template_shine() -> Image.Image:
    """Лучи света."""
    img = Image.new("RGBA", (STICKER_SIZE, STICKER_SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    cx, cy = STICKER_SIZE // 2, STICKER_SIZE // 2
    for i in range(12):
        a = math.radians(30 * i)
        x1 = cx + int(60 * math.cos(a))
        y1 = cy + int(60 * math.sin(a))
        x2 = cx + int(220 * math.cos(a))
        y2 = cy + int(220 * math.sin(a))
        draw.line((x1, y1, x2, y2), fill=(255, 220, 100, 220), width=14)
    draw.ellipse((cx - 50, cy - 50, cx + 50, cy + 50), fill=(255, 255, 200, 255))
    return resize_to_sticker(img)


def template_cat_emoji() -> Image.Image:
    """Шаблон: кот-смайлик."""
    img = Image.new("RGBA", (STICKER_SIZE, STICKER_SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    cx, cy = STICKER_SIZE // 2, STICKER_SIZE // 2
    # Мордочка
    draw.ellipse((cx - 180, cy - 160, cx + 180, cy + 200), fill=(255, 200, 80, 255))
    # Уши
    draw.polygon([(cx - 180, cy - 140), (cx - 100, cy - 140), (cx - 160, cy - 230)], fill=(255, 200, 80, 255))
    draw.polygon([(cx + 180, cy - 140), (cx + 100, cy - 140), (cx + 160, cy - 230)], fill=(255, 200, 80, 255))
    # Глаза
    draw.ellipse((cx - 100, cy - 40, cx - 40, cy + 20), fill=(40, 40, 40, 255))
    draw.ellipse((cx + 40, cy - 40, cx + 100, cy + 20), fill=(40, 40, 40, 255))
    draw.ellipse((cx - 80, cy - 25, cx - 60, cy - 5), fill=(255, 255, 255, 255))
    draw.ellipse((cx + 60, cy - 25, cx + 80, cy - 5), fill=(255, 255, 255, 255))
    # Нос
    draw.polygon([(cx, cy + 30), (cx - 20, cy + 60), (cx + 20, cy + 60)], fill=(255, 120, 120, 255))
    # Рот
    draw.arc((cx - 50, cy + 50, cx + 50, cy + 130), start=0, end=180, fill=(40, 40, 40, 255), width=6)
    # Усики
    for dx in (-1, 1):
        for dy in (0, 20, 40):
            draw.line((cx + dx * 30, cy + 60 + dy, cx + dx * 130, cy + 50 + dy), fill=(40, 40, 40, 255), width=3)
    return resize_to_sticker(img)


def template_dog_emoji() -> Image.Image:
    img = Image.new("RGBA", (STICKER_SIZE, STICKER_SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    cx, cy = STICKER_SIZE // 2, STICKER_SIZE // 2
    # Голова
    draw.ellipse((cx - 180, cy - 140, cx + 180, cy + 200), fill=(180, 130, 80, 255))
    # Уши (висячие)
    draw.ellipse((cx - 200, cy - 180, cx - 80, cy + 20), fill=(140, 90, 50, 255))
    draw.ellipse((cx + 80, cy - 180, cx + 200, cy + 20), fill=(140, 90, 50, 255))
    # Глаза
    draw.ellipse((cx - 90, cy - 40, cx - 30, cy + 20), fill=(40, 40, 40, 255))
    draw.ellipse((cx + 30, cy - 40, cx + 90, cy + 20), fill=(40, 40, 40, 255))
    # Нос
    draw.ellipse((cx - 25, cy + 60, cx + 25, cy + 100), fill=(40, 40, 40, 255))
    # Язык
    draw.ellipse((cx - 25, cy + 110, cx + 25, cy + 170), fill=(255, 100, 100, 255))
    return resize_to_sticker(img)


def template_random() -> Image.Image:
    """Случайная красивая абстракция."""
    img = Image.new("RGBA", (STICKER_SIZE, STICKER_SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    palette = [
        (255, 100, 100, 180), (100, 255, 100, 180), (100, 100, 255, 180),
        (255, 200, 100, 180), (200, 100, 255, 180), (100, 255, 200, 180),
    ]
    for _ in range(40):
        x = random.randint(0, STICKER_SIZE)
        y = random.randint(0, STICKER_SIZE)
        r = random.randint(20, 80)
        color = random.choice(palette)
        draw.ellipse((x - r, y - r, x + r, y + r), fill=color)
    return resize_to_sticker(img)


def generate_template(name: str) -> Optional[Image.Image]:
    """Получить шаблон по имени."""
    return {
        "heart": template_heart,
        "star": template_star,
        "fire": template_fire,
        "shine": template_shine,
        "cat": template_cat_emoji,
        "dog": template_dog_emoji,
        "random": template_random,
    }.get(name, lambda: None)()
