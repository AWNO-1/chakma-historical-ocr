"""
Authoritative Chakma Line Renderer for Chakma Historical OCR.
Renders full text lines onto PIL Canvases while precisely tracking character-level
bounding boxes, class IDs, reading orders, and spatial coordinates without separate glyph slicing.
"""

from dataclasses import asdict, dataclass, field
from pathlib import Path
import random
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

        # Compute character bounding boxes along the line
        rendered_chars: List[RenderedCharacter] = []
        curr_x = origin_x
        curr_y = origin_y
        current_word_id = 0
        current_reading_order = reading_order_start

        for char in text:
            if char == " ":
                current_word_id += 1
                curr_x += pil_font.getlength(" ")
                continue

            class_id = self.charset_engine.get_class_id(char)
            if class_id is None:
                # Unsupported character: advance width but log/skip class assignment
                logger.warning(f"Unsupported character in text: '{char}' (U+{ord(char):04X})")
                curr_x += pil_font.getlength(char)
                continue

            c_bbox = pil_font.getbbox(char)
            c_advance = pil_font.getlength(char)

            if c_bbox is not None:
                bx_min = curr_x + c_bbox[0]
                by_min = curr_y + c_bbox[1]
                bx_max = curr_x + c_bbox[2]
                by_max = curr_y + c_bbox[3]
            else:
                bx_min = curr_x
                by_min = curr_y
                bx_max = curr_x + target_size * 0.6
                by_max = curr_y + target_size * 0.8

            # Ensure positive box dimensions
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

            # In single line mode, global bbox equals local bbox
            global_box = BBox(
                x_min=local_box.x_min,
                y_min=local_box.y_min,
                x_max=local_box.x_max,
                y_max=local_box.y_max,
                class_id=class_id,
                class_name=local_box.class_name,
                confidence=1.0,
            )

            rendered_char = RenderedCharacter(
                character=char,
                class_id=class_id,
                local_bbox=local_box,
                global_bbox=global_box,
                line_id=line_id,
                word_id=current_word_id,
                reading_order=current_reading_order,
            )
            rendered_chars.append(rendered_char)
            current_reading_order += 1

            # Advance x cursor by character glyph advance
            curr_x += c_advance

        line_bbox = BBox(
            x_min=origin_x,
            y_min=origin_y,
            x_max=curr_x,
            y_max=origin_y + raw_h,
            class_id=-1,
            class_name="line",
            confidence=1.0,
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
        text_color: Tuple[int, int, int, int] = (20, 20, 20, 255),
        background_color: Tuple[int, int, int, int] = (255, 255, 255, 0),
    ) -> RenderedPageLines:
        """
        Render all lines of a PageLayout onto a full manuscript page canvas
        and return the assembled image with global character annotations.
        """
        page_img = Image.new("RGBA", (page_layout.width, page_layout.height), background_color)
        draw = ImageDraw.Draw(page_img)

        target_size = font_size if font_size is not None else self.default_font_size

        if font_path is None:
            supported = self.font_engine.get_supported_fonts()
            target_font_path = supported[0].path if supported else Path("fonts/NotoSansChakma-Regular.ttf")
        else:
            target_font_path = resolve_path(font_path)

        pil_font = self.font_engine.get_font(target_font_path, size=target_size)

        rendered_lines: List[RenderedLine] = []
        global_reading_order = 0

        for line_layout in page_layout.lines:
            line_text = line_layout.text
            start_x = line_layout.x
            start_y = line_layout.y

            if not line_text:
                continue

            # Render continuous line on page canvas
            draw.text((start_x, start_y), line_text, font=pil_font, fill=text_color)

            # Extract character bboxes from page layout or recalculate
            line_chars: List[RenderedCharacter] = []
            for char_layout in line_layout.characters:
                global_bbox = BBox(
                    x_min=char_layout.x,
                    y_min=char_layout.y,
                    x_max=char_layout.x + char_layout.width,
                    y_max=char_layout.y + char_layout.height,
                    class_id=char_layout.class_id,
                    class_name=char_layout.character,
                    confidence=1.0,
                )
                local_bbox = BBox(
                    x_min=char_layout.x - start_x,
                    y_min=char_layout.y - start_y,
                    x_max=char_layout.x - start_x + char_layout.width,
                    y_max=char_layout.y - start_y + char_layout.height,
                    class_id=char_layout.class_id,
                    class_name=char_layout.character,
                    confidence=1.0,
                )
                r_char = RenderedCharacter(
                    character=char_layout.character,
                    class_id=char_layout.class_id,
                    local_bbox=local_bbox,
                    global_bbox=global_bbox,
                    line_id=line_layout.line_id,
                    word_id=char_layout.word_id,
                    reading_order=char_layout.reading_order,
                )
                line_chars.append(r_char)
                global_reading_order += 1

            r_line = RenderedLine(
                image=page_img,  # Reference to page canvas
                text=line_text,
                line_id=line_layout.line_id,
                font_path=target_font_path,
                font_size=target_size,
                bbox=line_layout.bbox,
                characters=line_chars,
                width=int(line_layout.width),
                height=int(line_layout.height),
                reading_order=line_layout.line_id,
            )
            rendered_lines.append(r_line)

        total_chars = sum(len(l.characters) for l in rendered_lines)

        return RenderedPageLines(
            image=page_img,
            lines=rendered_lines,
            total_lines=len(rendered_lines),
            total_characters=total_chars,
            width=page_layout.width,
            height=page_layout.height,
        )
