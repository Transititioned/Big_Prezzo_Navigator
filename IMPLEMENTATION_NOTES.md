# Implementation Notes — Pass 1

## Review

- Reviewed `BIG_PREZO_PRODUCT_BRIEF.md` and `Speaking_Notes_Console_SKILL_v4_Native_PowerPoint_Navigation.md` in `C:\projects\big_prezzo_navigator`.
- `Speaking_Notes_Console_SKILL_v3_Persistence_Safety.md` is present and reviewed for the upcoming HTML console. Preserve stable note keys and every note type in the same save/load/export/import flows; distinguish browser cache from durable file saves; show unsaved-to-file state; provide a verified Save to File or portable HTML snapshot path; warn before losing unsaved edits; protect recovery sources; and test that exported HTML contains the exact edited note values. Do not treat a `localStorage` write or download request as proof of disk persistence.
- No material conflict with the product brief was found. v4 recommends multiple contents pages for large decks; this engine paginates the all-slide list at 18 rows per page rather than adding a second navigation hierarchy. This keeps every source slide reachable while preserving a small deterministic MVP.

## Architecture and decisions

- A small Python module (`big_prezo.py`) provides both callable functions and a CLI. `python-pptx` handles slide reading, generation, and slide-object hyperlinks; there is no LLM, web UI, notes console, account system, or agent framework.
- The manifest is built from source slides before adding navigation. Each record includes the original slide number, title, compact text, probable-section flag, inferred section label, and final output slide number. The summary exposes the number of probable section boundaries and whether the all-slides fallback applies.
- Section detection is deliberately transparent and conservative: a title must contain a common section word and the remaining extracted text must be at most 140 characters. It can miss unconventional dividers and can flag generic headings such as “Overview”; it is a deterministic hint, not authoritative classification. Keep it simple and expose boundary/section corrections for the user in Pass 2 rather than adding AI or a classification engine.
- Every source slide gets a clickable contents row. Rows follow source order, are grouped by inferred section labels, and paginate at 18 per contents slide. When no divider is detected, the manifest flags fallback and contents still lists every slide.
- The v4 native navigation pattern is used: create contents slides, add Home/TOC controls to original slides, and link with `shape.click_action.target_slide` to actual slide objects. The generated contents is inserted at the front; source slide order is preserved.
- Navigation shapes and contents slides use reserved `BigPrezo::` names. Reprocessing strips only those marked elements. Replacement contents slides are allocated before removing old generated contents so `python-pptx` does not reuse a live slide part name.
- The engine rejects same-path input/output and writes a distinct output PPTX. The source file is never overwritten.

## Deterministic vs. future AI

- Deterministic now: PPTX input, slide title/text extraction, compact manifest, section heuristic, fallback flag, slide mapping, contents generation, internal hyperlinks, Home controls, repeat-run cleanup.
- Optional AI later: narrative framing, speaking notes, transitions, tone adaptation, and takeaways. None is in Pass 1.

## Validation and limitations

- Nine automated tests cover source content/order and speaker-note preservation, native TOC and Home targets after save/reopen, generated-deck manifest extraction, invalid `rows_per_toc` values, section detection, all-slide fallback, multi-page contents cross-links, repeat processing, and empty/titleless slides.
- A local 20-slide sample deck was processed into a temporary output: 20 source slides, 0 probable section boundaries, 2 contents pages, 20 Home controls, and a written manifest.
- Microsoft PowerPoint slideshow interaction remains unverified. Manually open a generated deck in desktop PowerPoint, press F5, click a TOC row to reach its source slide, then click HOME / TOC to return. Check representative light/dark slides, media, animations, and any footer/logo overlap.
- `python-pptx` can alter or omit advanced PowerPoint features it does not fully support; review representative production files before broad deployment. The committed sample `20200814_Steering_Committee.pptx` contains Beyond Blue Ltd strategy, CRM/Salesforce Marketing Cloud, donor/supporter propensity and donation analytics, and an SFMC content URL with a query token. Manually inspect whether it is cleared for repository distribution; it has been retained pending that review.
- The returned `python-pptx` slide hyperlinks are verified structurally, but Python tests cannot prove PowerPoint Slide Show click hit-testing or visual quality on a projector.

## Pass 2 boundary

Add the upload/review/download flow and the separate HTML speaking-notes console. Reuse the v3 persistence safeguards if that document is supplied, and keep browser note persistence separate from the PPTX notes lifecycle. Do not add AI until the deterministic MVP is usable.
