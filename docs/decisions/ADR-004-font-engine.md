# ADR-004: Typography Font Engine and Glyph Coverage Verification

## Status
Accepted

## Date
2026-08-17

## Context
Rendering authentic synthetic manuscripts for Chakma historical OCR requires high-fidelity TrueType (`.ttf`) and OpenType (`.otf`) fonts. Fonts supplied to the pipeline must support the 71 canonical Chakma script characters (`U+11100..U+1114F`). Any font lacking essential glyphs or failing to render will introduce missing bounding boxes, blank glyphs, or corrupted training labels into the YOLO training dataset.

## Decision
1. **Dynamic Font Discovery:** The `FontEngine` discovers all `.ttf` and `.otf` font files in `fonts/` dynamically with lowercase suffix matching.
2. **Authoritative Cmap Parsing via `fontTools`:** Fonts are inspected at the binary level using `fontTools.ttLib.TTFont` to read official cmap tables and map Unicode code points directly against the 71 canonical classes in `CharsetEngine`.
3. **Strict Coverage Threshold (70% Minimum):**
   - A font is **Accepted (`is_valid = True`)** if its glyph coverage of the canonical 71 Chakma classes is $\ge 70.0\%$.
   - A font is **Rejected (`is_valid = False`)** if its coverage is below threshold or if Pillow FreeType loading fails, recording an explicit `rejection_reason`.
4. **Deterministic Font Sampling:** Samping a font from the pool of accepted fonts uses an isolated `random.Random(seed)` instance, ensuring reproducible layout generation.
5. **Descriptor & FreeType Caching:** Pillow `FreeTypeFont` objects are cached with size clamping between `font_size_min` (24px) and `font_size_max` (72px) to optimize memory and rendering performance.
6. **No Premature Canvas Rendering:** Rendering onto image canvases or line positioning is decoupled and strictly deferred to Stage 05 (Line and Layout Rendering).

## Consequences
### Positive
- Fully verified typography inventory ensuring no corrupt or non-supporting fonts enter the synthetic pipeline.
- Instant rejection of inappropriate system/user fonts with clear diagnostic reasoning.
- Support for multiple Chakma font styles (Regular, Bold, Semilight, Google Noto) providing realistic typographic variation.

### Constraints
- Fonts must be standard TrueType or OpenType Unicode fonts compatible with FreeType and `fontTools`.
