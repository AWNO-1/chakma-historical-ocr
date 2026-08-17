"""
Geometric Layout Visualizer and Verification Utility.
Demonstrates PageLayout, LineLayout, and CharacterLayout bounding boxes with ASCII wireframe
and YOLO coordinate exports without rendering text pixels.
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

from generator.layout_engine import LayoutEngine


SAMPLE_LINES = [
    "𑄟𑄚𑄪𑄌𑄴 𑄃𑄟𑄢𑄴 𑄘𑄬𑄌𑄴 𑄌𑄋𑄴𑄟 𑄞𑄌𑄴 𑄇𑄧𑄠𑄴𑅁",
    "𑄢𑄎 𑄘𑄬𑄌𑄮𑄖𑄴 𑄇𑄟𑄴 𑄉𑄧𑄢𑄬𑅁",
    "𑄃𑄟𑄢𑄴 𑄇𑄨𑄖𑄛𑄴 𑄖𑄧𑄣𑄬 𑄃𑄊𑄬𑅁",
    "𑄅𑄉𑄮 𑄟𑄚𑄪𑄌𑄴 𑄉𑄌𑄮𑄢𑄴 𑄖𑄧𑄣𑄬 𑄝𑄧𑄠𑄴𑅁",
]


def render_ascii_layout_wireframe(layout, grid_cols=60, grid_rows=24):
    """
    Render pure geometric 2D ASCII wireframe of the canvas showing page bounds,
    margins, and character boxes.
    """
    grid = [["." for _ in range(grid_cols)] for _ in range(grid_rows)]

    # Draw page boundary border
    for c in range(grid_cols):
        grid[0][c] = "-"
        grid[grid_rows - 1][c] = "-"
    for r in range(grid_rows):
        grid[r][0] = "|"
        grid[r][grid_cols - 1] = "|"
    grid[0][0] = "+"
    grid[0][grid_cols - 1] = "+"
    grid[grid_rows - 1][0] = "+"
    grid[grid_rows - 1][grid_cols - 1] = "+"

    scale_x = grid_cols / layout.width
    scale_y = grid_rows / layout.height

    # Mark character bounding boxes
    for char_box in layout.get_all_character_boxes():
        c_min = int(char_box.x_min * scale_x)
        c_max = int(char_box.x_max * scale_x)
        r_min = int(char_box.y_min * scale_y)
        r_max = int(char_box.y_max * scale_y)

        c_min = max(1, min(grid_cols - 2, c_min))
        c_max = max(1, min(grid_cols - 2, c_max))
        r_min = max(1, min(grid_rows - 2, r_min))
        r_max = max(1, min(grid_rows - 2, r_max))

        for r in range(r_min, r_max + 1):
            for c in range(c_min, c_max + 1):
                grid[r][c] = "#"

    return "\n".join("".join(row) for row in grid)


def demo():
    print("=" * 75)
    print("       CHAKMA LAYOUT & CHARACTER GEOMETRY ENGINE - DEMONSTRATION   ")
    print("=" * 75)

    engine = LayoutEngine(seed=42)
    layout = engine.generate_page_layout(SAMPLE_LINES, seed=42)
    val_report = engine.validate_layout(layout)

    print(f"\n[1] PAGE SPECIFICATION:")
    print(f"  * Canvas Dimensions : {layout.width} x {layout.height} px")
    print(f"  * Margins (T/B/L/R) : Top={layout.margin_top}px, Bottom={layout.margin_bottom}px, Left={layout.margin_left}px, Right={layout.margin_right}px")
    print(f"  * Total Lines       : {layout.total_lines}")
    print(f"  * Total Characters  : {layout.total_characters}")
    print(f"  * Layout Validation : {'[PASSED]' if val_report['is_valid'] else '[FAILED]'}")

    print(f"\n[2] LINE-LEVEL SPATIAL BOUNDS:")
    for line in layout.lines:
        print(f"  * Line {line.line_id}: x=[{line.x_min:.1f} .. {line.x_max:.1f}], y=[{line.y_min:.1f} .. {line.y_max:.1f}] | Chars: {len(line.characters):2d} | Words: {line.word_count}")

    print(f"\n[3] FIRST 8 CHARACTER GEOMETRY BOXES & YOLO COORDINATES:")
    all_boxes = layout.get_all_character_boxes()
    for b in all_boxes[:8]:
        cls_id, cx, cy, nw, nh = b.to_yolo(layout.width, layout.height)
        print(f"  * Order {b.reading_order:2d} | Line {b.line_id} | Word {b.word_id} | ID {b.class_id:2d} | Box: [{b.x_min:6.1f}, {b.y_min:6.1f}, {b.x_max:6.1f}, {b.y_max:6.1f}] | YOLO: ({cls_id:2d}, {cx:.4f}, {cy:.4f}, {nw:.4f}, {nh:.4f})")

    print(f"\n[4] GEOMETRIC WIREFRAME VISUALIZATION (No text rendering):")
    print(f"    Legend: '+' '-' '|' = Canvas Boundary, '.' = Empty Canvas, '#' = Character Geometry BBox")
    wireframe = render_ascii_layout_wireframe(layout)
    print(wireframe)

    print("\n" + "=" * 75)


if __name__ == "__main__":
    demo()
