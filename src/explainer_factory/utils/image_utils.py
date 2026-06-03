"""Image processing utilities."""

from pathlib import Path


def check_image_dimensions(file_path: Path) -> tuple[int, int] | None:
    """Get dimensions of an image without fully loading it.
    
    Args:
        file_path: Path to the image file.
        
    Returns:
        Tuple of (width, height) or None if invalid.
    """
    try:
        from PIL import Image
        with Image.open(file_path) as img:
            return img.size
    except Exception:
        return None
