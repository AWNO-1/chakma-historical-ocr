# Stage 07: Synthetic Sample Generator Core

## Overview
Stage 07 orchestrates and unifies all core generation subsystems (`CorpusEngine`, `CharsetEngine`, `FontEngine`, `LayoutEngine`, and `LineRenderer`) into the central `SyntheticGenerator` class. It executes an end-to-end, in-memory synthetic generation pipeline producing fully annotated `SyntheticSample` objects.

## Key Capabilities & Design
1. **Unified Orchestration Pipeline**:
   - **Text Generation**: Random sampling from sentences or vocabulary pools via `CorpusEngine`.
   - **Charset Validation**: Normalization (NFC) and verification against canonical `CharsetEngine` (71 classes).
   - **Font Selection**: Deterministic typography selection across validated fonts and size intervals.
   - **Layout Geometry**: Calculation of margins, line coordinates, and word spacing via `LayoutEngine`.
   - **Line Rendering**: Continuous text rendering and pixel-accurate grapheme cluster bounding box extraction via `LineRenderer`.
   - **Ground-Truth Extraction**: Construction of `SampleCharacter` instances containing class ID, text, spatial bounding box, line index, word index, and reading order.
   - **Sample Packaging**: Encapsulation into `SyntheticSample` in-memory object.

2. **In-Memory Operation**:
   - Operates purely in RAM without requiring disk I/O.
   - Decoupled from background synthesis (Stage 08) and geometric augmentations (Stage 09).

3. **Data Structures**:
   - `SampleCharacter`: Represents ground-truth character/cluster annotation.
   - `SampleMetadata`: Encapsulates typography, seed, dimensions, text lines, and line counts.
   - `SyntheticSample`: Holds the rendered PIL Image, character list, metadata, and YOLO export utilities (`to_yolo_lines()`).

4. **Deterministic Reproducibility**:
   - All random decisions (text choice, font choice, font size, margins, jitter) are strictly controlled by `seed`.

## Verification & Test Results
- **Unit Tests**: 8/8 tests passed in `tests/test_synthetic_generator.py` covering single sample creation, metadata integrity, seed reproducibility, custom text handling, batch generation, and YOLO formatting.
- **Whole Suite**: 62/62 tests passing across the entire repository.
- **Visual Samples**: 10 full manuscript samples generated and exported to artifact directory with both clean and annotated bounding box visualizations.
