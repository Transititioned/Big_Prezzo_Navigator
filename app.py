"""Local-first Gradio interface for the Big Prezo PowerPoint engine."""
from __future__ import annotations

import json
import tempfile
import time
import uuid
from pathlib import Path
from typing import Any

import gradio as gr
from pptx import Presentation

from big_prezo import manifest_for_slides, process_presentation

MAX_UPLOAD_BYTES = 250 * 1024 * 1024
OUTPUT_DIR = Path(tempfile.gettempdir()) / "big_prezo_outputs"
OUTPUT_RETENTION_SECONDS = 24 * 60 * 60


def _clean_old_outputs() -> None:
    """Expire only Big Prezo-generated files older than one day."""
    cutoff = time.time() - OUTPUT_RETENTION_SECONDS
    if not OUTPUT_DIR.is_dir():
        return
    for path in OUTPUT_DIR.iterdir():
        if path.is_file() and path.name.startswith("big_prezo_") and path.suffix in {".pptx", ".json"}:
            try:
                if path.stat().st_mtime < cutoff:
                    path.unlink(missing_ok=True)
            except OSError:
                continue


def _rows_from_table(table: Any) -> list[list[Any]]:
    if table is None:
        return []
    if hasattr(table, "tolist"):
        table = table.tolist()
    if hasattr(table, "values") and not isinstance(table, (list, tuple)):
        table = table.values.tolist()
    return [list(row) for row in table if row is not None]


def review_presentation(upload: str | None):
    """Return a read-only slide preview and an editable section map."""
    if not upload:
        raise gr.Error("Choose a PowerPoint file first.")
    path = Path(upload)
    if path.suffix.lower() != ".pptx":
        raise gr.Error("Please choose a .pptx PowerPoint file.")
    if not path.is_file():
        raise gr.Error("The uploaded PowerPoint is no longer available. Please upload it again.")
    if path.stat().st_size > MAX_UPLOAD_BYTES:
        raise gr.Error("This file is larger than the 250 MB local upload limit.")
    try:
        manifest = manifest_for_slides(Presentation(str(path)).slides)
    except Exception as exc:
        raise gr.Error(f"PowerPoint could not be read: {exc}") from exc

    preview = [[r["slide_number"], r["title"] or "(Untitled slide)", r["compact_text"]]
               for r in manifest["slides"]]
    sections = [[r["slide_number"], r["title"] or "(Untitled slide)",
                 bool(r["probable_section_boundary"]), r["section"]]
                for r in manifest["slides"]]
    starts = manifest["section_detection"]["probable_section_count"]
    note = (f"Found {len(preview)} slides and {starts} probable section starts. "
            "Edit the section table below; a checked row starts a section using its Section name.")
    return preview, sections, note


def generate_outputs(upload: str | None, table: Any, purpose: str, takeaway: str, audience: str):
    """Build a new navigable deck and JSON manifest without touching the upload."""
    if not upload:
        raise gr.Error("Choose a PowerPoint file first.")
    source = Path(upload)
    if not source.is_file():
        raise gr.Error("The uploaded PowerPoint is no longer available. Please upload it again.")
    if source.suffix.lower() != ".pptx" or source.stat().st_size > MAX_UPLOAD_BYTES:
        raise gr.Error("Choose a valid .pptx file smaller than 250 MB.")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    _clean_old_outputs()
    token = uuid.uuid4().hex
    pptx_path = OUTPUT_DIR / f"big_prezo_{token}.pptx"
    manifest_path = OUTPUT_DIR / f"big_prezo_{token}.json"
    try:
        manifest = process_presentation(source, pptx_path, manifest_path,
                                        section_rows=_rows_from_table(table) if table is not None else None)
        manifest["presentation_context"] = {
            "purpose": str(purpose or "").strip(),
            "main_takeaway": str(takeaway or "").strip(),
            "audience": str(audience or "").strip(),
        }
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    except Exception as exc:
        pptx_path.unlink(missing_ok=True)
        manifest_path.unlink(missing_ok=True)
        raise gr.Error(f"Could not generate the presentation: {exc}") from exc
    concise = (manifest["source_slide_count"] >= 30
               and manifest["section_detection"]["probable_section_count"] > 0)
    toc_description = ("A concise section-based contents page was added."
                       if concise else "A slide-by-slide contents page was added.")
    return (pptx_path, manifest_path,
            f"Done. Created a new PowerPoint and JSON manifest. {toc_description} Your uploaded file was not changed.")


CSS = """
.gradio-container { max-width: 1100px !important; margin: auto !important; }
.hero { padding: 24px 28px; border-radius: 18px; background: linear-gradient(120deg,#102b46,#23618a); color: white; margin-bottom: 18px; }
.hero h1 { margin: 0 0 5px; font-size: 2rem; }
.hero p { margin: 0; opacity: .9; }
.step { color: #23618a; font-weight: 700; letter-spacing: .04em; }
"""


def build_app() -> gr.Blocks:
    with gr.Blocks() as demo:
        gr.HTML("<div class='hero'><h1>Big Prezo</h1><p>Keep your slides. Find your way around.</p></div>")
        gr.Markdown("Make a new copy of your PowerPoint with clickable contents and Home links. Everything runs on this computer; there are no AI calls or uploads to a hosting service.")
        with gr.Group():
            gr.Markdown("<div class='step'>1 · ADD YOUR POWERPOINT</div>")
            upload = gr.File(label="PowerPoint file", file_types=[".pptx"], type="filepath")
            with gr.Row():
                purpose = gr.Textbox(label="Presentation purpose (optional)", placeholder="What do you need this presentation to do?")
                audience = gr.Textbox(label="Audience (optional)", placeholder="Who will be in the room?")
            takeaway = gr.Textbox(label="Main takeaway (optional)", placeholder="What should people remember?", lines=2)
            preview_button = gr.Button("Preview slides and sections", variant="secondary")
        with gr.Group():
            gr.Markdown("<div class='step'>2 · REVIEW SECTIONS</div>")
            status = gr.Markdown("Upload a deck and select **Preview slides and sections** to begin.")
            section_table = gr.Dataframe(
                headers=["Slide", "Slide title", "Start section", "Section name"],
                datatype=["number", "str", "bool", "str"],
                type="array", interactive=True, max_height=500,
                label="Section boundaries (edit the checked rows and names)")
            slide_preview = gr.Dataframe(
                headers=["Slide", "Title", "Extracted text"],
                datatype=["number", "str", "str"], type="array", interactive=False,
                max_height=450, label="Extracted slide list")
            preview_button.click(review_presentation, inputs=[upload], outputs=[slide_preview, section_table, status])
        with gr.Group():
            gr.Markdown("<div class='step'>3 · CREATE YOUR NAVIGABLE COPY</div>")
            generate_button = gr.Button("Generate PowerPoint and manifest", variant="primary")
            result_status = gr.Markdown()
            with gr.Row():
                deck_output = gr.File(label="Navigable PowerPoint")
                manifest_output = gr.File(label="JSON manifest")
            generate_button.click(generate_outputs,
                                  inputs=[upload, section_table, purpose, takeaway, audience],
                                  outputs=[deck_output, manifest_output, result_status])
        gr.Markdown("Your original presentation stays in place. For larger decks, the contents page links to each section; smaller decks get a slide-by-slide list.")
    return demo


demo = build_app()


if __name__ == "__main__":
    demo.launch(server_name="127.0.0.1", server_port=7860, inbrowser=True,
                share=False, theme=gr.themes.Soft(), css=CSS)
