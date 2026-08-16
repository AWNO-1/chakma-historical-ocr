"""
Visualization script for inspecting generated synthetic manuscript images.
"""

from pathlib import Path
from typing import Union
from PIL import Image
from utils.file_utils import resolve_path
from utils.image_utils import load_image
from utils.logging_utils import setup_logger

logger = setup_logger("visualize_synthetic")


def visualize_synthetic_sample(image_path: Union[str, Path]) -> Image.Image:
    """Load and preview a synthetic sample image."""
    path = resolve_path(image_path)
    logger.info(f"Visualizing synthetic image: {path}")
    return load_image(path)
