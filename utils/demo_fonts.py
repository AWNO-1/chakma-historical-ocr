"""
Demonstration and inspection script for Chakma Font Engine.
Lists all discovered fonts, accepted fonts, rejected fonts, rejection reasons, and glyph coverage.
"""

import sys
from pathlib import Path

# Configure UTF-8 encoding on Windows console
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

# Add project root to sys.path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from generator.font_engine import FontEngine


def demo():
    print("=" * 75)
    print("         CHAKMA FONT ENGINE - DISCOVERY & VALIDATION REPORT        ")
    print("=" * 75)

    engine = FontEngine(font_dir="fonts", seed=42)

    all_fonts = engine.get_all_fonts_metadata()
    supported = engine.get_supported_fonts()
    rejected = engine.get_rejected_fonts()

    print(f"\n[1] FONT SCAN SUMMARY:")
    print(f"  * Font Directory          : {engine.font_dir}")
    print(f"  * Total Discovered Files  : {len(all_fonts)}")
    print(f"  * Accepted Supporting     : {len(supported)}")
    print(f"  * Rejected / Non-Supporting: {len(rejected)}")
    print(f"  * Min Coverage Threshold  : {engine.min_coverage_threshold * 100:.1f}%")
    print(f"  * Font Size Range         : {engine.font_size_min}px .. {engine.font_size_max}px (Default: {engine.default_font_size}px)")

    print(f"\n[2] ACCEPTED FONTS (Passes >= {engine.min_coverage_threshold * 100:.1f}% Chakma Coverage):")
    for i, f in enumerate(supported, 1):
        print(f"  {i}. Name: {f.name:<25} Format: {f.format:<5} Size: {f.file_size_bytes/1024:.1f} KB")
        print(f"     - Chakma Coverage: {f.coverage_percentage:.2f}% ({f.supported_classes_count}/{engine.charset_engine.total_classes} classes)")
        print(f"     - Total Glyphs in Font: {f.total_cmap_glyphs}")
        if f.missing_classes_count > 0:
            missing_names = [engine.charset_engine.get_class_by_id(cid).name for cid in f.missing_classes[:3]]
            print(f"     - Missing classes ({f.missing_classes_count}): {', '.join(missing_names)} ...")
        else:
            print(f"     - Missing classes: None (100% Full Coverage)")

    if rejected:
        print(f"\n[3] REJECTED FONTS (Fails Validation):")
        for i, f in enumerate(rejected, 1):
            print(f"  {i}. Name: {f.name:<25} Format: {f.format:<5}")
            print(f"     - Chakma Coverage: {f.coverage_percentage:.2f}% ({f.supported_classes_count}/{engine.charset_engine.total_classes} classes)")
            print(f"     - Reason for Rejection: {f.rejection_reason}")

    print(f"\n[4] DETERMINISTIC FONT SAMPLING TEST (Seed=42):")
    sample_font = engine.get_random_font(seed=42)
    print(f"  * Sampled Font: {sample_font.name} ({sample_font.format})")
    print(f"  * Testing glyph check for '𑄇' (KAA, ID 7): {engine.supports_character(sample_font, '𑄇')}")
    print(f"  * Testing glyph check for '𑄃' (AA, ID 3) : {engine.supports_character(sample_font, '𑄃')}")
    print(f"  * Testing glyph check for '𑄶' (0, ID 53)  : {engine.supports_character(sample_font, '𑄶')}")

    print("\n" + "=" * 75)


if __name__ == "__main__":
    demo()
