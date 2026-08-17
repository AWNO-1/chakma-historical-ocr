"""
Authoritative Layout and Character Geometry Engine for Chakma Historical OCR.
Computes page geometry, margins, line bounding boxes, and character bounding boxes
prior to rendering, with deterministic reproducibility and reading-order assignment.
"""

from dataclasses import asdict, dataclass, field
from pathlib import Path
import random
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from generator.charset_engine import CharsetEngine
from generator.font_engine import FontEngine, FontMetadata
from utils.file_utils import load_yaml, resolve_path
from utils.geometry import BBox
from utils.logging_utils import setup_logger

logger = setup_logger("layout_engine")


@dataclass
class LayoutConfig:
    """Configuration options for LayoutEngine."""
    canvas_width: int = 1024
    canvas_height: int = 1024
    margin_top_range: Tuple[int, int] = (50, 90)
    margin_bottom_range: Tuple[int, int] = (50, 90)
    margin_left_range: Tuple[int, int] = (50, 90)
    margin_right_range: Tuple[int, int] = (50, 90)
    line_spacing_ratio: float = 1.6
    char_spacing_ratio: float = 0.05
    word_gap_ratio: float = 0.45
    font_size_min: int = 24
    font_size_max: int = 48
    default_font_size: int = 32


@dataclass
class CharacterLayout:
    """
    Spatial geometry and metadata for an individual character on the page canvas.
    """
    character: str
    class_id: int
    x: float
    y: float
    width: float
    height: float
    line_id: int
    word_id: int
    reading_order: int

    @property
    def x_min(self) -> float:
        return self.x

    @property
    def y_min(self) -> float:
        return self.y

    @property
    def x_max(self) -> float:
        return self.x + self.width

    @property
    def y_max(self) -> float:
        return self.y + self.height

    @property
    def bbox(self) -> BBox:
        return BBox(
            x_min=self.x_min,
            y_min=self.y_min,
            x_max=self.x_max,
            y_max=self.y_max,
            class_id=self.class_id,
            class_name=None,
            confidence=1.0,
        )

    def to_yolo(self, canvas_width: int, canvas_height: int) -> Tuple[int, float, float, float, float]:
        """Convert character geometry to normalized YOLO format."""
        return self.bbox.to_yolo(canvas_width, canvas_height)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class LineLayout:
    """
    Spatial geometry, text tokens, and character bounding box collection for a text line.
    """
    line_id: int
    text: str
    x: float
    y: float
    width: float
    height: float
    characters: List[CharacterLayout] = field(default_factory=list)
    word_count: int = 0
    reading_order: int = 0

    @property
    def x_min(self) -> float:
        return self.x

    @property
    def y_min(self) -> float:
        return self.y

    @property
    def x_max(self) -> float:
        return self.x + self.width

    @property
    def y_max(self) -> float:
        return self.y + self.height

    @property
    def bbox(self) -> BBox:
        return BBox(
            x_min=self.x_min,
            y_min=self.y_min,
            x_max=self.x_max,
            y_max=self.y_max,
            class_id=-1,
            class_name="line",
            confidence=1.0,
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "line_id": self.line_id,
            "text": self.text,
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
            "word_count": self.word_count,
            "reading_order": self.reading_order,
            "characters_count": len(self.characters),
            "characters": [c.to_dict() for c in self.characters],
        }


@dataclass
class PageLayout:
    """
    Complete geometric specification of a manuscript page.
    """
    width: int
    height: int
    margin_top: int
    margin_bottom: int
    margin_left: int
    margin_right: int
    lines: List[LineLayout] = field(default_factory=list)
    total_characters: int = 0
    total_lines: int = 0
    seed: int = 42

    def get_all_character_boxes(self) -> List[CharacterLayout]:
        """Return flattened list of all character layout objects in reading order."""
        boxes = []
        for line in self.lines:
            boxes.extend(line.characters)
        return sorted(boxes, key=lambda b: b.reading_order)

    def get_all_bboxes(self) -> List[BBox]:
        """Return flattened list of all character BBoxes."""
        return [char.bbox for char in self.get_all_character_boxes()]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "width": self.width,
            "height": self.height,
            "margin_top": self.margin_top,
            "margin_bottom": self.margin_bottom,
            "margin_left": self.margin_left,
            "margin_right": self.margin_right,
            "total_lines": self.total_lines,
            "total_characters": self.total_characters,
            "seed": self.seed,
            "lines": [line.to_dict() for line in self.lines],
        }


class LayoutEngine:
    """
    Spatial geometry engine responsible for calculating page layouts, line coordinates,
    and individual character bounding boxes without executing image rendering.
    """

    def __init__(
        self,
        config: Optional[LayoutConfig] = None,
        config_path: Optional[Union[str, Path]] = "config/synthetic.yaml",
        charset_engine: Optional[Union[CharsetEngine, str, Path]] = None,
        font_engine: Optional[FontEngine] = None,
        seed: int = 42,
    ):
        self.config_path = resolve_path(config_path) if config_path else None
        self.seed = seed
        self._rng = random.Random(self.seed)

        # Default configuration values
        self.canvas_width = 1024
        self.canvas_height = 1024
        self.min_lines_per_page = 5
        self.max_lines_per_page = 15
        self.margin_top_range = (50, 90)
        self.margin_bottom_range = (50, 90)
        self.margin_left_range = (50, 90)
        self.margin_right_range = (50, 90)
        self.line_spacing_ratio = 1.6
        self.char_spacing_ratio = 0.05
        self.word_gap_ratio = 0.45
        self.default_font_size = 32
        self.font_size_min = 24
        self.font_size_max = 48

        if config is not None:
            self.canvas_width = config.canvas_width
            self.canvas_height = config.canvas_height
            self.margin_top_range = config.margin_top_range
            self.margin_bottom_range = config.margin_bottom_range
            self.margin_left_range = config.margin_left_range
            self.margin_right_range = config.margin_right_range
            self.line_spacing_ratio = config.line_spacing_ratio
            self.char_spacing_ratio = config.char_spacing_ratio
            self.word_gap_ratio = config.word_gap_ratio
            self.font_size_min = config.font_size_min
            self.font_size_max = config.font_size_max
            self.default_font_size = config.default_font_size
        else:
            self._load_config()

        # Initialize engines
        if charset_engine is None:
            self.charset_engine = CharsetEngine()
        elif isinstance(charset_engine, (str, Path)):
            self.charset_engine = CharsetEngine(charset_path=charset_engine)
        else:
            self.charset_engine = charset_engine

        if font_engine is None:
            self.font_engine = FontEngine(charset_engine=self.charset_engine, seed=self.seed)
        else:
            self.font_engine = font_engine

    def _load_config(self) -> None:
        """Load geometry and canvas configuration from YAML."""
        if self.config_path and self.config_path.exists():
            try:
                cfg = load_yaml(self.config_path)
                gen_cfg = cfg.get("generation", {})
                self.canvas_width = int(gen_cfg.get("canvas_width", self.canvas_width))
                self.canvas_height = int(gen_cfg.get("canvas_height", self.canvas_height))
                self.min_lines_per_page = int(gen_cfg.get("min_lines_per_page", self.min_lines_per_page))
                self.max_lines_per_page = int(gen_cfg.get("max_lines_per_page", self.max_lines_per_page))
                self.line_spacing_ratio = float(gen_cfg.get("line_spacing_ratio", self.line_spacing_ratio))
                self.char_spacing_ratio = float(gen_cfg.get("char_spacing_ratio", self.char_spacing_ratio))
                self.default_font_size = int(gen_cfg.get("default_font_size", self.default_font_size))

                font_cfg = cfg.get("fonts", {})
                if "font_size_min" in font_cfg:
                    self.font_size_min = int(font_cfg["font_size_min"])
                if "font_size_max" in font_cfg:
                    self.font_size_max = int(font_cfg["font_size_max"])
            except Exception as e:
                logger.warning(f"Could not load layout configuration from {self.config_path}: {e}")

    def set_seed(self, seed: int) -> None:
        """Update deterministic RNG seed."""
        self.seed = seed
        self._rng = random.Random(seed)

    def calculate_margins(self, rng: Optional[random.Random] = None) -> Tuple[int, int, int, int]:
        """
        Calculate deterministic page margins: (margin_top, margin_bottom, margin_left, margin_right).
        """
        r = rng if rng is not None else self._rng
        m_top = r.randint(*self.margin_top_range)
        m_bottom = r.randint(*self.margin_bottom_range)
        m_left = r.randint(*self.margin_left_range)
        m_right = r.randint(*self.margin_right_range)
        return m_top, m_bottom, m_left, m_right

    def estimate_glyph_metrics(
        self,
        char: str,
        font_size: int,
        font_path: Optional[Union[str, Path]] = None,
    ) -> Tuple[float, float, float, float, float]:
        """
        Compute precise geometric glyph metrics without rasterization:
        Returns: (offset_x, offset_y, glyph_w, glyph_h, advance_width)
        """
        if font_path is None:
            supported_fonts = self.font_engine.get_supported_fonts()
            target_font_path = supported_fonts[0].path if supported_fonts else None
        else:
            target_font_path = resolve_path(font_path)

        if target_font_path and target_font_path.exists():
            pil_font = self.font_engine.get_font(target_font_path, size=font_size)
            try:
                # getbbox returns (left, top, right, bottom) relative to (0, 0) anchor
                bbox = pil_font.getbbox(char)
                if bbox is not None:
                    left, top, right, bottom = bbox
                    glyph_w = max(1.0, float(right - left))
                    glyph_h = max(1.0, float(bottom - top))
                    offset_x = float(left)
                    offset_y = float(top)
                    advance_w = float(pil_font.getlength(char))
                    if advance_w <= 0.0:
                        advance_w = glyph_w
                    return offset_x, offset_y, glyph_w, glyph_h, advance_w
            except Exception:
                pass

        # Robust parametric fallback estimation based on font_size
        glyph_w = font_size * 0.65
        glyph_h = font_size * 0.85
        offset_x = 0.0
        offset_y = 0.0
        advance_w = glyph_w + (font_size * self.char_spacing_ratio)
        return offset_x, offset_y, glyph_w, glyph_h, advance_w

    def wrap_text_lines(
        self,
        raw_lines: List[str],
        font_path: Path,
        font_size: int,
        max_width: float,
    ) -> List[str]:
        """
        Word-wrap input text lines so that no rendered line exceeds max_width.
        """
        pil_font = self.font_engine.get_font(font_path, size=font_size)
        wrapped: List[str] = []

        for line in raw_lines:
            words = line.strip().split()
            if not words:
                continue

            current_line_words: List[str] = []

            for word in words:
                candidate = " ".join(current_line_words + [word]) if current_line_words else word
                cand_w = pil_font.getlength(candidate)

                if cand_w <= max_width:
                    current_line_words.append(word)
                else:
                    if current_line_words:
                        wrapped.append(" ".join(current_line_words))
                        current_line_words = [word]
                    else:
                        # Single word exceeds line width: wrap it as single line
                        wrapped.append(word)
                        current_line_words = []

            if current_line_words:
                wrapped.append(" ".join(current_line_words))

        return wrapped if wrapped else [""]

    def generate_page_layout(
        self,
        lines_text: List[str],
        font_path: Optional[Union[str, Path]] = None,
        font_size: Optional[int] = None,
        seed: Optional[int] = None,
        wrap_lines: bool = False,
    ) -> PageLayout:
        """
        Compute complete geometric layout for a list of text lines across a page canvas.
        """
        rng = random.Random(seed) if seed is not None else self._rng
        actual_seed = seed if seed is not None else self.seed

        # 1. Resolve typography parameters
        if font_size is None:
            target_font_size = rng.randint(self.font_size_min, self.font_size_max)
        else:
            target_font_size = max(self.font_size_min, min(font_size, self.font_size_max))

        if font_path is None:
            font_meta = self.font_engine.get_random_font(seed=rng.randint(0, 1000000))
            target_font_path = font_meta.path
        else:
            target_font_path = resolve_path(font_path)

        # 2. Compute margins and available canvas area
        m_top, m_bottom, m_left, m_right = self.calculate_margins(rng=rng)
        available_width = self.canvas_width - m_left - m_right
        available_height = self.canvas_height - m_top - m_bottom

        line_step = target_font_size * self.line_spacing_ratio
        max_possible_lines = max(1, int(available_height // line_step))

        # Word-wrap input lines if requested
        if wrap_lines:
            wrapped_lines = self.wrap_text_lines(
                raw_lines=lines_text,
                font_path=target_font_path,
                font_size=target_font_size,
                max_width=available_width,
            )
            active_lines = wrapped_lines[:max_possible_lines] if wrapped_lines else [""]
        else:
            active_lines = lines_text[:max_possible_lines] if lines_text else [""]

        # 3. Position and compute each line
        lines_layout: List[LineLayout] = []
        current_y = float(m_top)
        global_reading_order = 0

        for line_idx, raw_line in enumerate(active_lines):
            # Guard against exceeding bottom boundary
            if current_y + target_font_size > (self.canvas_height - m_bottom):
                break

            # Compute line layout
            line_layout = self._compute_line_geometry(
                line_text=raw_line,
                line_id=line_idx,
                start_x=float(m_left),
                start_y=current_y,
                font_size=target_font_size,
                font_path=target_font_path,
                max_width=available_width,
                global_reading_order_start=global_reading_order,
                rng=rng,
            )
            lines_layout.append(line_layout)
            global_reading_order += len(line_layout.characters)
            current_y += line_step

        total_chars = sum(len(line.characters) for line in lines_layout)

        page_layout = PageLayout(
            width=self.canvas_width,
            height=self.canvas_height,
            margin_top=m_top,
            margin_bottom=m_bottom,
            margin_left=m_left,
            margin_right=m_right,
            lines=lines_layout,
            total_characters=total_chars,
            total_lines=len(lines_layout),
            seed=actual_seed,
        )

        return page_layout

    def _compute_line_geometry(
        self,
        line_text: str,
        line_id: int,
        start_x: float,
        start_y: float,
        font_size: int,
        font_path: Optional[Path],
        max_width: float,
        global_reading_order_start: int,
        rng: random.Random,
    ) -> LineLayout:
        """
        Compute character placement, word gaps, and coordinates along a single line.
        Enforces strict right-margin boundary clamping.
        """
        words = line_text.split(" ")
        characters_layout: List[CharacterLayout] = []

        curr_x = start_x
        reading_idx = global_reading_order_start
        char_spacing = font_size * self.char_spacing_ratio
        word_gap = font_size * self.word_gap_ratio
        max_x_boundary = start_x + max_width

        line_min_y = start_y
        line_max_y = start_y + font_size
        line_ended = False

        for word_idx, word in enumerate(words):
            if line_ended:
                break
            for char in word:
                class_id = self.charset_engine.get_class_id(char)
                if class_id is None:
                    # Skip unmapped symbols
                    continue

                off_x, off_y, glyph_w, glyph_h, adv_w = self.estimate_glyph_metrics(
                    char, font_size, font_path
                )

                # Micro-jitter for historical manuscript organic feel (sub-pixel)
                jitter_x = rng.uniform(-0.5, 0.5)
                jitter_y = rng.uniform(-0.5, 0.5)

                char_x = curr_x + off_x + jitter_x
                char_y = start_y + off_y + jitter_y
                char_w = max(2.0, glyph_w)
                char_h = max(2.0, glyph_h)

                # Boundary safety check: break before adding if character exceeds line boundary
                if (char_x + char_w) > max_x_boundary:
                    line_ended = True
                    break

                char_layout = CharacterLayout(
                    character=char,
                    class_id=class_id,
                    x=round(char_x, 2),
                    y=round(char_y, 2),
                    width=round(char_w, 2),
                    height=round(char_h, 2),
                    line_id=line_id,
                    word_id=word_idx,
                    reading_order=reading_idx,
                )
                characters_layout.append(char_layout)
                reading_idx += 1

                curr_x += adv_w + char_spacing

                line_min_y = min(line_min_y, char_y)
                line_max_y = max(line_max_y, char_y + char_h)

            # Word spacing after word completion
            curr_x += word_gap

        line_width = max(1.0, curr_x - start_x)
        line_height = max(float(font_size), line_max_y - line_min_y)

        return LineLayout(
            line_id=line_id,
            text=line_text,
            x=round(start_x, 2),
            y=round(start_y, 2),
            width=round(line_width, 2),
            height=round(line_height, 2),
            characters=characters_layout,
            word_count=len(words),
            reading_order=line_id,
        )

    def validate_layout(self, layout: PageLayout) -> Dict[str, Any]:
        """
        Perform geometric integrity checks on the generated page layout:
        - Bounding box dimension positivity (width > 0, height > 0)
        - Page boundary inclusion (no boxes outside canvas)
        - Monotonic and contiguous reading order
        - Line grouping consistency
        """
        errors: List[str] = []
        warnings: List[str] = []

        all_boxes = layout.get_all_character_boxes()

        # 1. Check reading order sequence
        reading_orders = [b.reading_order for b in all_boxes]
        expected_orders = list(range(len(all_boxes)))
        if reading_orders != expected_orders:
            errors.append(f"Reading order sequence is non-contiguous: {reading_orders[:10]}...")

        # 2. Check bounding box validity and boundaries
        for idx, char_box in enumerate(all_boxes):
            if char_box.width <= 0 or char_box.height <= 0:
                errors.append(f"Invalid box dimensions for char '{char_box.character}' (order {idx}): {char_box.width}x{char_box.height}")

            if not char_box.bbox.is_within_bounds(layout.width, layout.height):
                errors.append(
                    f"Char '{char_box.character}' (order {idx}) out of page bounds: "
                    f"[{char_box.x_min}, {char_box.y_min}, {char_box.x_max}, {char_box.y_max}] on {layout.width}x{layout.height}"
                )

        # 3. Check line grouping consistency
        for line in layout.lines:
            for char_box in line.characters:
                if char_box.line_id != line.line_id:
                    errors.append(
                        f"Line ID mismatch: char has line_id={char_box.line_id}, but belongs to line {line.line_id}"
                    )

        is_valid = len(errors) == 0

        report = {
            \"is_valid\": is_valid,
            \"total_lines\": layout.total_lines,
            \"total_characters\": layout.total_characters,
            \"errors\": errors,
            \"warnings\": warnings,
        }

        if not is_valid:
            logger.error(f"Layout validation FAILED: {errors}")
        else:
            logger.info(f"Layout validation PASSED: {layout.total_lines} lines, {layout.total_characters} characters verified.")

        return report
