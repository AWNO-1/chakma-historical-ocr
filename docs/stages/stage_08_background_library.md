# Stage 08: Historical Background Library and Loader

## Overview
Stage 08 implements the `BackgroundLibrary` subsystem responsible for managing real historical manuscript backgrounds (paper, parchment, manuscript pages, bamboo, and miscellaneous textures) without relying on synthetic or ML-generated textures. It provides deterministic, in-memory sampling and aspect-ratio-preserving cropping for synthetic manuscript generation.

## Key Architecture & Features
1. **Asset Discovery and Validation**:
   - Scans `data/backgrounds/` and its subdirectories (`paper`, `parchment`, `manuscript`, `bamboo`, `miscellaneous`).
   - Validates every image file with PIL `verify()` and tests full RGB decoding.
   - Detects and quarantines empty (0 bytes) or corrupted files with explicit logging and invalid error reporting.
   - Supported extensions: `.png`, `.jpg`, `.jpeg`, `.webp` (case-insensitive).

2. **Categorization and Sampling**:
   - Groups images dynamically by subdirectory.
   - Supports optional category weighting (`category_weights`) for controlling dataset distribution.
   - Supports deterministic category and image selection via `seed`.

3. **In-Memory Aspect-Ratio Preserving Cropping**:
   - Preserves texture aspect ratio when fitting to arbitrary target dimensions (e.g. 1024x1024).
   - If image is larger than target: performs random spatial crop within image boundaries.
   - If image is smaller: scales up preserving aspect ratio and crops the covered region.
   - Strictly avoids distortion, stretching, and artificial repeating/tiling artifacts.

4. **Graceful Fallback**:
   - In the event of an empty folder or unreadable source, produces a clean solid antique paper canvas in-memory (`LoadedBackground.is_fallback=True`).

5. **Diagnostic Inspection Utility**:
   - `debug/backgrounds/inspect_backgrounds.py`: Scans asset counts, prints category distribution, checks for invalid files, and exports representative sample crops.

## Test Results
- **Unit Tests**: 6/6 tests passing in `tests/test_backgrounds.py` covering discovery, corrupt file isolation, dimension compatibility, seed reproducibility, weighted distribution, and empty directory fallback.
- **Repository Suite**: 68/68 tests passing across all stages.
