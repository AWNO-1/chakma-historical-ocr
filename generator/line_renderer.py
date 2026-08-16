"""
Line Renderer for rendering text strings with glyph-level bounding box tracking.
"""

from typing import List, Tuple
from PIL import Image, ImageDraw, ImageFont
from utils.geometry import BBox
from generator.metadata import CharacterAnnotation


class LineRenderer:
    """
    Renders text line onto PIL Image/Draw context and records character-level bounding boxes.
    """

    def __init__(self):
        pass

    def render_line(
        self,
        image: Image.Image,
        text: str,
        position: Tuple[int, int],
        font: ImageFont.ImageFont,
        ink_color: Tuple[int, int, int] = (20, 20, 20),
    ) -> Tuple[Image.Image, List[CharacterAnnotation]]:
        """
        Render line onto image and return character bounding box annotations.
        Skeleton implementation for Stage 01.
        """
        # Placeholder for Stage 01
        return image, []
