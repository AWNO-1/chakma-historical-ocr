"""
Background Engine for sampling or generating historical manuscript backgrounds.
"""

from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
from PIL import Image
from utils.file_utils import resolve_path
from utils.image_utils import create_blank_canvas
from utils.logging_utils import setup_logger

logger = setup_logger("background_engine")


class BackgroundEngine:
    """
    Manages loading and synthesizing historical paper/parchment/manuscript backgrounds.
    """

    def __init__(self, backgrounds_dir: Union[str, Path] = "data/backgrounds"):
        self.backgrounds_dir = resolve_path(backgrounds_dir)
        self.categories: Dict[str, List[Path]] = {
            "paper": [],
            "parchment": [],
            "manuscript": [],
            "bamboo": [],
            "miscellaneous": [],
        }
        self._scan_backgrounds()

    def _scan_backgrounds(self) -> None:
        """Scan categories for background images."""
        if not self.backgrounds_dir.exists():
            return
        for cat in self.categories.keys():
            cat_dir = self.backgrounds_dir / cat
            if cat_dir.exists():
                images = list(cat_dir.glob("*.jpg")) + list(cat_dir.glob("*.png")) + list(cat_dir.glob("*.jpeg"))
                self.categories[cat] = images

    def get_background(
        self,
        category: Optional[str] = None,
        width: int = 1024,
        height: int = 1024,
    ) -> Tuple[Image.Image, str, str]:
        """
        Return a background image canvas, category name, and source file identifier.
        """
        # Default solid antique canvas if no background image is available
        canvas = create_blank_canvas(width, height, color=(245, 238, 220))
        return canvas, category or "default", "procedural_blank"
