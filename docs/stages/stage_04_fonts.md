# Stage 04: Chakma Font Engine and Glyph Coverage Verification

## Stage Information
- **Title:** Chakma Font Engine
- **Stage Number:** 04
- **Date:** 2026-08-17
- **Status:** WAITING FOR APPROVAL

## Objective
Implement an authoritative typography engine (`generator/font_engine.py`) capable of discovering `.ttf` and `.otf` fonts in `fonts/`, parsing binary cmap glyph tables via `fontTools`, validating coverage against the 71 canonical Chakma classes, recording font metadata, isolating accepted vs rejected fonts with reasons, and providing deterministic font retrieval.

## Implementation Details
1. **Configuration (`config/synthetic.yaml`):**
   - `font_dir`: `"fonts"`
   - `supported_extensions`: `[".ttf", ".otf"]`
   - `font_size_min`: 24
   - `font_size_max`: 72
   - `default_font_size`: 32
   - `min_coverage_threshold`: 0.70 (70.0%)

2. **Font Discovery and Parsing (`generator/font_engine.py`):**
   - `discover_fonts()`: Scans `fonts/` for all `.ttf` and `.otf` files.
   - `validate_font(path)`: Binary inspection of font cmap tables, character matching against 71 canonical Chakma classes, and Pillow FreeType load verification.
   - `get_supported_fonts()`: Returns list of accepted fonts exceeding coverage threshold.
   - `get_rejected_fonts()`: Returns list of rejected fonts with explicit rejection reasons.
   - `get_random_font(seed=None)`: Deterministic font sampling.
   - `supports_character(font, char_or_unicode)`: Granular character-level support queries.
   - `get_font(font, size)`: Cached PIL `FreeTypeFont` loader with size clamping.

3. **Font Assets in `fonts/`:**
   - `NotoSansChakma-Regular.ttf`: Official Google open-source Chakma font (100% coverage).
   - `Nirmala.ttf`: Authentic Windows Chakma Regular font (100% coverage).
   - `NirmalaB.ttf`: Authentic Windows Chakma Bold font (100% coverage).
   - `NirmalaS.ttf`: Authentic Windows Chakma Semilight font (100% coverage).
   - `arial.ttf`: Control test font (0.0% Chakma coverage, rejected).

4. **Unit Tests (`tests/test_fonts.py`):**
   - 8 comprehensive unit tests covering discovery, acceptance, rejection of non-supporting fonts, character support querying, deterministic random selection, caching, size bounds, and corrupted/non-existent file handling (36/36 tests passed in project suite).

## Font Discovery & Validation Results

| # | Font Name | Format | File Size | Glyphs | Chakma Coverage | Status | Rejection Reason |
|:---|:---|:---:|:---:|:---:|:---:|:---:|:---|
| 1 | `NotoSansChakma-Regular` | `.ttf` | 79.8 KB | 103 | **100.00% (71/71)** | **ACCEPTED** | None (Full Coverage) |
| 2 | `Nirmala` | `.ttf` | 1499.7 KB | 1516 | **100.00% (71/71)** | **ACCEPTED** | None (Full Coverage) |
| 3 | `NirmalaB` | `.ttf` | 1455.3 KB | 1516 | **100.00% (71/71)** | **ACCEPTED** | None (Full Coverage) |
| 4 | `NirmalaS` | `.ttf` | 1531.3 KB | 1516 | **100.00% (71/71)** | **ACCEPTED** | None (Full Coverage) |
| 5 | `arial` | `.ttf` | 1035.7 KB | 3381 | **0.00% (0/71)** | **REJECTED** | Glyph coverage (0.0%) is below minimum threshold (70.0%). Supported: 0/71 |

## Verification Results
- **Pass Rate:** 100% (36/36 unit tests passed in 6.99s).
- **Accepted Fonts Count:** 4 authentic Chakma typography styles.
- **Rejected Fonts Count:** 1 (correctly identified and isolated).
- **Canvas Rendering:** Decoupled and strictly deferred to Stage 05.
