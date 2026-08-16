"""
Transform Engine for geometric transforms (rotations, perspective distortions, warp).
"""

from typing import List, Tuple
from PIL import Image
from utils.geometry import BBox


class TransformEngine:
    """
    Applies geometric transformations to image while simultaneously updating bounding box coordinates.
    """

    def __init__(self, config: dict = None):
        self.config = config or {}

    def apply_perspective(
        self,
        image: Image.Image,
        boxes: List[BBox],
    ) -> Tuple[Image.Image, List[BBox]]:
        """
        Apply perspective warp to image and adjust all bounding boxes.
        Skeleton implementation for Stage 01.
        """
        return image, boxes
