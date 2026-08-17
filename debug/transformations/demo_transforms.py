"""
Stage 09 — Authoritative Historical Document Transformation Engine Visualizer.
Demonstrates:
- Real historical backgrounds (Paper, Parchment, Manuscript, Bamboo)
- Random font switching and font size variation across lines/words
- Multi-colored authentic non-black historical inks (Iron-gall, Sepia, Walnut, Charcoal, Rubricated red)
- Handwritten undulating curved baselines
- 3D Perspective homography
- Elastic mesh wrinkling
- Book-spine page curvature
- Backside ink bleed-through ghosting
- Historical ink fading & uneven flow
- Uneven vignette & directional illumination
- Exact character bounding box synchronicity
"""

import sys
from pathlib import Path
import json
import random
import numpy as np
from PIL import Image, ImageDraw, ImageFont

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Add project root to sys.path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from generator.api import SyntheticGenerator
from generator.background import BackgroundLibrary
from generator.line_renderer import LineRenderer
from generator.transform_engine import (
    TransformPipeline,
    apply_rotation,
    apply_translation,
    apply_perspective,
    apply_elastic,
    apply_curvature,
    apply_curved_baseline,
    validate_transformed_bboxes,
)
from generator.augmentations import (
    apply_blur,
    apply_noise,
    apply_ink_variation,
    apply_illumination,
    apply_bleedthrough,
    apply_compression_artifacts,
)
from utils.geometry import BBox

debug_out_dir = Path("debug/transformations")
debug_out_dir.mkdir(parents=True, exist_ok=True)

artifact_out_dir = Path(r"C:\Users\ComputerWorld\.gemini\antigravity\brain\8bf7dad0-1ef0-4dac-9c64-3bf0662958a7\images\stage09")
artifact_out_dir.mkdir(parents=True, exist_ok=True)


def draw_bboxes(image: Image.Image, bboxes: list[BBox]) -> Image.Image:
    """Draw clear, high-contrast bounding boxes with class tags on manuscript canvas."""
    vis = image.copy().convert("RGBA")
    overlay = Image.new("RGBA", vis.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    # Vivid palette to distinguish adjacent characters and diacritics
    palette = [
        (220, 20, 60, 230),   # Crimson
        (30, 144, 255, 230),  # Dodger Blue
        (46, 139, 87, 230),   # Sea Green
        (255, 140, 0, 230),   # Dark Orange
        (138, 43, 226, 230),  # Blue Violet
        (0, 180, 180, 230),   # Teal
        (210, 105, 30, 230),  # Chocolate
    ]

    for box in bboxes:
        c = palette[box.class_id % len(palette)]
        # Box rectangle
        draw.rectangle([box.x_min, box.y_min, box.x_max, box.y_max], outline=c, width=2)
        # Class tag badge
        tag_w = 14
        tag_h = 10
        draw.rectangle([box.x_min, max(0, box.y_min - tag_h), box.x_min + tag_w, max(tag_h, box.y_min)], fill=c)

    vis = Image.alpha_composite(vis, overlay)
    return vis.convert("RGB")


print("=" * 80)
print("STAGE 09 — AUTHORITATIVE HISTORICAL TRANSFORMATION ENGINE VISUALIZATION")
print("=" * 80)

# Initialize generator with real background library
gen = SyntheticGenerator(seed=777)

# 1. Base Authentic Historical Manuscript
# (Composited on real Parchment background with varied fonts, sizes, and non-black historical ink colors)
base_sample = gen.generate(
    use_real_background=True,
    background_category="parchment",
    random_font_per_line=True,
    random_size_jitter=4.0,
    baseline_jitter=2.0,
    ink_palettes=[
        (48, 34, 24, 245),   # Iron-gall brown
        (38, 28, 20, 250),   # Dark walnut
        (30, 30, 34, 255),   # Charcoal carbon
        (62, 48, 36, 235),   # Aged sepia
        (130, 35, 25, 245),  # Rubricated red line/title
    ],
    seed=101,
)

orig_img = base_sample.image
orig_boxes = [c.bbox for c in base_sample.characters]

print(f"Base Manuscript Canvas: {orig_img.width}x{orig_img.height} px | Background: {base_sample.metadata.extra.get('background')}")
print(f"Total Lines: {base_sample.metadata.total_lines} | Total Characters: {len(orig_boxes)}")

# Save 01 Base Manuscript (Clean & with BBoxes)
orig_img.save(debug_out_dir / "01_base_manuscript_clean.png")
orig_img.save(artifact_out_dir / "01_base_manuscript_clean.png")
orig_vis = draw_bboxes(orig_img, orig_boxes)
orig_vis.save(debug_out_dir / "01_base_manuscript_with_boxes.png")
orig_vis.save(artifact_out_dir / "01_base_manuscript_with_boxes.png")
print("[1/10] Saved Base Manuscript (Real Parchment + Multi-font/Multi-color Ink) -> 01_base_manuscript_with_boxes.png")

# 2. Handwritten Curved Baseline (Wavy line undulation)
wavy_img, wavy_boxes, wavy_params = apply_curved_baseline(orig_img, orig_boxes, amplitude=7.5, frequency=1.8, seed=42)
wavy_vis = draw_bboxes(wavy_img, wavy_boxes)
wavy_vis.save(debug_out_dir / "02_curved_baseline_with_boxes.png")
wavy_vis.save(artifact_out_dir / "02_curved_baseline_with_boxes.png")
print("\n[2/10] CURVED BASELINE (Handwritten Waviness):")
print(f"  - Parameters: Amplitude = {wavy_params['amplitude']}px, Frequency = {wavy_params['frequency']}, Phase = {wavy_params['phase_offset']}")
print(f"  - BBoxes Valid: {len(wavy_boxes)}/{len(orig_boxes)}")

# 3. Rotation & Skew (+3.5 deg)
rot_img, rot_boxes, rot_params = apply_rotation(orig_img, orig_boxes, angle_deg=3.5)
rot_vis = draw_bboxes(rot_img, rot_boxes)
rot_vis.save(debug_out_dir / "03_rotation_with_boxes.png")
rot_vis.save(artifact_out_dir / "03_rotation_with_boxes.png")
print("\n[3/10] ROTATION & SKEW (+3.5 deg):")
print(f"  - Affine Matrix: {rot_params['matrix'][0]}")
print(f"  - BBoxes Valid: {len(rot_boxes)}/{len(orig_boxes)}")

# 4. 3D Perspective Warp (Slanted camera angle)
persp_img, persp_boxes, persp_params = apply_perspective(orig_img, orig_boxes, scale=0.04, seed=42)
persp_vis = draw_bboxes(persp_img, persp_boxes)
persp_vis.save(debug_out_dir / "04_perspective_with_boxes.png")
persp_vis.save(artifact_out_dir / "04_perspective_with_boxes.png")
print("\n[4/10] 3D PERSPECTIVE WARP:")
print(f"  - Homography Matrix:\n    {persp_params['homography_matrix'][0]}\n    {persp_params['homography_matrix'][1]}\n    {persp_params['homography_matrix'][2]}")
print(f"  - BBoxes Valid: {len(persp_boxes)}/{len(orig_boxes)}")

# 5. Elastic Mesh Wrinkling (Paper fold deformation)
elast_img, elast_boxes, elast_params = apply_elastic(orig_img, orig_boxes, alpha=24.0, sigma=6.0, seed=42)
elast_vis = draw_bboxes(elast_img, elast_boxes)
elast_vis.save(debug_out_dir / "05_elastic_with_boxes.png")
elast_vis.save(artifact_out_dir / "05_elastic_with_boxes.png")
print("\n[5/10] ELASTIC MESH WRINKLING:")
print(f"  - Parameters: alpha = {elast_params['alpha']}, sigma = {elast_params['sigma']}")
print(f"  - BBoxes Valid: {len(elast_boxes)}/{len(orig_boxes)}")

# 6. Book Spine Page Curvature (3D cylindrical roll)
curv_img, curv_boxes, curv_params = apply_curvature(orig_img, orig_boxes, amplitude=18.0, frequency=1.0)
curv_vis = draw_bboxes(curv_img, curv_boxes)
curv_vis.save(debug_out_dir / "06_page_curvature_with_boxes.png")
curv_vis.save(artifact_out_dir / "06_page_curvature_with_boxes.png")
print("\n[6/10] BOOK SPINE PAGE CURVATURE:")
print(f"  - Function: y'(x) = y + {curv_params['amplitude']} * sin({curv_params['frequency']} * pi * x / W)")
print(f"  - BBoxes Valid: {len(curv_boxes)}/{len(orig_boxes)}")

# 7. Backside Ink Bleed-Through Ghosting
bleed_img = apply_bleedthrough(orig_img, intensity=0.22, blur_radius=3.5, seed=42)
bleed_vis = draw_bboxes(bleed_img, orig_boxes)
bleed_vis.save(debug_out_dir / "07_bleedthrough_with_boxes.png")
bleed_vis.save(artifact_out_dir / "07_bleedthrough_with_boxes.png")
print("\n[7/10] INK BLEED-THROUGH GHOSTING:")
print("  - Verso page text shadow faintly visible through translucent parchment.")

# 8. Historical Ink Fading & Color Variation
ink_fade_img = apply_ink_variation(orig_img, fade_ratio=0.35, density_jitter=0.2, seed=42)
ink_fade_vis = draw_bboxes(ink_fade_img, orig_boxes)
ink_fade_vis.save(debug_out_dir / "08_ink_fading_with_boxes.png")
ink_fade_vis.save(artifact_out_dir / "08_ink_fading_with_boxes.png")
print("\n[8/10] INK FADING & DENSITY VARIATION:")
print("  - Simulates non-uniform nib pressure, ink depletion, and stroke fading.")

# 9. Uneven Vignette & Directional Lighting Gradients
illum_img = apply_illumination(orig_img, pattern="vignette", intensity=0.35)
illum_img = apply_noise(illum_img, noise_type="speckle", var=0.005, seed=42)
illum_vis = draw_bboxes(illum_img, orig_boxes)
illum_vis.save(debug_out_dir / "09_illumination_vignette_with_boxes.png")
illum_vis.save(artifact_out_dir / "09_illumination_vignette_with_boxes.png")
print("\n[9/10] UNEVEN LIGHTING & VIGNETTING:")
print("  - Radial corner darkening and paper grain speckle noise.")

# 10. Complete Integrated Historical Manuscript Sample
# (Real background + Multi-font + Multi-color ink + Baseline curve + 3D perspective + Elastic warp + Bleedthrough + Vignette + Blur + JPEG)
full_sample = gen.generate(
    use_real_background=True,
    background_category="manuscript",
    random_font_per_line=True,
    random_size_jitter=4.0,
    baseline_jitter=2.0,
    ink_palettes=[
        (45, 32, 22, 245),
        (35, 26, 18, 250),
        (28, 28, 32, 255),
        (60, 46, 34, 235),
    ],
    apply_transforms=True,
    seed=888,
)

full_img = full_sample.image
full_boxes = [c.bbox for c in full_sample.characters]

full_img.save(debug_out_dir / "10_full_historical_sample_clean.png")
full_img.save(artifact_out_dir / "10_full_historical_sample_clean.png")
full_vis = draw_bboxes(full_img, full_boxes)
full_vis.save(debug_out_dir / "10_full_historical_sample_with_boxes.png")
full_vis.save(artifact_out_dir / "10_full_historical_sample_with_boxes.png")

print("\n[10/10] COMPLETE INTEGRATED HISTORICAL MANUSCRIPT SAMPLE:")
print(f"  - Sample ID: {full_sample.metadata.sample_id}")
print(f"  - Applied Transforms: {', '.join(full_sample.metadata.extra.get('applied_transforms', []))}")
print(f"  - Final Surviving BBoxes: {len(full_boxes)}")

print("=" * 80)
print("Successfully generated all 10 high-fidelity historical visualizations!")
print("=" * 80)
