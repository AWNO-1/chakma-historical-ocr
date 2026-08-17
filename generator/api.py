"""
Authoritative Synthetic Sample Generator Core for Chakma Historical OCR.
Orchestrates CorpusEngine, CharsetEngine, FontEngine, LayoutEngine, and LineRenderer
to produce in-memory annotated SyntheticSample objects with deterministic reproducibility.
"""

from pathlib import Path
import random
from typing import Any, Dict, List, Optional, Tuple, Union
from PIL import Image

from generator.charset_engine import CharsetEngine
from generator.corpus_engine import CorpusEngine
from generator.font_engine import FontEngine, FontMetadata
from generator.layout_engine import LayoutEngine, PageLayout
from generator.line_renderer import LineRenderer, RenderedPageLines
from generator.background import BackgroundLibrary, BackgroundEngine
from generator.transform_engine import TransformPipeline, TransformationResult
from generator.metadata import SampleCharacter, SampleMetadata, SyntheticSample, SyntheticSampleMetadata
from utils.file_utils import load_yaml, resolve_path
from utils.geometry import BBox
from utils.logging_utils import setup_logger

logger = setup_logger("synthetic_generator")


class SyntheticGenerator:
    """
    Authoritative Synthetic Manuscript Sample Generator for Chakma Historical OCR.
    Orchestrates the entire generation pipeline:
    Corpus Text Sampling -> Charset Normalization -> Typography & Layout -> Line Rendering ->
    Historical Background Compositing -> Transform & Degradation Pipeline -> SyntheticSample.
    """

    def __init__(
        self,
        config_path: Optional[Union[str, Path]] = "config/synthetic.yaml",
        charset_engine: Optional[CharsetEngine] = None,
        corpus_engine: Optional[CorpusEngine] = None,
        font_engine: Optional[FontEngine] = None,
        layout_engine: Optional[LayoutEngine] = None,
        line_renderer: Optional[LineRenderer] = None,
        background_engine: Optional[BackgroundLibrary] = None,
        transform_pipeline: Optional[TransformPipeline] = None,
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
        self.background_engine = background_engine if background_engine is not None else BackgroundLibrary(
            backgrounds_dir=self.config.get("backgrounds", {}).get("base_dir", "data/backgrounds"),
            seed=seed,
        )
        self.transform_pipeline = transform_pipeline if transform_pipeline is not None else TransformPipeline(
            config_path=self.config_path,
            seed=seed,
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
        self.background_engine.set_seed(seed)
        self.transform_pipeline.set_seed(seed)

    def generate(
        self,
        text_lines: Optional[List[str]] = None,
        num_lines: Optional[int] = None,
        font_path: Optional[Union[str, Path]] = None,
        font_size: Optional[int] = None,
        text_color: Optional[Tuple[int, int, int, int]] = None,
        background_color: Tuple[int, int, int, int] = (255, 255, 255, 0),
        use_real_background: bool = False,
        background_category: Optional[str] = None,
        apply_transforms: bool = False,
        random_font_per_line: bool = False,
        ink_palettes: Optional[List[Tuple[int, int, int, int]]] = None,
        baseline_jitter: float = 0.0,
        random_size_jitter: float = 0.0,
        sample_id: Optional[str] = None,
        seed: Optional[int] = None,
    ) -> SyntheticSample:
        """
        Generate a synthetic manuscript page sample.
        """
        actual_seed = seed if seed is not None else self._rng.randint(0, 1_000_000)
        rng = random.Random(actual_seed)
        sid = sample_id or f"sample_{actual_seed:06d}"

        # ------------------------------------------------------------------
        # 1. Text Sampling & Normalization
        # ------------------------------------------------------------------
        if text_lines is not None:
            raw_lines = text_lines
        else:
            lines_count = num_lines or rng.randint(self.min_lines_per_page, self.max_lines_per_page)
            raw_lines = [
                self.corpus_engine.get_random_sentence(seed=rng.randint(0, 1_000_000))
                for _ in range(lines_count)
            ]

        valid_lines: List[str] = []
        for line in raw_lines:
            cleaned_line = "".join(
                c for c in line if (c.isspace() or self.charset_engine.is_valid_char(c))
            ).strip()
            # Enforce Brahmic syllable integrity (no orphaned dependent vowels / modifiers)
            cleaned_line = self.charset_engine.repair_syllables(cleaned_line)
            if cleaned_line:
                valid_lines.append(cleaned_line)

        if not valid_lines:
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
            wrap_lines=True,
        )

        # ------------------------------------------------------------------
        # 4. Background Selection
        # ------------------------------------------------------------------
        bg_image: Optional[Image.Image] = None
        bg_info = "solid"
        if use_real_background or background_category is not None:
            loaded_bg = self.background_engine.get_background(
                category=background_category,
                width=self.canvas_width,
                height=self.canvas_height,
                seed=rng.randint(0, 1_000_000),
            )
            bg_image = loaded_bg.image
            bg_info = f"{loaded_bg.category} ({loaded_bg.source_path.name if loaded_bg.source_path else 'fallback'})"

        # ------------------------------------------------------------------
        # 5. Rendering
        # ------------------------------------------------------------------
        rendered_page: RenderedPageLines = self.line_renderer.render_page_lines(
            page_layout=page_layout,
            font_path=target_font_path,
            font_size=target_font_size,
            text_color=text_color,
            background_image=bg_image,
            background_color=background_color,
            ink_palettes=ink_palettes,
            random_font_per_line=random_font_per_line,
            random_size_jitter=random_size_jitter,
            baseline_jitter=baseline_jitter,
            seed=rng.randint(0, 1_000_000),
        )

        # ------------------------------------------------------------------
        # 6. Character Metadata Extraction
        # ------------------------------------------------------------------
        raw_characters: List[SampleCharacter] = []
        global_char_id = 0

        for r_line in rendered_page.lines:
            for r_char in r_line.characters:
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
                raw_characters.append(sample_char)
                global_char_id += 1

        final_image = rendered_page.image.convert("RGB")
        final_characters = raw_characters
        applied_transforms_list: List[str] = []
        transform_params_dict: Dict[str, Any] = {}

        # ------------------------------------------------------------------
        # 7. Transformation & Degradation Pipeline (if requested)
        # ------------------------------------------------------------------
        if apply_transforms:
            input_boxes = [c.bbox for c in raw_characters]
            trans_res: TransformationResult = self.transform_pipeline.apply(
                image=final_image,
                bboxes=input_boxes,
                seed=rng.randint(0, 1_000_000),
            )
            final_image = trans_res.image
            applied_transforms_list = trans_res.applied_transforms
            transform_params_dict = trans_res.parameters

            # Update characters with transformed bounding boxes
            updated_chars: List[SampleCharacter] = []
            for orig_c, trans_b in zip(raw_characters, trans_res.bboxes):
                updated_chars.append(SampleCharacter(
                    id=orig_c.id,
                    class_id=orig_c.class_id,
                    text=orig_c.text,
                    bbox=trans_b,
                    line_id=orig_c.line_id,
                    word_id=orig_c.word_id,
                    reading_order=orig_c.reading_order,
                ))
            final_characters = updated_chars

        # ------------------------------------------------------------------
        # 8. Sample Packaging
        # ------------------------------------------------------------------
        full_text = "\n".join(valid_lines)
        metadata = SampleMetadata(
            sample_id=sid,
            seed=actual_seed,
            width=final_image.width,
            height=final_image.height,
            font_name=font_name,
            font_size=target_font_size,
            total_lines=len(rendered_page.lines),
            total_characters=len(final_characters),
            text=full_text,
            lines_text=valid_lines,
            extra={
                "font_path": str(target_font_path),
                "background": bg_info,
                "applied_transforms": applied_transforms_list,
                "transform_parameters": transform_params_dict,
            },
        )

        return SyntheticSample(
            image=final_image,
            characters=final_characters,
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
