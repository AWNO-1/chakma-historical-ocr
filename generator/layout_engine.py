"""
Layout Engine for manuscript page structure and line/character coordinate placement.
"""

from dataclasses import dataclass
from typing import List, Tuple
from utils.geometry import BBox


@dataclass
class LayoutConfig:
    canvas_width: int = 1024
    canvas_height: int = 1024
    margin_top: int = 60
    margin_bottom: int = 60
    margin_left: int = 60
    margin_right: int = 60
    line_spacing: int = 40


class LayoutEngine:
    """
    Computes spatial placement for text lines and bounding boxes across the page canvas.
    """

    def __init__(self, config: LayoutConfig = LayoutConfig()):
        self.config = config

    def calculate_line_positions(self, num_lines: int) -> List[Tuple[int, int]]:
        """
        Compute (x, y) baseline positions for lines on canvas.
        """
        positions = []
        current_y = self.config.margin_top
        for _ in range(num_lines):
            positions.append((self.config.margin_left, current_y))
            current_y += self.config.line_spacing
        return positions
