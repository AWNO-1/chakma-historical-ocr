"""
Synthetic Data Generation Package for Chakma Historical OCR.
"""

from generator.metadata import CharacterAnnotation, LineAnnotation, SyntheticSampleMetadata
from generator.charset_engine import CharsetEngine
from generator.corpus_engine import CorpusEngine
from generator.font_engine import FontEngine
from generator.layout_engine import LayoutEngine, LayoutConfig
from generator.line_renderer import LineRenderer
from generator.background import BackgroundEngine
from generator.augmentations import AugmentationEngine
from generator.transform_engine import TransformEngine
from generator.annotation_engine import AnnotationEngine
from generator.api import SyntheticDataGenerator

__all__ = [
    "CharacterAnnotation",
    "LineAnnotation",
    "SyntheticSampleMetadata",
    "CharsetEngine",
    "CorpusEngine",
    "FontEngine",
    "LayoutEngine",
    "LayoutConfig",
    "LineRenderer",
    "BackgroundEngine",
    "AugmentationEngine",
    "TransformEngine",
    "AnnotationEngine",
    "SyntheticDataGenerator",
]
