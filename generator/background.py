"""
Authoritative Historical Background Library and Loader for Chakma Historical OCR.
Discovers, validates, categorizes, and loads real historical manuscript background images
with aspect-ratio-preserving cropping, category weighting, and deterministic in-memory operations.
"""

from dataclasses import asdict, dataclass, field
import math
from pathlib import Path
import random
from typing import Any, Dict, List, Optional, Tuple, Union
from PIL import Image

from utils.file_utils import load_yaml, resolve_path
from utils.image_utils import create_blank_canvas
from utils.logging_utils import setup_logger

logger = setup_logger("background_library")


@dataclass
class BackgroundMetadata:
    """
    Metadata representation of an inspected background image file.
    """
    path: Path
    category: str
    format: str
    width: int
    height: int
    file_size_bytes: int
    is_valid: bool = True
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["path"] = str(self.path)
        return d


@dataclass
class LoadedBackground:
    """
    Container for an in-memory processed background canvas and its ground-truth source metadata.
    """
    image: Image.Image
    category: str
    source_path: Optional[Path]
    crop_box: Tuple[int, int, int, int]
    original_size: Tuple[int, int]
    is_fallback: bool = False

    @property
    def width(self) -> int:
        return self.image.width

    @property
    def height(self) -> int:
        return self.image.height

    def to_dict(self) -> Dict[str, Any]:
        return {
            "category": self.category,
            "source_path": str(self.source_path) if self.source_path else "fallback_procedural",
            "crop_box": list(self.crop_box),
            "original_size": list(self.original_size),
            "width": self.width,
            "height": self.height,
            "is_fallback": self.is_fallback,
        }


class BackgroundLibrary:
    """
    Historical background asset management and in-memory sampling engine.
    Loads real background images from data/backgrounds/ without generating artificial ML textures.
    """

    DEFAULT_EXTENSIONS = [".png", ".jpg", ".jpeg", ".webp"]
    DEFAULT_FALLBACK_COLOR = (245, 238, 220)

    def __init__(
        self,
        backgrounds_dir: Union[str, Path] = "data/backgrounds",
        config_path: Optional[Union[str, Path]] = "config/synthetic.yaml",
        allowed_extensions: Optional[List[str]] = None,
        category_weights: Optional[Dict[str, float]] = None,
        fallback_color: Optional[Tuple[int, int, int]] = None,
        seed: int = 42,
    ):
        self.backgrounds_dir = resolve_path(backgrounds_dir)
        self.config_path = resolve_path(config_path) if config_path else None
        self.seed = seed
        self._rng = random.Random(seed)

        self.allowed_extensions = [
            ext.lower() for ext in (allowed_extensions or self.DEFAULT_EXTENSIONS)
        ]
        self.category_weights: Dict[str, float] = category_weights or {}
        self.fallback_color = fallback_color or self.DEFAULT_FALLBACK_COLOR

        self._load_config()

        self.categories: Dict[str, List[Path]] = {}
        self._all_metadata: List[BackgroundMetadata] = []
        self._invalid_files: List[BackgroundMetadata] = []

        self.refresh()

    def _load_config(self) -> None:
        """Load background parameters from synthetic.yaml if available."""
        if self.config_path and self.config_path.exists():
            try:
                cfg = load_yaml(self.config_path)
                bg_cfg = cfg.get("backgrounds", {})
                if "base_dir" in bg_cfg and self.backgrounds_dir == resolve_path("data/backgrounds"):
                    self.backgrounds_dir = resolve_path(bg_cfg["base_dir"])
                if "fallback_color" in bg_cfg and self.fallback_color == self.DEFAULT_FALLBACK_COLOR:
                    fb = bg_cfg["fallback_color"]
                    if isinstance(fb, (list, tuple)) and len(fb) == 3:
                        self.fallback_color = (int(fb[0]), int(fb[1]), int(fb[2]))
                if "category_weights" in bg_cfg and not self.category_weights:
                    self.category_weights = {
                        str(k): float(v) for k, v in bg_cfg["category_weights"].items()
                    }
            except Exception as e:
                logger.warning(f"Could not load background configuration from {self.config_path}: {e}")

    def set_seed(self, seed: int) -> None:
        """Update deterministic RNG seed."""
        self.seed = seed
        self._rng = random.Random(seed)

    def discover_files(self) -> Dict[str, List[Path]]:
        """
        Scan backgrounds_dir and its subfolders for valid image files.
        """
        discovered: Dict[str, List[Path]] = {}
        if not self.backgrounds_dir.exists():
            logger.warning(f"Backgrounds directory not found at: {self.backgrounds_dir}")
            return discovered

        # 1. Scan subdirectories as categories
        for sub_path in sorted(self.backgrounds_dir.iterdir()):
            if sub_path.is_dir() and not sub_path.name.startswith("."):
                cat_name = sub_path.name.lower()
                cat_files = []
                for file_path in sorted(sub_path.iterdir()):
                    if file_path.is_file() and file_path.suffix.lower() in self.allowed_extensions:
                        cat_files.append(file_path)
                discovered[cat_name] = cat_files

        # 2. Scan root directory files under 'miscellaneous' or 'default'
        root_files = []
        for file_path in sorted(self.backgrounds_dir.iterdir()):
            if file_path.is_file() and file_path.suffix.lower() in self.allowed_extensions:
                root_files.append(file_path)
        if root_files:
            discovered.setdefault("miscellaneous", []).extend(root_files)

        return discovered

    def validate_image_file(self, file_path: Path, category: str) -> BackgroundMetadata:
        """
        Verify that an image file exists, is uncorrupted, and can be decoded into RGB mode.
        """
        if not file_path.exists():
            return BackgroundMetadata(
                path=file_path,
                category=category,
                format="unknown",
                width=0,
                height=0,
                file_size_bytes=0,
                is_valid=False,
                error_message=f"File not found: {file_path}",
            )

        size_bytes = file_path.stat().st_size
        if size_bytes == 0:
            return BackgroundMetadata(
                path=file_path,
                category=category,
                format=file_path.suffix.lower().replace(".", "").upper(),
                width=0,
                height=0,
                file_size_bytes=0,
                is_valid=False,
                error_message="Empty file (0 bytes)",
            )

        try:
            with Image.open(file_path) as img:
                # verify basic structural integrity
                img.verify()

            # Re-open for mode and size inspection (verify closes file descriptor)
            with Image.open(file_path) as img:
                w, h = img.size
                fmt = img.format or file_path.suffix.lower().replace(".", "").upper()
                # Test RGB conversion in-memory
                _ = img.convert("RGB")

            return BackgroundMetadata(
                path=file_path,
                category=category,
                format=fmt,
                width=w,
                height=h,
                file_size_bytes=size_bytes,
                is_valid=True,
            )
        except Exception as e:
            return BackgroundMetadata(
                path=file_path,
                category=category,
                format=file_path.suffix.lower().replace(".", "").upper(),
                width=0,
                height=0,
                file_size_bytes=size_bytes,
                is_valid=False,
                error_message=str(e),
            )

    def refresh(self) -> None:
        """
        Scan directory, validate every image file, and populate category registries.
        """
        raw_discovery = self.discover_files()
        self.categories.clear()
        self._all_metadata.clear()
        self._invalid_files.clear()

        valid_count = 0
        invalid_count = 0

        for cat_name, file_paths in raw_discovery.items():
            valid_paths: List[Path] = []
            for fp in file_paths:
                meta = self.validate_image_file(fp, cat_name)
                self._all_metadata.append(meta)

                if meta.is_valid:
                    valid_paths.append(fp)
                    valid_count += 1
                else:
                    self._invalid_files.append(meta)
                    invalid_count += 1
                    logger.warning(f"Rejected invalid background image {fp.name}: {meta.error_message}")

            self.categories[cat_name] = valid_paths

        logger.info(
            f"BackgroundLibrary initialized: {valid_count} valid images across "
            f"{len(self.categories)} categories ({invalid_count} invalid)."
        )

    def get_categories(self) -> List[str]:
        """Return list of categories that contain at least one valid background image."""
        return sorted([cat for cat, paths in self.categories.items() if len(paths) > 0])

    def get_stats(self) -> Dict[str, Any]:
        """Return structured summary of background assets."""
        counts = {cat: len(paths) for cat, paths in self.categories.items()}
        total_images = sum(counts.values())
        return {
            "total_images": total_images,
            "total_categories": len(self.categories),
            "category_counts": counts,
            "active_categories": self.get_categories(),
            "invalid_files_count": len(self._invalid_files),
        }

    def get_invalid_files(self) -> List[Dict[str, Any]]:
        """Return list of corrupt or invalid files detected during scanning."""
        return [m.to_dict() for m in self._invalid_files]

    def _select_category(self, requested: Optional[str], rng: random.Random) -> Optional[str]:
        """
        Deterministically select an active category, respecting category_weights if configured.
        """
        active_cats = self.get_categories()
        if not active_cats:
            return None

        if requested is not None:
            norm_req = requested.lower()
            if norm_req in self.categories and len(self.categories[norm_req]) > 0:
                return norm_req
            logger.warning(f"Requested category '{requested}' not available or empty. Falling back.")

        # If weights are configured for active categories
        valid_weights = []
        for cat in active_cats:
            valid_weights.append(self.category_weights.get(cat, 1.0))

        if any(w > 0 for w in valid_weights):
            chosen = rng.choices(active_cats, weights=valid_weights, k=1)[0]
            return chosen

        return rng.choice(active_cats)

    def _crop_and_fit(
        self,
        img: Image.Image,
        target_width: int,
        target_height: int,
        rng: random.Random,
    ) -> Tuple[Image.Image, Tuple[int, int, int, int]]:
        """
        Extract an aspect-ratio-preserving in-memory crop matching exact target dimensions.
        Avoids stretching, shearing, and repetitive tiling artifacts.
        """
        orig_w, orig_h = img.size

        # Case 1: Image already covers target dimensions
        if orig_w >= target_width and orig_h >= target_height:
            max_x = orig_w - target_width
            max_y = orig_h - target_height
            left = rng.randint(0, max_x) if max_x > 0 else 0
            top = rng.randint(0, max_y) if max_y > 0 else 0
            crop_box = (left, top, left + target_width, top + target_height)
            cropped = img.crop(crop_box)
            return cropped, crop_box

        # Case 2: Image is smaller in one or both dimensions -> scale up preserving aspect ratio
        scale = max(target_width / orig_w, target_height / orig_h)
        new_w = max(target_width, int(math.ceil(orig_w * scale)))
        new_h = max(target_height, int(math.ceil(orig_h * scale)))

        scaled_img = img.resize((new_w, new_h), Image.Resampling.BICUBIC)
        max_x = max(0, new_w - target_width)
        max_y = max(0, new_h - target_height)
        left = rng.randint(0, max_x) if max_x > 0 else 0
        top = rng.randint(0, max_y) if max_y > 0 else 0
        crop_box = (left, top, left + target_width, top + target_height)
        cropped = scaled_img.crop(crop_box)
        return cropped, crop_box

    def get_background(
        self,
        category: Optional[str] = None,
        width: int = 1024,
        height: int = 1024,
        seed: Optional[int] = None,
    ) -> LoadedBackground:
        """
        Load and return a processed historical manuscript background in-memory.

        Returns LoadedBackground with RGB PIL image, category, source path, and crop bounds.
        """
        actual_seed = seed if seed is not None else self._rng.randint(0, 1_000_000)
        rng = random.Random(actual_seed)

        chosen_cat = self._select_category(category, rng)

        if chosen_cat is None:
            # Fallback antique procedural solid canvas
            fallback_img = create_blank_canvas(width, height, color=self.fallback_color)
            return LoadedBackground(
                image=fallback_img,
                category="procedural_fallback",
                source_path=None,
                crop_box=(0, 0, width, height),
                original_size=(width, height),
                is_fallback=True,
            )

        cat_images = self.categories[chosen_cat]
        chosen_path = rng.choice(cat_images)

        try:
            with Image.open(chosen_path) as raw_img:
                rgb_img = raw_img.convert("RGB")
                orig_size = rgb_img.size
                canvas, crop_box = self._crop_and_fit(rgb_img, width, height, rng)

            return LoadedBackground(
                image=canvas,
                category=chosen_cat,
                source_path=chosen_path,
                crop_box=crop_box,
                original_size=orig_size,
                is_fallback=False,
            )
        except Exception as e:
            logger.error(f"Error loading background image {chosen_path}: {e}. Returning fallback canvas.")
            fallback_img = create_blank_canvas(width, height, color=self.fallback_color)
            return LoadedBackground(
                image=fallback_img,
                category="error_fallback",
                source_path=chosen_path,
                crop_box=(0, 0, width, height),
                original_size=(width, height),
                is_fallback=True,
            )

    def sample(
        self,
        category: Optional[str] = None,
        width: int = 1024,
        height: int = 1024,
        seed: Optional[int] = None,
    ) -> Tuple[Image.Image, str, str]:
        """
        Legacy wrapper returning (PIL.Image, category_name, source_identifier).
        """
        loaded = self.get_background(category=category, width=width, height=height, seed=seed)
        source_id = loaded.source_path.name if loaded.source_path else "procedural_blank"
        return loaded.image, loaded.category, source_id


# Backward compatibility alias
BackgroundEngine = BackgroundLibrary
