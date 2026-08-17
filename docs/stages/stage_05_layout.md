# Stage 05: Layout and Character Geometry Engine

## Stage Information
- **Title:** Layout and Character Geometry Engine
- **Stage Number:** 05
- **Date:** 2026-08-17
- **Status:** WAITING FOR APPROVAL

## Objective
Compute spatial positions, page margins, line bounds, and character bounding boxes with exact reading-order assignment prior to any rendering or image rasterization, guaranteeing deterministic reproducibility and zero box leakage across canvas boundaries.

## Implementation Details
1. **Core Data Structures (`generator/layout_engine.py`):**
   - `CharacterLayout`: Represents an individual character on canvas with `character`, `class_id`, `(x, y, width, height)`, `line_id`, `word_id`, `reading_order`, and conversion methods `.bbox` / `.to_yolo()`.
   - `LineLayout`: Represents a text line containing an ordered list of `CharacterLayout` items and line bounding dimensions.
   - `PageLayout`: Represents a full manuscript page with dimensions, margins (top/bottom/left/right), line collections, and total character counts.
   - `LayoutConfig`: Configuration dataclass for default canvas dimensions and font sizing ranges.
2. **Authoritative Engine (`generator/layout_engine.py`):**
   - `calculate_margins(rng)`: Deterministic margin calculation within configured bounds.
   - `estimate_glyph_metrics(char, font_size, font_path)`: Metric extraction from font cmap and glyph metrics without rasterization.
   - `generate_page_layout(lines_text, font_path, font_size, seed)`: Generates complete `PageLayout` from input text lines.
   - `_compute_line_geometry(...)`: Calculates character placement, word gaps, micro-jitter, and enforces right-margin boundary clamping.
   - `validate_layout(layout)`: Multi-dimensional validation checking box dimension positivity, canvas boundary enclosure, monotonic contiguous reading order, and line grouping consistency.
3. **Geometry Primitives (`utils/geometry.py`):**
   - `BBox`: Enhanced with `.is_valid()`, `.is_within_bounds()`, `.clip()`, `.to_yolo()`, `.from_yolo()`.
   - `calculate_iou(b1, b2)`: Exact Intersection over Union calculation.
   - `calculate_intersection_area(b1, b2)`: Absolute pixel intersection.
   - `sort_bboxes_reading_order(boxes)`: Robust multiline reading order sorter.
4. **Unit Tests (`tests/test_layout.py`, `tests/test_geometry.py`):**
   - 15 combined unit tests verifying box validity, boundary inclusion, monotonic reading order, line grouping, seed reproducibility, IoU calculations, and YOLO format round-tripping (46/46 tests passed in project suite).

## Geometric Layout & Wireframe Demonstration (Seed=42)

### 1. Page Geometry Specifications
- **Canvas Dimensions:** 1024 x 1024 px
- **Margins:** Top=51px, Bottom=67px, Left=65px, Right=64px
- **Total Lines:** 4 lines
- **Total Characters:** 52 characters
- **Validation Result:** `is_valid = True` (0 errors, 0 out-of-bounds boxes)

### 2. Line Spatial Bounds
- **Line 0:** `x = [65.0 .. 966.4], y = [51.0 .. 136.5]` | Characters: 13 | Words: 6
- **Line 1:** `x = [65.0 .. 947.4], y = [147.0 .. 234.3]` | Characters: 13 | Words: 4
- **Line 2:** `x = [65.0 .. 987.4], y = [243.0 .. 314.4]` | Characters: 13 | Words: 4
- **Line 3:** `x = [65.0 .. 923.4], y = [339.0 .. 426.2]` | Characters: 13 | Words: 5

### 3. Sample Character Bounding Boxes & Normalized YOLO Coordinates

| Order | Line | Word | Class ID | Character | Box Coordinates `[x_min, y_min, x_max, y_max]` | Normalized YOLO `(class_id, cx, cy, w, h)` |
|:---:|:---:|:---:|:---:|:---:|:---|:---|
| 0 | 0 | 0 | 31 | 𑄟 | `[ 64.6,  75.6, 144.6, 121.6]` | `(31, 0.1022, 0.0963, 0.0781, 0.0449)` |
| 1 | 0 | 0 | 26 | 𑄚 | `[151.6,  76.0, 231.6, 122.0]` | `(26, 0.1871, 0.0967, 0.0781, 0.0449)` |
| 2 | 0 | 0 | 42 | 𑄪 | `[234.9, 112.5, 248.9, 136.5]` | `(42, 0.2362, 0.1216, 0.0137, 0.0234)` |
| 3 | 0 | 0 | 12 | 𑄌 | `[257.8,  75.7, 313.8, 121.7]` | `(12, 0.2791, 0.0964, 0.0547, 0.0449)` |
| 4 | 0 | 0 | 52 | 𑄴 | `[304.7,  66.1, 336.7, 121.1]` | `(52, 0.3132, 0.0914, 0.0312, 0.0537)` |
| 5 | 0 | 1 | 3 | 𑄃 | `[388.0,  76.2, 465.0, 122.2]` | `( 3, 0.4165, 0.0969, 0.0752, 0.0449)` |
| 6 | 0 | 1 | 31 | 𑄟 | `[471.1,  76.0, 551.1, 122.0]` | `(31, 0.4991, 0.0966, 0.0781, 0.0449)` |
| 7 | 0 | 1 | 34 | 𑄢 | `[557.4,  76.4, 633.4, 122.4]` | `(34, 0.5814, 0.0970, 0.0742, 0.0449)` |

### 4. Pure Geometric 2D Wireframe
```
+----------------------------------------------------------+
|..###########.#####..#################..###########.......|
|..#################..#################..###########.......|
|............##........####...###..........###......##.....|
|..##########.###################..###########..######.....|
|..##########.###################..###################.....|
|..#################..#################..##############....|
|..#################..#################..##############....|
|..##########.###########.#####..#################.........|
|..##########.#################..#################.........|
|..........................................................|
|..........................................................|
|..........................................................|
|..........................................................|
|..........................................................|
|..........................................................|
|..........................................................|
|..........................................................|
|..........................................................|
|..........................................................|
|..........................................................|
|..........................................................|
|..........................................................|
+----------------------------------------------------------+
```

## Verification Results
- **Pytest Pass Rate:** 100% (46/46 unit tests passed in 8.18s).
- **Pixel Rasterization / OpenCV:** Zero drawing used (100% decoupled geometric math).
