"""
Geometric primitives and spatial calculations for Chakma Historical OCR.
Handles Bounding Boxes, YOLO format conversions, IoU, and spatial sorting.
"""

from dataclasses import dataclass
from typing import List, Optional, Tuple


@dataclass
class Point:
    x: float
    y: float


@dataclass
class BBox:
    """
    Axis-aligned bounding box representation in absolute pixel coordinates.
    """
    x_min: float
    y_min: float
    x_max: float
    y_max: float
    class_id: int = -1
    class_name: Optional[str] = None
    confidence: float = 1.0

    @property
    def width(self) -> float:
        return max(0.0, self.x_max - self.x_min)

    @property
    def height(self) -> float:
        return max(0.0, self.y_max - self.y_min)

    @property
    def center_x(self) -> float:
        return self.x_min + self.width / 2.0

    @property
    def center_y(self) -> float:
        return self.y_min + self.height / 2.0

    @property
    def area(self) -> float:
        return self.width * self.height

    def to_yolo(self, image_width: int, image_height: int) -> Tuple[int, float, float, float, float]:
        """
        Convert to normalized YOLO format: (class_id, norm_center_x, norm_center_y, norm_w, norm_h).
        """
        if image_width <= 0 or image_height <= 0:
            raise ValueError(f"Invalid image dimensions: {image_width}x{image_height}")

        norm_cx = self.center_x / image_width
        norm_cy = self.center_y / image_height
        norm_w = self.width / image_width
        norm_h = self.height / image_height

        # Clamp normalized values between 0.0 and 1.0
        norm_cx = max(0.0, min(1.0, norm_cx))
        norm_cy = max(0.0, min(1.0, norm_cy))
        norm_w = max(0.0, min(1.0, norm_w))
        norm_h = max(0.0, min(1.0, norm_h))

        return self.class_id, norm_cx, norm_cy, norm_w, norm_h

    @classmethod
    def from_yolo(
        cls,
        class_id: int,
        norm_cx: float,
        norm_cy: float,
        norm_w: float,
        norm_h: float,
        image_width: int,
        image_height: int,
        confidence: float = 1.0,
        class_name: Optional[str] = None,
    ) -> "BBox":
        """
        Create BBox from normalized YOLO coordinate format.
        """
        cx = norm_cx * image_width
        cy = norm_cy * image_height
        w = norm_w * image_width
        h = norm_h * image_height

        x_min = cx - w / 2.0
        y_min = cy - h / 2.0
        x_max = cx + w / 2.0
        y_max = cy + h / 2.0

        return cls(
            x_min=max(0.0, x_min),
            y_min=max(0.0, y_min),
            x_max=min(float(image_width), x_max),
            y_max=min(float(image_height), y_max),
            class_id=class_id,
            class_name=class_name,
            confidence=confidence,
        )


def calculate_iou(box1: BBox, box2: BBox) -> float:
    """
    Calculate Intersection over Union (IoU) between two bounding boxes.
    """
    inter_x_min = max(box1.x_min, box2.x_min)
    inter_y_min = max(box1.y_min, box2.y_min)
    inter_x_max = min(box1.x_max, box2.x_max)
    inter_y_max = min(box1.y_max, box2.y_max)

    inter_w = max(0.0, inter_x_max - inter_x_min)
    inter_h = max(0.0, inter_y_max - inter_y_min)
    inter_area = inter_w * inter_h

    union_area = box1.area + box2.area - inter_area
    if union_area <= 0:
        return 0.0

    return inter_area / union_area


def sort_bboxes_reading_order(boxes: List[BBox], line_tolerance_ratio: float = 0.5) -> List[BBox]:
    """
    Deterministic reading-order sorting (top-to-bottom, left-to-right).
    Groups boxes into lines based on vertical overlap/tolerance, then sorts left-to-right within lines.
    """
    if not boxes:
        return []

    # Sort primarily by y_min
    sorted_by_y = sorted(boxes, key=lambda b: (b.y_min, b.x_min))

    lines: List[List[BBox]] = []
    current_line: List[BBox] = [sorted_by_y[0]]

    for box in sorted_by_y[1:]:
        # Calculate line vertical threshold from median height of current line
        avg_height = sum(b.height for b in current_line) / len(current_line)
        tolerance = avg_height * line_tolerance_ratio

        # Check if box center_y falls within vertical span of current line
        line_min_y = min(b.y_min for b in current_line)
        line_max_y = max(b.y_max for b in current_line)

        if abs(box.center_y - ((line_min_y + line_max_y) / 2.0)) <= tolerance:
            current_line.append(box)
        else:
            lines.append(current_line)
            current_line = [box]

    if current_line:
        lines.append(current_line)

    # Sort each line left-to-right
    ordered_boxes: List[BBox] = []
    for line in lines:
        ordered_boxes.extend(sorted(line, key=lambda b: b.x_min))

    return ordered_boxes
