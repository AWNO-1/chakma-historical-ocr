"""
Generate and Export 10 Synthetic Samples for Stage 07 Verification and Visualization.
"""

import sys
from pathlib import Path
from PIL import Image, ImageDraw

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Add project root to sys.path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from generator.api import SyntheticGenerator

artifact_dir = Path(r"C:\Users\ComputerWorld\.gemini\antigravity\brain\8bf7dad0-1ef0-4dac-9c64-3bf0662958a7\images\stage07")
artifact_dir.mkdir(parents=True, exist_ok=True)

gen = SyntheticGenerator(seed=42)
samples = gen.generate_batch(count=10, start_seed=42)

print("=" * 80)
print("STAGE 07 — SYNTHETIC SAMPLE GENERATION REPORT (10 SAMPLES)")
print("=" * 80)

for idx, sample in enumerate(samples, 1):
    meta = sample.metadata
    print(f"\n--- [Sample {idx}/10] ---")
    print(f"  Sample ID    : {meta.sample_id}")
    print(f"  Seed         : {meta.seed}")
    print(f"  Font         : {meta.font_name} ({meta.font_size}px)")
    print(f"  Dimensions   : {sample.width}x{sample.height} px")
    print(f"  Total Lines  : {meta.total_lines}")
    print(f"  Total Chars  : {sample.total_characters}")
    print(f"  Text Content :")
    for l_idx, line in enumerate(meta.lines_text, 1):
        print(f"    Line {l_idx}: {line}")

    # 1. Clean Canvas Image
    clean_canvas = Image.new("RGB", (sample.width, sample.height), (250, 250, 250))
    clean_canvas.paste(sample.image, (0, 0), sample.image)
    clean_path = artifact_dir / f"sample_{idx:02d}_clean.png"
    clean_canvas.save(clean_path)

    # 2. Annotated Bounding Box Image
    overlay_canvas = Image.new("RGB", (sample.width, sample.height), (250, 250, 250))
    overlay_canvas.paste(sample.image, (0, 0), sample.image)
    draw = ImageDraw.Draw(overlay_canvas)

    for char in sample.characters:
        b = char.bbox
        draw.rectangle([b.x_min, b.y_min, b.x_max, b.y_max], outline=(0, 180, 50), width=1)

    overlay_path = artifact_dir / f"sample_{idx:02d}_bboxes.png"
    overlay_canvas.save(overlay_path)

    print(f"  Saved Images : {clean_path.name} | {overlay_path.name}")

print("\n" + "=" * 80)
print(f"Successfully generated and exported all 10 samples to: {artifact_dir}")
print("=" * 80)
