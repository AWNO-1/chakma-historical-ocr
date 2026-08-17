"""
Comprehensive unit tests for Chakma Font Engine.
"""

from pathlib import Path
import pytest
from PIL import ImageFont

from generator.font_engine import FontEngine, FontMetadata
from generator.charset_engine import CharsetEngine


def test_font_engine_initialization_and_discovery():
    engine = FontEngine(font_dir="fonts")
    discovered = engine.discover_fonts()
    assert len(discovered) > 0
    assert any(f.suffix.lower() in [".ttf", ".otf"] for f in discovered)


def test_supported_fonts_acceptance():
    engine = FontEngine(font_dir="fonts")
    supported = engine.get_supported_fonts()

    assert len(supported) > 0, "Should find at least one supported Chakma font in fonts/"
    noto_or_nirmala = [f for f in supported if "noto" in f.name.lower() or "nirmala" in f.name.lower()]
    assert len(noto_or_nirmala) > 0

    first_supported = noto_or_nirmala[0]
    assert first_supported.is_valid is True
    assert first_supported.coverage_percentage >= 70.0
    assert first_supported.supported_classes_count >= 50
    assert first_supported.rejection_reason is None


def test_rejected_non_chakma_font():
    engine = FontEngine(font_dir="fonts")
    rejected = engine.get_rejected_fonts()

    # If arial.ttf exists in fonts/, it must be rejected
    arial_meta = [f for f in rejected if "arial" in f.name.lower()]
    if arial_meta:
        m = arial_meta[0]
        assert m.is_valid is False
        assert m.coverage_percentage < 10.0
        assert m.rejection_reason is not None
        assert "below minimum threshold" in m.rejection_reason


def test_supports_character_method():
    engine = FontEngine(font_dir="fonts")
    supported = engine.get_supported_fonts()
    assert len(supported) > 0
    font_meta = supported[0]

    # Consonant KAA (U+11107) -> should be supported
    assert engine.supports_character(font_meta, "𑄇") is True
    assert engine.supports_character(font_meta, "U+11107") is True

    # Non-Chakma character -> False
    assert engine.supports_character(font_meta, "A") is False
    assert engine.supports_character(font_meta, "U+0041") is False


def test_deterministic_random_font_selection():
    engine1 = FontEngine(seed=42)
    engine2 = FontEngine(seed=42)

    font1 = engine1.get_random_font()
    font2 = engine2.get_random_font()
    assert font1.name == font2.name
    assert font1.path == font2.path

    # Overridden seed
    f_seed1 = engine1.get_random_font(seed=999)
    f_seed2 = engine2.get_random_font(seed=999)
    assert f_seed1.name == f_seed2.name


def test_get_font_caching_and_size_bounds():
    engine = FontEngine(font_dir="fonts")
    supported = engine.get_supported_fonts()
    assert len(supported) > 0
    target_font = supported[0]

    # Test retrieval
    pil_font = engine.get_font(target_font.path, size=32)
    assert isinstance(pil_font, ImageFont.FreeTypeFont)
    assert pil_font.size == 32

    # Test size clamping (min 24, max 72)
    clamped_small = engine.get_font(target_font.path, size=10)
    assert clamped_small.size == engine.font_size_min

    clamped_large = engine.get_font(target_font.path, size=150)
    assert clamped_large.size == engine.font_size_max

    # Test caching (same instance returned)
    cached_font = engine.get_font(target_font.path, size=32)
    assert cached_font is pil_font


def test_corrupted_font_handling(tmp_path: Path):
    corrupt_file = tmp_path / "corrupt_font.ttf"
    corrupt_file.write_bytes(b"NOT_A_VALID_TTF_FONT_HEADER_OR_BINARY")

    engine = FontEngine(font_dir=tmp_path)
    meta = engine.validate_font(corrupt_file)

    assert meta.is_valid is False
    assert meta.coverage_percentage == 0.0
    assert meta.rejection_reason is not None


def test_nonexistent_font_handling(tmp_path: Path):
    nonexistent = tmp_path / "ghost_font.otf"
    engine = FontEngine(font_dir=tmp_path)
    meta = engine.validate_font(nonexistent)

    assert meta.is_valid is False
    assert "does not exist" in str(meta.rejection_reason)
