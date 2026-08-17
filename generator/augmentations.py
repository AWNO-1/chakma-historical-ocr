"""
Authoritative Historical Document Augmentation Engine for Chakma Historical OCR.
Implements realistic physical, photometric, and optical degradations:
- Gaussian, motion, and box blur
- Additive Gaussian, speckle, and salt-and-pepper noise
- Historical ink fading, intra-character stroke density jitter, and non-black color shifting (iron-gall/sepia/charcoal)
- Non-uniform lighting gradients and corner vignetting
- Backside ink bleed-through / ghosting
- JPEG compression and discrete cosine transform (DCT) blocking artifacts
"""

import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

from dataclasses import asdict, dataclass, field
import io
import math
from pathlib import Path
import random
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter, ImageOps
import cv2

from utils.file_utils import load_yaml, resolve_path
from utils.logging_utils import setup_logger

logger = setup_logger("augmentations")


@dataclass
class AugmentationConfig:
    """Configuration parameters and probabilities for photometric augmentations."""
    enabled: bool = True
    blur_prob: float = 0.5
    blur_kernel_range: Tuple[int, int] = (3, 5)
    noise_prob: float = 0.4
    noise_var_range: Tuple[float, float] = (0.002, 0.02)
    ink_fade_prob: float = 0.5
    ink_fade_range: Tuple[float, float] = (0.1, 0.35)
    ink_color_shift_prob: float = 0.6
    illumination_prob: float = 0.5
    illumination_intensity_range: Tuple[float, float] = (0.15, 0.4)
    bleedthrough_prob: float = 0.35
    bleedthrough_intensity_range: Tuple[float, float] = (0.08, 0.25)
    compression_prob: float = 0.4
    compression_quality_range: Tuple[int, int] = (45, 80)


def apply_blur(
    image: Image.Image,
    blur_type: str = "gaussian",
    kernel_size: int = 3,
    sigma: float = 1.0,
    angle_deg: float = 0.0,
) -> Image.Image:
    """
    Apply optical or motion blur to PIL Image.

    Supports:
    - 'gaussian': Standard isotropic Gaussian defocus
    - 'motion': Directional linear camera/scan motion blur
    - 'box': Defocus uniform box filter
    """
    if kernel_size <= 1:
        return image.copy()

    k = kernel_size if kernel_size % 2 == 1 else kernel_size + 1

    img_arr = np.array(image)

    if blur_type == "gaussian":
        blurred_arr = cv2.GaussianBlur(img_arr, (k, k), sigmaX=sigma, sigmaY=sigma)
    elif blur_type == "motion":
        # Generate directional linear motion kernel
        kernel = np.zeros((k, k), dtype=np.float32)
        center = k // 2
        # Line through center at specified angle
        rad = math.radians(angle_deg)
        cos_a = math.cos(rad)
        sin_a = math.sin(rad)
        for i in range(-center, center + 1):
            x = int(round(center + i * cos_a))
            y = int(round(center + i * sin_a))
            if 0 <= x < k and 0 <= y < k:
                kernel[y, x] = 1.0
        norm = np.sum(kernel)
        if norm > 0:
            kernel /= norm
        else:
            kernel[center, center] = 1.0
        blurred_arr = cv2.filter2D(img_arr, -1, kernel)
    elif blur_type == "box":
        blurred_arr = cv2.boxFilter(img_arr, -1, (k, k))
    else:
        blurred_arr = cv2.GaussianBlur(img_arr, (k, k), sigmaX=sigma)

    return Image.fromarray(blurred_arr, mode=image.mode)


def apply_noise(
    image: Image.Image,
    noise_type: str = "gaussian",
    var: float = 0.01,
    amount: float = 0.02,
    seed: Optional[int] = None,
) -> Image.Image:
    """
    Inject realistic sensor, chemical grain, or speckle noise into the image canvas.
    """
    rng = np.random.default_rng(seed)
    img_arr = np.array(image).astype(np.float32) / 255.0

    if noise_type == "gaussian":
        sigma = math.sqrt(max(1e-6, var))
        noise = rng.normal(0.0, sigma, img_arr.shape)
        noisy_arr = np.clip(img_arr + noise, 0.0, 1.0)
    elif noise_type == "speckle":
        noise = rng.normal(0.0, math.sqrt(max(1e-6, var)), img_arr.shape)
        noisy_arr = np.clip(img_arr + img_arr * noise, 0.0, 1.0)
    elif noise_type == "salt_pepper":
        noisy_arr = img_arr.copy()
        # Salt (white dust)
        num_salt = int(np.ceil(amount * img_arr.size * 0.5))
        coords = tuple(rng.integers(0, d, num_salt) for d in img_arr.shape)
        noisy_arr[coords] = 1.0
        # Pepper (dark ink specks)
        num_pepper = int(np.ceil(amount * img_arr.size * 0.5))
        coords = tuple(rng.integers(0, d, num_pepper) for d in img_arr.shape)
        noisy_arr[coords] = 0.0
    else:
        sigma = math.sqrt(max(1e-6, var))
        noise = rng.normal(0.0, sigma, img_arr.shape)
        noisy_arr = np.clip(img_arr + noise, 0.0, 1.0)

    result_uint8 = (noisy_arr * 255.0).astype(np.uint8)
    return Image.fromarray(result_uint8, mode=image.mode)


def apply_ink_variation(
    image: Image.Image,
    fade_ratio: float = 0.2,
    color_shift: Optional[Tuple[int, int, int]] = None,
    density_jitter: float = 0.15,
    seed: Optional[int] = None,
) -> Image.Image:
    """
    Simulate authentic historical ink aesthetics:
    - Non-black ink tinting: shifts deep black ink to iron-gall brown/sepia, charcoal, or walnut ink.
    - Ink fading: lightens dense strokes toward surrounding parchment tone.
    - Intra-stroke density jitter: simulates uneven ink flow and nib pressure across characters.
    """
    rng = np.random.default_rng(seed)
    img_arr = np.array(image.convert("RGB")).astype(np.float32)

    # 1. Identify dark ink regions using luminance
    luminance = 0.299 * img_arr[:, :, 0] + 0.587 * img_arr[:, :, 1] + 0.114 * img_arr[:, :, 2]
    # Ink mask: high value for dark pixels (< 120), low value for bright paper (> 180)
    ink_mask = np.clip((160.0 - luminance) / 100.0, 0.0, 1.0)[:, :, np.newaxis]

    # 2. Select historical ink palette if not explicitly provided
    if color_shift is None:
        historical_ink_palettes = [
            (42, 30, 22),   # Iron-gall brown
            (55, 42, 32),   # Aged sepia
            (32, 32, 36),   # Charcoal carbon ink
            (48, 38, 30),   # Walnut / bistre ink
            (25, 25, 28),   # Soft matte soot black
        ]
        chosen_idx = int(rng.integers(0, len(historical_ink_palettes)))
        target_ink_rgb = np.array(historical_ink_palettes[chosen_idx], dtype=np.float32)
    else:
        target_ink_rgb = np.array(color_shift, dtype=np.float32)

    # 3. Apply color shift and fading
    # Interpolate ink pixels toward historical ink tint
    tinted_arr = img_arr * (1.0 - ink_mask * 0.75) + target_ink_rgb * (ink_mask * 0.75)

    # Fade ink toward local background
    if fade_ratio > 0.0:
        tinted_arr = tinted_arr + (255.0 - tinted_arr) * (ink_mask * fade_ratio * 0.5)

    # 4. Intra-stroke non-uniform density jitter
    if density_jitter > 0.0:
        h, w = img_arr.shape[:2]
        noise_map = cv2.GaussianBlur(
            rng.uniform(-density_jitter, density_jitter, (h, w)).astype(np.float32),
            (15, 15),
            5.0,
        )[:, :, np.newaxis]
        tinted_arr = np.clip(tinted_arr + noise_map * 80.0 * ink_mask, 0.0, 255.0)

    result_uint8 = np.clip(tinted_arr, 0.0, 255.0).astype(np.uint8)
    return Image.fromarray(result_uint8, mode="RGB")


def apply_illumination(
    image: Image.Image,
    pattern: str = "vignette",
    intensity: float = 0.3,
    angle_deg: float = 45.0,
    seed: Optional[int] = None,
) -> Image.Image:
    """
    Apply uneven historical lighting gradients or corner shadow vignetting.
    """
    img_arr = np.array(image.convert("RGB")).astype(np.float32)
    h, w = img_arr.shape[:2]

    y_grid, x_grid = np.ogrid[:h, :w]

    if pattern == "vignette":
        # Radial distance from center normalized to [0, 1]
        cx, cy = w / 2.0, h / 2.0
        max_dist = math.sqrt(cx**2 + cy**2)
        dist_map = np.sqrt((x_grid - cx)**2 + (y_grid - cy)**2) / max_dist
        # Darken edges based on distance
        illum_map = 1.0 - (dist_map**1.5) * intensity
    elif pattern == "linear_gradient":
        rad = math.radians(angle_deg)
        cos_a = math.cos(rad)
        sin_a = math.sin(rad)
        # Project normalized coordinates along gradient axis
        norm_x = (x_grid / w) - 0.5
        norm_y = (y_grid / h) - 0.5
        proj = norm_x * cos_a + norm_y * sin_a
        # Scale between 1.0 - intensity and 1.0
        illum_map = 1.0 + proj * intensity
    elif pattern == "spotlight":
        rng = np.random.default_rng(seed)
        spot_cx = float(rng.uniform(0.3 * w, 0.7 * w))
        spot_cy = float(rng.uniform(0.3 * h, 0.7 * h))
        dist_map = np.sqrt((x_grid - spot_cx)**2 + (y_grid - spot_cy)**2) / (max(w, h) * 0.75)
        illum_map = 1.0 - np.clip(dist_map, 0.0, 1.0) * intensity
    else:
        illum_map = np.ones((h, w), dtype=np.float32)

    illum_map = np.clip(illum_map, 0.1, 1.5)[:, :, np.newaxis]
    result = np.clip(img_arr * illum_map, 0.0, 255.0).astype(np.uint8)
    return Image.fromarray(result, mode="RGB")


def apply_bleedthrough(
    image: Image.Image,
    backside_text_image: Optional[Image.Image] = None,
    intensity: float = 0.15,
    blur_radius: float = 3.0,
    seed: Optional[int] = None,
) -> Image.Image:
    """
    Simulate ink bleed-through from the verso (backside) of thin manuscript paper:
    Mirrors, blurs, and faintly superimposes backside text onto the recto page.
    """
    if intensity <= 0.0:
        return image.copy()

    w, h = image.size

    if backside_text_image is None:
        # Use a horizontally flipped, vertically shifted copy of the current image as backside proxy
        rng = np.random.default_rng(seed)
        backside = image.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
        shift_y = int(rng.integers(-20, 20))
        shifted = Image.new("RGB", (w, h), (255, 255, 255))
        shifted.paste(backside, (0, shift_y))
        backside_text_image = shifted
    else:
        backside_text_image = backside_text_image.resize((w, h)).transpose(Image.Transpose.FLIP_LEFT_RIGHT)

    # Convert backside to grayscale ink shadow
    back_gray = np.array(backside_text_image.convert("L")).astype(np.float32)
    # Blur the backside ink
    k = int(blur_radius * 2) + 1
    k = k if k % 2 == 1 else k + 1
    blurred_back = cv2.GaussianBlur(back_gray, (k, k), blur_radius)

    # Invert to make dark text high values
    ink_ghost = np.clip((220.0 - blurred_back) / 220.0, 0.0, 1.0)

    # Blend faint ink ghost into main image
    front_arr = np.array(image.convert("RGB")).astype(np.float32)
    ghost_tint = np.array([40.0, 32.0, 24.0], dtype=np.float32)  # Aged ghost brown

    # Darken front pixels where ghost ink appears
    ghost_factor = (ink_ghost * intensity)[:, :, np.newaxis]
    blended = front_arr * (1.0 - ghost_factor) + ghost_tint * ghost_factor

    result = np.clip(blended, 0.0, 255.0).astype(np.uint8)
    return Image.fromarray(result, mode="RGB")


def apply_compression_artifacts(image: Image.Image, quality: int = 65) -> Image.Image:
    """
    Simulate JPEG discrete cosine transform (DCT) block ringing and compression artifacts.
    """
    quality = max(10, min(quality, 95))
    buffer = io.BytesIO()
    rgb_img = image.convert("RGB")
    rgb_img.save(buffer, format="JPEG", quality=quality)
    buffer.seek(0)
    return Image.open(buffer).copy()


class AugmentationEngine:
    """
    Authoritative photometric and optical augmentation pipeline orchestrator.
    """

    def __init__(
        self,
        config: Optional[Union[AugmentationConfig, Dict[str, Any]]] = None,
        config_path: Optional[Union[str, Path]] = "config/synthetic.yaml",
        seed: int = 42,
    ):
        self.seed = seed
        self._rng = random.Random(seed)
        self.config = AugmentationConfig()

        if config is not None:
            if isinstance(config, AugmentationConfig):
                self.config = config
            elif isinstance(config, dict):
                self._update_config_from_dict(config)
        elif config_path:
            self._load_config(resolve_path(config_path))

    def _load_config(self, cfg_path: Path) -> None:
        """Load augmentation settings from YAML."""
        if cfg_path.exists():
            try:
                raw_cfg = load_yaml(cfg_path)
                aug_cfg = raw_cfg.get("augmentations", {})
                self._update_config_from_dict(aug_cfg)
            except Exception as e:
                logger.warning(f"Failed to load augmentations config from {cfg_path}: {e}")

    def _update_config_from_dict(self, d: Dict[str, Any]) -> None:
        if "enabled" in d:
            self.config.enabled = bool(d["enabled"])
        if "gaussian_blur" in d:
            self.config.blur_prob = float(d["gaussian_blur"].get("prob", self.config.blur_prob))
            self.config.blur_kernel_range = tuple(d["gaussian_blur"].get("kernel_size", self.config.blur_kernel_range))
        if "gaussian_noise" in d:
            self.config.noise_prob = float(d["gaussian_noise"].get("prob", self.config.noise_prob))
            self.config.noise_var_range = tuple(d["gaussian_noise"].get("var_limit", self.config.noise_var_range))
        if "ink_bleed" in d:
            self.config.bleedthrough_prob = float(d["ink_bleed"].get("prob", self.config.bleedthrough_prob))
        if "shadows" in d:
            self.config.illumination_prob = float(d["shadows"].get("prob", self.config.illumination_prob))

    def set_seed(self, seed: int) -> None:
        self.seed = seed
        self._rng = random.Random(seed)

    def apply(
        self,
        image: Image.Image,
        seed: Optional[int] = None,
    ) -> Tuple[Image.Image, List[str], Dict[str, Any]]:
        """
        Apply enabled photometric degradations probabilistically in sequence.
        Returns: (augmented_image, list_of_applied_augmentations, params_dict)
        """
        actual_seed = seed if seed is not None else self._rng.randint(0, 1_000_000)
        rng = random.Random(actual_seed)

        applied: List[str] = []
        params: Dict[str, Any] = {"seed": actual_seed}
        current_img = image.copy()

        if not self.config.enabled:
            return current_img, applied, params

        # 1. Ink variation (color shift & fading)
        if rng.random() < self.config.ink_fade_prob:
            fade = rng.uniform(*self.config.ink_fade_range)
            current_img = apply_ink_variation(
                current_img,
                fade_ratio=fade,
                seed=rng.randint(0, 1_000_000),
            )
            applied.append("ink_variation")
            params["ink_fade_ratio"] = round(fade, 3)

        # 2. Bleed-through (backside ghosting)
        if rng.random() < self.config.bleedthrough_prob:
            intensity = rng.uniform(*self.config.bleedthrough_intensity_range)
            current_img = apply_bleedthrough(
                current_img,
                intensity=intensity,
                seed=rng.randint(0, 1_000_000),
            )
            applied.append("bleedthrough")
            params["bleedthrough_intensity"] = round(intensity, 3)

        # 3. Uneven Illumination / Vignetting
        if rng.random() < self.config.illumination_prob:
            pattern = rng.choice(["vignette", "linear_gradient", "spotlight"])
            intensity = rng.uniform(*self.config.illumination_intensity_range)
            angle = rng.uniform(0.0, 360.0)
            current_img = apply_illumination(
                current_img,
                pattern=pattern,
                intensity=intensity,
                angle_deg=angle,
                seed=rng.randint(0, 1_000_000),
            )
            applied.append(f"illumination_{pattern}")
            params["illumination"] = {
                "pattern": pattern,
                "intensity": round(intensity, 3),
                "angle_deg": round(angle, 1),
            }

        # 4. Blur (Gaussian, motion, box)
        if rng.random() < self.config.blur_prob:
            blur_type = rng.choice(["gaussian", "motion", "box"])
            k_min, k_max = self.config.blur_kernel_range
            k_size = rng.choice([k for k in range(k_min, k_max + 1) if k % 2 == 1] or [3])
            sigma = rng.uniform(0.5, 1.5)
            angle = rng.uniform(0.0, 180.0)
            current_img = apply_blur(
                current_img,
                blur_type=blur_type,
                kernel_size=k_size,
                sigma=sigma,
                angle_deg=angle,
            )
            applied.append(f"blur_{blur_type}")
            params["blur"] = {"type": blur_type, "kernel_size": k_size, "sigma": round(sigma, 2)}

        # 5. Sensor / grain noise
        if rng.random() < self.config.noise_prob:
            noise_type = rng.choice(["gaussian", "speckle", "salt_pepper"])
            var = rng.uniform(*self.config.noise_var_range)
            current_img = apply_noise(
                current_img,
                noise_type=noise_type,
                var=var,
                amount=0.015,
                seed=rng.randint(0, 1_000_000),
            )
            applied.append(f"noise_{noise_type}")
            params["noise"] = {"type": noise_type, "variance": round(var, 5)}

        # 6. JPEG compression artifacts
        if rng.random() < self.config.compression_prob:
            quality = rng.randint(*self.config.compression_quality_range)
            current_img = apply_compression_artifacts(current_img, quality=quality)
            applied.append("jpeg_compression")
            params["jpeg_quality"] = quality

        return current_img, applied, params
