"""
Tests for Geometry primitives, BBox, YOLO coordinate conversion, IoU, and reading order sorting.
"""

import pytest
from utils.geometry import Point, BBox, calculate_iou, sort_bboxes_reading_order


def test_point():
    p = Point(x=10.0, y=20.0)
    assert p.x == 10.0
    assert p.y == 20.0


def test_bbox_properties():
    box = BBox(x_min=10.0, y_min=20.0, x_max=50.0, y_max=80.0, class_id=3)
    assert box.width == 40.0
    assert box.height == 60.0
    assert box.center_x == 30.0
    assert box.center_y == 50.0
    assert box.area == 2400.0


def test_bbox_yolo_roundtrip():
    img_w, img_h = 1000, 1000
    orig_box = BBox(x_min=100.0, y_min=200.0, x_max=300.0, y_max=400.0, class_id=5)

    cid, cx, cy, w, h = orig_box.to_yolo(img_w, img_h)
    assert cid == 5
    assert cx == pytest.approx(0.2, abs=1e-5)
    assert cy == pytest.approx(0.3, abs=1e-5)
    assert w == pytest.approx(0.2, abs=1e-5)
    assert h == pytest.approx(0.2, abs=1e-5)

    restored = BBox.from_yolo(cid, cx, cy, w, h, img_w, img_h)
    assert restored.x_min == pytest.approx(orig_box.x_min, abs=1e-3)
    assert restored.y_min == pytest.approx(orig_box.y_min, abs=1e-3)
    assert restored.x_max == pytest.approx(orig_box.x_max, abs=1e-3)
    assert restored.y_max == pytest.approx(orig_box.y_max, abs=1e-3)


def test_calculate_iou():
    box1 = BBox(x_min=0, y_min=0, x_max=10, y_max=10)
    box2 = BBox(x_min=5, y_min=0, x_max=15, y_max=10)
    # intersection: [5..10] x [0..10] = 50
    # union: 100 + 100 - 50 = 150
    # iou: 50 / 150 = 0.3333...
    assert calculate_iou(box1, box2) == pytest.approx(1.0 / 3.0, abs=1e-4)

    # Disjoint boxes
    box3 = BBox(x_min=20, y_min=20, x_max=30, y_max=30)
    assert calculate_iou(box1, box3) == 0.0


def test_sort_bboxes_reading_order():
    # Line 1: two boxes
    b1 = BBox(x_min=10, y_min=10, x_max=30, y_max=30, class_id=1)
    b2 = BBox(x_min=40, y_min=12, x_max=60, y_max=32, class_id=2)
    # Line 2: two boxes
    b3 = BBox(x_min=10, y_min=60, x_max=30, y_max=80, class_id=3)
    b4 = BBox(x_min=40, y_min=58, x_max=60, y_max=78, class_id=4)

    # Input in scrambled order
    scrambled = [b4, b1, b3, b2]
    ordered = sort_bboxes_reading_order(scrambled)

    assert [b.class_id for b in ordered] == [1, 2, 3, 4]
