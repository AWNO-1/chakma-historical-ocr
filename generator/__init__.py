"""
Synthetic Data Generation Package for Chakma Historical OCR.
"""

from generator.metadata import (
    SampleCharacter,
    SampleMetadata,
    SyntheticSample,
    CharacterAnnotation,
    LineAnnotation,
    SyntheticSampleMetadata,
)
from generator.charset_engine import CharsetEngine, ChakmaClass
from generator.corpus_engine import CorpusEngine
from generator.font_engine import FontEngine, FontMetadata
from generator.layout_engine import LayoutEngine, LayoutConfig, PageLayout, LineLayout, CharacterLayout
from generator.line_renderer import LineRenderer, RenderedCharacter, RenderedLine, RenderedPageLines
from generator.background import BackgroundLibrary, BackgroundEngine, BackgroundMetadata, LoadedBackground
from generator.augmentations import AugmentationEngine
from generator.transform_engine import TransformEngine
from generator.annotation_engine import AnnotationEngine
from generator.api import SyntheticGenerator, SyntheticDataGenerator

__all__ = [
    "SampleCharacter",
    "SampleMetadata",
    "SyntheticSample",
    "CharacterAnnotation",
    "LineAnnotation",
    "SyntheticSampleMetadata",
    "CharsetEngine",
    "ChakmaClass",
    "CorpusEngine",
    "FontEngine",
    "FontMetadata",
    "LayoutEngine",
    "LayoutConfig",
    "PageLayout",
    "LineLayout",
    "CharacterLayout",
    "LineRenderer",
    "RenderedCharacter",
    "RenderedLine",
    "RenderedPageLines",
    "BackgroundLibrary",
    "BackgroundEngine",
    "BackgroundMetadata",
    "LoadedBackground",
    "AugmentationEngine",
    "TransformEngine",
    "AnnotationEngine",
    "SyntheticGenerator",
    "SyntheticDataGenerator",
]
