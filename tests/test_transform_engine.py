"""
Unit and Integration Tests for Stage 09 — Historical Document Transformation Engine.
Tests all geometric transformations, optical/photometric degradations,
bounding box transformation synchronicity, coordinate validity, and pipeline determinism.
"""

from pathlib import Path
import numpy as np
import pytest
from PIL import Image

from generator.augmentations import (
    AugmentationEngine,
    apply_blur,
    apply_noise,
    apply_ink_variation,
    apply_illumination,
    apply_bleedthrough,
    apply_compression_artifacts,
)
from generator.transform_engine import (
    TransformPipeline,
    GeometricTransformConfig,
    TransformationResult,
    apply_rotation,
    apply_translation,
    apply_perspective,
    apply_elastic,
    apply_curvature,
    validate_transformed_bboxes,
)
from utils.geometry import BBox


@pytest.fixture
def sample_canvas_and_boxes() -> tuple[Image.Image, list[BBox]]:
    """Fixture providing a test 1024x1024 PIL image and a grid of valid bounding boxes."""
    img = Image.new("RGB", (1024, 1024), (245, 238, 220))
    boxes = [
        BBox(x_min=100.0, y_min=100.0, x_max=160.0, y_max=160.0, class_id=1, confidence=1.0),
        BBox(x_min=200.0, y_min=100.0, x_max=260.0, y_max=160.0, class_id=2, confidence=1.0),
        BBox(x_min=300.0, y_min=100.0, x_max=360.0, y_max=160.0, class_id=3, confidence=1.0),
        BBox(x_min=100.0, y_min=250.0, x_max=160.0, y_max=310.0, class_id=4, confidence=1.0),
        BBox(x_min=500.0, y_min=500.0, x_max=580.0, y_max=580.0, class_id=5, confidence=1.0),
        BBox(x_min=800.0, y_min=800.0, x_max=880.0, y_max=880.0, class_id=6, confidence=1.0),
    ]
    return img, boxes


def test_rotation_transformation(sample_canvas_and_boxes):
    """Verify rotation transforms image and updates bounding boxes without NaNs or zero area."""
    img, boxes = sample_canvas_and_boxes
    rot_img, rot_boxes, params = apply_rotation(img, boxes, angle_deg=5.0)

    assert isinstance(rot_img, Image.Image)
    assert rot_img.size == (1024, 1024)
    assert len(rot_boxes) == len(boxes)
    assert "angle_deg" in params
    assert "matrix" in params

    val = validate_transformed_bboxes(rot_boxes, 1024, 1024)
    assert val["is_valid"] is True
    assert len(val["errors"]) == 0

    # Center box at (500, 500) rotated around (512, 512) stays near center
    center_box = rot_boxes[4]
    assert 480.0 < center_box.center_x < 600.0
    assert 480.0 < center_box.center_y < 600.0


def test_translation_transformation(sample_canvas_and_boxes):
    """Verify translation shifts image and updates bounding box coordinates exactly."""
    img, boxes = sample_canvas_and_boxes
    tx, ty = 25.0, -15.0
    trans_img, trans_boxes, params = apply_translation(img, boxes, tx=tx, ty=ty)

    assert trans_img.size == (1024, 1024)
    assert len(trans_boxes) == len(boxes)

    val = validate_transformed_bboxes(trans_boxes, 1024, 1024)
    assert val["is_valid"] is True

    # Check first box exact shifted coordinates
    b0_orig = boxes[0]
    b0_trans = trans_boxes[0]
    assert pytest.approx(b0_trans.x_min, abs=0.1) == b0_orig.x_min + tx
    assert pytest.approx(b0_trans.y_min, abs=0.1) == b0_orig.y_min + ty


def test_perspective_warp(sample_canvas_and_boxes):
    """Verify perspective homography warps image and projects 4 bbox corners accurately."""
    img, boxes = sample_canvas_and_boxes
    warp_img, warp_boxes, params = apply_perspective(img, boxes, scale=0.03, seed=42)

    assert warp_img.size == (1024, 1024)
    assert len(warp_boxes) == len(boxes)
    assert "homography_matrix" in params

    val = validate_transformed_bboxes(warp_boxes, 1024, 1024)
    assert val["is_valid"] is True
    assert len(val["errors"]) == 0


def test_elastic_mesh_distortion(sample_canvas_and_boxes):
    """Verify smooth displacement field warps image and bounds correctly."""
    img, boxes = sample_canvas_and_boxes
    elast_img, elast_boxes, params = apply_elastic(img, boxes, alpha=20.0, sigma=6.0, seed=42)

    assert elast_img.size == (1024, 1024)
    assert len(elast_boxes) == len(boxes)
    assert "alpha" in params
    assert "sigma" in params

    val = validate_transformed_bboxes(elast_boxes, 1024, 1024)
    assert val["is_valid"] is True


def test_page_curvature(sample_canvas_and_boxes):
    """Verify book spine page curvature smoothly shifts coordinates and bboxes."""
    img, boxes = sample_canvas_and_boxes
    curv_img, curv_boxes, params = apply_curvature(
        img, boxes, amplitude=20.0, frequency=1.0, direction="vertical"
    )

    assert curv_img.size == (1024, 1024)
    assert len(curv_boxes) == len(boxes)
    assert "amplitude" in params

    val = validate_transformed_bboxes(curv_boxes, 1024, 1024)
    assert val["is_valid"] is True


def test_photometric_augmentations(sample_canvas_and_boxes):
    """Verify individual photometric and optical degradation functions execute properly."""
    img, _ = sample_canvas_and_boxes

    # 1. Blur
    for b_type in ["gaussian", "motion", "box"]:
        b_img = apply_blur(img, blur_type=b_type, kernel_size=3)
        assert b_img.size == img.size

    # 2. Noise
    for n_type in ["gaussian", "speckle", "salt_pepper"]:
        n_img = apply_noise(img, noise_type=n_type, var=0.01, seed=42)
        assert n_img.size == img.size

    # 3. Ink variation
    ink_img = apply_ink_variation(img, fade_ratio=0.3, color_shift=(40, 30, 20), seed=42)
    assert ink_img.size == img.size

    # 4. Illumination
    for pat in ["vignette", "linear_gradient", "spotlight"]:
        illum_img = apply_illumination(img, pattern=pat, intensity=0.3, seed=42)
        assert illum_img.size == img.size

    # 5. Bleed-through
    bleed_img = apply_bleedthrough(img, intensity=0.2, seed=42)
    assert bleed_img.size == img.size

    # 6. JPEG compression
    jpeg_img = apply_compression_artifacts(img, quality=60)
    assert jpeg_img.size == img.size


def test_transform_pipeline_end_to_end(sample_canvas_and_boxes):
    """Verify TransformPipeline executes combined geometric and optical stages with seed reproducibility."""
    img, boxes = sample_canvas_and_boxes
    pipeline = TransformPipeline(seed=42)

    res1 = pipeline.apply(img, boxes, seed=100)
    res2 = pipeline.apply(img, boxes, seed=100)

    assert isinstance(res1, TransformationResult)
    assert res1.image.size == (1024, 1024)
    assert res1.total_boxes > 0
    assert len(res1.applied_transforms) > 0

    # Determinism / byte-for-byte reproducibility
    assert res1.image.tobytes() == res2.image.tobytes()
    assert len(res1.bboxes) == len(res2.bboxes)
    for b1, b2 in zip(res1.bboxes, res2.bboxes):
        assert b1.x_min == b2.x_min
        assert b1.y_min == b2.y_min
        assert b1.x_max == b2.x_max
        assert b1.y_max == b2.y_max


def test_bbox_validation_catches_invalid_boxes():
    """Verify validate_transformed_bboxes correctly flags NaNs, negative dimensions, and out-of-bounds boxes."""
    invalid_boxes = [
        BBox(x_min=float("nan"), y_min=10.0, x_max=50.0, y_max=50.0),  # NaN
        BBox(x_min=50.0, y_min=50.0, x_max=40.0, y_max=60.0),          # x_max < x_min
        BBox(x_min=10.0, y_min=10.0, x_max=10.0, y_max=20.0),          # zero width
        BBox(x_min=-10.0, y_min=10.0, x_max=50.0, y_max=50.0),         # negative coordinate
        BBox(x_min=1000.0, y_min=10.0, x_max=1050.0, y_max=50.0),      # exceeds 1024 canvas
    ]
    report = validate_transformed_bboxes(invalid_boxes, canvas_width=1024, canvas_height=1024)
    assert report["is_valid"] is False
    assert len(report["errors"]) >= 5
