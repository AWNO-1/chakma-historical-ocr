# Stage 10 — Synthetic Ground Truth & YOLO Label Engine

## 1. Overview & Architecture
Stage 10 implements the authoritative Ground Truth and YOLO Label Engine for the Chakma Historical OCR system (`generator/annotation_engine.py`). It provides robust translation from in-memory character metadata (`SampleCharacter`, `SyntheticSample`) directly into standardized, normalized YOLO bounding box format (`<class_id> <x_center> <y_center> <width> <height>`) with coordinates in `[0.0, 1.0]`.

## 2. Key Components
- **`YoloAnnotation` Data Class**: Encapsulates single bounding box detection metadata with bidirectional conversions (`to_yolo_line()`, `to_bbox()`).
- **`YoloLabelWriter` Core Class**:
  - `to_yolo()`: Converts single characters, batches, or full `SyntheticSample` instances into normalized YOLO strings.
  - `write_label_file()`: Writes formatted `.txt` label files to disk with UTF-8 encoding.
  - `parse_label_file()`: Parses on-disk YOLO `.txt` files back into structured `YoloAnnotation` models.
  - `validate_label()`: Enforces strict 6-point geometric, linguistic, and range checks.
  - `validate_all()`: Aggregates validation reports across large sample batches.
  - `visualize_labels()`: Renders high-contrast bounding boxes with class IDs and character badges using a 71-color distinct Golden Angle palette.
- **Calibrated Photometric Noise**: Adjusted Gaussian noise variance range to `[0.001, 0.005]` preventing image saturation and ensuring realistic paper grain.

## 3. Validation Rules Enforced
1. **Class ID Existence**: Every `class_id` must exist in `CharsetEngine` (`0 <= class_id < 71`).
2. **Finite Numbers**: Strict assertion that coordinates contain no `NaN` or `Inf` values.
3. **Normalized Coordinate Range**: `0.0 <= x_center, y_center <= 1.0` and `0.0 < width, height <= 1.0`.
4. **Positive Non-Zero Area**: `width > 0.0` and `height > 0.0` with minimum bounding box area validation.
5. **Canvas Containment**: BBoxes must fall within normalized canvas bounds `[0.0, 1.0]`.
6. **Physical Size Consistency**: Assert non-degenerate pixel dimensions.

## 4. Batch Validation Results (100 Synthetic Samples)
- **Total Samples Generated**: 100
- **Total YOLO Labels**: 19,819
- **Valid Labels**: 19,819 (100.00%)
- **Invalid Labels**: 0 (0.00%)
- **Overall Dataset Status**: **PASSED (100% VALID)**
- **Test Suite Status**: 86 / 86 tests passed in 41.57s.
