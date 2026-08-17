"""
Authoritative Unit and Integration Tests for Stage 04: Font Discovery, Verification, and Registration.
"""

from pathlib import Path
import tempfile
import pytest
from PIL import ImageFont

from generator.charset_engine import CharsetEngine
from generator.font_engine import FontEngine, FontMetadata
from utils.font_utils import (
    CHAKMA_UNICODE_RANGE,
    compute_file_sha256,
    inspect_font_tables,
    scan_and_discover_fonts,
    verify_glyph_rendering,
)


@pytest.fixture(scope="module")
def charset_engine():
    return CharsetEngine()


@pytest.fixture(scope="module")
def font_engine(charset_engine):
    return FontEngine(base_dir="fonts", charset_engine=charset_engine, auto_discover=True)


# 1. Discovery Test
def test_font_discovery(font_engine):
    discovered = font_engine.get_all_discovered_fonts()
    assert len(discovered) >= 10
    file_names = [f.file_name for f in discovered]
    assert any("NotoSansChakma" in fn for fn in file_names)
    assert any("Chakma" in fn for fn in file_names)


# 2. Loading Test
def test_font_loading(font_engine):
    valid_fonts = font_engine.get_supported_fonts()
    assert len(valid_fonts) > 0
    for meta in valid_fonts:
        pil_font = font_engine.get_font(meta.id, size=32)
        assert isinstance(pil_font, ImageFont.FreeTypeFont)


# 3. Unicode Coverage Inspection
def test_unicode_coverage(font_engine):
    all_fonts = font_engine.get_all_discovered_fonts()
    for meta in all_fonts:
        assert meta.total_glyphs > 0
        assert meta.coverage_percent >= 0.0
        assert meta.coverage_status in ["FULL_SUPPORT", "PARTIAL_SUPPORT", "NO_CHAKMA_SUPPORT"]


# 4. Chakma Coverage Percentages
def test_chakma_coverage_thresholds(font_engine):
    valid_fonts = font_engine.get_supported_fonts()
    for meta in valid_fonts:
        assert meta.coverage_percent >= font_engine.min_coverage_threshold
        assert meta.chakma_supported > 0


# 5. Rendering Test
def test_font_rendering(font_engine, charset_engine):
    valid_fonts = font_engine.get_supported_fonts()
    first_font = valid_fonts[0]
    sample_classes = charset_engine.get_all_classes()[:5]

    for c in sample_classes:
        if c.character:
            res = verify_glyph_rendering(first_font.path, c.character, font_size=32)
            assert res["rendered"] is True
            assert res["is_blank"] is False
            assert res["pixel_count"] > 0
            assert res["width"] > 0
            assert res["height"] > 0


# 6. Missing Glyph & Rejection Test
def test_missing_glyph_detection(font_engine):
    rejected_meta = [f for f in font_engine.get_all_discovered_fonts() if not f.enabled_for_synthetic and not f.is_duplicate]
    # Arial should be detected and rejected for 0% Chakma coverage
    arial_matches = [f for f in font_engine.get_all_discovered_fonts() if "arial" in f.file_name.lower()]
    if arial_matches:
        arial_meta = arial_matches[0]
        assert arial_meta.enabled_for_synthetic is False
        assert arial_meta.coverage_status == "NO_CHAKMA_SUPPORT"
        assert arial_meta.coverage_percent == 0.0


# 7. Metadata JSON Generation
def test_metadata_generation(font_engine):
    meta_dir = Path("fonts/metadata")
    assert meta_dir.exists()
    all_fonts = font_engine.get_all_discovered_fonts()
    for meta in all_fonts:
        json_file = meta_dir / f"{meta.id}.json"
        assert json_file.exists()
        assert json_file.stat().st_size > 0


# 8. Reproducibility & Deterministic Selection Test
def test_font_reproducibility(font_engine):
    font_a1 = font_engine.get_random_font(seed=12345)
    font_a2 = font_engine.get_random_font(seed=12345)
    font_b = font_engine.get_random_font(seed=99999)

    assert font_a1.id == font_a2.id
    assert font_a1.name == font_a2.name


# 9. Duplicate Detection Test
def test_duplicate_detection(font_engine):
    all_fonts = font_engine.get_all_discovered_fonts()
    duplicate_fonts = [f for f in all_fonts if f.is_duplicate]
    for dup in duplicate_fonts:
        assert dup.duplicate_of is not None
        assert dup.enabled_for_synthetic is False


# 10. YAML Config Generation Test
def test_config_generation(font_engine):
    yaml_path = Path("config/fonts.yaml")
    assert yaml_path.exists()
    import yaml
    with open(yaml_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    assert "fonts" in data
    assert len(data["fonts"]) == len(font_engine.get_supported_fonts())
    for f_entry in data["fonts"]:
        assert "id" in f_entry
        assert "path" in f_entry
        assert "coverage" in f_entry
        assert f_entry["enabled_for_synthetic"] is True
