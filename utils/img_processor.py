# utils/img_processor.py
import io
from PIL import Image
from rembg import remove
from config import MAX_STICKER_SIZE


def process_image(image_bytes: bytes, remove_background: bool = True) -> io.BytesIO:
    """
    Process image: optionally remove background, crop transparent padding,
    resize to 512px max dimension, return PNG bytes buffer.
    
    Args:
        image_bytes: Raw input image bytes
        remove_background: Whether to remove background using rembg
        
    Returns:
        io.BytesIO containing processed PNG image
    """
    # Remove background if requested
    if remove_background:
        output_bytes = remove(image_bytes)
        img = Image.open(io.BytesIO(output_bytes))
    else:
        img = Image.open(io.BytesIO(image_bytes))
    
    # Convert to RGBA if not already
    if img.mode != 'RGBA':
        img = img.convert('RGBA')
    
    # Crop transparent padding if background was removed
    if remove_background:
        bbox = img.getbbox()
        if bbox:
            img = img.crop(bbox)
    
    # Calculate new size maintaining aspect ratio
    width, height = img.size
    max_dimension = max(width, height)
    
    if max_dimension > MAX_STICKER_SIZE:
        scale_factor = MAX_STICKER_SIZE / max_dimension
        new_width = int(width * scale_factor)
        new_height = int(height * scale_factor)
        img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    # Ensure at least one dimension is exactly 512px
    width, height = img.size
    if width != MAX_STICKER_SIZE and height != MAX_STICKER_SIZE:
        if width > height:
            new_width = MAX_STICKER_SIZE
            new_height = int(height * (MAX_STICKER_SIZE / width))
        else:
            new_height = MAX_STICKER_SIZE
            new_width = int(width * (MAX_STICKER_SIZE / height))
        img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    # Save to bytes buffer
    output_buffer = io.BytesIO()
    img.save(output_buffer, format='PNG', optimize=True)
    output_buffer.seek(0)
    
    return output_buffer
