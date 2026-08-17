"""
Setup fonts directory with authentic Chakma fonts from system or fallback,
plus a non-supporting font (for testing rejection).
"""
import shutil
from pathlib import Path

def setup_fonts():
    fonts_dir = Path("fonts")
    fonts_dir.mkdir(exist_ok=True)

    windows_fonts = Path("C:/Windows/Fonts")
    chakma_candidates = ["Nirmala.ttf", "NirmalaB.ttf", "NirmalaS.ttf"]
    non_supporting_candidates = ["arial.ttf", "calibri.ttf"]

    copied = 0
    for f_name in chakma_candidates:
        src = windows_fonts / f_name
        dst = fonts_dir / f_name
        if src.exists():
            shutil.copy2(src, dst)
            print(f"Copied Chakma font: {f_name} -> fonts/{f_name}")
            copied += 1

    for f_name in non_supporting_candidates:
        src = windows_fonts / f_name
        dst = fonts_dir / f_name
        if src.exists():
            shutil.copy2(src, dst)
            print(f"Copied non-supporting test font: {f_name} -> fonts/{f_name}")
            break

    print(f"Font directory setup complete with {len(list(fonts_dir.glob('*.[to]tf')))} font files.")

if __name__ == "__main__":
    setup_fonts()
