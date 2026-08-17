"""
Authoritative Font Discovery, Verification, and Registration Engine for Chakma Historical OCR.
Manages font lifecycle: discovery, OpenType table inspection, Unicode/Chakma glyph coverage,
rendering verification, visual deduplication, metadata persistence, and YAML registry export.
"""

from dataclasses import asdict, dataclass, field
import io
import json
from pathlib import Path
import random
import shutil
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple, Union
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import yaml

from generator.charset_engine import CharsetEngine, ChakmaClass
from utils.file_utils import ensure_dir, resolve_path, save_json, save_yaml
from utils.font_utils import (
    CHAKMA_UNICODE_RANGE,
    FontInspectionResult,
    compute_file_sha256,
    inspect_font_tables,
    scan_and_discover_fonts,
    verify_glyph_rendering,
)
from utils.logging_utils import setup_logger

logger = setup_logger("font_engine")


@dataclass
class FontMetadata:
    """
    Authoritative runtime and serialized metadata for a validated font.
    """
    id: str
    name: str
    file_name: str
    path: str
    style: str
    coverage_percent: float
    total_glyphs: int
    chakma_supported: int
    chakma_missing: int
    coverage_status: str  # FULL_SUPPORT, PARTIAL_SUPPORT, NO_CHAKMA_SUPPORT
    shaping_status: str   # TEXT_SHAPING_SUPPORTED, ISOLATED_RENDERING_SUPPORTED
    license: str
    source: str
    enabled_for_synthetic: bool = True
    is_duplicate: bool = False
    duplicate_of: Optional[str] = None
    file_hash: str = ""
    visual_glyph_hash: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class FontEngine:
    """
    Authoritative Font Management and Selection Engine.
    Discovers, validates, registers, and serves Chakma TrueType/OpenType fonts.
    """

    def __init__(
        self,
        base_dir: Union[str, Path] = "fonts",
        charset_engine: Optional[CharsetEngine] = None,
        min_coverage_threshold: float = 70.0,
        seed: int = 42,
        auto_discover: bool = True,
    ):
        self.base_dir = resolve_path(base_dir)
        self.raw_dir = ensure_dir(self.base_dir / "raw")
        self.validated_dir = ensure_dir(self.base_dir / "validated")
        self.rejected_dir = ensure_dir(self.base_dir / "rejected")
        self.metadata_dir = ensure_dir(self.base_dir / "metadata")
        self.collections_dir = ensure_dir(self.base_dir / "collections")

        self.charset_engine = charset_engine if charset_engine is not None else CharsetEngine()
        self.min_coverage_threshold = min_coverage_threshold
        self.seed = seed
        self._rng = random.Random(seed)

        self._fonts: Dict[str, FontMetadata] = {}
        self._valid_font_ids: List[str] = []
        self._rejected_font_ids: List[str] = []
        self._font_cache: Dict[Tuple[str, int], ImageFont.FreeTypeFont] = {}
        self._inspection_results: Dict[str, FontInspectionResult] = {}

        if auto_discover:
            self.refresh()

    def set_seed(self, seed: int) -> None:
        """Set random seed for deterministic font sampling."""
        self.seed = seed
        self._rng = random.Random(seed)

    def refresh(self) -> None:
        """
        Run full discovery, validation, deduplication, and registration pipeline.
        """
        logger.info("Starting Font Engine discovery and verification cycle...")
        self._fonts.clear()
        self._valid_font_ids.clear()
        self._rejected_font_ids.clear()
        self._inspection_results.clear()

        # Target Unicode codepoints from CharsetEngine (or official range)
        target_cps = []
        for c in self.charset_engine.get_all_classes():
            if c.unicode:
                try:
                    cp = int(c.unicode.upper().replace("U+", "").replace("0X", "").strip(), 16)
                    target_cps.append(cp)
                except ValueError:
                    if c.character:
                        target_cps.append(ord(c.character))
            elif c.character:
                target_cps.append(ord(c.character))

        if not target_cps:
            target_cps = list(CHAKMA_UNICODE_RANGE)

        # 1. Discover all candidate font files in raw and collections
        search_dirs = [self.raw_dir, self.collections_dir]
        discovered_paths = scan_and_discover_fonts(search_dirs, scan_zips=True)
        logger.info(f"Discovered {len(discovered_paths)} candidate font binaries.")

        # 2. Inspect each font
        seen_file_hashes: Dict[str, str] = {}

        for font_path in discovered_paths:
            insp = inspect_font_tables(font_path, target_unicodes=target_cps)

            # Deduplication Check: File Binary SHA-256
            if insp.file_hash in seen_file_hashes:
                insp.is_duplicate = True
                insp.duplicate_of = seen_file_hashes[insp.file_hash]
                logger.info(f"Detected binary duplicate font: {insp.file_name} is identical to {insp.duplicate_of}")
            else:
                seen_file_hashes[insp.file_hash] = insp.font_id

            # Determine eligibility
            is_eligible = (
                insp.is_valid
                and not insp.is_duplicate
                and insp.coverage.coverage_percent >= self.min_coverage_threshold
            )

            meta = FontMetadata(
                id=insp.font_id,
                name=insp.font_name,
                file_name=insp.file_name,
                path=insp.file_path,
                style=insp.style,
                coverage_percent=round(insp.coverage.coverage_percent, 2),
                total_glyphs=insp.coverage.total_glyphs,
                chakma_supported=insp.coverage.chakma_supported_count,
                chakma_missing=insp.coverage.chakma_missing_count,
                coverage_status=insp.coverage_status,
                shaping_status=insp.shaping.shaping_status,
                license=insp.license,
                source=insp.source,
                enabled_for_synthetic=is_eligible,
                is_duplicate=insp.is_duplicate,
                duplicate_of=insp.duplicate_of,
                file_hash=insp.file_hash,
                visual_glyph_hash=insp.visual_glyph_hash,
            )

            self._fonts[insp.font_id] = meta
            self._inspection_results[insp.font_id] = insp

            # 3. Save JSON metadata
            meta_json_path = self.metadata_dir / f"{insp.font_id}.json"
            save_json(insp.to_metadata_dict(), meta_json_path)

            # 4. Copy to validated / rejected directories
            src_file = Path(insp.file_path)
            if is_eligible:
                self._valid_font_ids.append(insp.font_id)
                dst_val = self.validated_dir / insp.file_name
                if not dst_val.exists() and src_file.exists():
                    shutil.copy2(src_file, dst_val)
                logger.info(f"Accepted Font [{insp.font_id}]: {insp.font_name} ({insp.coverage.coverage_percent:.1f}% coverage, style: {insp.style})")
            else:
                self._rejected_font_ids.append(insp.font_id)
                dst_rej = self.rejected_dir / insp.file_name
                if not dst_rej.exists() and src_file.exists():
                    shutil.copy2(src_file, dst_rej)
                logger.warning(f"Rejected Font [{insp.font_id}]: {insp.font_name} - Reason: {insp.rejection_reason or 'Duplicate'}")

        # 5. Export authoritative config/fonts.yaml
        self.export_fonts_yaml()

        logger.info(f"FontEngine initialized: {len(self._valid_font_ids)} accepted, {len(self._rejected_font_ids)} rejected.")

    def get_supported_fonts(self) -> List[FontMetadata]:
        """Return list of all registered valid fonts enabled for synthetic generation."""
        return [self._fonts[fid] for fid in self._valid_font_ids if self._fonts[fid].enabled_for_synthetic]

    def get_all_discovered_fonts(self) -> List[FontMetadata]:
        """Return metadata for all discovered fonts (valid and rejected)."""
        return list(self._fonts.values())

    def get_random_font(self, seed: Optional[int] = None, fallback_to_default: bool = True) -> FontMetadata:
        """
        Deterministically select a random validated font.
        """
        valid_fonts = self.get_supported_fonts()
        if not valid_fonts:
            if fallback_to_default:
                # Return default fallback metadata
                return FontMetadata(
                    id="fallback_font",
                    name="Default Fallback",
                    file_name="",
                    path="",
                    style="PRINT",
                    coverage_percent=100.0,
                    total_glyphs=71,
                    chakma_supported=71,
                    chakma_missing=0,
                    coverage_status="FULL_SUPPORT",
                    shaping_status="ISOLATED_RENDERING_SUPPORTED",
                    license="UNKNOWN",
                    source="SYSTEM",
                )
            raise RuntimeError("No validated Chakma fonts available in FontEngine registry.")

        rng = random.Random(seed) if seed is not None else self._rng
        return rng.choice(valid_fonts)

    def get_font(self, font_id_or_name: Union[str, Path, FontMetadata], size: int = 32) -> ImageFont.FreeTypeFont:
        """
        Retrieve cached PIL TrueType/FreeType font handle at requested pixel size.
        """
        if isinstance(font_id_or_name, FontMetadata):
            fid = font_id_or_name.id
            font_path = font_id_or_name.path
        elif isinstance(font_id_or_name, Path):
            p = resolve_path(font_id_or_name)
            fid = p.stem.lower().replace(" ", "_").replace("-", "_")
            font_path = str(p)
        else:
            fid = str(font_id_or_name)
            if fid in self._fonts:
                font_path = self._fonts[fid].path
            else:
                fid_lower = fid.lower()
                matched = next((
                    m for m in self._fonts.values()
                    if m.name.lower() == fid_lower
                    or Path(m.path).stem.lower() == fid_lower
                    or Path(m.file_name).name.lower() == fid_lower
                ), None)
                if matched:
                    fid = matched.id
                    font_path = matched.path
                elif Path(fid).exists():
                    font_path = str(resolve_path(fid))
                else:
                    first_valid = self.get_supported_fonts()
                    if first_valid:
                        fid = first_valid[0].id
                        font_path = first_valid[0].path
                    else:
                        return ImageFont.load_default()

        cache_key = (fid, size)
        if cache_key not in self._font_cache:
            try:
                self._font_cache[cache_key] = ImageFont.truetype(str(font_path), size)
            except Exception as e:
                logger.error(f"Failed to load font '{font_path}' at size {size}: {e}")
                self._font_cache[cache_key] = ImageFont.load_default()

        return self._font_cache[cache_key]

    def supports_character(self, font_id: str, character_or_codepoint: Union[str, int]) -> bool:
        """Check if a specific font supports a given character or Unicode codepoint."""
        cp = ord(character_or_codepoint) if isinstance(character_or_codepoint, str) else character_or_codepoint
        insp = self._inspection_results.get(font_id)
        if not insp:
            return False
        return cp in insp.coverage.chakma_supported_cps

    def get_font_metadata(self, font_id: str) -> Optional[FontMetadata]:
        """Return authoritative metadata for a given font ID."""
        return self._fonts.get(font_id)

    def get_font_coverage(self, font_id: str) -> Optional[Dict[str, Any]]:
        """Return coverage details dictionary for a given font."""
        meta = self._fonts.get(font_id)
        if not meta:
            return None
        return {
            "font_id": meta.id,
            "font_name": meta.name,
            "coverage_percent": meta.coverage_percent,
            "chakma_supported": meta.chakma_supported,
            "chakma_missing": meta.chakma_missing,
            "status": meta.coverage_status,
        }

    def export_fonts_yaml(self, output_path: Union[str, Path] = "config/fonts.yaml") -> Path:
        """
        Export registered valid fonts to authoritative YAML configuration.
        """
        out_p = resolve_path(output_path)
        ensure_dir(out_p.parent)

        data = {
            "version": "1.0",
            "min_coverage_threshold": self.min_coverage_threshold,
            "total_fonts_discovered": len(self._fonts),
            "total_fonts_valid": len(self._valid_font_ids),
            "total_fonts_rejected": len(self._rejected_font_ids),
            "fonts": [
                {
                    "id": m.id,
                    "name": m.name,
                    "file": m.file_name,
                    "path": str(Path("fonts/validated") / m.file_name),
                    "coverage": "full" if m.coverage_percent >= 90.0 else "partial",
                    "coverage_percent": m.coverage_percent,
                    "style": m.style,
                    "shaping": m.shaping_status,
                    "enabled_for_synthetic": m.enabled_for_synthetic,
                }
                for m in self.get_supported_fonts()
            ],
        }

        save_yaml(data, out_p)
        logger.info(f"Exported font registry ({len(data['fonts'])} fonts) to {out_p}")
        return out_p

    def generate_font_previews(
        self,
        output_dir: Union[str, Path] = "debug/fonts",
        font_size: int = 36,
    ) -> List[Path]:
        """
        Generate high-resolution grid preview PNG images for every validated font:
        Shows Class ID, Character, Unicode, and Rendered Glyph.
        """
        out_d = ensure_dir(output_dir)
        classes = self.charset_engine.get_all_classes()
        generated: List[Path] = []

        for fid in self._valid_font_ids:
            meta = self._fonts[fid]
            font = self.get_font(meta, size=font_size)
            header_font = ImageFont.load_default()

            cols = 6
            rows = (len(classes) + cols - 1) // cols
            cell_w, cell_h = 160, 100
            padding = 20

            img_w = cols * cell_w + padding * 2
            img_h = rows * cell_h + padding * 2 + 60

            canvas = Image.new("RGB", (img_w, img_h), (250, 248, 244))
            draw = ImageDraw.Draw(canvas)

            # Title Header
            title = f"Chakma Font Preview: {meta.name} ({meta.style}) — Coverage: {meta.coverage_percent:.1f}%"
            draw.text((padding, 15), title, fill=(30, 30, 30), font=header_font)
            draw.line([(padding, 45), (img_w - padding, 45)], fill=(180, 180, 180), width=1)

            for idx, c in enumerate(classes):
                col = idx % cols
                row = idx // cols
                x = padding + col * cell_w
                y = padding + 60 + row * cell_h

                # Cell background & border
                draw.rectangle([x, y, x + cell_w - 6, y + cell_h - 6], fill=(255, 255, 255), outline=(220, 220, 220))

                # Badge Header: ID and Unicode
                badge_txt = f"ID: {c.id:02d} | {c.unicode or 'N/A'}"
                draw.text((x + 8, y + 6), badge_txt, fill=(100, 100, 100), font=header_font)

                # Rendered Glyph
                char_to_render = c.character if c.character else "?"
                draw.text((x + 50, y + 32), char_to_render, fill=(20, 20, 20), font=font)

            out_path = out_d / f"font_preview_{fid}.png"
            canvas.save(out_path)
            generated.append(out_path)
            logger.info(f"Saved font preview -> {out_path}")

        return generated

    def generate_contact_sheet(
        self,
        output_path: Union[str, Path] = "debug/fonts/font_comparison_contact_sheet.png",
        sample_count: int = 16,
    ) -> Path:
        """
        Generate a side-by-side Contact Sheet comparing identical Chakma characters across all accepted fonts.
        """
        out_p = resolve_path(output_path)
        ensure_dir(out_p.parent)

        valid_fonts = self.get_supported_fonts()
        if not valid_fonts:
            raise RuntimeError("No valid fonts to compare in contact sheet.")

        classes = self.charset_engine.get_all_classes()[:sample_count]
        cell_w = 90
        cell_h = 75
        header_h = 80
        col_header_w = 140

        img_w = col_header_w + len(valid_fonts) * cell_w + 30
        img_h = header_h + len(classes) * cell_h + 30

        canvas = Image.new("RGB", (img_w, img_h), (248, 246, 240))
        draw = ImageDraw.Draw(canvas)
        def_font = ImageFont.load_default()

        # Title
        draw.text((20, 15), "Chakma OCR Font Comparison Contact Sheet (Side-by-Side Glyph Diversity)", fill=(20, 20, 20), font=def_font)

        # Column Headers (Font Names)
        for col_idx, f_meta in enumerate(valid_fonts):
            col_x = col_header_w + col_idx * cell_w
            short_name = f_meta.name[:12]
            draw.text((col_x + 5, 45), short_name, fill=(40, 40, 90), font=def_font)
            draw.text((col_x + 5, 60), f"({f_meta.style[:5]})", fill=(120, 120, 120), font=def_font)

        # Rows (Characters)
        for row_idx, c in enumerate(classes):
            row_y = header_h + row_idx * cell_h

            # Row Header
            lbl = f"ID {c.id:02d} [{c.name[:8]}]\n{c.unicode or ''}"
            draw.text((15, row_y + 15), lbl, fill=(50, 50, 50), font=def_font)
            draw.line([(10, row_y), (img_w - 10, row_y)], fill=(225, 225, 225), width=1)

            char_str = c.character if c.character else "?"

            # Render in each font
            for col_idx, f_meta in enumerate(valid_fonts):
                col_x = col_header_w + col_idx * cell_w
                f_font = self.get_font(f_meta, size=32)

                draw.rectangle([col_x + 2, row_y + 4, col_x + cell_w - 4, row_y + cell_h - 4], fill=(255, 255, 255), outline=(235, 235, 235))
                draw.text((col_x + 28, row_y + 18), char_str, fill=(15, 15, 15), font=f_font)

        canvas.save(out_p)
        logger.info(f"Saved font contact sheet -> {out_p}")
        return out_p

    def generate_inventory_report(
        self,
        output_dir: Union[str, Path] = "debug/fonts",
    ) -> Tuple[Path, Path]:
        """
        Generate comprehensive Font Inventory Report in HTML and Markdown formats.
        """
        out_d = ensure_dir(output_dir)
        all_fonts = self.get_all_discovered_fonts()

        valid_count = len(self._valid_font_ids)
        rejected_count = len(self._rejected_font_ids)
        full_count = sum(1 for f in all_fonts if f.coverage_status == "FULL_SUPPORT" and not f.is_duplicate)
        partial_count = sum(1 for f in all_fonts if f.coverage_status == "PARTIAL_SUPPORT")
        no_cov_count = sum(1 for f in all_fonts if f.coverage_status == "NO_CHAKMA_SUPPORT")

        # 1. Markdown Report
        md_lines = [
            "# Chakma Font Discovery & Verification Inventory Report",
            "",
            "## Summary Statistics",
            f"- **Total Discovered Fonts**: {len(all_fonts)}",
            f"- **Accepted / Validated Fonts**: {valid_count}",
            f"- **Rejected Fonts**: {rejected_count}",
            f"- **Full Support Fonts (>=70%)**: {full_count}",
            f"- **Partial Support Fonts (<70%)**: {partial_count}",
            f"- **No Chakma Support (0%)**: {no_cov_count}",
            "",
            "## Complete Font Registry Table",
            "| Font ID | Font Name | File Name | Style | Coverage (%) | Chakma Supported | Shaping Status | Status | Rejection Reason |",
            "| :--- | :--- | :--- | :--- | :---: | :---: | :--- | :--- | :--- |",
        ]

        for f in all_fonts:
            status_tag = "✅ VALID" if f.enabled_for_synthetic else ("⚠️ DUPLICATE" if f.is_duplicate else "❌ REJECTED")
            reason = f.duplicate_of or (self._inspection_results[f.id].rejection_reason if f.id in self._inspection_results else "N/A")
            md_lines.append(
                f"| `{f.id}` | **{f.name}** | `{f.file_name}` | {f.style} | {f.coverage_percent:.1f}% | {f.chakma_supported}/{f.chakma_supported + f.chakma_missing} | {f.shaping_status} | {status_tag} | {reason} |"
            )

        md_path = out_d / "font_inventory_report.md"
        md_path.write_text("\n".join(md_lines), encoding="utf-8")

        # 2. HTML Report
        html_rows = []
        for f in all_fonts:
            status_badge = "<span style='color: green; font-weight: bold;'>VALID</span>" if f.enabled_for_synthetic else (
                f"<span style='color: orange; font-weight: bold;'>DUPLICATE ({f.duplicate_of})</span>" if f.is_duplicate else
                "<span style='color: red; font-weight: bold;'>REJECTED</span>"
            )
            reason = f.duplicate_of or (self._inspection_results[f.id].rejection_reason if f.id in self._inspection_results else "N/A")
            html_rows.append(f"""
            <tr>
              <td><code>{f.id}</code></td>
              <td><strong>{f.name}</strong></td>
              <td><code>{f.file_name}</code></td>
              <td>{f.style}</td>
              <td style='text-align: center;'>{f.coverage_percent:.1f}%</td>
              <td style='text-align: center;'>{f.chakma_supported} / {f.chakma_supported + f.chakma_missing}</td>
              <td>{f.shaping_status}</td>
              <td>{status_badge}</td>
              <td style='font-size: 0.85em; color: #666;'>{reason}</td>
            </tr>
            """)

        html_content = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Chakma Font Discovery & Verification Report</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; margin: 30px; background: #fafafa; color: #222; }}
    h1 {{ color: #1a237e; border-bottom: 2px solid #1a237e; padding-bottom: 10px; }}
    .stats {{ display: flex; gap: 20px; margin-bottom: 25px; }}
    .card {{ background: #fff; border: 1px solid #ddd; border-radius: 8px; padding: 15px 25px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }}
    .card h3 {{ margin: 0 0 5px 0; font-size: 0.9em; color: #666; }}
    .card p {{ margin: 0; font-size: 1.8em; font-weight: bold; color: #1a237e; }}
    table {{ width: 100%; border-collapse: collapse; background: #fff; box-shadow: 0 2px 4px rgba(0,0,0,0.05); border-radius: 8px; overflow: hidden; }}
    th, td {{ padding: 12px 15px; border-bottom: 1px solid #eee; text-align: left; }}
    th {{ background: #f0f2f5; font-weight: 600; color: #333; }}
    tr:hover {{ background: #f9fbfd; }}
    code {{ background: #eee; padding: 2px 6px; border-radius: 4px; font-size: 0.9em; }}
  </style>
</head>
<body>
  <h1>Chakma Script Font Inventory & Verification Report</h1>
  <div class="stats">
    <div class="card"><h3>Total Discovered</h3><p>{len(all_fonts)}</p></div>
    <div class="card"><h3>Accepted (Valid)</h3><p style="color: green;">{valid_count}</p></div>
    <div class="card"><h3>Rejected</h3><p style="color: red;">{rejected_count}</p></div>
    <div class="card"><h3>Full Support</h3><p>{full_count}</p></div>
    <div class="card"><h3>Partial Support</h3><p>{partial_count}</p></div>
  </div>
  <table>
    <thead>
      <tr>
        <th>Font ID</th><th>Name</th><th>File</th><th>Style</th><th>Coverage</th><th>Chakma Glyphs</th><th>Shaping</th><th>Status</th><th>Notes / Reason</th>
      </tr>
    </thead>
    <tbody>
      {''.join(html_rows)}
    </tbody>
  </table>
</body>
</html>
"""
        html_path = out_d / "font_inventory_report.html"
        html_path.write_text(html_content, encoding="utf-8")
        logger.info(f"Saved inventory reports -> {md_path.name} and {html_path.name}")
        return md_path, html_path
