# ADR-009: Historical Document Transformation and Bounding Box Synchronicity

## Status
Accepted

## Context
Training OCR and character-level object detection models on synthetic historical documents requires realistic optical degradations and physical distortions (rotations, perspective tilts, elastic folds, curved spines). If geometric transformations are applied only to the raster image without recalculating character bounding boxes, the training annotations become misaligned and degrade detection accuracy.

## Decision
1. **Synchronous Geometric BBox Projection**:
   - For every geometric transformation (rotation, translation, perspective homography, elastic displacement, page curvature), the forward/backward mathematical mapping is applied simultaneously to the image pixel grid and to the 4 corner vertices of every character bounding box.
   - The transformed polygon vertices are used to recompute the exact enclosing axis-aligned bounding box (AABB), followed by strict boundary clipping and degenerate box pruning.
2. **Layered Photometric Degradation Pipeline**:
   - Decoupled `AugmentationEngine` applies optical degradations (blur, noise, ink fading, color shifts, illumination gradients, bleed-through) without altering geometric coordinates.
3. **Unified Pipeline Orchestrator**:
   - `TransformPipeline` chains geometric and photometric transformations into a single deterministic call with full parameter reporting.

## Consequences
- Guaranteed zero-drift alignment between image textures and character bounding boxes under arbitrary complex warps.
- Clean validation preventing any NaN, zero-area, or out-of-bounds annotations from entering training datasets.
- 100% deterministic reproducibility across training runs via RNG seeds.
