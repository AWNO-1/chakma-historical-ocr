# Stage 06: Chakma Line Renderer

## Stage Information
- **Title:** Chakma Line Renderer
- **Stage Number:** 06
- **Date:** 2026-08-17
- **Status:** WAITING FOR APPROVAL

## Objective
Render complete, continuous text lines onto Pillow canvases while precisely tracking character-level bounding boxes, class IDs, reading orders, and spatial coordinates without separate glyph slicing, background textures, or geometric transformations.

## Implementation Details
1. **Core Data Structures (`generator/line_renderer.py`):**
   - `RenderedCharacter`: Represents an individual rendered character containing `character`, `class_id`, `local_bbox`, `global_bbox`, `line_id`, `word_id`, and `reading_order`.
   - `RenderedLine`: Holds the rendered RGBA `Image.Image`, line text, font metadata, font size, line-level `BBox`, and the ordered list of `RenderedCharacter` items.
   - `RenderedPageLines`: Represents the complete assembled manuscript page canvas with all lines rendered and global character bounding boxes.
2. **Authoritative Engine (`generator/line_renderer.py`):**
   - `measure_character(char, font)`: Measures exact bounding box offsets for a single character relative to `(0, 0)` anchor.
   - `measure_text(text, font)`: Measures total pixel width and height of a text string.
   - `render_line(text, font_path, font_size, line_id, reading_order_start, ...)`: Renders full text line as a continuous string onto an isolated line canvas and computes character-level local and global bounding boxes.
   - `render_page_lines(page_layout, font_path, font_size, ...)`: Renders all lines of a `PageLayout` onto a full manuscript page canvas.
3. **Dedicated Test Suite (`tests/test_line_renderer.py`):**
   - 8 comprehensive unit tests covering:
     - Visible ink rendering verification (`test_glyph_rendering_and_ink`).
     - Empty text and whitespace handling (`test_empty_text_handling`).
     - Unsupported character resilience (`test_unsupported_glyph_handling`).
     - Multi-font rendering across all 4 accepted Chakma fonts (`test_multiple_fonts_rendering`).
     - Bounding-box ink containment consistency (`test_bounding_box_consistency`).
     - Character and text measurement (`test_measure_character_and_text`).
     - Full page canvas rendering (`test_render_page_lines`).
   - Project-wide pass rate: 100% (54/54 tests passed).

## Real Rendering Output Examples

### Sample 1: NotoSansChakma-Regular (36px)
- **Text:** `𑄟𑄚𑄪𑄌𑄴 𑄃𑄟𑄢𑄴 𑄘𑄬𑄌𑄴 𑄌𑄋𑄴𑄟 𑄞𑄌𑄴 𑄇𑄧𑄠𑄴𑅁`
- **Canvas Size:** 561 x 104 px (Padding=15px)
- **Total Characters:** 25 characters
- **Saved Asset:** `debug/rendered_samples/line_sample_1_NotoSansChakma-Regular_36px.png`
- **Character BBoxes (First 5):**
  - Order  0 | Word 0 | ID 31 (`𑄟`) -> Box: `[ 15.0,  37.0,  44.0,  57.0]` | Size: 29.0 x 20.0 px
  - Order  1 | Word 0 | ID 26 (`𑄚`) -> Box: `[ 44.0,  37.0,  80.0,  57.0]` | Size: 36.0 x 20.0 px
  - Order  2 | Word 0 | ID 42 (`𑄪`) -> Box: `[ 68.0,  57.0,  80.0,  69.0]` | Size: 12.0 x 12.0 px
  - Order  3 | Word 0 | ID 12 (`𑄌`) -> Box: `[ 80.0,  36.0, 106.0,  57.0]` | Size: 26.0 x 21.0 px
  - Order  4 | Word 0 | ID 52 (`𑄴`) -> Box: `[ 92.0,  29.0, 106.0,  57.0]` | Size: 14.0 x 28.0 px

### Sample 2: Nirmala (32px)
- **Text:** `𑄢𑄎 𑄘𑄬𑄌𑄮𑄖𑄴 𑄇𑄟𑄴 𑄉𑄧𑄢𑄬𑅁`
- **Canvas Size:** 434 x 93 px (Padding=15px)
- **Total Characters:** 16 characters
- **Saved Asset:** `debug/rendered_samples/line_sample_2_Nirmala_32px.png`
- **Character BBoxes (First 5):**
  - Order  0 | Word 0 | ID 34 (`𑄢`) -> Box: `[ 15.0,  27.0,  51.0,  50.0]` | Size: 36.0 x 23.0 px
  - Order  1 | Word 0 | ID 14 (`𑄎`) -> Box: `[ 51.0,  27.0,  81.0,  50.0]` | Size: 30.0 x 23.0 px
  - Order  2 | Word 1 | ID 24 (`𑄘`) -> Box: `[ 90.0,  27.0, 114.0,  50.0]` | Size: 24.0 x 23.0 px
  - Order  3 | Word 1 | ID 44 (`𑄬`) -> Box: `[114.0,  27.0, 132.0,  50.0]` | Size: 18.0 x 23.0 px
  - Order  4 | Word 1 | ID 12 (`𑄌`) -> Box: `[132.0,  27.0, 159.0,  50.0]` | Size: 27.0 x 23.0 px

### Sample 3: NirmalaB [Bold] (40px)
- **Text:** `𑄃𑄟𑄢𑄴 𑄇𑄨𑄖𑄛𑄴 𑄖𑄧𑄣𑄬 𑄃𑄊𑄬𑅁`
- **Canvas Size:** 610 x 94 px (Padding=15px)
- **Total Characters:** 17 characters
- **Saved Asset:** `debug/rendered_samples/line_sample_3_NirmalaB_40px.png`
- **Character BBoxes (First 5):**
  - Order  0 | Word 0 | ID  3 (`𑄃`) -> Box: `[ 15.0,  31.0,  63.0,  59.0]` | Size: 48.0 x 28.0 px
  - Order  1 | Word 0 | ID 31 (`𑄟`) -> Box: `[ 63.0,  31.0, 113.0,  59.0]` | Size: 50.0 x 28.0 px
  - Order  2 | Word 0 | ID 34 (`𑄢`) -> Box: `[113.0,  31.0, 160.0,  59.0]` | Size: 47.0 x 28.0 px
  - Order  3 | Word 0 | ID 52 (`𑄴`) -> Box: `[150.0,  25.0, 170.0,  59.0]` | Size: 20.0 x 34.0 px
  - Order  4 | Word 1 | ID  7 (`𑄇`) -> Box: `[171.0,  31.0, 212.0,  59.0]` | Size: 41.0 x 28.0 px

### Sample 4: NirmalaS [Semilight] (28px)
- **Text:** `𑄌𑄋𑄴𑄟 𑄥𑄋𑄴𑄇𑄳𑄢𑄨𑄖𑄨 𑄃𑄢𑄴 𑄞𑄌𑄴 𑄃𑄟𑄢𑄴 𑄉𑄧𑄢𑄧𑄛𑄴𑅂`
- **Canvas Size:** 625 x 88 px (Padding=15px)
- **Total Characters:** 30 characters
- **Saved Asset:** `debug/rendered_samples/line_sample_4_NirmalaS_28px.png`
- **Character BBoxes (First 5):**
  - Order  0 | Word 0 | ID 12 (`𑄌`) -> Box: `[ 15.0,  26.0,  39.0,  46.0]` | Size: 24.0 x 20.0 px
  - Order  1 | Word 0 | ID 11 (`𑄋`) -> Box: `[ 39.0,  26.0,  62.0,  46.0]` | Size: 23.0 x 20.0 px
  - Order  2 | Word 0 | ID 52 (`𑄴`) -> Box: `[ 55.0,  23.0,  69.0,  46.0]` | Size: 14.0 x 23.0 px
  - Order  3 | Word 0 | ID 31 (`𑄟`) -> Box: `[ 62.0,  26.0,  95.0,  46.0]` | Size: 33.0 x 20.0 px
  - Order  4 | Word 1 | ID 37 (`𑄥`) -> Box: `[103.0,  26.0, 135.0,  46.0]` | Size: 32.0 x 20.0 px

## Verification Summary
- **Unit Test Pass Rate:** 100% (54/54 tests passed in 7.99s).
- **Background / Transformations:** Zero background textures or transformations added (strictly pure line rendering).
