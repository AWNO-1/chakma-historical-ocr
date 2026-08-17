"""
Demonstration utility for Chakma Line Renderer.
Renders sample lines across multiple fonts and font sizes, displays character bounding boxes,
and saves verification PNG assets without background or transformations.
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

from generator.line_renderer import LineRenderer
from generator.layout_engine import LayoutEngine


DEMO_SAMPLES = [
    {
        "text": "𑄟𑄚𑄪𑄌𑄴 𑄃𑄟𑄢𑄴 𑄘𑄬𑄌𑄴 𑄌𑄋𑄴𑄟 𑄞𑄌𑄴 𑄇𑄧𑄠𑄴𑅁",
        "font_name": "NotoSansChakma-Regular.ttf",
        "font_size": 36,
    },
    {
        "text": "𑄢𑄎 𑄘𑄬𑄌𑄮𑄖𑄴 𑄇𑄟𑄴 𑄉𑄧𑄢𑄬𑅁",
        "font_name": "Nirmala.ttf",
        "font_size": 32,
    },
    {
        "text": "𑄃𑄟𑄢𑄴 𑄇𑄨𑄖𑄛𑄴 𑄖𑄧𑄣𑄬 𑄃𑄊𑄬𑅁",
        "font_name": "NirmalaB.ttf",
        "font_size": 40,
    },
    {
        "text": "𑄌𑄋𑄴𑄟 𑄥𑄋𑄴𑄇𑄳𑄢𑄨𑄖𑄨 𑄃𑄢𑄴 𑄞𑄌𑄴 𑄃𑄟𑄢𑄴 𑄉𑄧𑄢𑄧𑄛𑄴𑅂",
        "font_name": "NirmalaS.ttf",
        "font_size": 28,
    },
]


def demo():
    print("=" * 80)
    print("           CHAKMA LINE RENDERER - DEMONSTRATION & VERIFICATION           ")
    print("=" * 80)

    renderer = LineRenderer(seed=42)
    output_dir = project_root / "debug" / "rendered_samples"
    output_dir.mkdir(parents=True, exist_ok=True)

    for idx, sample in enumerate(DEMO_SAMPLES):
        text = sample["text"]
        font_path = project_root / "fonts" / sample["font_name"]
        font_size = sample["font_size"]

        rendered_line = renderer.render_line(
            text=text,
            font_path=font_path,
            font_size=font_size,
            line_id=idx,
            padding=15,
        )

        out_path = output_dir / f"line_sample_{idx+1}_{sample['font_name'].split('.')[0]}_{font_size}px.png"
        rendered_line.image.save(out_path)

        print(f"\n[SAMPLE {idx+1}]")
        print(f"  * Text String       : {text}")
        print(f"  * Typography        : Font={sample['font_name']} | Size={font_size}px")
        print(f"  * Line Canvas Size  : {rendered_line.width} x {rendered_line.height} px (Padding=15px)")
        print(f"  * Total Characters  : {len(rendered_line.characters)}")
        print(f"  * Saved Asset       : {out_path.relative_to(project_root)}")

        print(f"  * Character Bounding Boxes (First 5):")
        for c in rendered_line.characters[:5]:
            bbox = c.local_bbox
            print(f"    - Order {c.reading_order:2d} | Word {c.word_id} | ID {c.class_id:2d} ('{c.character}') -> Box: [{bbox.x_min:5.1f}, {bbox.y_min:5.1f}, {bbox.x_max:5.1f}, {bbox.y_max:5.1f}] | Size: {bbox.width:4.1f}x{bbox.height:4.1f}px")

    # Multiline page rendering demo
    print("\n" + "-" * 80)
    print("[PAGE-LEVEL RENDERING VERIFICATION]")
    layout_engine = LayoutEngine(seed=42)
    lines_text = [s["text"] for s in DEMO_SAMPLES]
    page_layout = layout_engine.generate_page_layout(lines_text, seed=42)
    page_render = renderer.render_page_lines(page_layout)

    page_out_path = output_dir / "page_canvas_render_sample.png"
    page_render.image.save(page_out_path)
    print(f"  * Page Canvas Dimensions : {page_render.width} x {page_render.height} px")
    print(f"  * Total Page Lines       : {page_render.total_lines}")
    print(f"  * Total Page Characters  : {page_render.total_characters}")
    print(f"  * Saved Page Asset       : {page_out_path.relative_to(project_root)}")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    demo()
