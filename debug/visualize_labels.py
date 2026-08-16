"""
Visualization script for inspecting ground truth YOLO labels overlaid on images.
"""

from pathlib import Path
from typing import List, Union
from PIL import Image
from utils.file_utils import resolve_path, read_text_lines
from utils.geometry import BBox
from utils.image_utils import load_image, draw_bounding_boxes
from utils.logging_utils import setup_logger

logger = setup_logger("visualize_labels")


def parse_yolo_label_file(label_path: Union[str, Path], img_w: int, img_h: int) -> List[BBox]:
    """Parse YOLO formatted label file into list of BBoxes."""
    path = resolve_path(label_path)
    if not path.exists():
        return []

    boxes = []
    lines = read_text_lines(path)
    for line in lines:
        parts = line.strip().split()
        if len(parts) >= 5:
            cid = int(parts[0])
            cx, cy, w, h = map(float, parts[1:5])
            bbox = BBox.from_yolo(cid, cx, cy, w, h, img_w, img_h)
            boxes.append(bbox)
    return boxes


def visualize_image_with_labels(
    image_path: Union[str, Path],
    label_path: Union[str, Path],
    output_path: Union[str, Path] = None,
) -> Image.Image:
    """Load image and draw YOLO label bounding boxes."""
    img = load_image(image_path)
    boxes = parse_yolo_label_file(label_path, img.width, img.height)
    annotated = draw_bounding_boxes(img, boxes, outline_color="green", width=2)

    if output_path:
        annotated.save(resolve_path(output_path))
    return annotated
