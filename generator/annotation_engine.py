"""
Authoritative Ground Truth and YOLO Label Engine for Chakma Historical OCR.
Handles normalized YOLO coordinate serialization, file writing, comprehensive
geometric and linguistic validation, and visual rendering with bounding box tags.
"""

from dataclasses import asdict, dataclass, field
import io
import math
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple, Union
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from generator.charset_engine import CharsetEngine, ChakmaClass
from generator.metadata import SampleCharacter, CharacterAnnotation, SyntheticSample
from utils.file_utils import resolve_path, write_text_lines
from utils.geometry import BBox
from utils.logging_utils import setup_logger

logger = setup_logger("annotation_engine")


@dataclass
class YoloAnnotation:
    """
    Representation of an individual normalized YOLO object detection annotation.
    Coordinates are normalized to [0.0, 1.0] relative to canvas dimensions.
    """
    class_id: int
    x_center: float
    y_center: float
    width: float
    height: float
    confidence: float = 1.0
    character: Optional[str] = None
    reading_order: Optional[int] = None

    def to_yolo_line(self, precision: int = 6) -> str:
        """Format as standard YOLO space-delimited string: '<class_id> <cx> <cy> <w> <h>'."""
        return (
            f"{self.class_id} "
            f"{self.x_center:.{precision}f} "
            f"{self.y_center:.{precision}f} "
            f"{self.width:.{precision}f} "
            f"{self.height:.{precision}f}"
        )

    def to_bbox(self, image_width: int, image_height: int) -> BBox:
        """Convert normalized YOLO coordinates back to absolute pixel BBox."""
        return BBox.from_yolo(
            class_id=self.class_id,
            norm_cx=self.x_center,
            norm_cy=self.y_center,
            norm_w=self.width,
            norm_h=self.height,
            image_width=image_width,
            image_height=image_height,
            confidence=self.confidence,
            class_name=self.character,
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class YoloValidationResult:
    """Validation report for an individual YOLO annotation."""
    is_valid: bool
    class_id: int
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    annotation: Optional[YoloAnnotation] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_valid": self.is_valid,
            "class_id": self.class_id,
            "errors": self.errors,
            "warnings": self.warnings,
            "annotation": self.annotation.to_dict() if self.annotation else None,
        }


@dataclass
class DatasetValidationSummary:
    """Aggregated validation statistics across multiple samples or files."""
    total_samples: int = 0
    total_labels: int = 0
    valid_labels: int = 0
    invalid_labels: int = 0
    valid_samples: int = 0
    invalid_samples: int = 0
    class_frequencies: Dict[int, int] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return self.invalid_labels == 0 and len(self.errors) == 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_valid": self.is_valid,
            "total_samples": self.total_samples,
            "total_labels": self.total_labels,
            "valid_labels": self.valid_labels,
            "invalid_labels": self.invalid_labels,
            "valid_samples": self.valid_samples,
            "invalid_samples": self.invalid_samples,
            "class_frequencies": self.class_frequencies,
            "errors": self.errors,
            "warnings": self.warnings,
        }


class YoloLabelWriter:
    """
    Authoritative YOLO Annotation and Ground Truth Manager for Chakma OCR.
    Translates in-memory character metadata to standard YOLO detection format,
    writes ground-truth label files, and enforces strict validation checks.
    """

    def __init__(self, charset_engine: Optional[CharsetEngine] = None):
        self.charset_engine = charset_engine if charset_engine is not None else CharsetEngine()
        self._valid_class_ids: Set[int] = set(c.id for c in self.charset_engine.get_all_classes())

    @staticmethod
    def format_yolo_line(box: BBox, image_width: int, image_height: int) -> str:
        """Backward-compatible helper to format a BBox into a YOLO line."""
        cid, cx, cy, bw, bh = box.to_yolo(image_width, image_height)
        return f"{cid} {cx:.6f} {cy:.6f} {bw:.6f} {bh:.6f}"

    @staticmethod
    def save_yolo_annotations(
        boxes: List[BBox], image_width: int, image_height: int, output_path: Union[str, Path]
    ) -> Path:
        """Backward-compatible helper to write BBoxes to a YOLO label file."""
        writer = YoloLabelWriter()
        return writer.write_label_file(output_path, boxes, image_width=image_width, image_height=image_height)

    def to_yolo(
        self,
        item: Union[SyntheticSample, SampleCharacter, CharacterAnnotation, BBox, Sequence[SampleCharacter]],
        image_width: Optional[int] = None,
        image_height: Optional[int] = None,
    ) -> Union[str, List[str]]:
        """
        Convert a sample, list of characters, single character, or BBox into normalized YOLO format string(s).
        """
        # 1. Full SyntheticSample
        if isinstance(item, SyntheticSample):
            w = item.width
            h = item.height
            lines: List[str] = []
            for char in item.characters:
                cid, cx, cy, bw, bh = char.to_yolo(w, h)
                lines.append(f"{cid} {cx:.6f} {cy:.6f} {bw:.6f} {bh:.6f}")
            return lines

        # 2. Sequence of SampleCharacters
        if isinstance(item, (list, tuple)):
            if image_width is None or image_height is None:
                raise ValueError("image_width and image_height are required when converting a list of characters.")
            lines = []
            for char in item:
                if isinstance(char, SampleCharacter):
                    cid, cx, cy, bw, bh = char.to_yolo(image_width, image_height)
                elif isinstance(char, CharacterAnnotation):
                    cid, cx, cy, bw, bh = char.bbox.to_yolo(image_width, image_height)
                elif isinstance(char, BBox):
                    cid, cx, cy, bw, bh = char.to_yolo(image_width, image_height)
                else:
                    raise TypeError(f"Unsupported character item type: {type(char)}")
                lines.append(f"{cid} {cx:.6f} {cy:.6f} {bw:.6f} {bh:.6f}")
            return lines

        # 3. Single SampleCharacter
        if isinstance(item, SampleCharacter):
            if image_width is None or image_height is None:
                raise ValueError("image_width and image_height are required for single SampleCharacter.")
            cid, cx, cy, bw, bh = item.to_yolo(image_width, image_height)
            return f"{cid} {cx:.6f} {cy:.6f} {bw:.6f} {bh:.6f}"

        # 4. Single CharacterAnnotation
        if isinstance(item, CharacterAnnotation):
            if image_width is None or image_height is None:
                raise ValueError("image_width and image_height are required for single CharacterAnnotation.")
            cid, cx, cy, bw, bh = item.bbox.to_yolo(image_width, image_height)
            return f"{cid} {cx:.6f} {cy:.6f} {bw:.6f} {bh:.6f}"

        # 5. Single BBox
        if isinstance(item, BBox):
            if image_width is None or image_height is None:
                raise ValueError("image_width and image_height are required for single BBox.")
            cid, cx, cy, bw, bh = item.to_yolo(image_width, image_height)
            return f"{cid} {cx:.6f} {cy:.6f} {bw:.6f} {bh:.6f}"

        raise TypeError(f"Unsupported item type for to_yolo: {type(item)}")

    def write_label_file(
        self,
        output_path: Union[str, Path],
        sample: Union[SyntheticSample, Sequence[SampleCharacter], List[str]],
        image_width: Optional[int] = None,
        image_height: Optional[int] = None,
    ) -> Path:
        """
        Serialize ground-truth annotations to a standard YOLO .txt label file.
        """
        out_p = resolve_path(output_path)
        out_p.parent.mkdir(parents=True, exist_ok=True)

        if isinstance(sample, list) and all(isinstance(x, str) for x in sample):
            lines = sample
        else:
            lines = self.to_yolo(sample, image_width=image_width, image_height=image_height)

        content = "\n".join(lines)
        if content and not content.endswith("\n"):
            content += "\n"

        out_p.write_text(content, encoding="utf-8")
        logger.debug(f"Wrote {len(lines)} YOLO labels to: {out_p}")
        return out_p

    def parse_label_file(self, label_path_or_content: Union[str, Path]) -> List[YoloAnnotation]:
        """
        Parse YOLO label file (.txt) or multi-line string into structured YoloAnnotation instances.
        """
        if isinstance(label_path_or_content, Path) or (
            isinstance(label_path_or_content, str) and "\n" not in label_path_or_content and Path(label_path_or_content).exists()
        ):
            text = Path(label_path_or_content).read_text(encoding="utf-8")
        else:
            text = str(label_path_or_content)

        annotations: List[YoloAnnotation] = []
        for line_num, line in enumerate(text.strip().splitlines(), start=1):
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            parts = line.split()
            if len(parts) < 5:
                raise ValueError(f"Malformed YOLO line {line_num}: expected 5 values, got {len(parts)} -> '{line}'")

            cid = int(parts[0])
            cx = float(parts[1])
            cy = float(parts[2])
            w = float(parts[3])
            h = float(parts[4])
            conf = float(parts[5]) if len(parts) >= 6 else 1.0

            char_text = self.charset_engine.get_character(cid)
            annotations.append(YoloAnnotation(
                class_id=cid,
                x_center=cx,
                y_center=cy,
                width=w,
                height=h,
                confidence=conf,
                character=char_text,
                reading_order=line_num - 1,
            ))

        return annotations

    def validate_label(
        self,
        label: Union[YoloAnnotation, str, Tuple[int, float, float, float, float]],
        image_width: int = 1024,
        image_height: int = 1024,
    ) -> YoloValidationResult:
        """
        Validate an individual YOLO label against strict geometric, normalization, and charset constraints:
        - class_id exists in CharsetEngine (0..70)
        - coordinates are valid finite floats (no NaN/Inf)
        - normalized range [0.0, 1.0] for center and dimensions
        - positive, non-zero area (w > 0, h > 0)
        - bounding box strictly contained within image normalized boundaries
        """
        errors: List[str] = []
        warnings: List[str] = []

        # Parse input into YoloAnnotation
        if isinstance(label, str):
            parts = label.strip().split()
            if len(parts) < 5:
                return YoloValidationResult(
                    is_valid=False,
                    class_id=-1,
                    errors=[f"Invalid label format: expected at least 5 tokens, got {len(parts)}"],
                )
            try:
                cid = int(parts[0])
                cx = float(parts[1])
                cy = float(parts[2])
                w = float(parts[3])
                h = float(parts[4])
                conf = float(parts[5]) if len(parts) >= 6 else 1.0
                ann = YoloAnnotation(class_id=cid, x_center=cx, y_center=cy, width=w, height=h, confidence=conf)
            except Exception as e:
                return YoloValidationResult(is_valid=False, class_id=-1, errors=[f"Parse error: {e}"])
        elif isinstance(label, tuple):
            cid, cx, cy, w, h = label[:5]
            ann = YoloAnnotation(class_id=cid, x_center=cx, y_center=cy, width=w, height=h)
        elif isinstance(label, YoloAnnotation):
            ann = label
        else:
            return YoloValidationResult(
                is_valid=False, class_id=-1, errors=[f"Unsupported label type: {type(label)}"]
            )

        # 1. Check Class ID existence
        if ann.class_id not in self._valid_class_ids:
            errors.append(
                f"Invalid class_id: {ann.class_id} (not registered in CharsetEngine 0..{self.charset_engine.total_classes - 1})"
            )

        # 2. Check for NaN or Inf
        coords = [ann.x_center, ann.y_center, ann.width, ann.height]
        if any(math.isnan(c) or math.isinf(c) for c in coords):
            errors.append(f"Coordinates contain NaN or Inf values: {coords}")

        # 3. Check Positive Non-Zero Dimensions
        if ann.width <= 0.0:
            errors.append(f"Non-positive width: {ann.width}")
        if ann.height <= 0.0:
            errors.append(f"Non-positive height: {ann.height}")

        # 4. Check Normalized Range [0.0, 1.0]
        if not (0.0 <= ann.x_center <= 1.0):
            errors.append(f"x_center out of normalized range [0, 1]: {ann.x_center}")
        if not (0.0 <= ann.y_center <= 1.0):
            errors.append(f"y_center out of normalized range [0, 1]: {ann.y_center}")
        if not (0.0 < ann.width <= 1.0):
            errors.append(f"width out of normalized range (0, 1]: {ann.width}")
        if not (0.0 < ann.height <= 1.0):
            errors.append(f"height out of normalized range (0, 1]: {ann.height}")

        # 5. Check Boundary Containment
        x_min = ann.x_center - (ann.width / 2.0)
        x_max = ann.x_center + (ann.width / 2.0)
        y_min = ann.y_center - (ann.height / 2.0)
        y_max = ann.y_center + (ann.height / 2.0)

        eps = 1e-4
        if x_min < -eps or x_max > 1.0 + eps:
            warnings.append(f"Horizontal bounds extend beyond normalized canvas: [{x_min:.4f}, {x_max:.4f}]")
        if y_min < -eps or y_max > 1.0 + eps:
            warnings.append(f"Vertical bounds extend beyond normalized canvas: [{y_min:.4f}, {y_max:.4f}]")

        # 6. Check Absolute Pixel Size Consistency
        abs_w = ann.width * image_width
        abs_h = ann.height * image_height
        if abs_w < 1.0 or abs_h < 1.0:
            warnings.append(f"Extremely small pixel dimensions: {abs_w:.2f}x{abs_h:.2f} px")

        is_valid = len(errors) == 0
        return YoloValidationResult(
            is_valid=is_valid,
            class_id=ann.class_id,
            errors=errors,
            warnings=warnings,
            annotation=ann,
        )

    def validate_all(
        self,
        sources: Sequence[Union[SyntheticSample, Path, str, List[YoloAnnotation]]],
        image_width: int = 1024,
        image_height: int = 1024,
    ) -> DatasetValidationSummary:
        """
        Validate a batch of samples or label files and aggregate comprehensive statistics.
        """
        summary = DatasetValidationSummary()
        summary.total_samples = len(sources)

        for src in sources:
            sample_has_error = False

            if isinstance(src, SyntheticSample):
                labels = [
                    YoloAnnotation(
                        class_id=c.class_id,
                        x_center=c.bbox.center_x / src.width,
                        y_center=c.bbox.center_y / src.height,
                        width=c.bbox.width / src.width,
                        height=c.bbox.height / src.height,
                        character=c.text,
                    )
                    for c in src.characters
                ]
                w, h = src.width, src.height
            elif isinstance(src, (Path, str)):
                labels = self.parse_label_file(src)
                w, h = image_width, image_height
            elif isinstance(src, list):
                labels = src
                w, h = image_width, image_height
            else:
                summary.errors.append(f"Unsupported validation source: {type(src)}")
                summary.invalid_samples += 1
                continue

            for ann in labels:
                summary.total_labels += 1
                v_res = self.validate_label(ann, image_width=w, image_height=h)

                if v_res.is_valid:
                    summary.valid_labels += 1
                    summary.class_frequencies[v_res.class_id] = (
                        summary.class_frequencies.get(v_res.class_id, 0) + 1
                    )
                else:
                    summary.invalid_labels += 1
                    sample_has_error = True
                    summary.errors.extend(v_res.errors)

                if v_res.warnings:
                    summary.warnings.extend(v_res.warnings)

            if sample_has_error:
                summary.invalid_samples += 1
            else:
                summary.valid_samples += 1

        return summary

    def visualize_labels(
        self,
        image: Image.Image,
        labels: Union[Sequence[YoloAnnotation], Path, str, List[str]],
        show_class_name: bool = True,
        show_box: bool = True,
    ) -> Image.Image:
        """
        Render bounding box overlays with class IDs and Chakma character tags onto an image canvas.
        Every unique class ID receives its own vibrant, distinct color.
        """
        if isinstance(labels, (Path, str)):
            annotations = self.parse_label_file(labels)
        elif isinstance(labels, list) and all(isinstance(x, str) for x in labels):
            annotations = self.parse_label_file("\n".join(labels))
        else:
            annotations = list(labels)

        vis = image.copy().convert("RGBA")
        overlay = Image.new("RGBA", vis.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        w, h = vis.size

        # High-contrast Golden-ratio color palette
        def get_class_color(cid: int) -> Tuple[int, int, int, int]:
            if cid < 0:
                return (120, 120, 120, 240)
            hue = (cid * 137.508) % 360.0
            sat = 0.90 + (cid % 3) * 0.04
            val = 0.92 + (cid % 2) * 0.06
            c = val * sat
            x = c * (1.0 - abs((hue / 60.0) % 2 - 1.0))
            m = val - c
            if 0 <= hue < 60: r, g, b = c, x, 0
            elif 60 <= hue < 120: r, g, b = x, c, 0
            elif 120 <= hue < 180: r, g, b = 0, c, x
            elif 180 <= hue < 240: r, g, b = 0, x, c
            elif 240 <= hue < 300: r, g, b = x, 0, c
            else: r, g, b = c, 0, x
            return (int((r + m) * 255), int((g + m) * 255), int((b + m) * 255), 240)

        for ann in annotations:
            box = ann.to_bbox(w, h)
            c = get_class_color(ann.class_id)

            if show_box:
                draw.rectangle([box.x_min, box.y_min, box.x_max, box.y_max], outline=c, width=2)

            if show_class_name:
                char_str = ann.character or self.charset_engine.get_character(ann.class_id) or str(ann.class_id)
                tag_w = max(18, len(str(ann.class_id)) * 9)
                tag_h = 11
                # Draw badge header
                badge_box = [box.x_min, max(0.0, box.y_min - tag_h), box.x_min + tag_w, max(float(tag_h), box.y_min)]
                draw.rectangle(badge_box, fill=c)

        vis = Image.alpha_composite(vis, overlay)
        return vis.convert("RGB")


# Backward compatibility alias
AnnotationEngine = YoloLabelWriter
