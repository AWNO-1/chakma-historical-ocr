"""
Annotation Engine for exporting annotations to standard YOLO format.
"""

from pathlib import Path
from typing import List, Union
from utils.file_utils import resolve_path, ensure_dir
from utils.geometry import BBox


class AnnotationEngine:
    """
    Handles converting character bounding boxes to YOLO annotation format (.txt).
    """

    @staticmethod
    def format_yolo_line(box: BBox, image_width: int, image_height: int) -> str:
        """
        Format a single BBox as a YOLO annotation string:
        <class_id> <x_center> <y_center> <width> <height>
        """
        cid, cx, cy, w, h = box.to_yolo(image_width, image_height)
        return f"{cid} {cx:.6f} {cy:.6f} {w:.6f} {h:.6f}"

    @classmethod
    def save_yolo_annotations(
        cls,
        boxes: List[BBox],
        image_width: int,
        image_height: int,
        output_path: Union[str, Path],
    ) -> Path:
        """
        Write all bounding boxes to a YOLO label file.
        """
        path = resolve_path(output_path)
        ensure_dir(path.parent)
        lines = [cls.format_yolo_line(b, image_width, image_height) for b in boxes if b.class_id >= 0]
        with open(path, "w", encoding="utf-8") as f:
            for line in lines:
                f.write(f"{line}\n")
        return path
