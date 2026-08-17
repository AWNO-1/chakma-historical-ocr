"""
Comprehensive unit tests for Layout and Character Geometry Engine.
"""

from pathlib import Path
import pytest

from generator.layout_engine import LayoutEngine, PageLayout, LineLayout, CharacterLayout
from generator.charset_engine import CharsetEngine
from generator.font_engine import FontEngine


SAMPLE_LINES = [
    "𑄟𑄚𑄪𑄌𑄴 𑄃𑄟𑄢𑄴 𑄘𑄬𑄌𑄴 𑄌𑄋𑄴𑄟 𑄞𑄌𑄴 𑄇𑄧𑄠𑄴𑅁",
    "𑄢𑄎 𑄘𑄬𑄌𑄮𑄖𑄴 𑄇𑄟𑄴 𑄉𑄧𑄢𑄬𑅁",
    "𑄃𑄟𑄢𑄴 𑄇𑄨𑄖𑄛𑄴 𑄖𑄧𑄣𑄬 𑄃𑄊𑄬𑅁",
    "𑄅𑄉𑄮 𑄟𑄚𑄪𑄌𑄴 𑄉𑄌𑄮𑄢𑄴 𑄖𑄧𑄣𑄬 𑄝𑄧𑄠𑄴𑅁",
    "𑄌𑄋𑄴𑄟 𑄥𑄋𑄴𑄇𑄳𑄢𑄨𑄖𑄨 𑄃𑄢𑄴 𑄞𑄌𑄴 𑄃𑄟𑄢𑄴 𑄉𑄧𑄢𑄧𑄛𑄴𑅂",
]


def test_layout_engine_initialization():
    engine = LayoutEngine(seed=42)
    assert engine.canvas_width == 1024
    assert engine.canvas_height == 1024
    assert engine.charset_engine.total_classes == 71


def test_page_layout_generation():
    engine = LayoutEngine(seed=42)
    layout = engine.generate_page_layout(SAMPLE_LINES, seed=42)

    assert isinstance(layout, PageLayout)
    assert layout.width == 1024
    assert layout.height == 1024
    assert layout.total_lines == len(SAMPLE_LINES)
    assert layout.total_characters > 0
    assert len(layout.lines) == len(SAMPLE_LINES)


def test_box_validity_and_dimensions():
    engine = LayoutEngine(seed=42)
    layout = engine.generate_page_layout(SAMPLE_LINES, seed=42)
    all_boxes = layout.get_all_character_boxes()

    for char_box in all_boxes:
        assert isinstance(char_box, CharacterLayout)
        assert char_box.width > 0.0, f"Width must be positive: {char_box}"
        assert char_box.height > 0.0, f"Height must be positive: {char_box}"
        assert char_box.class_id >= 0, f"Class ID must be valid: {char_box}"
        assert char_box.bbox.is_valid() is True


def test_page_boundary_inclusion():
    engine = LayoutEngine(seed=42)
    layout = engine.generate_page_layout(SAMPLE_LINES, seed=42)
    all_boxes = layout.get_all_character_boxes()

    for char_box in all_boxes:
        bbox = char_box.bbox
        assert bbox.x_min >= 0.0
        assert bbox.y_min >= 0.0
        assert bbox.x_max <= layout.width
        assert bbox.y_max <= layout.height


def test_monotonic_reading_order():
    engine = LayoutEngine(seed=42)
    layout = engine.generate_page_layout(SAMPLE_LINES, seed=42)
    all_boxes = layout.get_all_character_boxes()

    orders = [b.reading_order for b in all_boxes]
    assert orders == list(range(len(all_boxes))), "Reading order must be strictly contiguous from 0 to N-1."


def test_line_grouping_consistency():
    engine = LayoutEngine(seed=42)
    layout = engine.generate_page_layout(SAMPLE_LINES, seed=42)

    for line_idx, line in enumerate(layout.lines):
        assert line.line_id == line_idx
        for char_box in line.characters:
            assert char_box.line_id == line_idx


def test_deterministic_layout_reproducibility():
    engine1 = LayoutEngine(seed=12345)
    engine2 = LayoutEngine(seed=12345)

    layout1 = engine1.generate_page_layout(SAMPLE_LINES, seed=12345)
    layout2 = engine2.generate_page_layout(SAMPLE_LINES, seed=12345)

    assert layout1.margin_top == layout2.margin_top
    assert layout1.margin_left == layout2.margin_left
    assert layout1.total_characters == layout2.total_characters

    boxes1 = layout1.get_all_character_boxes()
    boxes2 = layout2.get_all_character_boxes()

    for b1, b2 in zip(boxes1, boxes2):
        assert b1.character == b2.character
        assert b1.class_id == b2.class_id
        assert b1.x == b2.x
        assert b1.y == b2.y
        assert b1.width == b2.width
        assert b1.height == b2.height
        assert b1.reading_order == b2.reading_order


def test_layout_validation_report():
    engine = LayoutEngine(seed=42)
    layout = engine.generate_page_layout(SAMPLE_LINES, seed=42)
    report = engine.validate_layout(layout)

    assert report["is_valid"] is True
    assert len(report["errors"]) == 0
    assert report["total_lines"] == len(SAMPLE_LINES)
    assert report["total_characters"] > 0
