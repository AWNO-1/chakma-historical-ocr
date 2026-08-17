"""
Authoritative Chakma Line Renderer for Chakma Historical OCR.
Renders full text lines onto PIL Canvases while precisely tracking character-level
bounding boxes, class IDs, reading orders, and spatial coordinates without separate glyph slicing.
"""

from dataclasses import asdict, dataclass, field
from pathlib import Path
import random
import unicodedata
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from generator.charset_engine import CharsetEngine
from generator.font_engine import FontEngine, FontMetadata
from generator.layout_engine import PageLayout, LineLayout, CharacterLayout
from utils.file_utils import resolve_path
from utils.geometry import BBox
from utils.logging_utils import setup_logger

logger = setup_logger("line_renderer")


@dataclass
class RenderedCharacter:
    """
    Metadata and bounding boxes for a single rendered character within a line/page.
    """
    character: str
    class_id: int
    local_bbox: BBox
    global_bbox: BBox
    line_id: int
    word_id: int
    reading_order: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "character": self.character,
            "class_id": self.class_id,
            "local_bbox": self.local_bbox.to_dict(),
            "global_bbox": self.global_bbox.to_dict(),
            "line_id": self.line_id,
            "word_id": self.word_id,
            "reading_order": self.reading_order,
        }


@dataclass
class RenderedLine:
    """
    Rendered line result containing the line image and character metadata.
    """
    image: Image.Image
    text: str
    line_id: int
    font_path: Path
    font_size: int
    bbox: BBox
    characters: List[RenderedCharacter] = field(default_factory=list)
    width: int = 0
    height: int = 0
    reading_order: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "text": self.text,
            "line_id": self.line_id,
            "font_path": str(self.font_path),
            "font_size": self.font_size,
            "width": self.width,
            "height": self.height,
            "bbox": self.bbox.to_dict(),
            "reading_order": self.reading_order,
            "character_count": len(self.characters),
            "characters": [c.to_dict() for c in self.characters],
        }


@dataclass
class RenderedPageLines:
    """
    Complete manuscript page render containing the assembled image and lines metadata.
    """
    image: Image.Image
    lines: List[RenderedLine] = field(default_factory=list)
    total_lines: int = 0
    total_characters: int = 0
    width: int = 1024
    height: int = 1024

    @property
    def all_characters(self) -> List[RenderedCharacter]:
        chars = []
        for line in self.lines:
            chars.extend(line.characters)
        return sorted(chars, key=lambda c: c.reading_order)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "width": self.width,
            "height": self.height,
            "total_lines": self.total_lines,
            "total_characters": self.total_characters,
            "lines": [line.to_dict() for line in self.lines],
        }


class LineRenderer:
    """
    Renders continuous text lines using Pillow while computing exact character bounding boxes.
    """

    def __init__(
        self,
        charset_engine: Optional[CharsetEngine] = None,
        font_engine: Optional[FontEngine] = None,
        default_font_size: int = 32,
        seed: int = 42,
    ):
        self.seed = seed
        self.default_font_size = default_font_size
        self._rng = random.Random(seed)

        self.charset_engine = charset_engine if charset_engine is not None else CharsetEngine()
        self.font_engine = font_engine if font_engine is not None else FontEngine(charset_engine=self.charset_engine, seed=seed)

    @staticmethod
    def _split_grapheme_clusters(text: str) -> List[Tuple[str, int]]:
        """
        Split text into grapheme clusters, each as (cluster_string, start_index).

        A grapheme cluster = one base character + all following combining marks
        (Unicode categories Mn, Mc, Me) and format characters (Cf, excluding space).
        This matches what a shaping engine renders as a single visual unit.
        """
        clusters: List[Tuple[str, int]] = []
        current_cluster = ""
        current_start = 0

        for i, char in enumerate(text):
            cat = unicodedata.category(char)
            is_combining = cat in ("Mn", "Mc", "Me") or (cat == "Cf" and char != " ")

            if is_combining and current_cluster:
                # Attach to current cluster
                current_cluster += char
            else:
                # Save previous cluster (if any) and start new one
                if current_cluster:
                    clusters.append((current_cluster, current_start))
                current_cluster = char
                current_start = i

        if current_cluster:
            clusters.append((current_cluster, current_start))

        return clusters

    @staticmethod
    def _rightmost_ink_col(img: Image.Image, threshold: int = 10) -> Optional[int]:
        """
        Return the rightmost column index that contains at least one pixel
        with alpha > threshold, or None if the image is fully transparent.
        """
        arr = np.array(img)           # shape: (H, W, 4)
        alpha = arr[:, :, 3]          # alpha channel
        cols = np.where(alpha.max(axis=0) > threshold)[0]
        return int(cols[-1]) if len(cols) > 0 else None

    @staticmethod
    def _ink_y_range(
        img: Image.Image,
        x_start: int,
        x_end: int,
        threshold: int = 10,
    ) -> Tuple[Optional[float], Optional[float]]:
        """
        Return (y_min, y_max) of ink pixels in the column band [x_start, x_end)
        of img, or (None, None) if no ink is found.
        """
        arr = np.array(img)
        col_lo = max(0, x_start)
        col_hi = min(img.width, x_end)
        if col_lo >= col_hi:
            return None, None
        region_alpha = arr[:, col_lo:col_hi, 3]
        rows = np.where(region_alpha.max(axis=1) > threshold)[0]
        if len(rows) == 0:
            return None, None
        return float(rows[0]), float(rows[-1] + 1)

    @staticmethod
    def _blend_ink_onto_canvas(page_canvas: Image.Image, line_img: Image.Image, paste_x: int, paste_y: int) -> None:
        """
        Subtractive ink-paper blending:
        Absorbs ink into paper texture fibers using multiply and luminance modulation,
        preventing flat/digital appearance and simulating physical quill-and-paper interaction.
        """
        line_w, line_h = line_img.size
        page_w, page_h = page_canvas.size

        x1 = max(0, paste_x)
        y1 = max(0, paste_y)
        x2 = min(page_w, paste_x + line_w)
        y2 = min(page_h, paste_y + line_h)

        if x1 >= x2 or y1 >= y2:
            return

        lx1 = x1 - paste_x
        ly1 = y1 - paste_y
        lx2 = lx1 + (x2 - x1)
        ly2 = ly1 + (y2 - y1)

        ink_crop = line_img.crop((lx1, ly1, lx2, ly2))
        ink_arr = np.array(ink_crop).astype(np.float32)
        alpha = (ink_arr[:, :, 3] / 255.0)[:, :, np.newaxis]

        if np.max(alpha) < 0.01:
            return

        paper_crop = page_canvas.crop((x1, y1, x2, y2)).convert("RGBA")
        paper_arr = np.array(paper_crop).astype(np.float32)

        ink_rgb = ink_arr[:, :, :3]
        paper_rgb = paper_arr[:, :, :3]

        # Realistic Subtractive Multiply Ink Blending:
        # Ink darkens underlying paper fibers according to alpha
        blended_rgb = paper_rgb * (1.0 - alpha * (1.0 - ink_rgb / 255.0))
        paper_arr[:, :, :3] = np.clip(blended_rgb, 0.0, 255.0)
        paper_arr[:, :, 3] = np.maximum(paper_arr[:, :, 3], ink_arr[:, :, 3])

        blended_crop = Image.fromarray(paper_arr.astype(np.uint8), mode="RGBA")
        page_canvas.paste(blended_crop, (x1, y1))

    def measure_character(self, char: str, font: ImageFont.FreeTypeFont) -> Tuple[float, float, float, float]:
        """
        Measure exact bounding box offsets for a single character relative to (0, 0) anchor.
        Returns: (left, top, right, bottom)
        """
        bbox = font.getbbox(char)
        if bbox is not None:
            return float(bbox[0]), float(bbox[1]), float(bbox[2]), float(bbox[3])
        return 0.0, 0.0, float(self.default_font_size * 0.6), float(self.default_font_size * 0.8)

    def measure_text(self, text: str, font: ImageFont.FreeTypeFont) -> Tuple[float, float]:
        """
        Measure total pixel width and height of a text string.
        Returns: (width, height)
        """
        if not text:
            return 0.0, 0.0
        bbox = font.getbbox(text)
        if bbox is not None:
            w = max(1.0, float(bbox[2] - bbox[0]))
            h = max(1.0, float(bbox[3] - bbox[1]))
            return w, h
        length = font.getlength(text)
        return float(length), float(font.size)

    def render_line(
        self,
        text: str,
        font_path: Optional[Union[str, Path]] = None,
        font_size: Optional[int] = None,
        line_id: int = 0,
        reading_order_start: int = 0,
        text_color: Tuple[int, int, int, int] = (20, 20, 20, 255),
        background_color: Tuple[int, int, int, int] = (0, 0, 0, 0),
        padding: int = 10,
    ) -> RenderedLine:
        """
        Render a full text line as a continuous string onto an isolated line image canvas
        and compute character-level local and global bounding boxes.
        """
        target_size = font_size if font_size is not None else self.default_font_size

        if font_path is None:
            supported = self.font_engine.get_supported_fonts()
            target_font_path = supported[0].path if supported else Path("fonts/NotoSansChakma-Regular.ttf")
        else:
            target_font_path = resolve_path(font_path)

        # Handle empty text case
        if not text or not text.strip():
            empty_img = Image.new("RGBA", (max(1, padding * 2), max(1, target_size + padding * 2)), background_color)
            return RenderedLine(
                image=empty_img,
                text=text,
                line_id=line_id,
                font_path=target_font_path,
                font_size=target_size,
                bbox=BBox(x_min=0, y_min=0, x_max=empty_img.width, y_max=empty_img.height, class_name="line"),
                characters=[],
                width=empty_img.width,
                height=empty_img.height,
                reading_order=reading_order_start,
            )

        pil_font = self.font_engine.get_font(target_font_path, size=target_size)

        # Measure line dimensions
        text_bbox = pil_font.getbbox(text)
        if text_bbox is not None:
            min_x_off, min_y_off, max_x_off, max_y_off = text_bbox
            raw_w = max_x_off - min(0, min_x_off)
            raw_h = max_y_off - min(0, min_y_off)
        else:
            raw_w = int(pil_font.getlength(text))
            raw_h = target_size
            min_x_off, min_y_off = 0, 0

        img_w = int(raw_w + (padding * 2) + 20)
        img_h = int(raw_h + (padding * 2) + 20)

        # Create transparent canvas and draw full line
        line_img = Image.new("RGBA", (img_w, img_h), background_color)
        draw = ImageDraw.Draw(line_img)

        origin_x = float(padding - min(0, min_x_off))
        origin_y = float(padding - min(0, min_y_off))

        # Render continuous line
        draw.text((origin_x, origin_y), text, font=pil_font, fill=text_color)

        # ------------------------------------------------------------------
        # Progressive pixel-delta bbox computation per character & diacritic.
        #
        # For every codepoint (consonant, independent vowel, dependent vowel
        # sign/matra, virama/maaw, digit, punctuation):
        # We render progressive prefixes on a canvas and extract the exact
        # bounding box of the newly added ink pixels (diff mask).
        # This gives ground-truth bounding boxes for ALL 71 individual classes
        # (including diacritics positioned over or under base consonants)
        # matching YOLO multi-class detection specifications.
        # ------------------------------------------------------------------
        rendered_chars: List[RenderedCharacter] = []
        current_word_id = 0
        current_reading_order = reading_order_start

        prev_img = Image.new("RGBA", (img_w, img_h), (0, 0, 0, 0))

        for i, char in enumerate(text):
            if char == " ":
                current_word_id += 1
                continue

            class_id = self.charset_engine.get_class_id(char)
            if class_id is None:
                logger.warning(f"Unsupported character in text: '{char}' (U+{ord(char):04X})")
                continue

            prefix = text[:i + 1]
            curr_img = Image.new("RGBA", (img_w, img_h), (0, 0, 0, 0))
            curr_draw = ImageDraw.Draw(curr_img)
            curr_draw.text((origin_x, origin_y), prefix, font=pil_font, fill=(0, 0, 0, 255))

            curr_arr = np.array(curr_img)[:, :, 3]
            prev_arr = np.array(prev_img)[:, :, 3]

            diff = (curr_arr > 10) & (prev_arr <= 10)
            rows, cols = np.where(diff)

            if len(rows) > 0 and len(cols) > 0:
                bx_min = float(cols.min())
                bx_max = float(cols.max() + 1)
                by_min = float(rows.min())
                by_max = float(rows.max() + 1)
            else:
                # Fallback to font advance if diff is identical
                cursor_x = origin_x + pil_font.getlength(text[:i])
                adv = max(2.0, pil_font.getlength(prefix) - pil_font.getlength(text[:i]))
                bx_min = cursor_x
                bx_max = cursor_x + adv
                by_min = float(origin_y)
                by_max = float(origin_y + target_size * 0.85)

            char_w = max(2.0, bx_max - bx_min)
            char_h = max(2.0, by_max - by_min)

            local_box = BBox(
                x_min=round(bx_min, 2),
                y_min=round(by_min, 2),
                x_max=round(bx_min + char_w, 2),
                y_max=round(by_min + char_h, 2),
                class_id=class_id,
                class_name=self.charset_engine.get_character(class_id),
                confidence=1.0,
            )
            global_box = BBox(
                x_min=local_box.x_min,
                y_min=local_box.y_min,
                x_max=local_box.x_max,
                y_max=local_box.y_max,
                class_id=class_id,
                class_name=local_box.class_name,
                confidence=1.0,
            )

            rendered_chars.append(RenderedCharacter(
                character=char,
                class_id=class_id,
                local_bbox=local_box,
                global_bbox=global_box,
                line_id=line_id,
                word_id=current_word_id,
                reading_order=current_reading_order,
            ))
            current_reading_order += 1
            prev_img = curr_img

        # Line bbox from actual ink pixels
        line_arr = np.array(line_img)
        line_alpha = line_arr[:, :, 3]
        ink_cols = np.where(line_alpha.max(axis=0) > 10)[0]
        ink_rows = np.where(line_alpha.max(axis=1) > 10)[0]
        if len(ink_cols) > 0 and len(ink_rows) > 0:
            line_bbox = BBox(
                x_min=float(ink_cols[0]),
                y_min=float(ink_rows[0]),
                x_max=float(ink_cols[-1] + 1),
                y_max=float(ink_rows[-1] + 1),
                class_id=-1,
                class_name="line",
                confidence=1.0,
            )
        else:
            line_bbox = BBox(
                x_min=origin_x, y_min=origin_y,
                x_max=origin_x + raw_w, y_max=origin_y + raw_h,
                class_id=-1, class_name="line", confidence=1.0,
            )

        return RenderedLine(
            image=line_img,
            text=text,
            line_id=line_id,
            font_path=target_font_path,
            font_size=target_size,
            bbox=line_bbox,
            characters=rendered_chars,
            width=img_w,
            height=img_h,
            reading_order=reading_order_start,
        )

    def render_page_lines(
        self,
        page_layout: PageLayout,
        font_path: Optional[Union[str, Path]] = None,
        font_size: Optional[int] = None,
        text_color: Optional[Tuple[int, int, int, int]] = None,
        background_image: Optional[Image.Image] = None,
        background_color: Tuple[int, int, int, int] = (255, 255, 255, 0),
        ink_palettes: Optional[List[Tuple[int, int, int, int]]] = None,
        random_font_per_line: bool = False,
        random_size_jitter: float = 0.0,
        baseline_jitter: float = 0.0,
        seed: Optional[int] = None,
    ) -> RenderedPageLines:
        """
        Render all lines of a PageLayout onto a full manuscript page canvas.
        Supports real background image compositing, varied historical ink colors,
        multi-font selection per line, and baseline/size jitter.
        """
        rng = random.Random(seed) if seed is not None else self._rng

        # Base canvas: either provided background texture or blank RGBA
        if background_image is not None:
            page_img = background_image.copy().convert("RGBA")
            if page_img.size != (page_layout.width, page_layout.height):
                page_img = page_img.resize((page_layout.width, page_layout.height), Image.Resampling.BICUBIC)
        else:
            page_img = Image.new("RGBA", (page_layout.width, page_layout.height), background_color)

        base_size = font_size if font_size is not None else self.default_font_size

        supported_fonts = self.font_engine.get_supported_fonts()
        if font_path is None:
            default_font_path = supported_fonts[0].path if supported_fonts else Path("fonts/NotoSansChakma-Regular.ttf")
        else:
            default_font_path = resolve_path(font_path)

        # Authentic historical ink colors (iron-gall, walnut, charcoal, soot, sepia)
        default_palettes = [
            (45, 32, 24, 245),   # Iron-gall brown
            (36, 26, 18, 250),   # Walnut dark brown
            (28, 28, 32, 255),   # Charcoal carbon ink
            (58, 48, 38, 235),   # Aged sepia
            (22, 22, 25, 255),   # Soft soot black
        ]
        active_palettes = ink_palettes or default_palettes

        rendered_lines: List[RenderedLine] = []
        global_reading_order = 0

        for line_layout in page_layout.lines:
            if not line_layout.text:
                continue

            # Resolve line font
            if random_font_per_line and len(supported_fonts) > 1:
                line_font_path = rng.choice(supported_fonts).path
            else:
                line_font_path = default_font_path

            # Resolve line font size with jitter
            if random_size_jitter > 0:
                size_delta = int(round(rng.uniform(-random_size_jitter, random_size_jitter)))
                line_font_size = max(18, base_size + size_delta)
            else:
                line_font_size = base_size

            # Resolve line ink color
            if text_color is not None:
                line_color = text_color
            else:
                line_color = rng.choice(active_palettes)

            # Baseline jitter
            y_offset = rng.uniform(-baseline_jitter, baseline_jitter) if baseline_jitter > 0 else 0.0

            paste_x = int(round(line_layout.x))
            paste_y = int(round(line_layout.y + y_offset))

            # Render line to its own transparent canvas
            r_line_single = self.render_line(
                text=line_layout.text,
                font_path=line_font_path,
                font_size=line_font_size,
                line_id=line_layout.line_id,
                reading_order_start=global_reading_order,
                text_color=line_color,
                background_color=(0, 0, 0, 0),
                padding=0,
            )

            # Composite line onto page canvas with realistic subtractive paper fiber blending
            self._blend_ink_onto_canvas(page_img, r_line_single.image, paste_x, paste_y)

            # Shift every character's local_bbox by the paste offset → global_bbox
            global_chars: List[RenderedCharacter] = []
            for rc in r_line_single.characters:
                lb = rc.local_bbox
                gb = BBox(
                    x_min=round(lb.x_min + paste_x, 2),
                    y_min=round(lb.y_min + paste_y, 2),
                    x_max=round(lb.x_max + paste_x, 2),
                    y_max=round(lb.y_max + paste_y, 2),
                    class_id=rc.class_id,
                    class_name=lb.class_name,
                    confidence=1.0,
                )
                global_chars.append(RenderedCharacter(
                    character=rc.character,
                    class_id=rc.class_id,
                    local_bbox=lb,
                    global_bbox=gb,
                    line_id=rc.line_id,
                    word_id=rc.word_id,
                    reading_order=rc.reading_order,
                ))

            global_reading_order += len(global_chars)

            # Tight line bbox derived from actual rendered character positions
            if global_chars:
                lx_min = min(c.global_bbox.x_min for c in global_chars)
                ly_min = min(c.global_bbox.y_min for c in global_chars)
                lx_max = max(c.global_bbox.x_max for c in global_chars)
                ly_max = max(c.global_bbox.y_max for c in global_chars)
                tight_bbox = BBox(
                    x_min=lx_min, y_min=ly_min, x_max=lx_max, y_max=ly_max,
                    class_id=-1, class_name="line", confidence=1.0,
                )
            else:
                tight_bbox = line_layout.bbox

            rendered_lines.append(RenderedLine(
                image=page_img,
                text=line_layout.text,
                line_id=line_layout.line_id,
                font_path=line_font_path,
                font_size=line_font_size,
                bbox=tight_bbox,
                characters=global_chars,
                width=r_line_single.width,
                height=r_line_single.height,
                reading_order=line_layout.line_id,
            ))

        total_chars = sum(len(l.characters) for l in rendered_lines)

        return RenderedPageLines(
            image=page_img,
            lines=rendered_lines,
            total_lines=len(rendered_lines),
            total_characters=total_chars,
            width=page_layout.width,
            height=page_layout.height,
        )
