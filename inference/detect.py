"""
YOLO Character Detector Inference Wrapper.
Encapsulates character bounding box detection and class classification.
"""

from pathlib import Path
from typing import List, Optional, Union
from PIL import Image
from utils.file_utils import resolve_path
from utils.geometry import BBox
from utils.logging_utils import setup_logger

logger = setup_logger("inference_detect")


class CharacterDetector:
    """
    Inference interface for the trained YOLO character detector.
    """

    def __init__(
        self,
        weights_path: Optional[Union[str, Path]] = None,
        conf_threshold: float = 0.25,
        iou_threshold: float = 0.5,
    ):
        self.weights_path = resolve_path(weights_path) if weights_path else None
        self.conf_threshold = conf_threshold
        self.iou_threshold = iou_threshold
        self.model = None
        self._load_model()

    def _load_model(self) -> None:
        """Load YOLO model weights if available."""
        if self.weights_path and self.weights_path.exists():
            logger.info(f"Loading weights from {self.weights_path}")
        else:
            logger.info("Detector initialized in skeleton mode (no weights loaded).")

    def detect(self, image: Union[Image.Image, str, Path]) -> List[BBox]:
        """
        Run character detection on input image and return list of BBox detections.
        Skeleton implementation for Stage 01.
        """
        logger.info("Detect method called (skeleton).")
        return []
