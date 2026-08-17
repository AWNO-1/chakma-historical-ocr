"""
Authoritative Synthetic Sample Generator Core for Chakma Historical OCR.
Orchestrates CorpusEngine, CharsetEngine, FontEngine, LayoutEngine, and LineRenderer
to produce in-memory annotated SyntheticSample objects with deterministic reproducibility.
"""

from pathlib import Path
import random
from typing import Any, Dict, List, Optional, Tuple, Union
from PIL import Image

from generator.background import BackgroundEngine
from generator.charset_engine import CharsetEngine
from generator.corpus_engine import CorpusEngine
from generator.font_engine import FontEngine, FontMetadata
from generator.layout_engine import LayoutEngine, PageLayout
from generator.line_renderer import LineRenderer, RenderedPageLines
from generator.metadata import (
    SampleCharacter,
    SampleMetadata,
    SyntheticSample,
    SyntheticSampleMetadata,
)
from utils.file_utils import load_yaml, resolve_path
from utils.geometry import BBox
from utils.logging_utils import setup_logger

logger = setup_logger("synthetic_generator")


class SyntheticGenerator:
    """
    Main Synthetic Manuscript Generator for Chakma Script.
    Executes the complete in-memory pipeline:
    Text -> Charset Validation -> Font Selection -> Layout -> Rendering -> Metadata -> SyntheticSample
    """

    def __init__(
        self,
        config_path: Union[str, Path] = "config/synthetic.yaml",
        charset_engine: Optional[CharsetEngine] = None,
        corpus_engine: Optional[CorpusEngine] = None,
        font_engine: Optional[FontEngine] = None,
        layout_engine: Optional[LayoutEngine] = None,
        line_renderer: Optional[LineRenderer] = None,
        seed: int = 42,
    ):
        self.config_path = resolve_path(config_path) if config_path else None
        self.seed = seed
        self._rng = random.Random(seed)

        # 1. Load configuration
        self.config = load_yaml(self.config_path) if (self.config_path and self.config_path.exists()) else {}
        gen_cfg = self.config.get("generation", {})
        fonts_cfg = self.config.get("fonts", {})

        self.canvas_width = int(gen_cfg.get("canvas_width", 1024))
        self.canvas_height = int(gen_cfg.get("canvas_height", 1024))
        self.min_lines_per_page = int(gen_cfg.get("min_lines_per_page", 4))
        self.max_lines_per_page = int(gen_cfg.get("max_lines_per_page", 12))
        self.font_size_min = int(fonts_cfg.get("font_size_min", 24))
        self.font_size_max = int(fonts_cfg.get("font_size_max", 48))
        self.default_font_size = int(fonts_cfg.get("default_font_size", 32))

        # 2. Initialize sub-engines (allow DI for tests)
        self.charset_engine = charset_engine if charset_engine is not None else CharsetEngine()
        self.corpus_engine = corpus_engine if corpus_engine is not None else CorpusEngine(
            charset_engine=self.charset_engine, seed=seed
        )
        self.font_engine = font_engine if font_engine is not None else FontEngine(
            charset_engine=self.charset_engine, seed=seed
        )
        self.layout_engine = layout_engine if layout_engine is not None else LayoutEngine(
            config_path=self.config_path,
            charset_engine=self.charset_engine,
            font_engine=self.font_engine,
            seed=seed,
        )
        self.line_renderer = line_renderer if line_renderer is not None else LineRenderer(
            charset_engine=self.charset_engine,
            font_engine=self.font_engine,
            default_font_size=self.default_font_size,
            seed=seed,
        )
        self.background_engine = BackgroundEngine(
            backgrounds_dir=self.config.get("backgrounds", {}).get("base_dir", "data/backgrounds")
        )

        logger.info(f"SyntheticGenerator initialized with seed={self.seed}")

    def set_seed(self, seed: int) -> None:
        """Update RNG seed across all underlying engines."""
        self.seed = seed
        self._rng = random.Random(seed)
        self.corpus_engine.set_seed(seed)
        self.font_engine.set_seed(seed)
        self.layout_engine.set_seed(seed)
        self.line_renderer.seed = seed

    def generate(
        self,
        seed: Optional[int] = None,
        font_path: Optional[Union[str, Path]] = None,
        font_size: Optional[int] = None,
        num_lines: Optional[int] = None,
        text_lines: Optional[List[str]] = None,
        sample_id: Optional[str] = None,
        text_color: Tuple[int, int, int, int] = (15, 15, 15, 255),
        background_color: Tuple[int, int, int, int] = (255, 255, 255, 0),
    ) -> SyntheticSample:
        """
        Generate a single in-memory synthetic manuscript sample.

        Pipeline Flow:
        1. Text sampling / input resolution
        2. Charset validation & normalization
        3. Font & typography selection
        4. Geometric layout calculation
        5. Continuous line rendering with grapheme cluster bbox extraction
        6. Character metadata packaging into SyntheticSample
        """
        actual_seed = seed if seed is not None else self._rng.randint(0, 1_000_000)
        rng = random.Random(actual_seed)
        sid = sample_id if sample_id is not None else f"sample_{actual_seed:06d}"

        # ------------------------------------------------------------------
        # 1. Text & Charset Validation
        # ------------------------------------------------------------------
        if text_lines is not None and len(text_lines) > 0:
            raw_lines = [self.corpus_engine.normalize_text(line) for line in text_lines]
        else:
            n_lines = num_lines if num_lines is not None else rng.randint(
                self.min_lines_per_page, self.max_lines_per_page
            )
            raw_lines = self.corpus_engine.get_random_sentences(
                count=n_lines, seed=rng.randint(0, 1_000_000)
            )

        # Validate that lines contain valid Chakma characters
        valid_lines: List[str] = []
        for line in raw_lines:
            cleaned_line = "".join(
                c for c in line if (c.isspace() or self.charset_engine.is_valid_char(c))
            ).strip()
            if cleaned_line:
                valid_lines.append(cleaned_line)

        if not valid_lines:
            # Fallback to single corpus word if text was empty
            valid_lines = [self.corpus_engine.get_random_sentence(seed=rng.randint(0, 1_000_000))]

        # ------------------------------------------------------------------
        # 2. Font Selection
        # ------------------------------------------------------------------
        if font_path is not None:
            target_font_path = resolve_path(font_path)
            font_meta = self.font_engine.get_font_metadata(target_font_path)
            font_name = font_meta.name if font_meta else target_font_path.stem
        else:
            font_meta = self.font_engine.get_random_font(seed=rng.randint(0, 1_000_000))
            target_font_path = font_meta.path
            font_name = font_meta.name

        # Font size resolution
        if font_size is not None:
            target_font_size = max(self.font_size_min, min(font_size, self.font_size_max))
        else:
            target_font_size = rng.randint(self.font_size_min, self.font_size_max)

        # ------------------------------------------------------------------
        # 3. Layout Calculation
        # ------------------------------------------------------------------
        page_layout: PageLayout = self.layout_engine.generate_page_layout(
            lines_text=valid_lines,
            font_path=target_font_path,
            font_size=target_font_size,
            seed=rng.randint(0, 1_000_000),
        )

        # ------------------------------------------------------------------
        # 4. Rendering
        # ------------------------------------------------------------------
        rendered_page: RenderedPageLines = self.line_renderer.render_page_lines(
            page_layout=page_layout,
            font_path=target_font_path,
            font_size=target_font_size,
            text_color=text_color,
            background_color=background_color,
        )

        # ------------------------------------------------------------------
        # 5. Character Metadata Extraction
        # ------------------------------------------------------------------
        characters: List[SampleCharacter] = []
        global_char_id = 0

        for r_line in rendered_page.lines:
            for r_char in r_line.characters:
                # Ensure class ID validity
                cid = r_char.class_id if r_char.class_id is not None else 0
                sample_char = SampleCharacter(
                    id=global_char_id,
                    class_id=cid,
                    text=r_char.character,
                    bbox=r_char.global_bbox,
                    line_id=r_char.line_id,
                    word_id=r_char.word_id,
                    reading_order=r_char.reading_order,
                )
                characters.append(sample_char)
                global_char_id += 1

        # ------------------------------------------------------------------
        # 6. Sample Packaging
        # ------------------------------------------------------------------
        full_text = "\n".join(valid_lines)
        metadata = SampleMetadata(
            sample_id=sid,
            seed=actual_seed,
            width=rendered_page.width,
            height=rendered_page.height,
            font_name=font_name,
            font_size=target_font_size,
            total_lines=len(rendered_page.lines),
            total_characters=len(characters),
            text=full_text,
            lines_text=valid_lines,
            extra={
                "font_path": str(target_font_path),
                "margin_top": page_layout.margin_top,
                "margin_left": page_layout.margin_left,
            },
        )

        return SyntheticSample(
            image=rendered_page.image,
            characters=characters,
            metadata=metadata,
            seed=actual_seed,
        )

    def generate_batch(
        self,
        count: int,
        start_seed: Optional[int] = None,
        font_path: Optional[Union[str, Path]] = None,
        font_size: Optional[int] = None,
    ) -> List[SyntheticSample]:
        """
        Generate a batch of in-memory synthetic manuscript samples.
        """
        base_seed = start_seed if start_seed is not None else self._rng.randint(0, 1_000_000)
        samples: List[SyntheticSample] = []

        for i in range(count):
            sample_seed = base_seed + i
            sample = self.generate(
                seed=sample_seed,
                font_path=font_path,
                font_size=font_size,
                sample_id=f"batch_sample_{sample_seed:06d}",
            )
            samples.append(sample)

        logger.info(f"Generated batch of {count} synthetic samples starting at seed={base_seed}")
        return samples

    # -------------------------------------------------------------------------
    # Backward compatibility method for Stage 01 tests
    # -------------------------------------------------------------------------
    def generate_sample(
        self, sample_id: str, seed: Optional[int] = None
    ) -> Optional[SyntheticSampleMetadata]:
        """
        Legacy wrapper returning SyntheticSampleMetadata for backward compatibility.
        """
        sample = self.generate(seed=seed, sample_id=sample_id)
        return SyntheticSampleMetadata(
            sample_id=sample_id,
            image_filename=f"{sample_id}.jpg",
            label_filename=f"{sample_id}.txt",
            width=sample.width,
            height=sample.height,
            background_category="none",
            background_source="in_memory",
            lines=[],
            total_characters=sample.total_characters,
            seed=seed,
        )


# Alias for backward compatibility
SyntheticDataGenerator = SyntheticGenerator
