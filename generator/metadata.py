"""
Authoritative Metadata Schemas and Data Structures for Chakma Historical OCR.
Defines SyntheticSample, SampleCharacter, and SampleMetadata for the in-memory generation pipeline.
"""

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
from PIL import Image

from utils.geometry import BBox


@dataclass
class SampleCharacter:
    """
    Metadata and spatial annotation for an individual rendered character in a SyntheticSample.
    """
    id: int
    class_id: int
    text: str
    bbox: BBox
    line_id: int
    word_id: int
    reading_order: int

    @property
    def character(self) -> str:
        """Alias for text for backward compatibility."""
        return self.text

    def to_yolo(self, canvas_width: int, canvas_height: int) -> Tuple[int, float, float, float, float]:
        """Convert character bounding box to normalized YOLO format."""
        return self.bbox.to_yolo(canvas_width, canvas_height)

    def to_dict(self) -> Dict[str, Any]:
        """Convert character annotation to serializable dictionary."""
        return {
            "id": self.id,
            "class_id": self.class_id,
            "text": self.text,
            "bbox": self.bbox.to_dict(),
            "line_id": self.line_id,
            "word_id": self.word_id,
            "reading_order": self.reading_order,
        }


@dataclass
class SampleMetadata:
    """
    Contextual and typographic metadata for a generated synthetic sample.
    """
    sample_id: str
    seed: int
    width: int
    height: int
    font_name: str
    font_size: int
    total_lines: int
    total_characters: int
    text: str
    lines_text: List[str] = field(default_factory=list)
    extra: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert metadata to dictionary."""
        return {
            "sample_id": self.sample_id,
            "seed": self.seed,
            "width": self.width,
            "height": self.height,
            "font_name": self.font_name,
            "font_size": self.font_size,
            "total_lines": self.total_lines,
            "total_characters": self.total_characters,
            "text": self.text,
            "lines_text": self.lines_text,
            "extra": self.extra,
        }


@dataclass
class SyntheticSample:
    """
    Complete in-memory synthetic manuscript sample containing rendered PIL image,
    character annotations, metadata, and RNG seed.
    """
    image: Image.Image
    characters: List[SampleCharacter] = field(default_factory=list)
    metadata: Optional[SampleMetadata] = None
    seed: int = 42

    @property
    def width(self) -> int:
        return self.image.width if self.image else 1024

    @property
    def height(self) -> int:
        return self.image.height if self.image else 1024

    @property
    def total_characters(self) -> int:
        return len(self.characters)

    @property
    def total_lines(self) -> int:
        if self.metadata:
            return self.metadata.total_lines
        lines_set = {c.line_id for c in self.characters}
        return len(lines_set)

    @property
    def all_bboxes(self) -> List[BBox]:
        return [c.bbox for c in self.characters]

    def to_yolo_lines(self) -> List[str]:
        """Generate normalized YOLO format string lines for all characters."""
        w, h = self.width, self.height
        lines = []
        for char in self.characters:
            cid, cx, cy, bw, bh = char.to_yolo(w, h)
            lines.append(f"{cid} {cx:.6f} {cy:.6f} {bw:.6f} {bh:.6f}")
        return lines

    def to_dict(self) -> Dict[str, Any]:
        """Convert sample representation to dictionary (excluding raw PIL image)."""
        return {
            "seed": self.seed,
            "width": self.width,
            "height": self.height,
            "total_characters": self.total_characters,
            "total_lines": self.total_lines,
            "metadata": self.metadata.to_dict() if self.metadata else None,
            "characters": [c.to_dict() for c in self.characters],
        }


# =========================================================================
# Backward Compatibility Classes for Stage 01 / existing test suites
# =========================================================================

@dataclass
class CharacterAnnotation:
    """Legacy CharacterAnnotation dataclass."""
    char: str
    class_id: int
    bbox: BBox
    font_name: str
    font_size: int
    line_index: int
    char_index_in_line: int


@dataclass
class LineAnnotation:
    """Legacy LineAnnotation dataclass."""
    line_index: int
    text: str
    bbox: BBox
    characters: List[CharacterAnnotation] = field(default_factory=list)


@dataclass
class SyntheticSampleMetadata:
    """Legacy SyntheticSampleMetadata dataclass."""
    sample_id: str
    image_filename: str
    label_filename: str
    width: int
    height: int
    background_category: str
    background_source: str
    lines: List[LineAnnotation] = field(default_factory=list)
    total_characters: int = 0
    augmentations_applied: List[str] = field(default_factory=list)
    seed: Optional[int] = None
    extra: Dict[str, Any] = field(default_factory=dict)
