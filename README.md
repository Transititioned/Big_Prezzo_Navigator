# Big Prezo - Local PowerPoint Navigator

Big Prezo creates a new copy of your PowerPoint with clickable contents links and Home controls. The local Gradio app lets you review extracted slides, correct section boundaries and names, and download the navigable deck and its JSON manifest. It runs on your computer and makes no AI calls or network requests with your presentation.

## Run the local app (Windows)

Double-click `run_local.bat`. The launcher creates a project-local `.venv`, installs the dependency ranges in `requirements.txt` on first use, then starts the app at <http://127.0.0.1:7860>. Stop it by closing the window or pressing `Ctrl+C`. Python 3.11 or newer is recommended; the launcher uses an installed Python and does not install Python itself.

The app accepts `.pptx` files up to 250 MB. Choose **Preview slides and sections**, then edit the section table. Check **Start section** on a row to start a section and enter its name. The name then applies to following slides until another checked row. Generate downloads for a new PowerPoint and JSON manifest. Your source presentation is never overwritten. Generated files are stored in the operating system's temporary directory and expire after 24 hours.

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

Section detection is deterministic and intentionally conservative. Users can correct section starts and names in the app before generation. Decks with no detected section dividers still get a slide-by-slide contents page.

## Validate

Run the automated tests with:

```powershell
python -m unittest discover -s tests -v
```

Manual PowerPoint check remains required: open the generated file in desktop PowerPoint, start Slide Show with F5, click a contents row to jump to the intended source slide, then click HOME / TOC to return. Check representative slides, footer/logo overlap, animations, and media. Automated tests verify saved hyperlink targets and source slide content, but cannot prove desktop Slide Show click behavior or all PowerPoint rendering behavior.
