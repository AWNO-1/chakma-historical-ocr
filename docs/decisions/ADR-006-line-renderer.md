# ADR-006: Continuous Line Rendering and Glyph-Level Coordinate Tracking

## Status
Accepted

## Date
2026-08-17

## Context
Rendering text character-by-character onto individual image patches and then stitching them together introduces unnatural kerning, destroys Brahmic abugida combining marks/matras (which must attach above, below, or beside base consonants with zero advance width), and produces unrealistic typographic artifacts. However, rendering a full text line as a continuous string requires a reliable method to track exact ground-truth bounding boxes, Class IDs, and reading orders for every character in the line.

## Decision
1. **Continuous Line Rendering:** Lines are rendered as unified typographic strings using Pillow's `ImageDraw.Draw.text()` and FreeType font shaper without individual character image slicing.
2. **Explicit Character Coordinate Extraction:** While rendering the line, character bounding boxes are calculated from font glyph offsets (`font.getbbox(char)`) and advance widths (`font.getlength(char)`).
3. **Combining Mark Handling:** Non-spacing combining marks (dependent vowels, signs, virama) with zero advance width are positioned relative to their attachment anchor on the base consonant, ensuring their bounding boxes precisely enclose their ink pixels without disrupting subsequent character placement.
4. **Isolated Line Canvas Architecture:** Each rendered line is represented by a `RenderedLine` dataclass holding the RGBA image, line metadata, and an ordered list of `RenderedCharacter` objects.
5. **No Background or Degradation:** Stage 06 is strictly limited to typographic line rendering on transparent/plain canvases. Background synthesis and augmentations remain decoupled in subsequent pipeline stages.

## Consequences
### Positive
- Natural Brahmic text rendering with authentic kerning, ligature support, and correct diacritic attachments.
- Strict 1:1 ground-truth bounding box alignment containing actual visible ink pixels.
- Modular `RenderedLine` and `RenderedPageLines` structures ready for seamless composition with `BackgroundEngine` and `TransformEngine`.

### Constraints
- Glyph metrics depend on font FreeType tables; unmapped characters are skipped with logged warnings.
