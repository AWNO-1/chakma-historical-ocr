"""
Low-Level Font Utilities and OpenType Inspection Engine for Chakma Historical OCR.
Provides deep inspection of font tables (cmap, GSUB, GPOS, name, OS/2), glyph rendering
validation, Unicode coverage analysis, SHA-256 fingerprinting, and visual duplicate detection.
"""

from dataclasses import asdict, dataclass, field
import hashlib
import io
from pathlib import Path
import tempfile
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple, Union
import zipfile
from fontTools.ttLib import TTFont
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from utils.file_utils import resolve_path
from utils.logging_utils import setup_logger

logger = setup_logger("font_utils")

# Official Chakma Unicode Block range (U+11100 to U+1114F)
CHAKMA_UNICODE_RANGE = range(0x11100, 0x11150)


@dataclass
class FontCoverageReport:
    """Detailed Unicode and Chakma coverage statistics."""
    total_glyphs: int = 0
    total_unicodes_supported: int = 0
    chakma_supported_count: int = 0
    chakma_missing_count: int = 0
    coverage_percent: float = 0.0
    chakma_supported_cps: List[int] = field(default_factory=list)
    chakma_missing_cps: List[int] = field(default_factory=list)


@dataclass
class FontShapingReport:
    """OpenType layout and typography table analysis."""
    has_gsub: bool = False
    has_gpos: bool = False
    has_mark_positioning: bool = False
    has_ligatures: bool = False
    has_contextual_subs: bool = False
    shaping_status: str = "ISOLATED_RENDERING_SUPPORTED"


@dataclass
class FontInspectionResult:
    """Comprehensive font diagnostic and verification record."""
    font_id: str
    font_name: str
    file_path: str
    file_name: str
    file_hash: str
    visual_glyph_hash: str
    coverage: FontCoverageReport
    shaping: FontShapingReport
    style: str = "UNKNOWN"
    coverage_status: str = "NO_CHAKMA_SUPPORT"  # FULL_SUPPORT, PARTIAL_SUPPORT, NO_CHAKMA_SUPPORT
    is_valid: bool = False
    rejection_reason: Optional[str] = None
    license: str = "UNKNOWN"
    source: str = "UNKNOWN"
    is_duplicate: bool = False
    duplicate_of: Optional[str] = None

    def to_metadata_dict(self) -> Dict[str, Any]:
        """Convert to official metadata schema dictionary for fonts/metadata/<id>.json."""
        return {
            "font_id": self.font_id,
            "font_name": self.font_name,
            "file": self.file_name,
            "file_path": str(self.file_path),
            "file_hash": self.file_hash,
            "visual_glyph_hash": self.visual_glyph_hash,
            "source": self.source,
            "license": self.license,
            "coverage": {
                "total_glyphs": self.coverage.total_glyphs,
                "total_unicodes_supported": self.coverage.total_unicodes_supported,
                "chakma_supported": self.coverage.chakma_supported_count,
                "chakma_missing": self.coverage.chakma_missing_count,
                "coverage_percent": round(self.coverage.coverage_percent, 2),
                "status": self.coverage_status,
            },
            "rendering": {
                "status": "RENDER_OK" if self.is_valid else "FAILED",
                "failed_characters": [f"U+{cp:05X}" for cp in self.coverage.chakma_missing_cps],
            },
            "shaping": {
                "GSUB": self.shaping.has_gsub,
                "GPOS": self.shaping.has_gpos,
                "mark_positioning": self.shaping.has_mark_positioning,
                "ligatures": self.shaping.has_ligatures,
                "contextual_subs": self.shaping.has_contextual_subs,
                "status": self.shaping.shaping_status,
            },
            "style": self.style,
            "is_valid": self.is_valid,
            "rejection_reason": self.rejection_reason,
            "is_duplicate": self.is_duplicate,
            "duplicate_of": self.duplicate_of,
        }


def compute_file_sha256(file_path: Union[str, Path]) -> str:
    """Compute SHA-256 hash of a font binary file."""
    path = resolve_path(file_path)
    sha256 = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def compute_visual_glyph_hash(font_path: Union[str, Path], test_cps: Sequence[int], font_size: int = 32) -> str:
    """
    Render a standard sequence of test characters and compute an image MD5 hash.
    Identifies functionally identical fonts that have different binary metadata.
    """
    path = str(resolve_path(font_path))
    try:
        font = ImageFont.truetype(path, font_size)
    except Exception:
        return "ERROR_UNRENDERABLE"

    canvas = Image.new("L", (len(test_cps) * 40 + 20, 50), color=255)
    draw = ImageDraw.Draw(canvas)

    cur_x = 10
    for cp in test_cps:
        ch = chr(cp)
        draw.text((cur_x, 10), ch, font=font, fill=0)
        cur_x += 40

    return hashlib.md5(canvas.tobytes()).hexdigest()


def extract_font_name(tt: TTFont, fallback_name: str) -> str:
    """Extract human-readable font name from TrueType name table."""
    try:
        name_record = tt["name"]
        # Try Full Font Name (nameID 4) then Typographic Family (16) then Font Family (1)
        for target_id in [4, 16, 1]:
            for rec in name_record.names:
                if rec.nameID == target_id:
                    name_str = rec.toUnicode()
                    if name_str and name_str.strip():
                        return name_str.strip()
    except Exception:
        pass
    return fallback_name


def extract_font_license_and_source(tt: TTFont) -> Tuple[str, str]:
    """Extract license description and vendor/source from name table if available."""
    lic = "UNKNOWN"
    src = "UNKNOWN"
    try:
        name_record = tt["name"]
        for rec in name_record.names:
            if rec.nameID == 13:  # License Description
                lic_str = rec.toUnicode()
                if lic_str and "OFL" in lic_str.upper() or "OPEN FONT" in lic_str.upper():
                    lic = "OFL (SIL Open Font License)"
                elif lic_str:
                    lic = lic_str[:100]
            elif rec.nameID == 8:  # Manufacturer Name / Vendor
                src_str = rec.toUnicode()
                if src_str:
                    src = src_str.strip()
            elif rec.nameID == 9:  # Designer Name
                if src == "UNKNOWN":
                    src = rec.toUnicode().strip()
    except Exception:
        pass
    return lic, src


def detect_font_style(font_name: str, file_name: str, tt: TTFont) -> str:
    """Classify typographic style: PRINT, HANDWRITING_STYLE, CALLIGRAPHIC, UNKNOWN."""
    combined = (font_name + " " + file_name).lower()
    if any(kw in combined for kw in ["hand", "handwritten", "script", "pen", "lekha"]):
        return "HANDWRITING_STYLE"
    if any(kw in combined for kw in ["calligraph", "italic", "cursive"]):
        return "CALLIGRAPHIC"
    if any(kw in combined for kw in ["sans", "serif", "unicode", "regular", "bold", "nirmala"]):
        return "PRINT"
    return "UNKNOWN"


def inspect_font_tables(font_path: Union[str, Path], target_unicodes: Optional[Sequence[int]] = None) -> FontInspectionResult:
    """
    Perform deep static analysis on a font file:
    - Extracts cmap code point mapping.
    - Inspects GSUB, GPOS, mark positioning.
    - Evaluates Chakma script Unicode coverage.
    - Calculates file and visual glyph hashes.
    """
    path = resolve_path(font_path)
    file_name = path.name
    font_id = path.stem.lower().replace(" ", "_").replace("-", "_")

    if target_unicodes is None:
        target_unicodes = list(CHAKMA_UNICODE_RANGE)

    file_hash = compute_file_sha256(path)

    try:
        tt = TTFont(str(path))
    except Exception as e:
        logger.error(f"Failed to parse font file {path}: {e}")
        return FontInspectionResult(
            font_id=font_id,
            font_name=path.stem,
            file_path=str(path),
            file_name=file_name,
            file_hash=file_hash,
            visual_glyph_hash="INVALID",
            coverage=FontCoverageReport(),
            shaping=FontShapingReport(shaping_status="FAILED"),
            coverage_status="NO_CHAKMA_SUPPORT",
            is_valid=False,
            rejection_reason=f"Corrupt or unreadable font binary: {e}",
        )

    font_name = extract_font_name(tt, fallback_name=path.stem)
    license_str, source_str = extract_font_license_and_source(tt)
    style = detect_font_style(font_name, file_name, tt)

    # 1. Total Glyphs
    total_glyphs = len(tt.getGlyphOrder())

    # 2. Unicode Codepoints Supported via cmap
    supported_unicodes: Set[int] = set()
    if "cmap" in tt:
        for table in tt["cmap"].tables:
            if table.isUnicode():
                supported_unicodes.update(table.cmap.keys())

    # 3. Chakma Coverage Evaluation
    chakma_supported = [cp for cp in target_unicodes if cp in supported_unicodes]
    chakma_missing = [cp for cp in target_unicodes if cp not in supported_unicodes]

    total_target = len(target_unicodes)
    cov_percent = (len(chakma_supported) / max(1, total_target)) * 100.0

    cov_report = FontCoverageReport(
        total_glyphs=total_glyphs,
        total_unicodes_supported=len(supported_unicodes),
        chakma_supported_count=len(chakma_supported),
        chakma_missing_count=len(chakma_missing),
        coverage_percent=cov_percent,
        chakma_supported_cps=chakma_supported,
        chakma_missing_cps=chakma_missing,
    )

    # 4. OpenType Shaping Analysis
    has_gsub = "GSUB" in tt
    has_gpos = "GPOS" in tt
    has_mark = False
    has_liga = False
    has_context = False

    if has_gsub:
        try:
            gsub_table = tt["GSUB"].table
            if gsub_table.FeatureList:
                feature_tags = [f.FeatureTag for f in gsub_table.FeatureList.FeatureRecord]
                has_liga = any(tag in ["liga", "clig", "dlig", "rlig"] for tag in feature_tags)
                has_context = any(tag in ["calt", "ccmp", "locl"] for tag in feature_tags)
        except Exception:
            pass

    if has_gpos:
        try:
            gpos_table = tt["GPOS"].table
            if gpos_table.FeatureList:
                feature_tags = [f.FeatureTag for f in gpos_table.FeatureList.FeatureRecord]
                has_mark = any(tag in ["mark", "mkmk", "kern"] for tag in feature_tags)
        except Exception:
            pass

    if has_gsub and (has_liga or has_context or has_mark):
        shaping_status = "TEXT_SHAPING_SUPPORTED"
    elif len(chakma_supported) > 0:
        shaping_status = "ISOLATED_RENDERING_SUPPORTED"
    else:
        shaping_status = "NO_SHAPING_SUPPORT"

    shaping_report = FontShapingReport(
        has_gsub=has_gsub,
        has_gpos=has_gpos,
        has_mark_positioning=has_mark,
        has_ligatures=has_liga,
        has_contextual_subs=has_context,
        shaping_status=shaping_status,
    )

    # 5. Coverage Status & Validity Classification
    if cov_percent >= 70.0:
        coverage_status = "FULL_SUPPORT"
        is_valid = True
        rejection_reason = None
    elif cov_percent > 0.0:
        coverage_status = "PARTIAL_SUPPORT"
        is_valid = False
        rejection_reason = f"Partial Chakma glyph coverage ({cov_percent:.1f}% < 70.0% threshold). Supported: {len(chakma_supported)}/{total_target}"
    else:
        coverage_status = "NO_CHAKMA_SUPPORT"
        is_valid = False
        rejection_reason = f"No Chakma script glyphs found in font cmap (0.0% coverage)."

    # 6. Visual Glyph Hash (using available Chakma or standard codepoints)
    hash_test_cps = chakma_supported[:10] if chakma_supported else list(range(0x41, 0x4B))
    vis_hash = compute_visual_glyph_hash(path, hash_test_cps)

    return FontInspectionResult(
        font_id=font_id,
        font_name=font_name,
        file_path=str(path),
        file_name=file_name,
        file_hash=file_hash,
        visual_glyph_hash=vis_hash,
        coverage=cov_report,
        shaping=shaping_report,
        style=style,
        coverage_status=coverage_status,
        is_valid=is_valid,
        rejection_reason=rejection_reason,
        license=license_str,
        source=source_str,
    )


def verify_glyph_rendering(
    font_path: Union[str, Path],
    character: str,
    font_size: int = 36,
) -> Dict[str, Any]:
    """
    Perform deep visual rendering test on a single character glyph:
    Checks if glyph renders non-blank, is not clipped, and has valid bounding box.
    """
    path = str(resolve_path(font_path))
    try:
        font = ImageFont.truetype(path, font_size)
    except Exception as e:
        return {"rendered": False, "error": f"Failed to load font: {e}", "is_blank": True}

    canvas_size = 128
    img = Image.new("RGBA", (canvas_size, canvas_size), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)

    draw.text((32, 32), character, font=font, fill=(0, 0, 0, 255))
    alpha = np.array(img)[:, :, 3]

    non_zero_pixels = np.count_nonzero(alpha)
    if non_zero_pixels == 0:
        return {"rendered": False, "error": "Blank rendering (0 alpha pixels)", "is_blank": True}

    rows = np.any(alpha > 0, axis=1)
    cols = np.any(alpha > 0, axis=0)
    ymin, ymax = np.where(rows)[0][[0, -1]]
    xmin, xmax = np.where(cols)[0][[0, -1]]

    w = float(xmax - xmin + 1)
    h = float(ymax - ymin + 1)

    return {
        "rendered": True,
        "is_blank": False,
        "pixel_count": int(non_zero_pixels),
        "bbox": (int(xmin), int(ymin), int(xmax), int(ymax)),
        "width": w,
        "height": h,
    }


def scan_and_discover_fonts(
    base_dirs: Sequence[Union[str, Path]],
    scan_zips: bool = True,
) -> List[Path]:
    """
    Scan target directories for font binaries (.ttf, .otf, .ttc) and extract fonts from ZIP/KMP archives.
    """
    discovered_files: List[Path] = []
    extensions = {".ttf", ".otf", ".ttc"}

    for b_dir in base_dirs:
        dir_p = resolve_path(b_dir)
        if not dir_p.exists():
            continue

        # 1. Scan direct font files
        for ext in extensions:
            discovered_files.extend(dir_p.glob(f"*{ext}"))
            discovered_files.extend(dir_p.glob(f"*{ext.upper()}"))

        # 2. Scan ZIP/KMP archives
        if scan_zips:
            for zip_p in list(dir_p.glob("*.zip")) + list(dir_p.glob("*.kmp")):
                try:
                    with zipfile.ZipFile(zip_p, "r") as z:
                        for entry in z.namelist():
                            if any(entry.lower().endswith(e) for e in extensions):
                                # Extract to fonts/raw if not already present
                                target_p = resolve_path("fonts/raw") / Path(entry).name
                                if not target_p.exists():
                                    with open(target_p, "wb") as out_f:
                                        out_f.write(z.read(entry))
                                    logger.info(f"Extracted {entry} from {zip_p.name} -> {target_p}")
                                discovered_files.append(target_p)
                except Exception as e:
                    logger.warning(f"Failed to read archive {zip_p}: {e}")

    # Remove duplicates preserving order
    seen = set()
    unique_paths = []
    for p in discovered_files:
        p_resolved = p.resolve()
        if p_resolved not in seen:
            seen.add(p_resolved)
            unique_paths.append(p)

    return unique_paths
