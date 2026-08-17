# Stage 09: Historical Document Transformation Engine

## Overview
Stage 09 implements the `TransformPipeline` and `AugmentationEngine` subsystems responsible for simulating authentic physical degradations, geometric distortions, and historical manuscript imperfections while guaranteeing mathematical synchronicity between image warping and character-level bounding box recalculations.

## Key Features & Implementations

### 1. Geometric Transformations (`generator/transform_engine.py`)
- **Affine Rotation (`apply_rotation`)**:
  - Warps image using 2D rotation matrix `M`.
  - Transforms all 4 polygon vertices of each BBox through `M` and recomputes the enclosing axis-aligned bounding box (AABB).
- **Translation (`apply_translation`)**:
  - Shifts canvas and shifts all BBox coordinates by `(tx, ty)`.
- **Perspective Projection (`apply_perspective`)**:
  - Uses 3x3 Homography matrix `H` to simulate 3D camera angles and uneven scan planes.
  - Projects each BBox corner through homogeneous coordinate mapping `[X, Y, Z]^T = H @ [x, y, 1]^T` and computes new AABB.
- **Elastic Mesh Distortion (`apply_elastic`)**:
  - Generates smooth Gaussian displacement fields `(dx, dy)` across canvas.
  - Remaps image with `cv2.remap` and projects BBox vertices through the local displacement field.
- **Page Curvature & Curved Baselines (`apply_curvature`)**:
  - Simulates book-spine roll and page curvature via sine wave mapping `y'(x) = y + A * sin(f * pi * x / W)`.
  - Evaluates curvature function on BBox corners to preserve exact alignment.

### 2. Optical & Photometric Augmentations (`generator/augmentations.py`)
- **Blur**: Gaussian defocus, directional motion blur, and box filter.
- **Noise**: Additive Gaussian noise, sensor speckle, and salt-and-pepper aging dust.
- **Historical Ink Aesthetics**:
  - Ink color shift away from jet black towards authentic iron-gall brown/sepia, charcoal, and walnut tones.
  - Ink fading and intra-stroke density flow variations.
- **Uneven Illumination**: Corner shadow vignetting, directional lighting gradients, and localized spotlights.
- **Backside Bleed-Through**: Inverted, horizontally flipped, and blurred ghosting from the reverse side of paper.
- **JPEG Compression**: DCT blocking artifacts and frequency loss.

### 3. Coordinate Integrity & Validation
- Bounding boxes undergo strict validation (`validate_transformed_bboxes`):
  - Verification of non-NaN / non-Inf values.
  - Verification of positive width, height, and area (`area >= 1.0`).
  - Strict clipping to canvas boundaries `[0, width]` x `[0, height]`.
  - Preservation of Class IDs and confidence values.

## Test Results
- **Unit & Integration Suite**: 8/8 tests passing in `tests/test_transform_engine.py`.
- **Repository-Wide Test Suite**: 76/76 tests passing across all 9 stages.
