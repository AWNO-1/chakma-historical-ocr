"""
Unit and Integration Tests for Stage 10: Synthetic Ground Truth and YOLO Label Engine.
"""

from pathlib import Path
import tempfile
import numpy as np
import pytest
from PIL import Image

from generator.annotation_engine import (
    YoloLabelWriter,
    YoloAnnotation,
    YoloValidationResult,
    DatasetValidationSummary,
)
from generator.api import SyntheticGenerator
from generator.charset_engine import CharsetEngine
from generator.metadata import SampleCharacter, SyntheticSample, CharacterAnnotation
from utils.geometry import BBox


@pytest.fixture
def charset_engine():
    return CharsetEngine()


@pytest.fixture
def yolo_writer(charset_engine):
    return YoloLabelWriter(charset_engine=charset_engine)


@pytest.fixture
def synthetic_generator():
    return SyntheticGenerator(seed=42)


def test_yolo_annotation_conversion(yolo_writer):
    ann = YoloAnnotation(
        class_id=14,
        x_center=0.5,
        y_center=0.5,
        width=0.2,
        height=0.1,
    )
    line = ann.to_yolo_line()
    assert line == "14 0.500000 0.500000 0.200000 0.100000"

    bbox = ann.to_bbox(1000, 1000)
    assert bbox.x_min == 400.0
    assert bbox.x_max == 600.0
    assert bbox.y_min == 450.0
    assert bbox.y_max == 550.0
    assert bbox.class_id == 14


def test_to_yolo_single_character(yolo_writer):
    char = SampleCharacter(
        id=0,
        class_id=5,
        text="𑄅",
        bbox=BBox(x_min=100.0, y_min=200.0, x_max=200.0, y_max=300.0, class_id=5),
        line_id=0,
        word_id=0,
        reading_order=0,
    )
    line = yolo_writer.to_yolo(char, image_width=1000, image_height=1000)
    assert line == "5 0.150000 0.250000 0.100000 0.100000"


def test_write_and_parse_label_file(yolo_writer):
    with tempfile.TemporaryDirectory() as tmp_dir:
        label_file = Path(tmp_dir) / "sample_001.txt"
        chars = [
            SampleCharacter(
                id=0,
                class_id=0,
                text="𑄀",
                bbox=BBox(x_min=100.0, y_min=100.0, x_max=150.0, y_max=150.0, class_id=0),
                line_id=0,
                word_id=0,
                reading_order=0,
            ),
            SampleCharacter(
                id=1,
                class_id=10,
                text="𑄊",
                bbox=BBox(x_min=200.0, y_min=200.0, x_max=280.0, y_max=260.0, class_id=10),
                line_id=0,
                word_id=0,
                reading_order=1,
            ),
        ]

        out_path = yolo_writer.write_label_file(label_file, chars, image_width=1000, image_height=1000)
        assert out_path.exists()

        parsed = yolo_writer.parse_label_file(out_path)
        assert len(parsed) == 2
        assert parsed[0].class_id == 0
        assert parsed[1].class_id == 10
        assert parsed[0].width == pytest.approx(0.05)
        assert parsed[0].height == pytest.approx(0.05)


def test_validate_label_valid_cases(yolo_writer):
    valid_ann = YoloAnnotation(class_id=0, x_center=0.5, y_center=0.5, width=0.1, height=0.1)
    res = yolo_writer.validate_label(valid_ann)
    assert res.is_valid
    assert len(res.errors) == 0


def test_validate_label_invalid_class_id(yolo_writer):
    invalid_ann = YoloAnnotation(class_id=999, x_center=0.5, y_center=0.5, width=0.1, height=0.1)
    res = yolo_writer.validate_label(invalid_ann)
    assert not res.is_valid
    assert any("Invalid class_id: 999" in e for e in res.errors)


def test_validate_label_out_of_bounds(yolo_writer):
    invalid_ann = YoloAnnotation(class_id=0, x_center=1.5, y_center=0.5, width=0.1, height=0.1)
    res = yolo_writer.validate_label(invalid_ann)
    assert not res.is_valid
    assert any("x_center out of normalized range" in e for e in res.errors)


def test_validate_label_nan_coordinates(yolo_writer):
    invalid_ann = YoloAnnotation(class_id=0, x_center=float("nan"), y_center=0.5, width=0.1, height=0.1)
    res = yolo_writer.validate_label(invalid_ann)
    assert not res.is_valid
    assert any("NaN or Inf" in e for e in res.errors)


def test_validate_label_zero_area(yolo_writer):
    invalid_ann = YoloAnnotation(class_id=0, x_center=0.5, y_center=0.5, width=0.0, height=0.1)
    res = yolo_writer.validate_label(invalid_ann)
    assert not res.is_valid
    assert any("Non-positive width" in e for e in res.errors)


def test_validate_all_batch_summary(yolo_writer, synthetic_generator):
    samples = synthetic_generator.generate_batch(count=5, start_seed=100)
    summary = yolo_writer.validate_all(samples)

    assert isinstance(summary, DatasetValidationSummary)
    assert summary.total_samples == 5
    assert summary.total_labels > 0
    assert summary.valid_labels == summary.total_labels
    assert summary.invalid_labels == 0
    assert summary.is_valid
    assert len(summary.class_frequencies) > 0


def test_visualize_labels(yolo_writer):
    img = Image.new("RGB", (400, 400), (255, 255, 255))
    labels = [
        YoloAnnotation(class_id=0, x_center=0.25, y_center=0.25, width=0.1, height=0.1),
        YoloAnnotation(class_id=15, x_center=0.75, y_center=0.75, width=0.1, height=0.1),
    ]
    vis = yolo_writer.visualize_labels(img, labels)
    assert isinstance(vis, Image.Image)
    assert vis.size == (400, 400)
    arr = np.array(vis)
    # Ensure drawing made changes to solid white background
    assert np.any(arr != 255)
