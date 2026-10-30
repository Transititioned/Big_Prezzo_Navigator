# Big Prezo - Local PowerPoint Navigator

Big Prezo creates a new copy of your PowerPoint with clickable contents links and Home controls. The default workflow is upload, generate, download. The app handles slide analysis and contents organization automatically; **Advanced options** lets you review and adjust the automatic grouping when needed. Purpose, audience, and takeaway are optional. The app runs on your computer and makes no AI calls or network requests with your presentation.

## Run the local app (Windows)

Double-click `run_local.bat`. The launcher creates a project-local `.venv`, installs the dependency ranges in `requirements.txt` on first use, then starts the app at <http://127.0.0.1:7860>. Stop it by closing the window or pressing `Ctrl+C`. Python 3.11 or newer is recommended; the launcher uses an installed Python and does not install Python itself.

The app accepts `.pptx` files up to 250 MB. Select **Generate navigable PowerPoint** to process the upload automatically. To adjust contents grouping, expand **Advanced options**, review the rows, and check **Start section** where a new group should begin; its name applies to following slides until the next checked row. Your source presentation is never overwritten. Generated files are stored in the operating system's temporary directory and expire after 24 hours.

The local rotating log is `big_prezo.log` in the app's temporary output folder (up to 1 MB per file and three backups). It records processing stages and tracebacks with short job references, but does not record slide text, notes, or optional context fields. User-facing errors include the reference to help locate the local diagnostic entry.

For decks with 30 or more slides, the contents page is a concise section index linking to the start of each section. Shorter decks get a slide-by-slide contents list.

To run without the launcher:

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python app.py
```

The app exposes a standard Gradio Blocks object and has no Spaces-only dependencies. Hosting is not configured.

## Pass 1 command line

The original engine remains available:

```powershell
python -m pip install -r requirements.txt
python -m big_prezo build input.pptx output_navigable.pptx --manifest output_manifest.json
```

Contents pages are inserted at the front. Source slides retain their order. `output_slide_number` in the JSON manifest accounts for inserted contents pages. Processing an already processed output removes only engine-marked navigation and rebuilds it, avoiding duplicate contents pages or Home controls.

To extract a manifest without modifying the presentation:

```powershell
python -m big_prezo manifest input.pptx output_manifest.json
```

Contents organization is deterministic and intentionally conservative. Users can optionally correct grouping in Advanced options. Decks with no detected dividers still get a slide-by-slide contents page.

## Validate

Run the automated tests with:

```powershell
python -m unittest discover -s tests -v
```

Manual PowerPoint check remains required: open the generated file in desktop PowerPoint, start Slide Show with F5, click a contents row to jump to the intended source slide, then click HOME / TOC to return. Check representative slides, footer/logo overlap, animations, and media. Automated tests verify saved hyperlink targets and source slide content, but cannot prove desktop Slide Show click behavior or all PowerPoint rendering behavior.
