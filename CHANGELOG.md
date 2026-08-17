# Changelog

All notable changes to the Chakma Historical OCR project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [0.9.0] - 2026-08-17 - Stage 09: Historical Document Transformation Engine

### Added
- Authoritative `TransformPipeline` and `TransformEngine` in `generator/transform_engine.py` orchestrating geometric transformations with synchronous bounding box coordinate mapping.
- Geometric transform functions: `apply_rotation()`, `apply_translation()`, `apply_perspective()`, `apply_elastic()`, and `apply_curvature()`.
- Synchronous 4-corner bounding box polygon projection with exact axis-aligned bounding box (AABB) calculation, non-degeneracy validation, and canvas boundary clipping.
- Comprehensive `AugmentationEngine` in `generator/augmentations.py` simulating realistic photometric and optical degradations:
  - Multi-type blur (Gaussian defocus, directional motion blur, box filter).
  - Additive Gaussian, speckle, and salt-and-pepper aging dust noise.
  - Authentic non-black historical ink tone shifts (iron-gall brown/sepia, charcoal, walnut), ink fading, and intra-stroke density jitter.
  - Non-uniform lighting gradients, corner shadow vignetting, and spotlights.
  - Backside ink bleed-through / ghosting simulation from reverse paper page.
  - JPEG discrete cosine transform (DCT) compression artifacts.
- Dedicated unit test suite `tests/test_transform_engine.py` with 8 tests covering rotation, translation, perspective, elastic, curvature, photometric augmentations, end-to-end pipeline determinism, and invalid box quarantine (76 tests total in project suite).
- Visualization diagnostic utility `debug/transformations/demo_transforms.py` generating before/after comparison images with bounding-box overlays and transformation matrix logging.
- Documentation report `docs/stages/stage_09_historical_transforms.md` and Architecture Decision Record `ADR-009-historical-transformation-engine.md`.

## [0.8.0] - 2026-08-17 - Stage 08: Historical Background Library and Loader

### Added
- Authoritative `BackgroundLibrary` in `generator/background.py` managing authentic digitized historical manuscript surfaces across categories (`paper`, `parchment`, `manuscript`, `bamboo`, `miscellaneous`).
- Structured dataclasses `BackgroundMetadata` and `LoadedBackground` tracking ground-truth image source, format, crop bounds, and fallback status.
- In-memory aspect-ratio-preserving cropping and scaling preventing distortion, shearing, and repetitive tiling artifacts.
- Deterministic seed reproducibility and weighted category sampling (`category_weights`).
- Corrupt and invalid file detection, logging, and isolation.
- Dedicated unit test suite `tests/test_backgrounds.py` with 6 tests covering discovery, corrupt file handling, dimension compatibility, seed reproducibility, weighted distribution, and empty directory fallback (68 tests total in project suite).
- Inspection and diagnostic script `debug/backgrounds/inspect_backgrounds.py` reporting category distribution, image metrics, and exporting representative sample crops.
- Documentation report `docs/stages/stage_08_background_library.md` and Architecture Decision Record `ADR-008-historical-background-library.md`.

## [0.7.0] - 2026-08-17 - Stage 07: Synthetic Sample Generator Core

### Added
- Authoritative `SyntheticGenerator` in `generator/api.py` seamlessly connecting `CorpusEngine`, `CharsetEngine`, `FontEngine`, `LayoutEngine`, and `LineRenderer` into an in-memory synthetic manuscript generation pipeline.
- Structured dataclasses `SyntheticSample`, `SampleCharacter`, and `SampleMetadata` in `generator/metadata.py` encapsulating raw PIL canvas, character-level ground truth annotations, typography attributes, reading order, and RNG seed.
- Pipeline flow: Text sampling -> Charset validation & normalization -> Font & size selection -> Page layout geometry -> Continuous line rendering -> Ground-truth character metadata extraction -> SyntheticSample packaging.
- Deterministic batch generation via `generate_batch()` and normalized YOLO format export via `SyntheticSample.to_yolo_lines()`.
- Dedicated test suite `tests/test_synthetic_generator.py` with 8 comprehensive unit and integration tests (62 tests passing across whole project).
- Visual verification script `utils/generate_stage07_samples.py` generating 10 multi-line synthetic samples with clean renders and character bounding-box overlays.
- Documentation report `docs/stages/stage_07_synthetic_generator.md` and Architecture Decision Record `ADR-007-synthetic-generator-core.md`.

## [0.6.0] - 2026-08-17 - Stage 06: Chakma Line Renderer

### Added
- Authoritative `LineRenderer` in `generator/line_renderer.py` rendering full continuous text lines using Pillow while tracking character-level bounding boxes and class IDs.
- Structured dataclasses `RenderedCharacter`, `RenderedLine`, and `RenderedPageLines` encapsulating RGBA image canvases and ground-truth metadata.
- Accurate measurement and bounding box computation for Brahmic combining marks / matras (vowel signs, virama/maaw) relative to base consonant anchors with zero-width advances.
- Multi-font and multi-size text line and page-level canvas rendering.
- Dedicated unit test suite `tests/test_line_renderer.py` with 8 tests covering visible ink rendering, empty text handling, unsupported glyph resilience, multi-font support, bounding box ink containment, character/text measurement, and page canvas generation (54 tests total in project suite).
- Demonstration utility `utils/demo_renderer.py` exporting verified sample line PNGs and page canvases in `debug/rendered_samples/`.
- Architectural Decision Record `ADR-006-line-renderer.md`.
- Documentation report `docs/stages/stage_06_line_renderer.md`.

## [0.5.0] - 2026-08-17 - Stage 05: Layout and Character Geometry Engine

### Added
- Authoritative `LayoutEngine` in `generator/layout_engine.py` responsible for computing page geometry, margins, line bounding boxes, and individual character bounding boxes.
- CharacterLayout, LineLayout, and PageLayout dataclasses with bounding box coordinates, reading order indexing, and YOLO export capability.
- Multi-line page layout calculation with random font size, margin constraints, and character spacing.
- Robust geometry validation suite testing non-zero box dimensions, page containment, and monotonic reading order.
- Unit and integration tests in `tests/test_layout.py` and `tests/test_geometry.py`.
- Architectural Decision Record `ADR-005-layout-and-geometry-engine.md`.
- Documentation report `docs/stages/stage_05_layout_engine.md`.

## [0.4.0] - 2026-08-17 - Stage 04: Font Engine

### Added
- Comprehensive `FontEngine` in `generator/font_engine.py` discovering, validating, and managing Chakma OpenType/TrueType fonts.
- Dynamic font discovery with automatic glyph coverage verification against the 71-class canonical Chakma charset.
- Font caching mechanism for Pillow ImageFont instances with arbitrary point sizes.
- Parametric font metadata extraction (coverage, family name, license).
- Comprehensive test suite `tests/test_fonts.py` with 8 unit tests.
- Architectural Decision Record `ADR-004-font-engine.md`.
- Documentation report `docs/stages/stage_04_font_engine.md`.

## [0.3.0] - 2026-08-16 - Stage 03: Corpus Engine

### Added
- Complete text extraction and sampling engine (`generator/corpus_engine.py`).
- Deterministic text sampling (words, phrases, sentences, line counts).
- Automatic text normalization with CharsetEngine integration.
- N-gram analysis, vocabulary frequency analysis, and OOV rate calculations.
- Comprehensive test suite in `tests/test_corpus.py` (8 tests).
- Architectural Decision Record `ADR-003-corpus-engine.md`.
- Documentation report `docs/stages/stage_03_corpus_engine.md`.

## [0.2.0] - 2026-08-16 - Stage 02: Charset Validation & Normalization Engine

### Added
- Canonical 71-class Chakma Unicode specification in `corpus/charset.json`.
- Complete Charset Engine in `generator/charset_engine.py`.
- Unicode NFC normalization, character validation, and class ID mapping.
- 9 unit tests in `tests/test_charset.py`.
- Architectural Decision Record `ADR-002-canonical-charset.md`.
- Documentation report `docs/stages/stage_02_charset_engine.md`.

## [0.1.0] - 2026-08-16 - Stage 01: Project Setup & Environment Baseline

### Added
- Complete project directory structure and configuration files.
- Python environment verification scripts and basic smoke tests.
- GitHub repository baseline and Notion project tracking setup.
- Initial architecture documentation.
