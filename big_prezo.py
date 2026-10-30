from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any, Iterable

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.util import Inches, Pt

_MARKER_TOC = "BigPrezo::GeneratedToc"
_MARKER_HOME = "BigPrezo::Home::"
_SECTION_WORDS = re.compile(r"\b(part|section|chapter|appendix|appendices|workstream|agenda|overview|closing|q\s*&\s*a)\b", re.I)
_MAX_ROW_CHARS = 96
_DEFAULT_ROWS_PER_TOC = 18


def _shape_text(shape: Any) -> str:
    if not getattr(shape, "has_text_frame", False):
        return ""
    return "\n".join(p.text for p in shape.text_frame.paragraphs).strip()


def _slide_text(slide: Any) -> list[str]:
    return [text for shape in slide.shapes if (text := _shape_text(shape))]


def _slide_title(slide: Any, texts: list[str]) -> str:
    title_shape = getattr(slide.shapes, "title", None)
    title = _shape_text(title_shape) if title_shape is not None else ""
    if title:
        return title
    return next((line.strip() for text in texts for line in text.splitlines() if line.strip()), "")


def probable_section_boundary(title: str, compact_text: str, *, max_body_chars: int = 140) -> bool:
    """Return true when a titled slide uses section vocabulary and has little body copy."""
    title = (title or "").strip()
    if not title:
        return False
    body = compact_text.replace(title, "", 1).strip()
    explicit = bool(_SECTION_WORDS.search(title))
    sparse = len(body) <= max_body_chars
    return explicit and sparse


def manifest_for_slides(slides: Iterable[Any], *, compact_limit: int = 500) -> dict[str, Any]:
    records = []
    section = "Opening"
    for number, slide in enumerate(slides, 1):
        texts = _slide_text(slide)
        title = _slide_title(slide, texts)
        compact = re.sub(r"\s+", " ", " | ".join(texts)).strip()[:compact_limit]
        boundary = probable_section_boundary(title, compact)
        if boundary:
            section = title
        records.append({
            "slide_number": number,
            "title": title,
            "compact_text": compact,
            "probable_section_boundary": boundary,
            "section": section,
        })
    section_count = sum(record["probable_section_boundary"] for record in records)
    return {
        "source_slide_count": len(records),
        "section_detection": {
            "probable_section_count": section_count,
            "all_slides_fallback": section_count == 0,
        },
        "slides": records,
    }


def _remove_shape(slide: Any, shape: Any) -> None:
    shape._element.getparent().remove(shape._element)


def _delete_slide(prs: Any, slide: Any) -> None:
    for sld_id in list(prs.slides._sldIdLst):
        if prs.part.related_part(sld_id.rId).partname == slide.part.partname:
            prs.slides._sldIdLst.remove(sld_id)
            prs.part.drop_rel(sld_id.rId)
            return


def _remove_generated_navigation(prs: Any) -> None:
    """Remove only shapes/slides explicitly marked as engine-owned."""
    for slide in list(prs.slides):
        generated_toc = any(shape.name == _MARKER_TOC for shape in slide.shapes)
        if generated_toc:
            for sld_id in list(slide_ids):
                if prs.part.related_part(sld_id.rId).partname == slide.part.partname:
                    slide_ids.remove(sld_id)
                    prs.part.drop_rel(sld_id.rId)
                    break
            continue
        for shape in list(slide.shapes):
            if shape.name.startswith(_MARKER_HOME):
                _remove_shape(slide, shape)


def _set_hyperlink(shape: Any, target_slide: Any) -> None:
    shape.click_action.target_slide = target_slide


def _add_text_shape(slide: Any, x: int, y: int, w: int, h: int, text: str,
                    *, font_size: int, color: RGBColor, bold: bool = False,
                    name: str | None = None, align: Any = PP_ALIGN.LEFT,
                    fill: RGBColor | None = None) -> Any:
    shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE if fill else MSO_SHAPE.RECTANGLE,
                                   x, y, w, h)
    if name:
        shape.name = name
    if fill:
        shape.fill.solid()
        shape.fill.fore_color.rgb = fill
        shape.line.fill.background()
    else:
        shape.fill.background()
        shape.line.fill.background()
    tf = shape.text_frame
    tf.clear()
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    tf.margin_left = Inches(0.12)
    tf.margin_right = Inches(0.12)
    tf.margin_top = Inches(0.02)
    tf.margin_bottom = Inches(0.02)
    p = tf.paragraphs[0]
    p.alignment = align
    run = p.add_run()
    run.text = text
    run.font.name = "Aptos"
    run.font.size = Pt(font_size)
    run.font.bold = bold
    run.font.color.rgb = color
    return shape


def _insert_slides_at_front(prs: Any, new_slides: list[Any]) -> None:
    sld_ids = prs.slides._sldIdLst
    for slide in reversed(new_slides):
        for sld_id in list(sld_ids):
            if prs.part.related_part(sld_id.rId).partname == slide.part.partname:
                sld_ids.remove(sld_id)
                sld_ids.insert(0, sld_id)
                break


def _add_home_button(slide: Any, target: Any, number: int, width: int, height: int) -> None:
    button_w, button_h = Inches(0.86), Inches(0.30)
    margin = Inches(0.18)
    x = max(Inches(0.1), width - button_w - margin)
    y = max(Inches(0.1), height - button_h - margin)
    button = _add_text_shape(slide, x, y, button_w, button_h, "HOME / TOC",
                             font_size=9, color=RGBColor(255, 255, 255), bold=True,
                             name=f"{_MARKER_HOME}{number}", align=PP_ALIGN.CENTER,
                             fill=RGBColor(31, 78, 121))
    _set_hyperlink(button, target)


def _section_label(record: dict[str, Any]) -> str:
    return str(record.get("section") or "Slides")


def _add_toc_slides(prs: Any, source_slides: list[Any], manifest: dict[str, Any],
                    *, rows_per_toc: int = _DEFAULT_ROWS_PER_TOC) -> list[Any]:
    layout = prs.slide_layouts[6] if len(prs.slide_layouts) > 6 else prs.slide_layouts[-1]
    records = manifest["slides"]
    chunks = [records[i:i + rows_per_toc] for i in range(0, len(records), rows_per_toc)] or [[]]
    toc_slides: list[Any] = [prs.slides.add_slide(layout) for _ in chunks]
    width, height = prs.slide_width, prs.slide_height
    for page_index, chunk in enumerate(chunks):
        slide = toc_slides[page_index]
        marker = _add_text_shape(slide, 0, 0, 1, 1, "", font_size=1,
                                 color=RGBColor(255, 255, 255), name=_MARKER_TOC)
        marker.left = -Inches(1)
        marker.top = -Inches(1)
        _add_text_shape(slide, Inches(0.55), Inches(0.27), width - Inches(1.1), Inches(0.48),
                        "Contents" if len(chunks) == 1 else f"Contents · {page_index + 1} of {len(chunks)}",
                        font_size=26, color=RGBColor(31, 78, 121), bold=True, name="BigPrezo::TocHeading")
        top, bottom = Inches(0.95), Inches(0.72)
        row_h = max(Inches(0.25), int((height - top - bottom) / max(1, rows_per_toc)))
        row_w = width - Inches(1.1)
        last_section = None
        for row_index, record in enumerate(chunk):
            slide_number = record["slide_number"]
            target = source_slides[slide_number - 1]
            section = _section_label(record)
            row_y = top + row_index * row_h
            label = f"{slide_number:02d}  {record['title'] or '(Untitled slide)'}"
            if section and section != "Opening" and section != last_section:
                label = f"{section}   ·   {label}"
            last_section = section
            label = label[:_MAX_ROW_CHARS]
            row = _add_text_shape(slide, Inches(0.55), row_y, row_w, row_h - Inches(0.035), label,
                                  font_size=12, color=RGBColor(31, 41, 55),
                                  fill=RGBColor(232, 240, 248), name=f"BigPrezo::TocEntry::{slide_number}")
            _set_hyperlink(row, target)
        if page_index > 0:
            prev = _add_text_shape(slide, Inches(0.55), height - Inches(0.55), Inches(2.1), Inches(0.3),
                                   "‹ Previous contents", font_size=10, color=RGBColor(31, 78, 121),
                                   name="BigPrezo::TocPrevious")
            _set_hyperlink(prev, toc_slides[page_index - 1])
        if page_index + 1 < len(chunks):
            nxt = _add_text_shape(slide, width - Inches(2.65), height - Inches(0.55), Inches(2.1), Inches(0.3),
                                  "Next contents ›", font_size=10, color=RGBColor(31, 78, 121),
                                  align=PP_ALIGN.RIGHT, name="BigPrezo::TocNext")
            _set_hyperlink(nxt, toc_slides[page_index + 1])
    return toc_slides


def process_presentation(input_path: str | Path, output_path: str | Path,
                         manifest_path: str | Path | None = None, *,
                         rows_per_toc: int = _DEFAULT_ROWS_PER_TOC) -> dict[str, Any]:
    source = Path(input_path).resolve()
    output = Path(output_path).resolve()
    if source == output:
        raise ValueError("Output must be a new path; the original PPTX is never overwritten.")
    if not source.is_file():
        raise FileNotFoundError(source)
    prs = Presentation(str(source))
    # Keep old engine TOCs in the slide list until replacements are allocated.
    # python-pptx derives the next part name from slide count; deleting first can
    # reuse a live source slide's part name and corrupt repeated processing.
    old_toc_slides = [slide for slide in prs.slides
                      if any(shape.name == _MARKER_TOC for shape in slide.shapes)]
    original_slides = [slide for slide in prs.slides if slide not in old_toc_slides]
    for slide in original_slides:
        for shape in list(slide.shapes):
            if shape.name.startswith(_MARKER_HOME):
                _remove_shape(slide, shape)
    manifest = manifest_for_slides(original_slides)
    toc_slides = _add_toc_slides(prs, original_slides, manifest, rows_per_toc=rows_per_toc)
    for old_slide in old_toc_slides:
        _delete_slide(prs, old_slide)
    for number, slide in enumerate(original_slides, 1):
        _add_home_button(slide, toc_slides[0], number, prs.slide_width, prs.slide_height)
    _insert_slides_at_front(prs, toc_slides)
    toc_count = len(toc_slides)
    manifest["toc_slide_count"] = toc_count
    manifest["contents_slide_numbers"] = list(range(1, toc_count + 1))
    for record in manifest["slides"]:
        record["output_slide_number"] = record["slide_number"] + toc_count
    output.parent.mkdir(parents=True, exist_ok=True)
    prs.save(str(output))
    if manifest_path:
        path = Path(manifest_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return manifest


def extract_manifest_file(input_path: str | Path, output_path: str | Path) -> dict[str, Any]:
    prs = Presentation(str(input_path))
    _remove_generated_navigation(prs)
    manifest = manifest_for_slides(prs.slides)
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Create a deterministic, navigable PowerPoint copy.")
    sub = parser.add_subparsers(dest="command", required=True)
    build = sub.add_parser("build", help="Add linked contents and Home controls to a copy of a PPTX.")
    build.add_argument("input", type=Path)
    build.add_argument("output", type=Path)
    build.add_argument("--manifest", type=Path, help="Optional JSON manifest output path.")
    build.add_argument("--rows-per-toc", type=int, default=_DEFAULT_ROWS_PER_TOC)
    manifest_cmd = sub.add_parser("manifest", help="Extract a JSON manifest without modifying the deck.")
    manifest_cmd.add_argument("input", type=Path)
    manifest_cmd.add_argument("output", type=Path)
    args = parser.parse_args(argv)
    if args.command == "build":
        result = process_presentation(args.input, args.output, args.manifest, rows_per_toc=args.rows_per_toc)
        print(f"Created {args.output} ({result['source_slide_count']} source slides; {result['toc_slide_count']} contents slides).")
    else:
        result = extract_manifest_file(args.input, args.output)
        print(f"Wrote {args.output} ({result['source_slide_count']} slides).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
