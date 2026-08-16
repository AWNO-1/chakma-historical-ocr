"""
Metadata schemas and dataclasses for generated synthetic manuscripts.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from utils.geometry import BBox


@dataclass
class CharacterAnnotation:
    """Represents a single rendered character annotation."""
    char: str
    class_id: int
    bbox: BBox
    font_name: str
    font_size: int
    line_index: int
    char_index_in_line: int


@dataclass
class LineAnnotation:
    """Represents a single rendered line containing multiple characters."""
    line_index: int
    text: str
    bbox: BBox
    characters: List[CharacterAnnotation] = field(default_factory=list)


@dataclass
class SyntheticSampleMetadata:
    """Complete metadata for a single synthetic generated manuscript image."""
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
