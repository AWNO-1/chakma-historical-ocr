"""
Inspect Windows Fonts directory and fonts/ for Chakma glyph support.
"""
from pathlib import Path
from fontTools.ttLib import TTFont
import unicodedata

def search_chakma_fonts():
    # Chakma code points: 0x11100 .. 0x11147
    chakma_cps = set(range(0x11100, 0x11148))

    search_dirs = [
        Path("fonts"),
        Path("C:/Windows/Fonts"),
    ]

    found_fonts = []
    print(f"Scanning for fonts supporting Chakma script (U+11100..U+1114F)...")

    for s_dir in search_dirs:
        if not s_dir.exists():
            continue
        for font_file in s_dir.glob("*.[to]tf"):
            try:
                tt = TTFont(font_file, fontNumber=0)
                cmap = tt.getBestCmap()
                if cmap:
                    supported = set(cmap.keys()) & chakma_cps
                    if len(supported) > 0:
                        print(f"Found supporting font: {font_file.name} in {s_dir} -> {len(supported)}/{len(chakma_cps)} Chakma chars")
                        found_fonts.append((font_file, len(supported)))
            except Exception as e:
                continue

    print(f"\nTotal fonts supporting Chakma found: {len(found_fonts)}")

if __name__ == "__main__":
    search_chakma_fonts()
