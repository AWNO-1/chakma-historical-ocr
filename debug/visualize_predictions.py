"""
Visualization script for inspecting model prediction bounding boxes and detections.
"""

from pathlib import Path
from typing import List, Union
from PIL import Image
from utils.file_utils import resolve_path
from utils.geometry import BBox
from utils.image_utils import load_image, draw_bounding_boxes
from utils.logging_utils import setup_logger

logger = setup_logger("visualize_predictions")


def visualize_predictions(
    image_path: Union[str, Path],
    predicted_boxes: List[BBox],
    output_path: Union[str, Path] = None,
) -> Image.Image:
    """Draw predicted bounding boxes with confidence onto image."""
    img = load_image(image_path)
    annotated = draw_bounding_boxes(img, predicted_boxes, outline_color="red", width=2, draw_labels=True)

    if output_path:
        annotated.save(resolve_path(output_path))
    return annotated
