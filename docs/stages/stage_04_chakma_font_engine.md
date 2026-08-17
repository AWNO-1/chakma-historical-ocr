# Stage 04 — Chakma Font Discovery, Verification, and Registration

## 1. Overview & Architectural Goals
Stage 04 implements a font discovery, OpenType table inspection, Unicode coverage verification, and registration pipeline for the Chakma script (`generator/font_engine.py` and `utils/font_utils.py`). It ensures that only font files with verified Chakma Unicode glyph coverage (`U+11100..U+1114F`) and non-degenerate rendering are registered for synthetic OCR training.

## 2. Directory Structure
```
fonts/
├── raw/            # Discovered candidate font files
├── validated/      # Accepted fonts meeting >=70% Chakma coverage
├── rejected/       # Rejected fonts (e.g. 0% coverage like Arial)
├── metadata/       # Machine-readable JSON metadata (<font_id>.json)
└── collections/    # ZIP/KMP packages
```

## 3. Font Discovery & Verification Summary
- **Total Fonts Discovered**: 13
- **Accepted / Validated Fonts**: 12
- **Rejected Fonts**: 1 (`arial.ttf` - 0.0% Chakma glyph coverage)

### Accepted Font Registry
1. `chakma_unicode`: **Chakma Unicode** (100.0% coverage, Style: `PRINT`)
2. `chakmaunicode_bold`: **Chakma Unicode Bold** (100.0% coverage, Style: `PRINT`)
3. `chakmaunicode_bolditalic`: **Chakma Unicode Bold Italic** (100.0% coverage, Style: `CALLIGRAPHIC`)
4. `chakmaunicode_italic`: **Chakma Unicode Italic** (100.0% coverage, Style: `CALLIGRAPHIC`)
5. `chakmaunicode_regular`: **Chakma Unicode Regular** (100.0% coverage, Style: `PRINT`)
6. `notosanschakma_regular`: **Noto Sans Chakma Regular** (100.0% coverage, Style: `PRINT`)
7. `notosanschakma_regular2`: **Noto Sans Chakma Regular v2** (100.0% coverage, Style: `PRINT`)
8. `notosanschakma_google`: **Noto Sans Chakma Google Fonts** (100.0% coverage, Style: `PRINT`)
9. `ribenguni_regular`: **RibengUni Regular** (98.6% coverage, Style: `PRINT`)
10. `nirmala`: **Nirmala UI** (100.0% coverage, Style: `PRINT`)
11. `nirmalab`: **Nirmala UI Bold** (100.0% coverage, Style: `PRINT`)
12. `nirmalas`: **Nirmala UI Semilight** (100.0% coverage, Style: `PRINT`)

## 4. Key Verification Features
- **TrueType / OpenType Parsing**: Inspects `cmap`, `GSUB`, `GPOS`, `name`, `OS/2` tables.
- **Visual Duplicate Detection**: Computes SHA-256 binary file hash to detect duplicates across directories.
- **Rendering Quality Assurance**: Verifies non-blank, non-zero alpha glyph bounding boxes.
- **Deterministic Selection**: Reproducible random font selection using seed.
- **Authoritative Configuration Export**: Auto-generates `config/fonts.yaml`.

## 5. Test Suite Verification
- Executed `pytest`: **88 / 88 passed in 156.41s**.
