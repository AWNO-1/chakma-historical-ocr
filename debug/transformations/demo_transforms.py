"""
Stage 09 — Authoritative Historical Document Transformation Visualizer.
Features:
- Real Historical Backgrounds with Subtractive Ink-Fiber Absorption Blending
- Genuine Manuscript Scribe Inscription (Rubricated crimson titles, varied historical ink palettes)
- Syllable/Akshara Grammar Engine (Zero standalone/orphaned dependent vowels or modifiers)
- Multi-font switching and per-character scribe baseline micro-jitter
- DRAMATIC, HIGH-IMPACT Geometric Transformations (Rotation, Perspective, Curved Baseline, Elastic, Page Curvature)
- Unique, high-contrast, deterministic color palette for EVERY unique Chakma character class ID
"""

import sys
from pathlib import Path
import random
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import cv2

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Add project root to sys.path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from generator.charset_engine import CharsetEngine
from generator.font_engine import FontEngine
from generator.background import BackgroundLibrary
from generator.transform_engine import (
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
font_engine = FontEngine(charset_engine=charset, seed=42)
bg_lib = BackgroundLibrary(seed=42)


def get_class_color(class_id: int) -> tuple[int, int, int, int]:
    """
    Generate a distinct, deterministic, vibrant RGB color for each of the 71 Chakma classes.
    Uses golden ratio hue sampling around the 360-degree color wheel for maximum contrast between classes.
    """
    if class_id < 0:
        return (120, 120, 120, 240)
    # Golden angle in degrees ~ 137.508°
    hue = (class_id * 137.508) % 360.0
    sat = 0.90 + (class_id % 3) * 0.04
    val = 0.92 + (class_id % 2) * 0.06

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
        tag_w = 18
        tag_h = 11
        draw.rectangle([box.x_min, max(0, box.y_min - tag_h), box.x_min + tag_w, max(tag_h, box.y_min)], fill=c)

    vis = Image.alpha_composite(vis, overlay)
    return vis.convert("RGB")


def create_authentic_manuscript_sample(
    lines: list[str],
    bg_img: Image.Image,
    seed: int = 101,
) -> tuple[Image.Image, list[BBox]]:
    """
    Renders lines onto background with authentic scribe handwriting dynamics:
    - Random rubricated crimson red (#8C2018) on random words/lines
    - Body lines in varied antique historical ink palettes (Iron-gall, Dark Walnut, Aged Sepia, Charcoal)
    - Per-character micro baseline drift and size fluctuation
    - Subtractive physical ink-fiber absorption
    - Syllable repair (zero orphaned diacritics)
    """
    rng = random.Random(seed)
    w, h = bg_img.size

    ink_canvas = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(ink_canvas)

    # Distinct authentic historical ink palettes
    palettes = [
        (140, 32, 22, 245),   # Rubricated Crimson Red
        (42, 28, 18, 250),    # Iron-gall Dark Brown
        (58, 42, 28, 235),    # Walnut Brown
        (76, 58, 42, 220),    # Faded Sepia
        (30, 30, 36, 250),    # Charcoal Carbon
        (50, 36, 26, 240),    # Bistre Brown
    ]

    all_bboxes: list[BBox] = []
    supported_fonts = font_engine.get_supported_fonts()

    start_y = 80
    line_spacing = 82

    for line_idx, raw_line in enumerate(lines):
        if not raw_line.strip():
            continue

        # Enforce Brahmic syllable integrity (no orphaned dependent vowels / modifiers)
        line = charset.repair_syllables(raw_line)

        # Random line font & size
        line_font_meta = rng.choice(supported_fonts)
        base_font_size = rng.randint(30, 36)

        # Base line ink color (random historical ink)
        body_palettes = palettes[1:]  # Iron-gall, Walnut, Sepia, Charcoal, Bistre
        line_base_color = rng.choice(body_palettes)
        line_is_rubricated = (rng.random() < 0.15)  # 15% chance entire line is rubricated in red

        curr_x = 70.0 + rng.uniform(-8.0, 8.0)
        curr_y = start_y + (line_idx * line_spacing) + rng.uniform(-3.0, 3.0)

        words = line.split(" ")
        for word in words:
            if not word:
                continue

            # Random per-word rubrication (e.g. key words, numbers, or random chance)
            word_is_rubricated = line_is_rubricated or (rng.random() < 0.12)
            active_color = palettes[0] if word_is_rubricated else line_base_color

            for char in word:
                cid = charset.get_class_id(char)
                if cid is None:
                    continue

                # Scribe variation per glyph
                glyph_size = max(24, base_font_size + rng.randint(-2, 2))
                glyph_font = font_engine.get_font(line_font_meta.path, size=glyph_size)

                # Baseline drift per character
                char_y_off = rng.uniform(-2.0, 2.0)
                gx = curr_x
                gy = curr_y + char_y_off

                # Measure glyph advance
                bbox_tuple = glyph_font.getbbox(char)
                if bbox_tuple is not None:
                    gw = max(4.0, float(bbox_tuple[2] - bbox_tuple[0]))
                    gh = max(4.0, float(bbox_tuple[3] - bbox_tuple[1]))
                    bx_min = gx + bbox_tuple[0]
                    by_min = gy + bbox_tuple[1]
                else:
                    gw = float(glyph_font.getlength(char))
                    gh = float(glyph_size * 0.8)
                    bx_min = gx
                    by_min = gy

                # Draw character with slight ink density variation
                c_alpha = max(180, min(255, active_color[3] + rng.randint(-20, 10)))
                char_color = (active_color[0], active_color[1], active_color[2], c_alpha)
                draw.text((gx, gy), char, font=glyph_font, fill=char_color)

                # Bounding box
                char_box = BBox(
                    x_min=round(bx_min, 2),
                    y_min=round(by_min, 2),
                    x_max=round(bx_min + gw, 2),
                    y_max=round(by_min + gh, 2),
                    class_id=cid,
                    class_name=charset.get_character(cid),
                    confidence=1.0,
                ).clip(w, h)

                all_bboxes.append(char_box)
                curr_x += glyph_font.getlength(char) + rng.uniform(-0.5, 0.8)

            # Space advance
            curr_x += glyph_font.getlength(" ") + rng.uniform(2.0, 6.0)

    # Subtractive Ink Absorption Blending into Paper Texture Fibers
    paper_arr = np.array(bg_img.convert("RGBA")).astype(np.float32)
    ink_arr = np.array(ink_canvas).astype(np.float32)

    alpha = (ink_arr[:, :, 3] / 255.0)[:, :, np.newaxis]
    paper_gray = (cv2.cvtColor(paper_arr[:, :, :3].astype(np.uint8), cv2.COLOR_RGB2GRAY).astype(np.float32) / 255.0)[:, :, np.newaxis]

    # Ink settles deeper into darker texture crevices
    absorption = 1.0 + (1.0 - paper_gray) * 0.45
    eff_alpha = np.clip(alpha * absorption, 0.0, 1.0)

    ink_rgb = ink_arr[:, :, :3]
    paper_rgb = paper_arr[:, :, :3]

    blended_rgb = paper_rgb * (1.0 - eff_alpha * (1.0 - ink_rgb / 255.0))
    paper_arr[:, :, :3] = np.clip(blended_rgb, 0.0, 255.0)

    final_manuscript = Image.fromarray(paper_arr.astype(np.uint8), mode="RGBA").convert("RGB")
    return final_manuscript, all_bboxes


print("=" * 80)
print("STAGE 09 — AUTHORITATIVE HISTORICAL TRANSFORMATION ENGINE VISUALIZATION")
print("=" * 80)

# Load real parchment background
bg_obj = bg_lib.get_background(category="parchment", width=1024, height=1024, seed=101)
bg_img = bg_obj.image

# Sentences from corpus
sample_lines = [
    "𑄟𑄚𑄪𑄌𑄴 𑄃𑄟𑄢𑄴 𑄘𑄬𑄌𑄴 𑄌𑄋𑄴𑄟 𑄞𑄌𑄴 𑄇𑄧𑄠𑄴𑅁",
    "𑄢𑄎 𑄘𑄬𑄌𑄮𑄖𑄴 𑄇𑄟𑄴 𑄉𑄧𑄢𑄬𑅁",
    "𑄃𑄟𑄢𑄴 𑄇𑄨𑄖𑄛𑄴 𑄖𑄧𑄣𑄬 𑄃𑄊𑄬𑅁",
    "𑄅𑄉𑄮 𑄟𑄚𑄪𑄌𑄴 𑄉𑄌𑄮𑄢𑄴 𑄖𑄧𑄣𑄬 𑄝𑄧𑄠𑄴𑅁",
    "𑄌𑄋𑄴𑄟 𑄥𑄋𑄴𑄇𑄳𑄢𑄨𑄖𑄨 𑄃𑄢𑄴 𑄞𑄌𑄴 𑄃𑄟𑄢𑄴 𑄉𑄧𑄢𑄧𑄛𑄴𑅂",
    "𑄛𑄮𑄠𑄴 𑄛𑄧𑄢𑄨 𑄎𑄨𑄚𑄨𑄌𑄴 𑄥𑄨𑄊𑄮𑄚𑄴 𑄉𑄧𑄢𑄮𑅁",
    "𑄘𑄨𑄚𑄴 𑄢𑄭𑄖𑄴 𑄇𑄟𑄴 𑄉𑄧𑄢𑄨 𑄟𑄚𑄪𑄌𑄴 𑄝𑄌𑄬𑅁",
    "𑄖𑄢𑄴 𑄇𑄗 𑄥𑄪𑄚𑄨 𑄟𑄧𑄚𑄴 𑄈𑄪𑄌𑄨 𑄦𑄧𑄠𑄴𑅁",
    "𑄃𑄬 𑄇𑄨𑄖𑄛𑄴𑄈𑄚𑄴 𑄇𑄧𑄢𑄴 𑄃𑄊𑄬𑅃",
    "𑄷𑄸𑄹 𑄝𑄧𑄏𑄧𑄢𑄴 𑄃𑄉𑄬 𑄢𑄎 𑄃𑄬𑄟𑄳𑄦𑄚𑄴 𑄣𑄬𑄈𑄨 𑄉𑄨𑄠𑄬𑅂",
]

# 1. Base Authentic Historical Manuscript
orig_img, orig_boxes = create_authentic_manuscript_sample(sample_lines, bg_img, seed=101)

print(f"Base Manuscript Canvas: {orig_img.width}x{orig_img.height} px | Background: parchment")
print(f"Total Lines: {len(sample_lines)} | Total Characters: {len(orig_boxes)}")
print(f"Unique Character Classes in Sample: {len(set(b.class_id for b in orig_boxes))}")

# Save 01 Base Manuscript (Clean & with BBoxes)
orig_img.save(debug_out_dir / "01_base_manuscript_clean.png")
orig_img.save(artifact_out_dir / "01_base_manuscript_clean.png")
orig_vis = draw_bboxes_with_unique_class_colors(orig_img, orig_boxes)
orig_vis.save(debug_out_dir / "01_base_manuscript_with_boxes.png")
orig_vis.save(artifact_out_dir / "01_base_manuscript_with_boxes.png")
print("[1/10] Saved Base Manuscript (Real Parchment + Rubrication + Multi-color Ink) -> 01_base_manuscript_with_boxes.png")

# 2. Dramatic Handwritten Curved Baseline (Amplitude = 22px)
wavy_img, wavy_boxes, wavy_params = apply_curved_baseline(orig_img, orig_boxes, amplitude=22.0, frequency=2.0, seed=42)
wavy_vis = draw_bboxes_with_unique_class_colors(wavy_img, wavy_boxes)
wavy_vis.save(debug_out_dir / "02_curved_baseline_with_boxes.png")
wavy_vis.save(artifact_out_dir / "02_curved_baseline_with_boxes.png")
print("\n[2/10] DRAMATIC CURVED BASELINE:")
print(f"  - Amplitude = 22.0px, Frequency = 2.0")
print(f"  - BBoxes Valid: {len(wavy_boxes)}/{len(orig_boxes)}")

# 3. Dramatic Document Rotation & Skew (-12.5 deg)
rot_img, rot_boxes, rot_params = apply_rotation(orig_img, orig_boxes, angle_deg=-12.5)
rot_vis = draw_bboxes_with_unique_class_colors(rot_img, rot_boxes)
rot_vis.save(debug_out_dir / "03_rotation_with_boxes.png")
rot_vis.save(artifact_out_dir / "03_rotation_with_boxes.png")
print("\n[3/10] DRAMATIC ROTATION & SKEW (-12.5 deg):")
print(f"  - BBoxes Valid: {len(rot_boxes)}/{len(orig_boxes)}")

# 4. Dramatic 3D Perspective Warp (scale = 0.12)
persp_img, persp_boxes, persp_params = apply_perspective(orig_img, orig_boxes, scale=0.12, seed=42)
persp_vis = draw_bboxes_with_unique_class_colors(persp_img, persp_boxes)
persp_vis.save(debug_out_dir / "04_perspective_with_boxes.png")
persp_vis.save(artifact_out_dir / "04_perspective_with_boxes.png")
print("\n[4/10] DRAMATIC 3D PERSPECTIVE WARP (scale=0.12):")
print(f"  - BBoxes Valid: {len(persp_boxes)}/{len(orig_boxes)}")

# 5. Dramatic Elastic Mesh Wrinkling & Paper Folds (alpha = 52.0)
elast_img, elast_boxes, elast_params = apply_elastic(orig_img, orig_boxes, alpha=52.0, sigma=8.0, seed=42)
elast_vis = draw_bboxes_with_unique_class_colors(elast_img, elast_boxes)
elast_vis.save(debug_out_dir / "05_elastic_with_boxes.png")
elast_vis.save(artifact_out_dir / "05_elastic_with_boxes.png")
print("\n[5/10] DRAMATIC ELASTIC MESH WRINKLING (alpha=52.0):")
print(f"  - BBoxes Valid: {len(elast_boxes)}/{len(orig_boxes)}")

# 6. Dramatic Book Spine Page Curvature (amplitude = 42.0px)
curv_img, curv_boxes, curv_params = apply_curvature(orig_img, orig_boxes, amplitude=42.0, frequency=1.0)
curv_vis = draw_bboxes_with_unique_class_colors(curv_img, curv_boxes)
curv_vis.save(debug_out_dir / "06_page_curvature_with_boxes.png")
curv_vis.save(artifact_out_dir / "06_page_curvature_with_boxes.png")
print("\n[6/10] DRAMATIC BOOK SPINE PAGE CURVATURE (amplitude=42.0px):")
print(f"  - BBoxes Valid: {len(curv_boxes)}/{len(orig_boxes)}")

# 7. Dramatic Backside Ink Bleed-Through Ghosting (intensity = 0.48)
bleed_img = apply_bleedthrough(orig_img, intensity=0.48, blur_radius=4.5, seed=42)
bleed_vis = draw_bboxes_with_unique_class_colors(bleed_img, orig_boxes)
bleed_vis.save(debug_out_dir / "07_bleedthrough_with_boxes.png")
bleed_vis.save(artifact_out_dir / "07_bleedthrough_with_boxes.png")
print("\n[7/10] DRAMATIC INK BLEED-THROUGH GHOSTING (intensity=0.48):")

# 8. Dramatic Historical Ink Fading & Color Variation (fade = 0.55)
ink_fade_img = apply_ink_variation(orig_img, fade_ratio=0.55, density_jitter=0.35, seed=42)
ink_fade_vis = draw_bboxes_with_unique_class_colors(ink_fade_img, orig_boxes)
ink_fade_vis.save(debug_out_dir / "08_ink_fading_with_boxes.png")
ink_fade_vis.save(artifact_out_dir / "08_ink_fading_with_boxes.png")
print("\n[8/10] DRAMATIC INK FADING & DENSITY VARIATION (fade_ratio=0.55):")

# 9. Dramatic Uneven Vignette & Directional Lighting Gradients (intensity = 0.60)
illum_img = apply_illumination(orig_img, pattern="vignette", intensity=0.60)
illum_img = apply_noise(illum_img, noise_type="speckle", var=0.012, seed=42)
illum_vis = draw_bboxes_with_unique_class_colors(illum_img, orig_boxes)
illum_vis.save(debug_out_dir / "09_illumination_vignette_with_boxes.png")
illum_vis.save(artifact_out_dir / "09_illumination_vignette_with_boxes.png")
print("\n[9/10] DRAMATIC UNEVEN LIGHTING & VIGNETTING (intensity=0.60):")

# 10. Complete Integrated Historical Manuscript Sample
# (Real background + Rubrication + Subtractive ink blend + Wavy baseline + 3D perspective + Elastic warp + Bleedthrough + Vignette + JPEG)
full_img, full_boxes, _ = apply_curved_baseline(orig_img, orig_boxes, amplitude=16.0, frequency=2.0, seed=777)
full_img, full_boxes, _ = apply_perspective(full_img, full_boxes, scale=0.08, seed=777)
full_img, full_boxes, _ = apply_elastic(full_img, full_boxes, alpha=35.0, sigma=7.0, seed=777)
full_img = apply_bleedthrough(full_img, intensity=0.38, blur_radius=3.5, seed=777)
full_img = apply_illumination(full_img, pattern="vignette", intensity=0.45)
full_img = apply_ink_variation(full_img, fade_ratio=0.35, density_jitter=0.25, seed=777)
full_img = apply_noise(full_img, noise_type="gaussian", var=0.005, seed=777)
full_img = apply_compression_artifacts(full_img, quality=55)

full_img.save(debug_out_dir / "10_full_historical_sample_clean.png")
full_img.save(artifact_out_dir / "10_full_historical_sample_clean.png")
full_vis = draw_bboxes_with_unique_class_colors(full_img, full_boxes)
full_vis.save(debug_out_dir / "10_full_historical_sample_with_boxes.png")
full_vis.save(artifact_out_dir / "10_full_historical_sample_with_boxes.png")

print("\n[10/10] COMPLETE INTEGRATED HISTORICAL MANUSCRIPT SAMPLE:")
print(f"  - Final Surviving BBoxes: {len(full_boxes)}")

print("=" * 80)
print("Successfully generated all 10 high-fidelity historical visualizations!")
print("=" * 80)
