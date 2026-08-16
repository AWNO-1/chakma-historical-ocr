"""
Image processing utilities for Chakma Historical OCR.
Handles loading, saving, canvas creation, and visual overlay drawing.
"""

from pathlib import Path
from typing import List, Optional, Tuple, Union
import numpy as np
from PIL import Image, ImageDraw

from utils.file_utils import resolve_path, ensure_dir
from utils.geometry import BBox


def load_image(image_path: Union[str, Path]) -> Image.Image:
    """
    Load image from path as RGB PIL Image.
    """
    path = resolve_path(image_path)
    if not path.exists():
        raise FileNotFoundError(f"Image not found at: {path}")
    return Image.open(path).convert("RGB")


def save_image(image: Image.Image, output_path: Union[str, Path], quality: int = 95) -> Path:
    """
    Save PIL image to file.
    """
    path = resolve_path(output_path)
    ensure_dir(path.parent)
    image.save(path, quality=quality)
    return path


def create_blank_canvas(
    width: int,
    height: int,
    color: Tuple[int, int, int] = (245, 238, 220),
) -> Image.Image:
    """
    Create a new RGB image canvas with solid background color.
    """
    return Image.new("RGB", (width, height), color)


def draw_bounding_boxes(
    image: Image.Image,
    boxes: List[BBox],
    outline_color: str = "red",
    width: int = 2,
    draw_labels: bool = True,
) -> Image.Image:
    """
    Draw bounding boxes on a copy of the image.
    """
    annotated = image.copy()
    draw = ImageDraw.Draw(annotated)

    for box in boxes:
        draw.rectangle(
            [(box.x_min, box.y_min), (box.x_max, box.y_max)],
            outline=outline_color,
            width=width,
        )
        if draw_labels and box.class_name:
            label_text = f"{box.class_name} ({box.confidence:.2f})" if box.confidence < 1.0 else box.class_name
            draw.text((box.x_min, max(0.0, box.y_min - 12)), label_text, fill=outline_color)

    return annotated


def pil_to_numpy(image: Image.Image) -> np.ndarray:
    """
    Convert PIL Image to NumPy array (H, W, C) RGB.
    """
    return np.array(image)


def numpy_to_pil(array: np.ndarray) -> Image.Image:
    """
    Convert NumPy array (H, W, C) to PIL Image.
    """
    return Image.fromarray(array.astype(np.uint8))
