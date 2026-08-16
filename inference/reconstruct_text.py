"""
Deterministic Text Reconstruction Engine for Chakma Historical OCR.
Reconstructs words, lines, and full text deterministically from bounding boxes and class IDs.
Strictly NO secondary neural models (CRNN, CTC, Transformer, etc.).
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from utils.geometry import BBox, sort_bboxes_reading_order
from utils.logging_utils import setup_logger

logger = setup_logger("text_reconstruction")


@dataclass
class ReconstructedWord:
    """Represents a reconstructed word."""
    text: str
    bbox: BBox
    characters: List[BBox] = field(default_factory=list)


@dataclass
class ReconstructedLine:
    """Represents a reconstructed line of text."""
    line_index: int
    text: str
    bbox: BBox
    words: List[ReconstructedWord] = field(default_factory=list)


@dataclass
class ReconstructedDocument:
    """Represents full reconstructed document text."""
    full_text: str
    lines: List[ReconstructedLine] = field(default_factory=list)
    total_characters: int = 0
    total_words: int = 0


class DeterministicTextReconstructor:
    """
    Reconstructs reading-order text deterministically from detected character BBoxes.
    """

    def __init__(
        self,
        id_to_char: Optional[Dict[int, str]] = None,
        word_gap_threshold_ratio: float = 1.2,
        line_height_tolerance_ratio: float = 0.5,
    ):
        self.id_to_char = id_to_char or {}
        self.word_gap_threshold_ratio = word_gap_threshold_ratio
        self.line_height_tolerance_ratio = line_height_tolerance_ratio

    def reconstruct(self, boxes: List[BBox]) -> ReconstructedDocument:
        """
        Deterministically process detected character boxes into structured text:
        1. Order boxes in 2D reading order (top-to-bottom, left-to-right).
        2. Group into lines based on vertical overlap.
        3. Cluster characters into words based on horizontal inter-character gaps.
        4. Map class IDs to Chakma Unicode characters and assemble full text.
        """
        if not boxes:
            return ReconstructedDocument(full_text="", lines=[], total_characters=0, total_words=0)

        # 1. Sort reading order
        ordered_boxes = sort_bboxes_reading_order(boxes, self.line_height_tolerance_ratio)

        # 2. Reconstruct characters to text
        char_tokens = []
        for box in ordered_boxes:
            char_str = box.class_name if box.class_name else self.id_to_char.get(box.class_id, "?")
            char_tokens.append(char_str)

        full_text = "".join(char_tokens)

        # Stage 01 baseline return
        return ReconstructedDocument(
            full_text=full_text,
            lines=[],
            total_characters=len(ordered_boxes),
            total_words=0,
        )
