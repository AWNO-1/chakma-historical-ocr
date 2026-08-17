"""
Authoritative Font Engine for Chakma Historical OCR.
Handles font discovery (.ttf / .otf), cmap glyph table validation against the 71 canonical Chakma classes,
font metadata extraction, coverage calculation, and deterministic font retrieval.
"""

from dataclasses import asdict, dataclass, field
from pathlib import Path
import random
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from fontTools.ttLib import TTFont
from PIL import ImageFont

from generator.charset_engine import CharsetEngine, ChakmaClass
from utils.file_utils import load_yaml, resolve_path
from utils.logging_utils import setup_logger

logger = setup_logger("font_engine")


@dataclass
class FontMetadata:
    """
    Metadata representation of a scanned and validated typography font.
    """
    name: str
    path: Path
    format: str
    file_size_bytes: int
    total_cmap_glyphs: int
    supported_classes_count: int
    missing_classes_count: int
    coverage_percentage: float
    supported_classes: List[int] = field(default_factory=list)
    missing_classes: List[int] = field(default_factory=list)
    is_valid: bool = False
    rejection_reason: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["path"] = str(self.path)
        return d


class FontEngine:
    """
    Typography engine for discovering, validating, and serving Chakma fonts.
    """

    def __init__(
        self,
        font_dir: Union[str, Path] = "fonts",
        config_path: Optional[Union[str, Path]] = "config/synthetic.yaml",
        charset_engine: Optional[Union[CharsetEngine, str, Path]] = None,
        min_coverage_threshold: Optional[float] = None,
        seed: int = 42,
    ):
        self.font_dir = resolve_path(font_dir)
        self.config_path = resolve_path(config_path) if config_path else None
        self.seed = seed
        self._rng = random.Random(self.seed)

        # Load configuration parameters
        self.font_size_min = 24
        self.font_size_max = 72
        self.default_font_size = 32
        self.supported_extensions = [".ttf", ".otf"]
        self.min_coverage_threshold = 0.70 if min_coverage_threshold is None else min_coverage_threshold

        self._load_config()

        # Initialize Charset Engine
        if charset_engine is None:
            self.charset_engine = CharsetEngine()
        elif isinstance(charset_engine, (str, Path)):
            self.charset_engine = CharsetEngine(charset_path=charset_engine)
        else:
            self.charset_engine = charset_engine

        self._discovered_fonts: List[Path] = []
        self._fonts_metadata: Dict[str, FontMetadata] = {}
        self._supported_fonts: List[FontMetadata] = []
        self._rejected_fonts: List[FontMetadata] = []

        # Font cache for loaded Pillow font objects: (path_str, size) -> FreeTypeFont
        self._font_cache: Dict[Tuple[str, int], ImageFont.FreeTypeFont] = {}

        self.refresh()

    def _load_config(self) -> None:
        """Load font parameters from synthetic.yaml if available."""
        if self.config_path and self.config_path.exists():
            try:
                cfg = load_yaml(self.config_path)
                font_cfg = cfg.get("fonts", {})
                if "font_size_min" in font_cfg:
                    self.font_size_min = int(font_cfg["font_size_min"])
                if "font_size_max" in font_cfg:
                    self.font_size_max = int(font_cfg["font_size_max"])
                if "default_font_size" in font_cfg:
                    self.default_font_size = int(font_cfg["default_font_size"])
                if "supported_extensions" in font_cfg:
                    self.supported_extensions = [ext.lower() for ext in font_cfg["supported_extensions"]]
                if "min_coverage_threshold" in font_cfg and self.min_coverage_threshold == 0.70:
                    self.min_coverage_threshold = float(font_cfg["min_coverage_threshold"])
            except Exception as e:
                logger.warning(f"Could not load font configuration from {self.config_path}: {e}")

    def set_seed(self, seed: int) -> None:
        """Update deterministic RNG seed."""
        self.seed = seed
        self._rng = random.Random(seed)

    def discover_fonts(self) -> List[Path]:
        """
        Scan font directory for all .ttf and .otf font files.
        """
        if not self.font_dir.exists():
            logger.warning(f"Font directory not found at {self.font_dir}. Creating it.")
            self.font_dir.mkdir(parents=True, exist_ok=True)
            return []

        discovered = []
        for file_path in self.font_dir.iterdir():
            if file_path.is_file() and file_path.suffix.lower() in self.supported_extensions:
                discovered.append(file_path)

        # Sort for deterministic order
        discovered.sort(key=lambda p: p.name.lower())
        self._discovered_fonts = discovered
        logger.info(f"Discovered {len(discovered)} font files in {self.font_dir}")
        return list(discovered)

    def validate_font(self, font_path: Union[str, Path]) -> FontMetadata:
        """
        Perform in-depth inspection on a font file:
        - Check file existence and integrity
        - Read cmap table with fontTools
        - Check support for each of the 71 canonical Chakma classes
        - Test loading with PIL.ImageFont
        - Compute coverage percentage and accept/reject decision
        """
        path = resolve_path(font_path)
        name = path.stem
        fmt = path.suffix.lower()

        if not path.exists():
            return FontMetadata(
                name=name,
                path=path,
                format=fmt,
                file_size_bytes=0,
                total_cmap_glyphs=0,
                supported_classes_count=0,
                missing_classes_count=self.charset_engine.total_classes,
                coverage_percentage=0.0,
                supported_classes=[],
                missing_classes=list(range(self.charset_engine.total_classes)),
                is_valid=False,
                rejection_reason=f"File does not exist: {path}",
            )

        file_size = path.stat().st_size

        # 1. Parse font tables via fontTools
        try:
            tt = TTFont(str(path), fontNumber=0)
            cmap = tt.getBestCmap()
            if cmap is None:
                cmap = {}
                for table in tt["cmap"].tables:
                    if table.isUnicode():
                        cmap.update(table.cmap)
            total_glyphs = len(cmap)
        except Exception as e:
            return FontMetadata(
                name=name,
                path=path,
                format=fmt,
                file_size_bytes=file_size,
                total_cmap_glyphs=0,
                supported_classes_count=0,
                missing_classes_count=self.charset_engine.total_classes,
                coverage_percentage=0.0,
                supported_classes=[],
                missing_classes=list(range(self.charset_engine.total_classes)),
                is_valid=False,
                rejection_reason=f"Failed to parse font tables: {e}",
            )

        # 2. Test Pillow FreeType font loading
        try:
            _ = ImageFont.truetype(str(path), size=self.default_font_size)
        except Exception as e:
            return FontMetadata(
                name=name,
                path=path,
                format=fmt,
                file_size_bytes=file_size,
                total_cmap_glyphs=total_glyphs,
                supported_classes_count=0,
                missing_classes_count=self.charset_engine.total_classes,
                coverage_percentage=0.0,
                supported_classes=[],
                missing_classes=list(range(self.charset_engine.total_classes)),
                is_valid=False,
                rejection_reason=f"Pillow FreeType loading failed: {e}",
            )

        # 3. Check coverage against all 71 Chakma classes
        supported_class_ids: List[int] = []
        missing_class_ids: List[int] = []

        all_classes = self.charset_engine.get_all_classes()
        for cls_obj in all_classes:
            cp_int = int(cls_obj.unicode.replace("U+", ""), 16)
            if cp_int in cmap:
                supported_class_ids.append(cls_obj.id)
            else:
                missing_class_ids.append(cls_obj.id)

        total_classes = len(all_classes)
        coverage_ratio = len(supported_class_ids) / total_classes if total_classes > 0 else 0.0
        coverage_pct = round(coverage_ratio * 100.0, 2)

        # 4. Acceptance Criteria
        is_valid = coverage_ratio >= self.min_coverage_threshold
        rejection_reason = None
        if not is_valid:
            rejection_reason = (
                f"Glyph coverage ({coverage_pct}%) is below minimum threshold "
                f"({self.min_coverage_threshold * 100.0}%). Supported: {len(supported_class_ids)}/{total_classes}"
            )

        metadata = FontMetadata(
            name=name,
            path=path,
            format=fmt,
            file_size_bytes=file_size,
            total_cmap_glyphs=total_glyphs,
            supported_classes_count=len(supported_class_ids),
            missing_classes_count=len(missing_class_ids),
            coverage_percentage=coverage_pct,
            supported_classes=supported_class_ids,
            missing_classes=missing_class_ids,
            is_valid=is_valid,
            rejection_reason=rejection_reason,
        )

        return metadata

    def refresh(self) -> None:
        """
        Discover and validate all fonts in the font directory.
        """
        self.discover_fonts()
        self._fonts_metadata.clear()
        self._supported_fonts.clear()
        self._rejected_fonts.clear()

        for font_path in self._discovered_fonts:
            meta = self.validate_font(font_path)
            self._fonts_metadata[str(font_path)] = meta
            self._fonts_metadata[font_path.stem] = meta

            if meta.is_valid:
                self._supported_fonts.append(meta)
                logger.info(
                    f"Accepted font: {meta.name} ({meta.format}) - "
                    f"Coverage: {meta.coverage_percentage}% ({meta.supported_classes_count}/{self.charset_engine.total_classes})"
                )
            else:
                self._rejected_fonts.append(meta)
                logger.warning(
                    f"Rejected font: {meta.name} ({meta.format}) - "
                    f"Reason: {meta.rejection_reason}"
                )

    def get_supported_fonts(self) -> List[FontMetadata]:
        """Return list of all accepted fonts meeting coverage threshold."""
        return list(self._supported_fonts)

    def get_rejected_fonts(self) -> List[FontMetadata]:
        """Return list of all rejected fonts with reasons."""
        return list(self._rejected_fonts)

    def get_all_fonts_metadata(self) -> List[FontMetadata]:
        """Return metadata for all discovered fonts."""
        return list(self._fonts_metadata.values())

    def get_font_metadata(self, font_name_or_path: Union[str, Path]) -> Optional[FontMetadata]:
        """Lookup metadata for a specific font."""
        key = str(font_name_or_path)
        if key in self._fonts_metadata:
            return self._fonts_metadata[key]
        stem = Path(font_name_or_path).stem
        return self._fonts_metadata.get(stem)

    def get_random_font(self, seed: Optional[int] = None) -> FontMetadata:
        """
        Deterministically sample a supported Chakma font.
        """
        if not self._supported_fonts:
            raise ValueError(
                f"No supported Chakma fonts available in {self.font_dir}. "
                f"Please add at least one valid Chakma font (e.g. Noto Sans Chakma)."
            )

        rng = random.Random(seed) if seed is not None else self._rng
        return rng.choice(self._supported_fonts)

    def supports_character(
        self,
        font: Union[FontMetadata, Path, str],
        char_or_unicode: str,
    ) -> bool:
        """
        Check if a font supports a specific Chakma character or Unicode string.
        """
        if isinstance(font, FontMetadata):
            meta = font
        else:
            meta = self.get_font_metadata(font)
            if meta is None:
                meta = self.validate_font(font)

        class_id = self.charset_engine.get_class_id(char_or_unicode)
        if class_id is None:
            return False

        return class_id in meta.supported_classes

    def get_font(
        self,
        font_path: Union[str, Path, FontMetadata],
        size: Optional[int] = None,
    ) -> ImageFont.FreeTypeFont:
        """
        Retrieve cached PIL FreeTypeFont instance with bounded font size.
        """
        if isinstance(font_path, FontMetadata):
            p = font_path.path
        else:
            p = resolve_path(font_path)

        target_size = self.default_font_size if size is None else int(size)
        target_size = max(self.font_size_min, min(target_size, self.font_size_max))

        cache_key = (str(p), target_size)
        if cache_key not in self._font_cache:
            if not p.exists():
                raise FileNotFoundError(f"Font file does not exist: {p}")
            self._font_cache[cache_key] = ImageFont.truetype(str(p), size=target_size)

        return self._font_cache[cache_key]
