"""
Stage 08 Historical Backgrounds Inspector and Visualizer.
Scans and displays asset statistics, categories, sample dimensions, invalid files,
and exports representative background crops for inspection.
"""

import sys
from pathlib import Path
from PIL import Image

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Add project root to sys.path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from generator.background import BackgroundLibrary

debug_out_dir = Path("debug/backgrounds")
debug_out_dir.mkdir(parents=True, exist_ok=True)

lib = BackgroundLibrary(backgrounds_dir="data/backgrounds", seed=42)
stats = lib.get_stats()
invalid_files = lib.get_invalid_files()

print("=" * 80)
print("STAGE 08 — HISTORICAL BACKGROUND ASSET LIBRARY REPORT")
print("=" * 80)
print(f"Total Background Images : {stats['total_images']}")
print(f"Total Categories Scanned: {stats['total_categories']}")
print(f"Active Categories       : {', '.join(stats['active_categories'])}")
print(f"Invalid / Corrupt Files : {stats['invalid_files_count']}")
print("-" * 80)
print("CATEGORY DISTRIBUTION:")
for cat, count in stats["category_counts"].items():
    print(f"  - {cat:15s}: {count:3d} images")

print("-" * 80)
print("REPRESENTATIVE SAMPLES PER CATEGORY:")

for cat in stats["active_categories"]:
    cat_paths = lib.categories[cat]
    print(f"\n[{cat.upper()}] ({len(cat_paths)} images)")
    for idx, p in enumerate(cat_paths[:3], 1):
        with Image.open(p) as img:
            w, h = img.size
            fmt = img.format
            sz_kb = p.stat().st_size / 1024
        print(f"  {idx}. {p.name:50s} | {w:4d}x{h:<4d} px | {fmt:4s} | {sz_kb:6.1f} KB")

    # Sample a 1024x1024 crop for this category
    loaded = lib.get_background(category=cat, width=1024, height=1024, seed=42 + len(cat))
    out_name = f"sample_bg_{cat}_1024x1024.png"
    loaded.image.save(debug_out_dir / out_name)
    print(f"  -> Exported 1024x1024 representative crop to: {out_name}")

if invalid_files:
    print("-" * 80)
    print("INVALID FILES REPORT:")
    for inv in invalid_files:
        print(f"  - Path: {inv['path']}")
        print(f"    Error: {inv['error_message']}")
else:
    print("-" * 80)
    print("INVALID FILES REPORT: Zero corrupt or unreadable files found. All images validated successfully.")

print("=" * 80)
