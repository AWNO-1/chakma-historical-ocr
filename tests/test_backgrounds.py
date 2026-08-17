"""
Unit and Integration Tests for Stage 08 — Historical Background Library and Loader.
Tests image discovery, validation, corrupt file rejection, seed reproducibility,
weighted category distribution, and aspect-ratio preserving dimension fitting.
"""

from pathlib import Path
import pytest
from PIL import Image

from generator.background import BackgroundLibrary, LoadedBackground, BackgroundMetadata


@pytest.fixture
def bg_lib() -> BackgroundLibrary:
    """Fixture providing initialized BackgroundLibrary on data/backgrounds."""
    return BackgroundLibrary(backgrounds_dir="data/backgrounds", seed=42)


def test_background_discovery_and_categorization(bg_lib: BackgroundLibrary):
    """Verify that background files are scanned and categorized accurately."""
    stats = bg_lib.get_stats()
    assert stats["total_images"] > 0
    assert len(stats["active_categories"]) >= 1
    assert "paper" in stats["active_categories"]

    for cat in stats["active_categories"]:
        assert len(bg_lib.categories[cat]) > 0


def test_corrupt_file_handling(tmp_path: Path):
    """Verify corrupt, empty, or non-image files are excluded and recorded in invalid list."""
    test_dir = tmp_path / "test_bgs"
    valid_cat = test_dir / "valid_cat"
    valid_cat.mkdir(parents=True, exist_ok=True)

    # 1. Create a valid image
    valid_img = Image.new("RGB", (200, 200), (220, 210, 190))
    valid_path = valid_cat / "valid_sample.jpg"
    valid_img.save(valid_path)

    # 2. Create an empty file (0 bytes)
    empty_path = valid_cat / "empty_corrupt.png"
    empty_path.touch()

    # 3. Create a garbage text file pretending to be jpg
    garbage_path = valid_cat / "garbage_fake.jpg"
    garbage_path.write_text("This is not an image content!", encoding="utf-8")

    lib = BackgroundLibrary(backgrounds_dir=test_dir, seed=42)
    stats = lib.get_stats()

    assert stats["total_images"] == 1
    assert len(lib.categories["valid_cat"]) == 1
    assert lib.categories["valid_cat"][0].name == "valid_sample.jpg"

    invalid_files = lib.get_invalid_files()
    assert len(invalid_files) == 2
    invalid_names = {f["path"].split("\\")[-1].split("/")[-1] for f in invalid_files}
    assert "empty_corrupt.png" in invalid_names
    assert "garbage_fake.jpg" in invalid_names


def test_dimension_compatibility(bg_lib: BackgroundLibrary):
    """Verify loaded backgrounds match the requested width and height exactly."""
    test_dimensions = [
        (1024, 1024),
        (800, 600),
        (1280, 720),
        (512, 512),
        (1600, 900),
    ]

    for w, h in test_dimensions:
        loaded = bg_lib.get_background(width=w, height=h, seed=123)
        assert isinstance(loaded, LoadedBackground)
        assert isinstance(loaded.image, Image.Image)
        assert loaded.image.mode == "RGB"
        assert loaded.image.size == (w, h)
        assert loaded.width == w
        assert loaded.height == h


def test_seed_reproducibility(bg_lib: BackgroundLibrary):
    """Verify that identical seeds produce byte-for-byte identical images and metadata."""
    bg1 = bg_lib.get_background(width=1024, height=1024, seed=999)
    bg2 = bg_lib.get_background(width=1024, height=1024, seed=999)

    assert bg1.category == bg2.category
    assert bg1.source_path == bg2.source_path
    assert bg1.crop_box == bg2.crop_box
    assert bg1.image.tobytes() == bg2.image.tobytes()


def test_category_selection_and_weights(tmp_path: Path):
    """Verify explicit category selection and weighted distribution."""
    test_dir = tmp_path / "weighted_bgs"
    for cat in ["paper", "parchment", "manuscript"]:
        d = test_dir / cat
        d.mkdir(parents=True, exist_ok=True)
        img = Image.new("RGB", (300, 300), (200, 200, 200))
        img.save(d / f"{cat}_sample.png")

    weights = {"paper": 1.0, "parchment": 0.0, "manuscript": 0.0}
    lib = BackgroundLibrary(
        backgrounds_dir=test_dir, category_weights=weights, seed=42
    )

    # 1. Test explicit category override
    bg_parchment = lib.get_background(category="parchment", seed=10)
    assert bg_parchment.category == "parchment"

    # 2. Test weighted sampling (100% paper)
    for s in range(10):
        bg = lib.get_background(seed=s)
        assert bg.category == "paper"


def test_graceful_empty_directory_fallback(tmp_path: Path):
    """Verify fallback solid canvas is produced gracefully when no images are found."""
    empty_dir = tmp_path / "empty_backgrounds"
    empty_dir.mkdir(parents=True, exist_ok=True)

    lib = BackgroundLibrary(backgrounds_dir=empty_dir, seed=42)
    bg = lib.get_background(width=800, height=600)

    assert bg.is_fallback is True
    assert bg.category == "procedural_fallback"
    assert bg.image.size == (800, 600)
    assert bg.image.mode == "RGB"
