"""
Font Engine for loading Chakma TrueType / OpenType fonts and glyph metrics.
"""

from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
from PIL import ImageFont
from utils.file_utils import resolve_path
from utils.logging_utils import setup_logger

logger = setup_logger("font_engine")


class FontEngine:
    """
    Manages loading and rendering Chakma fonts.
    """

    def __init__(self, fonts_dir: Union[str, Path] = "fonts"):
        self.fonts_dir = resolve_path(fonts_dir)
        self.available_fonts: List[Path] = []
        self._font_cache: Dict[Tuple[str, int], ImageFont.FreeTypeFont] = {}
        self._scan_fonts()

    def _scan_fonts(self) -> None:
        """Scan fonts directory for .ttf and .otf files."""
        if self.fonts_dir.exists():
            self.available_fonts = list(self.fonts_dir.glob("*.ttf")) + list(self.fonts_dir.glob("*.otf"))
            logger.info(f"Discovered {len(self.available_fonts)} font(s) in {self.fonts_dir}")
        else:
            logger.warning(f"Fonts directory does not exist: {self.fonts_dir}")

    def get_font(self, font_name: Optional[str] = None, size: int = 32) -> Optional[ImageFont.FreeTypeFont]:
        """
        Retrieve cached or load font at specified size.
        """
        # Skeleton implementation for Stage 01
        return None
