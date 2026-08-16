"""
Tests for Synthetic Generator skeleton and Annotation Engine.
"""

import pytest
from pathlib import Path
from generator.api import SyntheticDataGenerator
from generator.annotation_engine import AnnotationEngine
from utils.geometry import BBox


def test_generator_initialization():
    gen = SyntheticDataGenerator()
    assert gen.config is not None
    assert gen.charset_engine is not None
    assert gen.corpus_engine is not None
    assert gen.font_engine is not None
    assert gen.background_engine is not None


def test_annotation_engine_formatting(tmp_path: Path):
    box = BBox(x_min=100, y_min=200, x_max=300, y_max=400, class_id=2)
    line = AnnotationEngine.format_yolo_line(box, image_width=1000, image_height=1000)
    parts = line.split()
    assert len(parts) == 5
    assert parts[0] == "2"

    out_file = tmp_path / "label_test.txt"
    saved_path = AnnotationEngine.save_yolo_annotations([box], 1000, 1000, out_file)
    assert saved_path.exists()
    content = saved_path.read_text(encoding="utf-8").strip()
    assert content == line
