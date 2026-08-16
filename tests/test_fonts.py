"""
Tests for Font Engine.
"""

import pytest
from generator.font_engine import FontEngine


def test_font_engine_init():
    engine = FontEngine()
    assert engine.fonts_dir.exists()
    assert isinstance(engine.available_fonts, list)


def test_font_engine_get_font():
    engine = FontEngine()
    font = engine.get_font()
    assert font is None or hasattr(font, "getbbox")
