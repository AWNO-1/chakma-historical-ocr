"""
Stage 09 Historical Document Transformation Visualizer and Diagnostic Utility.
Generates a multi-line Chakma manuscript sample, applies each geometric transformation
and optical degradation, tracks bounding boxes, and exports before/after side-by-side visualizations.
"""

import sys
from pathlib import Path
import json
import numpy as np
from PIL import Image, ImageDraw, ImageFont

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Add project root to sys.path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from generator.api import SyntheticGenerator
from generator.transform_engine import (
    TransformPipeline,
    apply_rotation,
    apply_translation,
    apply_perspective,
    apply_elastic,
    apply_curvature,
    validate_transformed_bboxes,
)
from utils.geometry import BBox

debug_out_dir = Path("debug/transformations")
debug_out_dir.mkdir(parents=True, exist_ok=True)

artifact_out_dir = Path(r"C:\Users\ComputerWorld\.gemini\antigravity\brain\8bf7dad0-1ef0-4dac-9c64-3bf0662958a7\images\stage09")
artifact_out_dir.mkdir(parents=True, exist_ok=True)


def draw_bboxes(image: Image.Image, bboxes: list[BBox], color: tuple = (220, 30, 30, 255)) -> Image.Image:
    """Draw bounding boxes with class IDs onto image canvas."""
    vis = image.copy().convert("RGBA")
    overlay = Image.new("RGBA", vis.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    # Color palette for classes
    palette = [
        (230, 40, 40, 220),
        (30, 140, 240, 220),
        (40, 180, 60, 220),
        (240, 140, 20, 220),
        (160, 40, 220, 220),
        (20, 180, 180, 220),
    ]

    for box in bboxes:
        c = palette[box.class_id % len(palette)]
        # Box rectangle
        draw.rectangle([box.x_min, box.y_min, box.x_max, box.y_max], outline=c, width=2)
        # Class label tag
        draw.rectangle([box.x_min, max(0, box.y_min - 10), box.x_min + 14, max(10, box.y_min)], fill=c)

    vis = Image.alpha_composite(vis, overlay)
    return vis.convert("RGB")


print("=" * 80)
print("STAGE 09 — HISTORICAL DOCUMENT TRANSFORMATION ENGINE REPORT")
print("=" * 80)

# 1. Generate base synthetic page sample
gen = SyntheticGenerator(seed=42)
sample = gen.generate(seed=42)
orig_img = sample.image
orig_boxes = [c.bbox for c in sample.characters]

print(f"Base Sample ID    : {sample.metadata.sample_id}")
print(f"Original Canvas   : {orig_img.width}x{orig_img.height} px")
print(f"Total BBoxes      : {len(orig_boxes)}")
print(f"Font Used         : {sample.metadata.font_name} ({sample.metadata.font_size}px)")

# Save original clean & with boxes
orig_vis = draw_bboxes(orig_img, orig_boxes)
orig_vis.save(debug_out_dir / "01_original_with_boxes.png")
orig_vis.save(artifact_out_dir / "01_original_with_boxes.png")
print("\n[1/7] Saved Original sample with BBoxes -> 01_original_with_boxes.png")

# 2. Test Rotation
rot_img, rot_boxes, rot_params = apply_rotation(orig_img, orig_boxes, angle_deg=3.5)
rot_vis = draw_bboxes(rot_img, rot_boxes)
rot_vis.save(debug_out_dir / "02_rotation_with_boxes.png")
rot_vis.save(artifact_out_dir / "02_rotation_with_boxes.png")
print("\n[2/7] ROTATION (+3.5 deg):")
print(f"  - Parameters: Angle = {rot_params['angle_deg']}°, Center = {rot_params['center']}")
print(f"  - Affine Matrix:\n    {rot_params['matrix'][0]}\n    {rot_params['matrix'][1]}")
print(f"  - Surviving BBoxes: {len(rot_boxes)}/{len(orig_boxes)}")

# 3. Test Translation
trans_img, trans_boxes, trans_params = apply_translation(orig_img, orig_boxes, tx=25.0, ty=-15.0)
trans_vis = draw_bboxes(trans_img, trans_boxes)
trans_vis.save(debug_out_dir / "03_translation_with_boxes.png")
trans_vis.save(artifact_out_dir / "03_translation_with_boxes.png")
print("\n[3/7] TRANSLATION (dx=+25px, dy=-15px):")
print(f"  - Parameters: tx = {trans_params['tx']} px, ty = {trans_params['ty']} px")
print(f"  - Surviving BBoxes: {len(trans_boxes)}/{len(orig_boxes)}")

# 4. Test Perspective Warp
persp_img, persp_boxes, persp_params = apply_perspective(orig_img, orig_boxes, scale=0.035, seed=42)
persp_vis = draw_bboxes(persp_img, persp_boxes)
persp_vis.save(debug_out_dir / "04_perspective_with_boxes.png")
persp_vis.save(artifact_out_dir / "04_perspective_with_boxes.png")
print("\n[4/7] PERSPECTIVE WARP (scale=0.035):")
print(f"  - Homography 3x3 Matrix:\n    {persp_params['homography_matrix'][0]}\n    {persp_params['homography_matrix'][1]}\n    {persp_params['homography_matrix'][2]}")
print(f"  - Surviving BBoxes: {len(persp_boxes)}/{len(orig_boxes)}")

# 5. Test Elastic Mesh Distortion
elast_img, elast_boxes, elast_params = apply_elastic(orig_img, orig_boxes, alpha=22.0, sigma=6.0, seed=42)
elast_vis = draw_bboxes(elast_img, elast_boxes)
elast_vis.save(debug_out_dir / "05_elastic_with_boxes.png")
elast_vis.save(artifact_out_dir / "05_elastic_with_boxes.png")
print("\n[5/7] ELASTIC MESH DISTORTION (alpha=22.0, sigma=6.0):")
print(f"  - Displacement Field: alpha = {elast_params['alpha']}, sigma = {elast_params['sigma']}")
print(f"  - Surviving BBoxes: {len(elast_boxes)}/{len(orig_boxes)}")

# 6. Test Page Curvature
curv_img, curv_boxes, curv_params = apply_curvature(orig_img, orig_boxes, amplitude=16.0, frequency=1.0)
curv_vis = draw_bboxes(curv_img, curv_boxes)
curv_vis.save(debug_out_dir / "06_curvature_with_boxes.png")
curv_vis.save(artifact_out_dir / "06_curvature_with_boxes.png")
print("\n[6/7] PAGE CURVATURE (amplitude=16.0px, freq=1.0):")
print(f"  - Spine Curvature Function: y'(x) = y + {curv_params['amplitude']} * sin({curv_params['frequency']} * pi * x / W)")
print(f"  - Surviving BBoxes: {len(curv_boxes)}/{len(orig_boxes)}")

# 7. Test Full TransformPipeline (Geometric + Photometric chained)
pipeline = TransformPipeline(seed=42)
pipeline_res = pipeline.apply(orig_img, orig_boxes, seed=12345)
pipe_vis = draw_bboxes(pipeline_res.image, pipeline_res.bboxes)
pipe_vis.save(debug_out_dir / "07_full_pipeline_with_boxes.png")
pipe_vis.save(artifact_out_dir / "07_full_pipeline_with_boxes.png")
print("\n[7/7] FULL TRANSFORMATION PIPELINE (Geometric + Photometric):")
print(f"  - Applied Transforms: {', '.join(pipeline_res.applied_transforms)}")
print(f"  - Final Surviving BBoxes: {pipeline_res.total_boxes}/{len(orig_boxes)}")
print(f"  - Validation Status     : {pipeline_res.parameters['bbox_validation']['is_valid']}")
print(f"  - Errors Count          : {len(pipeline_res.parameters['bbox_validation']['errors'])}")

print("=" * 80)
print(f"Successfully exported all 7 visualization comparison images to:")
print(f"  - {debug_out_dir.resolve()}")
print(f"  - {artifact_out_dir.resolve()}")
print("=" * 80)
