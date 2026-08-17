"""
Stage 09 — Authoritative Historical Document Transformation Visualizer.
Features:
- Real Historical Backgrounds with Subtractive Ink-Fiber Absorption Blending
- Syllable/Akshara Grammar Engine (Zero standalone/orphaned dependent vowels or modifiers)
- Multi-colored authentic non-black historical inks (Iron-gall, Sepia, Walnut, Charcoal, Rubricated red)
- Multi-font switching and font size variations across lines
- Strong, expressive geometric transformations (Rotation, Perspective, Curved Baseline, Elastic, Page Curvature)
- Unique, high-contrast, deterministic color palette for EVERY unique Chakma character class ID
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
from generator.charset_engine import CharsetEngine
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

charset = CharsetEngine()


def get_class_color(class_id: int) -> tuple[int, int, int, int]:
    """
    Generate a distinct, deterministic, vibrant RGB color for each of the 71 Chakma classes.
    Uses golden ratio hue sampling around the 360-degree color wheel for maximum contrast between classes.
    """
    if class_id < 0:
        return (120, 120, 120, 240)
    # Golden angle in degrees ~ 137.508°
    hue = (class_id * 137.508) % 360.0
    sat = 0.88 + (class_id % 3) * 0.04
    val = 0.90 + (class_id % 2) * 0.08

    # HSV to RGB conversion
    c = val * sat
    x = c * (1.0 - abs((hue / 60.0) % 2 - 1.0))
    m = val - c

    if 0 <= hue < 60:
        r, g, b = c, x, 0
    elif 60 <= hue < 120:
        r, g, b = x, c, 0
    elif 120 <= hue < 180:
        r, g, b = 0, c, x
    elif 180 <= hue < 240:
        r, g, b = 0, x, c
    elif 240 <= hue < 300:
        r, g, b = x, 0, c
    else:
        r, g, b = c, 0, x

    return (int((r + m) * 255), int((g + m) * 255), int((b + m) * 255), 240)


def draw_bboxes_with_unique_class_colors(image: Image.Image, bboxes: list[BBox]) -> Image.Image:
    """Draw bounding boxes where EVERY unique class ID receives its own distinct color and badge."""
    vis = image.copy().convert("RGBA")
    overlay = Image.new("RGBA", vis.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    for box in bboxes:
        c = get_class_color(box.class_id)
        # Box rectangle
        draw.rectangle([box.x_min, box.y_min, box.x_max, box.y_max], outline=c, width=2)
        # Class tag badge with ID
        tag_w = 16
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
# (Composited on real Parchment background with physical ink-fiber absorption, varied fonts, sizes, and non-black historical ink colors)
base_sample = gen.generate(
    use_real_background=True,
    background_category="parchment",
    random_font_per_line=True,
    random_size_jitter=5.0,
    baseline_jitter=2.5,
    ink_palettes=[
        (46, 32, 22, 245),   # Iron-gall brown
        (36, 26, 18, 250),   # Dark walnut
        (28, 28, 32, 255),   # Charcoal carbon
        (62, 48, 36, 235),   # Aged sepia
        (135, 32, 25, 245),  # Rubricated red line/title
    ],
    seed=101,
)

orig_img = base_sample.image
orig_boxes = [c.bbox for c in base_sample.characters]

print(f"Base Manuscript Canvas: {orig_img.width}x{orig_img.height} px | Background: {base_sample.metadata.extra.get('background')}")
print(f"Total Lines: {base_sample.metadata.total_lines} | Total Characters: {len(orig_boxes)}")
print(f"Unique Character Classes in Sample: {len(set(c.class_id for c in base_sample.characters))}")

# Save 01 Base Manuscript (Clean & with BBoxes)
orig_img.save(debug_out_dir / "01_base_manuscript_clean.png")
orig_img.save(artifact_out_dir / "01_base_manuscript_clean.png")
orig_vis = draw_bboxes_with_unique_class_colors(orig_img, orig_boxes)
orig_vis.save(debug_out_dir / "01_base_manuscript_with_boxes.png")
orig_vis.save(artifact_out_dir / "01_base_manuscript_with_boxes.png")
print("[1/10] Saved Base Manuscript (Real Parchment + Multi-font/Multi-color Ink) -> 01_base_manuscript_with_boxes.png")

# 2. Strong Handwritten Curved Baseline (Wavy line undulation)
wavy_img, wavy_boxes, wavy_params = apply_curved_baseline(orig_img, orig_boxes, amplitude=14.0, frequency=2.0, seed=42)
wavy_vis = draw_bboxes_with_unique_class_colors(wavy_img, wavy_boxes)
wavy_vis.save(debug_out_dir / "02_curved_baseline_with_boxes.png")
wavy_vis.save(artifact_out_dir / "02_curved_baseline_with_boxes.png")
print("\n[2/10] CURVED BASELINE (Handwritten Waviness):")
print(f"  - Parameters: Amplitude = {wavy_params['amplitude']}px, Frequency = {wavy_params['frequency']}, Phase = {wavy_params['phase_offset']}")
print(f"  - BBoxes Valid: {len(wavy_boxes)}/{len(orig_boxes)}")

# 3. Strong Rotation & Skew (+7.5 deg)
rot_img, rot_boxes, rot_params = apply_rotation(orig_img, orig_boxes, angle_deg=7.5)
rot_vis = draw_bboxes_with_unique_class_colors(rot_img, rot_boxes)
rot_vis.save(debug_out_dir / "03_rotation_with_boxes.png")
rot_vis.save(artifact_out_dir / "03_rotation_with_boxes.png")
print("\n[3/10] ROTATION & SKEW (+7.5 deg):")
print(f"  - Affine Matrix: {rot_params['matrix'][0]}")
print(f"  - BBoxes Valid: {len(rot_boxes)}/{len(orig_boxes)}")

# 4. Strong 3D Perspective Warp (Slanted camera angle)
persp_img, persp_boxes, persp_params = apply_perspective(orig_img, orig_boxes, scale=0.075, seed=42)
persp_vis = draw_bboxes_with_unique_class_colors(persp_img, persp_boxes)
persp_vis.save(debug_out_dir / "04_perspective_with_boxes.png")
persp_vis.save(artifact_out_dir / "04_perspective_with_boxes.png")
print("\n[4/10] 3D PERSPECTIVE WARP (scale=0.075):")
print(f"  - Homography Matrix:\n    {persp_params['homography_matrix'][0]}\n    {persp_params['homography_matrix'][1]}\n    {persp_params['homography_matrix'][2]}")
print(f"  - BBoxes Valid: {len(persp_boxes)}/{len(orig_boxes)}")

# 5. Strong Elastic Mesh Wrinkling (Paper fold deformation)
elast_img, elast_boxes, elast_params = apply_elastic(orig_img, orig_boxes, alpha=38.0, sigma=7.0, seed=42)
elast_vis = draw_bboxes_with_unique_class_colors(elast_img, elast_boxes)
elast_vis.save(debug_out_dir / "05_elastic_with_boxes.png")
elast_vis.save(artifact_out_dir / "05_elastic_with_boxes.png")
print("\n[5/10] ELASTIC MESH WRINKLING (alpha=38.0):")
print(f"  - Parameters: alpha = {elast_params['alpha']}, sigma = {elast_params['sigma']}")
print(f"  - BBoxes Valid: {len(elast_boxes)}/{len(orig_boxes)}")

# 6. Strong Book Spine Page Curvature (3D cylindrical roll)
curv_img, curv_boxes, curv_params = apply_curvature(orig_img, orig_boxes, amplitude=28.0, frequency=1.0)
curv_vis = draw_bboxes_with_unique_class_colors(curv_img, curv_boxes)
curv_vis.save(debug_out_dir / "06_page_curvature_with_boxes.png")
curv_vis.save(artifact_out_dir / "06_page_curvature_with_boxes.png")
print("\n[6/10] BOOK SPINE PAGE CURVATURE (amplitude=28.0px):")
print(f"  - Function: y'(x) = y + {curv_params['amplitude']} * sin({curv_params['frequency']} * pi * x / W)")
print(f"  - BBoxes Valid: {len(curv_boxes)}/{len(orig_boxes)}")

# 7. Strong Backside Ink Bleed-Through Ghosting
bleed_img = apply_bleedthrough(orig_img, intensity=0.35, blur_radius=4.0, seed=42)
bleed_vis = draw_bboxes_with_unique_class_colors(bleed_img, orig_boxes)
bleed_vis.save(debug_out_dir / "07_bleedthrough_with_boxes.png")
bleed_vis.save(artifact_out_dir / "07_bleedthrough_with_boxes.png")
print("\n[7/10] INK BLEED-THROUGH GHOSTING (intensity=0.35):")
print("  - Verso page text shadow clearly visible through translucent parchment.")

# 8. Historical Ink Fading & Color Variation
ink_fade_img = apply_ink_variation(orig_img, fade_ratio=0.45, density_jitter=0.25, seed=42)
ink_fade_vis = draw_bboxes_with_unique_class_colors(ink_fade_img, orig_boxes)
ink_fade_vis.save(debug_out_dir / "08_ink_fading_with_boxes.png")
ink_fade_vis.save(artifact_out_dir / "08_ink_fading_with_boxes.png")
print("\n[8/10] INK FADING & DENSITY VARIATION:")
print("  - Simulates non-uniform nib pressure, ink depletion, and stroke fading.")

# 9. Uneven Vignette & Directional Lighting Gradients
illum_img = apply_illumination(orig_img, pattern="vignette", intensity=0.45)
illum_img = apply_noise(illum_img, noise_type="speckle", var=0.008, seed=42)
illum_vis = draw_bboxes_with_unique_class_colors(illum_img, orig_boxes)
illum_vis.save(debug_out_dir / "09_illumination_vignette_with_boxes.png")
illum_vis.save(artifact_out_dir / "09_illumination_vignette_with_boxes.png")
print("\n[9/10] UNEVEN LIGHTING & VIGNETTING:")
print("  - Radial corner darkening and paper grain speckle noise.")

# 10. Complete Integrated Historical Manuscript Sample
# (Real background + Subtractive ink blend + Multi-font + Multi-color ink + Baseline curve + 3D perspective + Elastic warp + Bleedthrough + Vignette + JPEG)
full_sample = gen.generate(
    use_real_background=True,
    background_category="manuscript",
    random_font_per_line=True,
    random_size_jitter=5.0,
    baseline_jitter=2.5,
    ink_palettes=[
        (48, 34, 24, 245),
        (36, 26, 18, 250),
        (28, 28, 32, 255),
        (62, 48, 36, 235),
    ],
    apply_transforms=True,
    seed=888,
)

full_img = full_sample.image
full_boxes = [c.bbox for c in full_sample.characters]

full_img.save(debug_out_dir / "10_full_historical_sample_clean.png")
full_img.save(artifact_out_dir / "10_full_historical_sample_clean.png")
full_vis = draw_bboxes_with_unique_class_colors(full_img, full_boxes)
full_vis.save(debug_out_dir / "10_full_historical_sample_with_boxes.png")
full_vis.save(artifact_out_dir / "10_full_historical_sample_with_boxes.png")

print("\n[10/10] COMPLETE INTEGRATED HISTORICAL MANUSCRIPT SAMPLE:")
print(f"  - Sample ID: {full_sample.metadata.sample_id}")
print(f"  - Applied Transforms: {', '.join(full_sample.metadata.extra.get('applied_transforms', []))}")
print(f"  - Final Surviving BBoxes: {len(full_boxes)}")

print("=" * 80)
print("Successfully generated all 10 high-fidelity historical visualizations with per-class unique colors!")
print("=" * 80)
