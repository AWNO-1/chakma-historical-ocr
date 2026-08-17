"""
Comprehensive unit tests for geometric primitives and spatial calculations.
"""

import pytest
from utils.geometry import (
    Point,
    BBox,
    calculate_iou,
    calculate_intersection_area,
    sort_bboxes_reading_order,
)


def test_point():
    p = Point(10.5, 20.25)
    assert p.x == 10.5
    assert p.y == 20.25
    assert p.to_tuple() == (10.5, 20.25)


def test_bbox_properties():
    box = BBox(x_min=10.0, y_min=20.0, x_max=60.0, y_max=120.0, class_id=7)
    assert box.width == 50.0
    assert box.height == 100.0
    assert box.center_x == 35.0
    assert box.center_y == 70.0
    assert box.area == 5000.0
    assert box.is_valid() is True
    assert box.is_within_bounds(1024, 1024) is True


def test_bbox_yolo_roundtrip():
    orig_box = BBox(x_min=100.0, y_min=200.0, x_max=300.0, y_max=400.0, class_id=3)
    img_w, img_h = 1000, 1000

    cls_id, cx, cy, w, h = orig_box.to_yolo(img_w, img_h)
    assert cls_id == 3
    assert cx == 0.2
    assert cy == 0.3
    assert w == 0.2
    assert h == 0.2

    reconstructed = BBox.from_yolo(cls_id, cx, cy, w, h, img_w, img_h)
    assert abs(reconstructed.x_min - orig_box.x_min) < 1e-5
    assert abs(reconstructed.y_min - orig_box.y_min) < 1e-5
    assert abs(reconstructed.x_max - orig_box.x_max) < 1e-5
    assert abs(reconstructed.y_max - orig_box.y_max) < 1e-5


def test_calculate_iou():
    # Identical boxes
    b1 = BBox(0, 0, 10, 10)
    b2 = BBox(0, 0, 10, 10)
    assert calculate_iou(b1, b2) == 1.0

    # Disjoint boxes
    b3 = BBox(20, 20, 30, 30)
    assert calculate_iou(b1, b3) == 0.0

    # 50% area overlap (intersection=50, union=150 -> IoU = 1/3)
    b4 = BBox(0, 0, 10, 10)  # Area 100
    b5 = BBox(5, 0, 15, 10)  # Area 100, intersection = 5*10 = 50, union = 150
    assert abs(calculate_iou(b4, b5) - (50.0 / 150.0)) < 1e-5


def test_calculate_intersection_area():
    b1 = BBox(0, 0, 10, 10)
    b2 = BBox(5, 0, 15, 10)
    assert calculate_intersection_area(b1, b2) == 50.0


def test_bbox_clipping():
    out_of_bounds = BBox(x_min=-10.0, y_min=-5.0, x_max=1050.0, y_max=1030.0)
    clipped = out_of_bounds.clip(1024, 1024)
    assert clipped.x_min == 0.0
    assert clipped.y_min == 0.0
    assert clipped.x_max == 1024.0
    assert clipped.y_max == 1024.0


def test_sort_bboxes_reading_order():
    # Two lines of boxes out of order
    # Line 1 (y ≈ 50): box A at x=100, box B at x=30
    box_1b = BBox(x_min=100, y_min=50, x_max=120, y_max=80)
    box_1a = BBox(x_min=30, y_min=52, x_max=50, y_max=82)

    # Line 2 (y ≈ 120): box C at x=200, box D at x=40
    box_2b = BBox(x_min=200, y_min=120, x_max=220, y_max=150)
    box_2a = BBox(x_min=40, y_min=122, x_max=60, y_max=152)

    unsorted = [box_2b, box_1b, box_2a, box_1a]
    ordered = sort_bboxes_reading_order(unsorted, line_tolerance_ratio=0.6)

    assert ordered == [box_1a, box_1b, box_2a, box_2b]
