# Big Prezo â€” Pass 1 engine

A deterministic Python engine that extracts a slide manifest and creates a new PPTX copy with native PowerPoint contents links and Home controls. It does not call an LLM or modify the input file.

## Install

```powershell
python -m pip install -r requirements.txt
```

## Build a navigable copy

```powershell
python -m big_prezo build input.pptx output_navigable.pptx --manifest output_manifest.json
```

Contents pages are inserted at the front. Source slides retain their order. `output_slide_number` in the JSON manifest accounts for inserted contents pages. Processing an already processed output removes only engine-marked navigation and rebuilds it, avoiding duplicate contents pages or Home controls.

To extract a manifest without modifying the presentation:

```powershell
python -m big_prezo manifest input.pptx output_manifest.json
```

Section detection is deterministic and intentionally conservative: a titled slide is marked as a probable section boundary when its title includes common section vocabulary (Part, Section, Chapter, Appendix, Workstream, Agenda, Overview, Closing, or Q&A) and the remaining extracted text is short. Detection is a hint, not a claim. The JSON summary reports how many probable boundaries were found and whether the all-slides fallback was used. All slides appear in the contents; when there are no probable section dividers, this becomes an all-slides contents list automatically.

## Validate

Run the automated tests with:

```powershell
python -m unittest discover -s tests -v
```

Manual PowerPoint check remains required: open the generated file in desktop PowerPoint, start Slide Show with F5, click a contents row to jump to the intended source slide, then click HOME / TOC to return. Check light and dark slide backgrounds, footer/logo overlap, animations, and media. Automated tests verify saved hyperlink targets and source slide content, but cannot prove desktop Slide Show click behavior or all PowerPoint rendering behavior.
