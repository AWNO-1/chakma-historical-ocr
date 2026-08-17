"""
Comprehensive unit tests for Chakma Line Renderer.
"""

from pathlib import Path
import numpy as np
import pytest
from PIL import Image

from generator.charset_engine import CharsetEngine
from generator.font_engine import FontEngine
from generator.layout_engine import LayoutEngine
from generator.line_renderer import (
    LineRenderer,
    RenderedCharacter,
    RenderedLine,
    RenderedPageLines,
)

SAMPLE_TEXT = "𑄟𑄚𑄪𑄌𑄴 𑄃𑄟𑄢𑄴 𑄘𑄬𑄌𑄴"


def test_line_renderer_initialization():
    renderer = LineRenderer(seed=42)
    assert renderer.default_font_size == 32
    assert renderer.charset_engine.total_classes == 71


def test_glyph_rendering_and_ink():
    renderer = LineRenderer(seed=42)
    res = renderer.render_line(SAMPLE_TEXT, font_size=36)

    assert isinstance(res, RenderedLine)
    assert isinstance(res.image, Image.Image)
    assert res.width > 0
    assert res.height > 0
    assert len(res.characters) > 0

    # Verify that image is not completely blank/transparent
    arr = np.array(res.image)
    assert np.any(arr[:, :, 3] > 0), "Rendered line must contain visible alpha ink pixels."


def test_empty_text_handling():
    renderer = LineRenderer(seed=42)
    res = renderer.render_line("", font_size=32)

    assert isinstance(res, RenderedLine)
    assert res.text == ""
    assert len(res.characters) == 0
    assert res.width > 0
    assert res.height > 0

    res_whitespace = renderer.render_line("   ", font_size=32)
    assert len(res_whitespace.characters) == 0


def test_unsupported_glyph_handling():
    renderer = LineRenderer(seed=42)
    # Text with standard Chakma letters + foreign Latin character 'Z'
    text_with_unsupported = "𑄟𑄚𑄪𑄌𑄴 Z 𑄃𑄟𑄢𑄴"
    res = renderer.render_line(text_with_unsupported, font_size=32)

    assert isinstance(res, RenderedLine)
    # The valid Chakma characters should be recorded, foreign character should not crash
    assert len(res.characters) > 0
    char_symbols = [c.character for c in res.characters]
    assert "Z" not in char_symbols


def test_multiple_fonts_rendering():
    renderer = LineRenderer(seed=42)
    supported_fonts = renderer.font_engine.get_supported_fonts()

    assert len(supported_fonts) >= 2, "Expected at least 2 accepted Chakma fonts."

    for font_meta in supported_fonts:
        res = renderer.render_line(SAMPLE_TEXT, font_path=font_meta.path, font_size=32)
        assert isinstance(res, RenderedLine)
        assert res.font_path == font_meta.path
        assert len(res.characters) > 0
        arr = np.array(res.image)
        assert np.any(arr[:, :, 3] > 0), f"Font {font_meta.name} must render visible ink pixels."


def test_bounding_box_consistency():
    renderer = LineRenderer(seed=42)
    res = renderer.render_line(SAMPLE_TEXT, font_size=36, padding=20)
    arr = np.array(res.image)

    for char_meta in res.characters:
        bbox = char_meta.local_bbox
        assert bbox.is_valid()
        x1 = max(0, int(bbox.x_min))
        y1 = max(0, int(bbox.y_min))
        x2 = min(res.width, int(bbox.x_max))
        y2 = min(res.height, int(bbox.y_max))

        crop = arr[y1:y2, x1:x2]
        # Verify that ink pixels exist inside the character bbox
        assert np.any(crop[:, :, 3] > 0), f"Character '{char_meta.character}' bbox must enclose ink pixels."


def test_measure_character_and_text():
    renderer = LineRenderer(seed=42)
    pil_font = renderer.font_engine.get_font("fonts/NotoSansChakma-Regular.ttf", size=32)

    l, t, r, b = renderer.measure_character("𑄟", pil_font)
    assert r >= l
    assert b >= t

    w, h = renderer.measure_text(SAMPLE_TEXT, pil_font)
    assert w > 0.0
    assert h > 0.0


def test_render_page_lines():
    layout_engine = LayoutEngine(seed=42)
    renderer = LineRenderer(seed=42)

    lines = [
        "𑄟𑄚𑄪𑄌𑄴 𑄃𑄟𑄢𑄴 𑄘𑄬𑄌𑄴 𑄌𑄋𑄴𑄟 𑄞𑄌𑄴 𑄇𑄧𑄠𑄴𑅁",
        "𑄢𑄎 𑄘𑄬𑄌𑄮𑄖𑄴 𑄇𑄟𑄴 𑄉𑄧𑄢𑄬𑅁",
    ]
    page_layout = layout_engine.generate_page_layout(lines, seed=42)
    page_render = renderer.render_page_lines(page_layout)

    assert isinstance(page_render, RenderedPageLines)
    assert page_render.total_lines == 2
    assert page_render.total_characters > 0
    assert isinstance(page_render.image, Image.Image)
    assert page_render.image.size == (1024, 1024)

    arr = np.array(page_render.image)
    assert np.any(arr[:, :, 3] > 0), "Page canvas must contain rendered text lines."
