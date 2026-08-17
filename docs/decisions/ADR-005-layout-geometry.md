# ADR-005: Pre-Rendering Layout and Character Geometry Engine

## Status
Accepted

## Date
2026-08-17

## Context
In a character-level YOLO OCR system, bounding boxes and reading orders must be computed with mathematical precision before text is rendered or degraded. Computing geometry during or after pixel rasterization (e.g. via connected components or contour detection) is prone to segmentation errors, merged diacritics, and non-deterministic variations.

## Decision
1. **Pre-Rendering Geometric Computation:** All bounding boxes, margins, line positions, and character coordinates are computed purely geometrically prior to any pixel rasterization.
2. **Explicit Hierarchy Dataclasses:**
   - `CharacterLayout`: Stores `character`, `class_id`, `(x, y, width, height)`, `line_id`, `word_id`, and global monotonic `reading_order`.
   - `LineLayout`: Encapsulates full text, line bounding box, and the ordered list of `CharacterLayout` elements.
   - `PageLayout`: Encapsulates page dimensions, top/bottom/left/right margins, and the collection of `LineLayout` rows.
3. **No Pixel Rasterization / No OpenCV Drawing:** The layout engine operates purely on geometric math and font glyph metrics (`font.getbbox()`, `font.getlength()`). OpenCV is not used for text drawing or box estimation.
4. **Deterministic Random Variations:** Margin dimensions, font size variations, character micro-jitter, and line spacing are governed by isolated `random.Random(seed)` instances to ensure 100% reproducible bounding box coordinates.
5. **Strict Boundary Clamping:** Character sequence placement strictly checks `(char_x + char_w) <= max_x_boundary` before insertion, preventing any character box from protruding outside canvas margins.

## Consequences
### Positive
- Perfect ground-truth bounding box alignment that matches exact font glyph metrics without heuristic contour estimation.
- 100% reproducible YOLO annotation labels (`(class_id, cx, cy, w, h)`) across independent runs.
- Clean separation between geometric layout calculation and subsequent canvas rendering/augmentation.

### Constraints
- Text sequences that exceed canvas width are truncated at the word/character boundary rather than wrapping uncontrollably.
