"""
Authoritative Historical Document Transformation Engine for Chakma Historical OCR.
Simulates geometric distortions, perspective shifts, mesh warps, and page curvature
while rigorously computing synchronous coordinate transformations for Character Bounding Boxes.
"""

import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

from dataclasses import asdict, dataclass, field
import math
from pathlib import Path
import random
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
import numpy as np
from PIL import Image
import cv2

from generator.augmentations import (
    AugmentationEngine,
    apply_blur,
    apply_noise,
    apply_ink_variation,
    apply_illumination,
    apply_bleedthrough,
    apply_compression_artifacts,
)
from utils.file_utils import load_yaml, resolve_path
from utils.geometry import BBox
from utils.logging_utils import setup_logger

logger = setup_logger("transform_engine")


@dataclass
class GeometricTransformConfig:
    """Configuration and probabilities for geometric transformation stages."""
    enabled: bool = True
    rotation_prob: float = 0.5
    rotation_range_deg: Tuple[float, float] = (-7.0, 7.0)
    translation_prob: float = 0.4
    translation_range_px: Tuple[float, float] = (-25.0, 25.0)
    perspective_prob: float = 0.45
    perspective_scale_range: Tuple[float, float] = (0.04, 0.09)
    elastic_prob: float = 0.4
    elastic_alpha_range: Tuple[float, float] = (25.0, 45.0)
    elastic_sigma_range: Tuple[float, float] = (5.0, 8.0)
    curvature_prob: float = 0.4
    curvature_amplitude_range: Tuple[float, float] = (16.0, 32.0)
    curvature_frequency_range: Tuple[float, float] = (0.8, 1.5)
    curved_baseline_prob: float = 0.45
    curved_baseline_amplitude_range: Tuple[float, float] = (6.0, 14.0)
    curved_baseline_frequency_range: Tuple[float, float] = (1.5, 3.0)
    fill_color: Tuple[int, int, int] = (245, 238, 220)


@dataclass
class TransformationResult:
    """
    Encapsulates the transformed image canvas, updated character bounding boxes,
    and ground-truth transformation parameters/matrices.
    """
    image: Image.Image
    bboxes: List[BBox]
    parameters: Dict[str, Any]
    applied_transforms: List[str]

    @property
    def total_boxes(self) -> int:
        return len(self.bboxes)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_boxes": self.total_boxes,
            "applied_transforms": self.applied_transforms,
            "parameters": self.parameters,
            "bboxes": [b.to_dict() for b in self.bboxes],
        }


def _box_to_quad_points(box: BBox) -> np.ndarray:
    """Return 4 corner vertices of bounding box: (top-left, top-right, bottom-right, bottom-left)."""
    return np.array([
        [box.x_min, box.y_min],
        [box.x_max, box.y_min],
        [box.x_max, box.y_max],
        [box.x_min, box.y_max],
    ], dtype=np.float32)


def _quad_points_to_bbox(
    points: np.ndarray,
    orig_box: BBox,
    canvas_w: int,
    canvas_h: int,
    min_area: float = 1.0,
    min_dimension: float = 1.0,
) -> Optional[BBox]:
    """
    Compute new axis-aligned BBox enclosing transformed quadrilateral vertices.
    Clamps coordinates strictly to canvas bounds and verifies non-degeneracy.
    """
    # Guard against NaNs or Infs
    if not np.all(np.isfinite(points)):
        return None

    x_min = float(np.min(points[:, 0]))
    y_min = float(np.min(points[:, 1]))
    x_max = float(np.max(points[:, 0]))
    y_max = float(np.max(points[:, 1]))

    # Strict canvas clipping
    x_min_clipped = max(0.0, min(float(canvas_w), x_min))
    y_min_clipped = max(0.0, min(float(canvas_h), y_min))
    x_max_clipped = max(0.0, min(float(canvas_w), x_max))
    y_max_clipped = max(0.0, min(float(canvas_h), y_max))

    width = x_max_clipped - x_min_clipped
    height = y_max_clipped - y_min_clipped
    area = width * height

    # Validate non-zero dimensions and minimum area
    if width < min_dimension or height < min_dimension or area < min_area:
        return None

    return BBox(
        x_min=round(x_min_clipped, 2),
        y_min=round(y_min_clipped, 2),
        x_max=round(x_max_clipped, 2),
        y_max=round(y_max_clipped, 2),
        class_id=orig_box.class_id,
        class_name=orig_box.class_name,
        confidence=orig_box.confidence,
    )


def validate_transformed_bboxes(
    bboxes: List[BBox],
    canvas_width: int,
    canvas_height: int,
) -> Dict[str, Any]:
    """
    Verify geometric integrity of transformed bounding boxes:
    - No NaN/Inf coordinates
    - Positive width and height
    - Non-zero area
    - Strict containment within canvas boundaries
    """
    errors: List[str] = []

    for idx, box in enumerate(bboxes):
        coords = [box.x_min, box.y_min, box.x_max, box.y_max]
        if any(math.isnan(c) or math.isinf(c) for c in coords):
            errors.append(f"Box {idx} contains NaN/Inf coordinates: {coords}")

        if box.x_max <= box.x_min:
            errors.append(f"Box {idx} has invalid horizontal bounds: x_min={box.x_min}, x_max={box.x_max}")

        if box.y_max <= box.y_min:
            errors.append(f"Box {idx} has invalid vertical bounds: y_min={box.y_min}, y_max={box.y_max}")

        if box.width <= 0.0 or box.height <= 0.0 or box.area <= 0.0:
            errors.append(f"Box {idx} has non-positive area or dimensions: {box.width}x{box.height}")

        if not box.is_within_bounds(canvas_width, canvas_height):
            errors.append(f"Box {idx} exceeds canvas bounds ({canvas_width}x{canvas_height}): [{box.x_min}, {box.y_min}, {box.x_max}, {box.y_max}]")

    is_valid = len(errors) == 0
    if not is_valid:
        logger.error(f"Transformed BBoxes validation FAILED ({len(errors)} errors): {errors[:5]}")

    return {
        "is_valid": is_valid,
        "total_boxes": len(bboxes),
        "errors": errors,
    }


def apply_rotation(
    image: Image.Image,
    bboxes: List[BBox],
    angle_deg: float,
    center: Optional[Tuple[float, float]] = None,
    fill_color: Tuple[int, int, int] = (245, 238, 220),
) -> Tuple[Image.Image, List[BBox], Dict[str, Any]]:
    """
    Rotate image by angle_deg and synchronously transform all character bounding boxes.
    """
    w, h = image.size
    cx = center[0] if center is not None else w / 2.0
    cy = center[1] if center is not None else h / 2.0

    # 2D affine rotation matrix
    M = cv2.getRotationMatrix2D((cx, cy), angle_deg, 1.0)

    # 1. Transform image
    img_arr = np.array(image.convert("RGB"))
    rotated_arr = cv2.warpAffine(
        img_arr,
        M,
        (w, h),
        flags=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=fill_color,
    )
    rotated_image = Image.fromarray(rotated_arr, mode="RGB")

    # 2. Transform character bounding boxes
    transformed_boxes: List[BBox] = []
    for box in bboxes:
        quad = _box_to_quad_points(box)
        # Apply affine transformation: [x', y']^T = M[:, :2] @ [x, y]^T + M[:, 2]
        rot_quad = (M[:, :2] @ quad.T).T + M[:, 2]
        new_box = _quad_points_to_bbox(rot_quad, box, w, h)
        if new_box is not None:
            transformed_boxes.append(new_box)

    params = {
        "angle_deg": round(angle_deg, 3),
        "center": (round(cx, 1), round(cy, 1)),
        "matrix": M.tolist(),
    }
    return rotated_image, transformed_boxes, params


def apply_translation(
    image: Image.Image,
    bboxes: List[BBox],
    tx: float,
    ty: float,
    fill_color: Tuple[int, int, int] = (245, 238, 220),
) -> Tuple[Image.Image, List[BBox], Dict[str, Any]]:
    """
    Translate image by (tx, ty) pixels and synchronously shift all bounding boxes.
    """
    w, h = image.size
    M = np.float32([[1.0, 0.0, tx], [0.0, 1.0, ty]])

    # 1. Transform image
    img_arr = np.array(image.convert("RGB"))
    translated_arr = cv2.warpAffine(
        img_arr,
        M,
        (w, h),
        flags=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=fill_color,
    )
    translated_image = Image.fromarray(translated_arr, mode="RGB")

    # 2. Shift bounding boxes
    transformed_boxes: List[BBox] = []
    for box in bboxes:
        shifted_box = BBox(
            x_min=box.x_min + tx,
            y_min=box.y_min + ty,
            x_max=box.x_max + tx,
            y_max=box.y_max + ty,
            class_id=box.class_id,
            class_name=box.class_name,
            confidence=box.confidence,
        ).clip(w, h)

        if shifted_box.is_valid(min_size=1.0):
            transformed_boxes.append(shifted_box)

    params = {"tx": round(tx, 2), "ty": round(ty, 2), "matrix": M.tolist()}
    return translated_image, transformed_boxes, params


def apply_perspective(
    image: Image.Image,
    bboxes: List[BBox],
    scale: float = 0.03,
    matrix: Optional[np.ndarray] = None,
    fill_color: Tuple[int, int, int] = (245, 238, 220),
    seed: Optional[int] = None,
) -> Tuple[Image.Image, List[BBox], Dict[str, Any]]:
    """
    Apply perspective projection (homography) warp and compute exact corner projections for all boxes.
    """
    w, h = image.size
    rng = np.random.default_rng(seed)

    if matrix is not None:
        H = matrix
    else:
        # Generate 4 corner displacements
        src_pts = np.float32([[0, 0], [w, 0], [w, h], [0, h]])
        max_delta = scale * min(w, h)
        deltas = rng.uniform(-max_delta, max_delta, (4, 2)).astype(np.float32)
        dst_pts = src_pts + deltas
        H = cv2.getPerspectiveTransform(src_pts, dst_pts)

    # 1. Warp image
    img_arr = np.array(image.convert("RGB"))
    warped_arr = cv2.warpPerspective(
        img_arr,
        H,
        (w, h),
        flags=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=fill_color,
    )
    warped_image = Image.fromarray(warped_arr, mode="RGB")

    # 2. Warp bounding boxes
    transformed_boxes: List[BBox] = []
    for box in bboxes:
        quad = _box_to_quad_points(box)  # (4, 2)
        # Homogeneous coordinates: [X, Y, Z]^T = H @ [x, y, 1]^T
        ones = np.ones((4, 1), dtype=np.float32)
        homo_quad = np.hstack([quad, ones])  # (4, 3)
        proj = (H @ homo_quad.T).T  # (4, 3)

        # Normalize by Z
        z = proj[:, 2:3]
        z[z == 0] = 1e-6
        warped_quad = proj[:, :2] / z

        new_box = _quad_points_to_bbox(warped_quad, box, w, h)
        if new_box is not None:
            transformed_boxes.append(new_box)

    params = {"scale": round(scale, 4), "homography_matrix": H.tolist()}
    return warped_image, transformed_boxes, params


def apply_elastic(
    image: Image.Image,
    bboxes: List[BBox],
    alpha: float = 25.0,
    sigma: float = 6.0,
    fill_color: Tuple[int, int, int] = (245, 238, 220),
    seed: Optional[int] = None,
) -> Tuple[Image.Image, List[BBox], Dict[str, Any]]:
    """
    Apply smooth elastic / mesh displacement field and map bounding boxes through the displacement field.
    """
    w, h = image.size
    rng = np.random.default_rng(seed)

    # Generate random displacement field and smooth with Gaussian filter
    k = int(math.ceil(sigma * 4)) | 1
    rand_x = rng.uniform(-1.0, 1.0, (h, w)).astype(np.float32)
    rand_y = rng.uniform(-1.0, 1.0, (h, w)).astype(np.float32)

    dx = cv2.GaussianBlur(rand_x, (k, k), sigma) * alpha
    dy = cv2.GaussianBlur(rand_y, (k, k), sigma) * alpha

    grid_y, grid_x = np.indices((h, w), dtype=np.float32)
    map_x = grid_x + dx
    map_y = grid_y + dy

    # 1. Remap image
    img_arr = np.array(image.convert("RGB"))
    warped_arr = cv2.remap(
        img_arr,
        map_x,
        map_y,
        interpolation=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=fill_color,
    )
    warped_image = Image.fromarray(warped_arr, mode="RGB")

    # 2. Transform bounding box vertices using displacement field
    transformed_boxes: List[BBox] = []
    for box in bboxes:
        quad = _box_to_quad_points(box)
        warped_quad = np.zeros_like(quad)

        for i in range(4):
            px = int(np.clip(round(quad[i, 0]), 0, w - 1))
            py = int(np.clip(round(quad[i, 1]), 0, h - 1))
            # Coordinate transformation under remap
            warped_quad[i, 0] = quad[i, 0] - dx[py, px]
            warped_quad[i, 1] = quad[i, 1] - dy[py, px]

        new_box = _quad_points_to_bbox(warped_quad, box, w, h)
        if new_box is not None:
            transformed_boxes.append(new_box)

    params = {"alpha": round(alpha, 2), "sigma": round(sigma, 2)}
    return warped_image, transformed_boxes, params


def apply_curvature(
    image: Image.Image,
    bboxes: List[BBox],
    amplitude: float = 15.0,
    frequency: float = 1.0,
    direction: str = "vertical",
    fill_color: Tuple[int, int, int] = (245, 238, 220),
) -> Tuple[Image.Image, List[BBox], Dict[str, Any]]:
    """
    Simulate historical page book-binding curvature and curved baseline.
    Applies exact mathematical sine / cylindrical warp to image and bounding boxes.
    """
    w, h = image.size
    grid_y, grid_x = np.indices((h, w), dtype=np.float32)

    if direction == "vertical":
        # Curvature along X axis affecting Y coordinates
        phase = frequency * np.pi * (grid_x / float(w))
        disp_y = (amplitude * np.sin(phase)).astype(np.float32)
        map_x = grid_x
        map_y = grid_y - disp_y
    else:
        # Curvature along Y axis affecting X coordinates
        phase = frequency * np.pi * (grid_y / float(h))
        disp_x = (amplitude * np.sin(phase)).astype(np.float32)
        map_x = grid_x - disp_x
        map_y = grid_y

    # 1. Remap image
    img_arr = np.array(image.convert("RGB"))
    warped_arr = cv2.remap(
        img_arr,
        map_x,
        map_y,
        interpolation=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=fill_color,
    )
    warped_image = Image.fromarray(warped_arr, mode="RGB")

    # 2. Transform bounding box coordinates
    transformed_boxes: List[BBox] = []
    for box in bboxes:
        quad = _box_to_quad_points(box)
        warped_quad = quad.copy()

        if direction == "vertical":
            phase_pts = frequency * np.pi * (quad[:, 0] / float(w))
            warped_quad[:, 1] += amplitude * np.sin(phase_pts)
        else:
            phase_pts = frequency * np.pi * (quad[:, 1] / float(h))
            warped_quad[:, 0] += amplitude * np.sin(phase_pts)

        new_box = _quad_points_to_bbox(warped_quad, box, w, h)
        if new_box is not None:
            transformed_boxes.append(new_box)

    params = {
        "amplitude": round(amplitude, 2),
        "frequency": round(frequency, 2),
        "direction": direction,
    }
    return warped_image, transformed_boxes, params


def apply_curved_baseline(
    image: Image.Image,
    bboxes: List[BBox],
    amplitude: float = 8.0,
    frequency: float = 2.0,
    fill_color: Tuple[int, int, int] = (245, 238, 220),
    seed: Optional[int] = None,
) -> Tuple[Image.Image, List[BBox], Dict[str, Any]]:
    """
    Simulate natural handwriting baseline drift/curvature along text lines.
    Applies multi-frequency wavy displacement along the horizontal axis and transforms BBoxes.
    """
    w, h = image.size
    rng = np.random.default_rng(seed)
    phase_offset = float(rng.uniform(0.0, 2 * np.pi))

    grid_y, grid_x = np.indices((h, w), dtype=np.float32)
    # Undulating baseline wave: dy(x)
    phase = (frequency * 2.0 * np.pi * (grid_x / float(w))) + phase_offset
    disp_y = (amplitude * np.sin(phase)).astype(np.float32)

    map_x = grid_x
    map_y = grid_y - disp_y

    # 1. Remap image
    img_arr = np.array(image.convert("RGB"))
    warped_arr = cv2.remap(
        img_arr,
        map_x,
        map_y,
        interpolation=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=fill_color,
    )
    warped_image = Image.fromarray(warped_arr, mode="RGB")

    # 2. Transform bounding box coordinates
    transformed_boxes: List[BBox] = []
    for box in bboxes:
        quad = _box_to_quad_points(box)
        warped_quad = quad.copy()
        pts_phase = (frequency * 2.0 * np.pi * (quad[:, 0] / float(w))) + phase_offset
        warped_quad[:, 1] += amplitude * np.sin(pts_phase)

        new_box = _quad_points_to_bbox(warped_quad, box, w, h)
        if new_box is not None:
            transformed_boxes.append(new_box)

    params = {
        "amplitude": round(amplitude, 2),
        "frequency": round(frequency, 2),
        "phase_offset": round(phase_offset, 3),
    }
    return warped_image, transformed_boxes, params


class TransformPipeline:
    """
    Unified authoritative Historical Document Transformation and Augmentation Pipeline.
    Applies chained geometric transformations and optical degradations while strictly
    maintaining character-level bounding box ground truth.
    """

    def __init__(
        self,
        geom_config: Optional[GeometricTransformConfig] = None,
        aug_engine: Optional[AugmentationEngine] = None,
        config_path: Optional[Union[str, Path]] = "config/synthetic.yaml",
        seed: int = 42,
    ):
        self.seed = seed
        self._rng = random.Random(seed)
        self.geom_config = geom_config or GeometricTransformConfig()
        self.aug_engine = aug_engine or AugmentationEngine(config_path=config_path, seed=seed)

        if config_path and geom_config is None:
            self._load_config(resolve_path(config_path))

    def _load_config(self, cfg_path: Path) -> None:
        """Load geometric transform settings from synthetic.yaml."""
        if cfg_path.exists():
            try:
                raw_cfg = load_yaml(cfg_path)
                aug_cfg = raw_cfg.get("augmentations", {})
                if "perspective_transform" in aug_cfg:
                    pt = aug_cfg["perspective_transform"]
                    self.geom_config.perspective_prob = float(pt.get("prob", self.geom_config.perspective_prob))
                    self.geom_config.perspective_scale_range = tuple(pt.get("scale", self.geom_config.perspective_scale_range))
            except Exception as e:
                logger.warning(f"Could not load transform configuration from {cfg_path}: {e}")

    def set_seed(self, seed: int) -> None:
        self.seed = seed
        self._rng = random.Random(seed)
        self.aug_engine.set_seed(seed)

    def apply(
        self,
        image: Image.Image,
        bboxes: List[BBox],
        seed: Optional[int] = None,
    ) -> TransformationResult:
        """
        Execute the full chain of geometric transforms followed by photometric degradations.
        """
        actual_seed = seed if seed is not None else self._rng.randint(0, 1_000_000)
        rng = random.Random(actual_seed)

        curr_img = image.copy()
        curr_boxes = [box.clip(curr_img.width, curr_img.height) for box in bboxes]
        applied: List[str] = []
        all_params: Dict[str, Any] = {"seed": actual_seed}

        w, h = curr_img.size
        fill = self.geom_config.fill_color

        # ------------------------------------------------------------------
        # 1. Geometric Transformations (Synchronous BBox adjustments)
        # ------------------------------------------------------------------
        if self.geom_config.enabled:
            # A. Rotation
            if rng.random() < self.geom_config.rotation_prob:
                angle = rng.uniform(*self.geom_config.rotation_range_deg)
                curr_img, curr_boxes, p = apply_rotation(curr_img, curr_boxes, angle, fill_color=fill)
                applied.append("rotation")
                all_params["rotation"] = p

            # B. Translation
            if rng.random() < self.geom_config.translation_prob:
                tx = rng.uniform(*self.geom_config.translation_range_px)
                ty = rng.uniform(*self.geom_config.translation_range_px)
                curr_img, curr_boxes, p = apply_translation(curr_img, curr_boxes, tx, ty, fill_color=fill)
                applied.append("translation")
                all_params["translation"] = p

            # C. Perspective Warp
            if rng.random() < self.geom_config.perspective_prob:
                scale = rng.uniform(*self.geom_config.perspective_scale_range)
                curr_img, curr_boxes, p = apply_perspective(
                    curr_img, curr_boxes, scale=scale, fill_color=fill, seed=rng.randint(0, 1_000_000)
                )
                applied.append("perspective")
                all_params["perspective"] = p

            # D. Elastic Mesh Distortion
            if rng.random() < self.geom_config.elastic_prob:
                alpha = rng.uniform(*self.geom_config.elastic_alpha_range)
                sigma = rng.uniform(*self.geom_config.elastic_sigma_range)
                curr_img, curr_boxes, p = apply_elastic(
                    curr_img, curr_boxes, alpha=alpha, sigma=sigma, fill_color=fill, seed=rng.randint(0, 1_000_000)
                )
                applied.append("elastic")
                all_params["elastic"] = p

            # E. Page Curvature
            if rng.random() < self.geom_config.curvature_prob:
                amp = rng.uniform(*self.geom_config.curvature_amplitude_range)
                freq = rng.uniform(*self.geom_config.curvature_frequency_range)
                curr_img, curr_boxes, p = apply_curvature(
                    curr_img, curr_boxes, amplitude=amp, frequency=freq, fill_color=fill
                )
                applied.append("curvature")
                all_params["curvature"] = p

            # F. Curved Baseline (Line-level waviness)
            if rng.random() < self.geom_config.curved_baseline_prob:
                amp = rng.uniform(*self.geom_config.curved_baseline_amplitude_range)
                freq = rng.uniform(*self.geom_config.curved_baseline_frequency_range)
                curr_img, curr_boxes, p = apply_curved_baseline(
                    curr_img, curr_boxes, amplitude=amp, frequency=freq, fill_color=fill, seed=rng.randint(0, 1_000_000)
                )
                applied.append("curved_baseline")
                all_params["curved_baseline"] = p

        # ------------------------------------------------------------------
        # 2. Photometric / Optical Degradations (Image canvas only)
        # ------------------------------------------------------------------
        curr_img, aug_applied, aug_params = self.aug_engine.apply(curr_img, seed=rng.randint(0, 1_000_000))
        applied.extend(aug_applied)
        all_params["augmentations"] = aug_params

        # ------------------------------------------------------------------
        # 3. Final Validation
        # ------------------------------------------------------------------
        val_report = validate_transformed_bboxes(curr_boxes, w, h)
        all_params["bbox_validation"] = val_report

        return TransformationResult(
            image=curr_img,
            bboxes=curr_boxes,
            parameters=all_params,
            applied_transforms=applied,
        )


# Backward compatibility alias
TransformEngine = TransformPipeline
