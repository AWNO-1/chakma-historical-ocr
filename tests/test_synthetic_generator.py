"""
Unit and Integration Tests for Stage 07 — Synthetic Sample Generator Core.
Verifies pipeline flow, in-memory operations, deterministic reproducibility,
character metadata integrity, and YOLO format export.
"""

import pytest
from pathlib import Path
from PIL import Image

from generator.api import SyntheticGenerator, SyntheticDataGenerator
from generator.metadata import SampleCharacter, SampleMetadata, SyntheticSample
from utils.geometry import BBox


@pytest.fixture
def generator() -> SyntheticGenerator:
    """Fixture providing initialized SyntheticGenerator."""
    return SyntheticGenerator(seed=42)


def test_generator_initialization(generator: SyntheticGenerator):
    """Verify all sub-engines are connected and initialized."""
    assert generator.charset_engine is not None
    assert generator.corpus_engine is not None
    assert generator.font_engine is not None
    assert generator.layout_engine is not None
    assert generator.line_renderer is not None
    assert generator.seed == 42


def test_generate_single_sample(generator: SyntheticGenerator):
    """Verify single sample generation produces a valid SyntheticSample object."""
    sample = generator.generate(seed=100)
    assert isinstance(sample, SyntheticSample)
    assert isinstance(sample.image, Image.Image)
    assert sample.width == 1024
    assert sample.height == 1024
    assert sample.seed == 100
    assert sample.total_characters > 0
    assert sample.total_lines > 0
    assert sample.metadata is not None
    assert sample.metadata.sample_id == "sample_000100"
    assert len(sample.characters) == sample.total_characters


def test_character_metadata_integrity(generator: SyntheticGenerator):
    """Verify individual character annotations have complete, valid spatial and class metadata."""
    sample = generator.generate(seed=200, num_lines=3)
    assert len(sample.characters) > 0

    for idx, char in enumerate(sample.characters):
        assert isinstance(char, SampleCharacter)
        assert char.id == idx
        assert isinstance(char.class_id, int)
        assert 0 <= char.class_id < 71
        assert len(char.text) > 0
        assert isinstance(char.bbox, BBox)
        assert char.bbox.width >= 1.0
        assert char.bbox.height >= 1.0
        assert char.bbox.is_within_bounds(sample.width, sample.height)
        assert char.reading_order >= 0
        assert char.line_id >= 0
        assert char.word_id >= 0


def test_deterministic_reproducibility(generator: SyntheticGenerator):
    """Verify identical seeds produce identical images, characters, and metadata."""
    sample1 = generator.generate(seed=555)
    sample2 = generator.generate(seed=555)

    assert sample1.image.tobytes() == sample2.image.tobytes()
    assert sample1.total_characters == sample2.total_characters
    assert sample1.total_lines == sample2.total_lines
    assert sample1.metadata.text == sample2.metadata.text

    for c1, c2 in zip(sample1.characters, sample2.characters):
        assert c1.class_id == c2.class_id
        assert c1.text == c2.text
        assert c1.bbox.x_min == c2.bbox.x_min
        assert c1.bbox.y_min == c2.bbox.y_min
        assert c1.bbox.x_max == c2.bbox.x_max
        assert c1.bbox.y_max == c2.bbox.y_max


def test_custom_text_and_typography(generator: SyntheticGenerator):
    """Verify generator respects explicit user-provided text lines and font settings."""
    custom_lines = [
        "𑄟𑄚𑄪𑄌𑄴 𑄃𑄟𑄢𑄴 𑄘𑄬𑄌𑄴",
        "𑄢𑄎 𑄘𑄬𑄌𑄮𑄖𑄴 𑄇𑄟𑄴 𑄉𑄧𑄢𑄬𑅁",
    ]
    sample = generator.generate(
        seed=333,
        text_lines=custom_lines,
        font_size=36,
    )
    assert sample.metadata.total_lines == 2
    assert sample.metadata.font_size == 36
    assert sample.metadata.lines_text == custom_lines
    assert sample.total_characters > 0


def test_batch_generation(generator: SyntheticGenerator):
    """Verify batch generation produces multiple distinct samples in-memory."""
    batch = generator.generate_batch(count=5, start_seed=1000)
    assert len(batch) == 5
    seeds = [s.seed for s in batch]
    assert seeds == [1000, 1001, 1002, 1003, 1004]

    # Ensure samples are distinct
    assert batch[0].image.tobytes() != batch[1].image.tobytes()


def test_yolo_export_format(generator: SyntheticGenerator):
    """Verify character bounding boxes export to valid normalized YOLO lines."""
    sample = generator.generate(seed=777)
    yolo_lines = sample.to_yolo_lines()
    assert len(yolo_lines) == sample.total_characters

    for line in yolo_lines:
        parts = line.split()
        assert len(parts) == 5
        cid = int(parts[0])
        cx, cy, w, h = map(float, parts[1:])
        assert 0 <= cid < 71
        assert 0.0 <= cx <= 1.0
        assert 0.0 <= cy <= 1.0
        assert 0.0 < w <= 1.0
        assert 0.0 < h <= 1.0


def test_backward_compatibility_alias():
    """Verify SyntheticDataGenerator alias and generate_sample method work as expected."""
    legacy_gen = SyntheticDataGenerator(seed=888)
    meta = legacy_gen.generate_sample("sample_legacy_01", seed=888)
    assert meta is not None
    assert meta.sample_id == "sample_legacy_01"
    assert meta.width == 1024
    assert meta.height == 1024
