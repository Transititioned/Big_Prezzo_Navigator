---
name: speaking-notes-console
description: Build, repair, and safely update a portable HTML speaking-notes console using either stacked slides or a stationary presentation pane with modal section navigation, while protecting all presenter and section-introduction notes.
---

# Speaking Notes Console Skill

**Version:** 3.0 (29 October 2026)  
**Applies to:** New builds and safe modifications of existing consoles  
**Design principle:** The slide comes to the presenter; the presenter should not have to hunt for it.

## Purpose

Use this skill when creating or modifying a self-contained HTML presentation console that shows:

- a slide screenshot or thumbnail
- large editable speaking notes beside it
- a table of contents
- keyboard navigation
- fullscreen and slide zoom
- persistent notes
- optional multiple speaking-note "visits" to the same slide
- a fixed single-slide working pane with section-aware modal navigation
- a slide-image preview on hover or keyboard focus
- independent introduction notes for section-opening slides

The priority order is:

1. **Never lose presenter notes**
2. **Navigation must land reliably on the intended slide**
3. **The notes pane must remain easy to read and edit**
4. **Edits to layout or content must not silently change saved-note keys**
5. **The console should remain a single portable HTML file**
6. **Section navigation must not displace the active speaking-notes workspace**

This is a presenter tool, not a website redesign exercise. Reliability beats cleverness.

---

# Core UX and Choosing the Layout Mode

There are **two supported layout modes**. Pick one per console; do not accidentally combine their scrolling mechanics.

| Mode | Best for | Navigation behaviour |
|---|---|---|
| **Stationary presenter stage (preferred for multi-section decks)** | Steering committees, workshops, and decks where the presenter jumps around | Exactly one slide occupies a stable working pane; Contents/section buttons open a modal; clicking a slide replaces the visible slide in place |
| **Stacked / native-anchor legacy mode** | Existing working consoles, deliberately scrollable handouts | All `.slide-card` elements remain vertically stacked; contents links scroll to them using native anchors |

Common to both modes:

- sticky top controls for **Home / Contents**, Previous / Next, note font size, Fullscreen, Export Snapshot and optional slide Zoom
- one semantic `.slide-card` per source slide, with **one normal presenter-note editor per slide**
- slide screenshot at left, dominant editable notes pane at right
- persistent note keys and a separate backup/export path
- keyboard: `←` / `PageUp` = previous; `→` / `PageDown` = next; `F` = fullscreen; `T` / `Home` = contents (scroll in legacy mode, open navigator in stationary mode); `Z` = slide zoom; `Esc` = close zoom or modal

The screenshot is supporting context. **The notes pane is the dominant working area.** Do not make the user scroll a long deck merely to move between presentation parts when a stationary stage is appropriate.

---

# Design Pattern 1 — Stationary Presentation Stage + Modal Navigator

## Problem

A top-bar "Part 1" button that jumps to the first slide solves only half the navigation problem: the presenter arrives at a title slide, with no quick view of the other slides in that part. Vertically stacked slides create unnecessary movement during a live meeting.

## Solution

Use **one stable presentation workspace** plus **one shared slide-selection modal**. The modal is a temporary navigation surface, *not* the speaking workspace.

### Presenter interaction contract

1. Clicking **Home / Contents** opens the full navigator.
2. Clicking any **section/part shortcut** opens the same navigator, filtered to that section.
3. The modal lists slides **vertically in source/presentation order within each section**; never use an alternating two-column reading sequence.
4. **Hover or keyboard focus** on a slide row changes the *modal preview only*. Do **not** change the live slide or the main notes.
5. **Click or Enter** on a slide row closes the modal and displays that slide **in the existing fixed working pane**. No journey down a scrolling page.
6. Previous / Next moves one slide in the chosen presentation sequence, including when moving between sections. The main notes remain editable.
7. **Esc** closes the active zoom first, otherwise the modal. The modal should return focus sensibly and never trigger background navigation while open.

### Generalised data model

Do not hardcode "three parts", particular slide numbers, or business names. Derive section grouping from deck structure or supply an explicit mapping:

```javascript
const groups = [
  { id: 'opening', label: 'Opening', slides: [1] },
  {
    id: 'section-a', label: 'Section A', slides: [2, 3, 4],
    opener: 2, introNoteKey: 'section_a_intro'
  },
  {
    id: 'section-b', label: 'Section B', slides: [5, 6, 7],
    opener: 5, introNoteKey: 'section_b_intro'
  },
  { id: 'appendix', label: 'Appendices', slides: [8, 9] }
];
```

These numbers are illustrative, not required positions. Every source slide has **one stable content identity**; a presentation number is merely where it currently appears. Preserve established `data-note-key` values on reordering.

- Show a shortcut for each important named part when space permits. A compact "More" or "All" option is preferable to overflowing the header.
- Additional groups (workstreams, appendices, Q&A) are not automatically "parts"; they can remain accessible through **Home / All**.
- Allow the presenter to open any slide from the full navigator, including slides without a top-bar shortcut.
- Keep the preview image sourced from the slide already embedded in the document; do not create extra notes editors or load remote assets.

### Minimal stage mechanism

```css
/* Stationary mode ONLY. Do not combine with stacked-slide CSS. */
.slide-card { display: none; }
.slide-card.active-slide { display: flex; }
.nav-overlay[hidden] { display: none !important; }
```

```javascript
let current = 1;
const slide = n => document.getElementById('slide-' + n);

function showSlide(n) {
  const target = slide(n);
  if (!target) return; // Never blank the presenter pane for a bad target.
  document.querySelector('.slide-card.active-slide')
    ?.classList.remove('active-slide');
  target.classList.add('active-slide');
  current = n;
  const note = target.querySelector('textarea.notes');
  if (note) note.scrollTop = 0;
  const progress = document.getElementById('progress');
  if (progress) progress.textContent = `${n} / ${document.querySelectorAll('.slide-card').length}`;
}

function chooseSlide(n) {
  closeNavigator();
  showSlide(n);
}
```

This is a **simple visible-slide toggle**, not a framework-driven SPA. Leave hidden `.slide-card` elements in the DOM so their note fields are still available to autosave, snapshot export and JSON backup.

### Modal structure and behaviour

```html
<div id="navigator" class="nav-overlay" role="dialog"
     aria-modal="true" aria-labelledby="nav-title" hidden>
  <div class="nav-panel">
    <h2 id="nav-title">Jump to slide</h2>
    <nav id="nav-filters" aria-label="Presentation sections"></nav>
    <div class="nav-layout">
      <div id="nav-list" aria-label="Slides in selected section"></div>
      <div id="nav-preview" aria-label="Slide preview"></div>
    </div>
    <button type="button" onclick="closeNavigator()">Close</button>
  </div>
</div>
```

- Render slide rows as real buttons; mouseenter/focus updates the preview, click selects the slide.
- Use one shared modal rather than a different modal per section.
- While the modal is open, block PageUp/PageDown/arrow commands from changing the live slide; allow typing in any note field without hijacking shortcuts.
- Put initial focus in the modal, support keyboard selection, and restore/transfer focus on close. Trap focus within the modal if it remains open during Tab navigation.
- A preview should remain visually stable when the user moves the pointer from the list into the preview notes editor; never destroy an editor because hover has changed.
- Opening the modal does not change `current`, the main slide, or the main slide's note scroll position.
- In stationary mode, "Home" opens **All Slides**, not a physical scroll to a hidden contents page.

### Invariant

**Previewing is not navigating.** Only an explicit selection changes the presenter stage.

---

# Design Pattern 2 — Contextual Section-Introduction Notes

## Problem

Section-opening slides often need short transition remarks, separate from ordinary slide-by-slide speaking notes. Duplicating the opener slide or overwriting its normal notes introduces note-key and export risks.

## Solution

For a section that has introduction remarks, show two tabs in the **right side of the navigator preview** when its opening slide is previewed:

- **Slide image** — previews that slide.
- **Intro speaking notes** — an editable, independently saved plain-text editor.

The normal speaking notes for the opening slide still live in its usual presentation pane and retain their existing key. The introduction is a *separate note*, not a replacement or second copy of the slide.

### Rules

1. Make this feature **data-driven**, by the group's `opener` and `introNoteKey`, not by fixed slide numbers or hardcoded names like `part1`.
2. Expose these two tabs **only when the previewed slide is a configured section opener**. For a non-opener, show the normal image preview without a redundant Intro tab.
3. On opening the navigator, default the right pane to **Slide image**. Keep the intro notes editable in the same modal without navigating away.
4. Store the introduction in a distinct `<textarea>` with its own semantic `data-note-key` (for example `section_a_intro`). **Never reuse** the opening slide's normal key.
5. The intro textarea must participate in the **same save, load, plain-text paste, Export Snapshot, Export JSON and Import JSON** processes as every other note.
6. Switching between image and intro views must **hide, not recreate**, the note textarea. Preserve its value, caret/selection when practical, and note scroll position.
7. If the section opener moves to another position, keep the intro note key tied to the section's stable identity, not the new slide number.
8. New intro notes start empty (or with explicit user-provided text); do not fabricate remarks from a divider slide.

### Example markup

```html
<div class="intro-tabs" role="tablist" aria-label="Preview mode">
  <button type="button" role="tab" id="preview-image-tab"
          aria-selected="true">Slide image</button>
  <button type="button" role="tab" id="preview-notes-tab"
          aria-selected="false">Intro speaking notes</button>
</div>

<!-- One persistent field per section; hide non-active fields. -->
<div class="intro-editor" data-section="section-a" hidden>
  <label for="intro-section-a">Section A — opening remarks</label>
  <textarea id="intro-section-a" class="notes intro-notes"
            data-note-key="section_a_intro"></textarea>
</div>
```

Use a consistent dynamic lookup: `groups.find(g => g.opener === previewSlide)` determines whether an intro exists and which field to display. Build one intro editor per configured section *once* at document creation, not afresh every time the modal opens.

**Don't confuse this with repeated visits to the same slide:** visit tabs distinguish two moments in a presentation; introduction notes are separate context for a section opener in the navigator. Both patterns can coexist with distinct, stable keys.

### Example persistence identity

| Content | Stable key |
|---|---|
| Normal notes for opener slide | Existing slide key, e.g. `2` |
| Additional notes for Section A introduction | `section_a_intro` |
| Revisited closing comments on that opener | Existing visit key, e.g. `2_visit2` |

The values are examples. **Preserve already-established keys** in existing consoles; never rename to match this naming style just for tidiness.

---

# Design Pattern 3 — A Single Notes Registry for All Editors

Normal slide notes, section-introduction notes, and repeated-visit notes must use **one discovery mechanism** for persistence and exports. A note is a note regardless of which pane currently shows it.

```javascript
const noteEls = () =>
  [...document.querySelectorAll('textarea[data-note-key]')];
```

- Iterate **all** note fields, including hidden intro editors, not merely the active slide.
- Validate unique `data-note-key` values and unique textarea IDs before handoff.
- Make every notes editor use plain-text paste and the same save lifecycle.
- Export Snapshot must write each live `.value` into the corresponding cloned `<textarea>` *before* serialising the complete HTML file.
- JSON export must include all semantic note keys; import should map by key, report unrecognised keys and **not silently erase** existing notes.
- Never delete legacy keys or aliases when adding a new note type.
- Do not assume `localStorage` works identically across browsers, `file://` origins, machines or downloaded versions. The snapshot/export remains the portable source of truth.

This pattern prevents an easy regression: a new introduction editor appears to autosave, but is omitted from the downloaded HTML or JSON backup.

---

# Non-Negotiable Safety Rules

## 1. Presenter notes are sacred

When modifying an existing console:

- Do not replace or blank existing `<textarea>` contents unless explicitly asked.
- Do not change a note's persistence key unless the migration is deliberate and tested.
- Before editing, extract every note field and its key.
- After editing, compare every note field and key with the source.
- Fail the build if any note disappears unexpectedly.

A safe note identity is:

```text
data-note-key
```

with fallback to the textarea ID only when no explicit key exists.

Preferred markup:

```html
<textarea
  class="notes editable"
  data-note-key="7"
  id="notes-7"
>Existing note text...</textarea>
```

For special repeated visits, use semantic keys:

```html
data-note-key="4_visit1"
data-note-key="4_visit2"
```

Do not renumber persistence keys merely because slides move in the deck.

---

## CRITICAL INCIDENT RULE — Prove disk persistence before delivery (29 October 2026)

**Failure observed:** A console displayed **“Saved locally”** after a textarea edit. That meant a `localStorage` write, not a write to the HTML file. A later version used the older embedded textarea defaults, and the presenter believed substantial edits had been preserved. An uploaded original HTML file was byte-for-byte identical to the original build and did not contain the browser-only revisions.

This is a **data-loss incident**, not a cosmetic or navigation defect. Treat it as release-blocking.

**Mandatory design controls for every new or updated editable console:**

1. **Never label a browser cache write “Saved”, “Saved locally”, or “Safe”.** Label it explicitly **“Browser cache only — NOT saved to HTML”**.
2. **Use a visible unsaved-to-file indicator** whenever any current `.value` differs from the last confirmed disk-saved or embedded baseline. Make this clear even when the browser cache is working.
3. **Use a real Save to File action** where the browser supports a user-initiated file picker / writable file handle. Report success only after the file write and close both succeed. On browsers without this capability, offer a portable HTML snapshot download and tell users to verify the file in Downloads. A download *request* alone is not evidence of a persisted file.
4. **Warn before closing or replacing a page** if notes have changed but no durable save has been confirmed. Browser `beforeunload` warnings are a safety net, not a substitute for disk persistence.
5. **Never silently replace browser-edited notes with embedded defaults.** A reset-to-draft control is destructive. Remove it or require confirmed prior durable backup; a JSON download *request* alone is insufficient protection.
6. **When the user requests a new version**, require the latest saved snapshot or notes JSON before claiming it includes recent manual edits. The old file’s embedded defaults are not proof of what the user has typed in the browser.
7. **Preserve recovery sources**, including old file versions, existing `localStorage` keys and any JSON backups. When recovering, instruct the user to return to the **exact original file/location/browser profile** and export current note values before trying a new version.
8. **Regression test the actual save bytes**: write a unique user edit into a note, save/export to an HTML file, parse the saved file with a fresh parser and verify that exact text is inside the correct `<textarea>` key. Repeat for an introduction note. Test browser cache restoration separately and never conflate the two.

Acceptance fails if an edited note only survives in the open browser session, if the UI claims a disk save where none occurred, if a cross-version export silently reverts to old embedded values, or if the presenter cannot tell which copy contains the latest work.

---

## 2. Browser autosave is NOT embedded-file persistence

This caused a real failure and must be treated explicitly.

Typing into the console can save notes to `localStorage`, but that does **not** rewrite the HTML file on disk.

Therefore:

- An uploaded/downloaded HTML file may contain older textarea defaults even if the presenter sees newer notes in their browser.
- Do not claim that recent browser-edited notes are preserved merely because the HTML file has the same localStorage keys.
- When creating a new version from an uploaded HTML file, preserve the textarea values in that file exactly, but recognise that newer browser-only edits may exist outside it.
- Never overwrite a user's known newer notes with older embedded defaults.

### Preferred future-proof feature

Include an **Export Snapshot** control where practical.

It should:

1. copy every current textarea `.value` into its HTML text content
2. serialise the current document
3. download a new self-contained HTML snapshot

That turns browser-edited notes into actual embedded defaults and avoids dependence on localStorage when moving the file between versions or machines.

Optionally also provide:

- Export Notes JSON
- Import Notes JSON

---

## 3. Use `<textarea>`, not `contenteditable`

Rich pasted HTML previously damaged the console DOM.

Use plain-text `<textarea>` note editors.

Force paste to plain text:

```javascript
el.addEventListener('paste', (e) => {
  e.preventDefault();
  const text = (e.clipboardData || window.clipboardData)
    .getData('text/plain');
  const start = el.selectionStart;
  const end = el.selectionEnd;
  el.setRangeText(text, start, end, 'end');
  el.dispatchEvent(new Event('input', { bubbles: true }));
});
```

This prevents copied ChatGPT, Outlook, Teams, Word, or web formatting from inserting HTML into the console.

---

# Navigation: Known-Good **Stacked / Native-Anchor** Pattern

**This section applies only to existing or deliberately scrollable consoles.** In stationary mode, use Design Pattern 1 instead: a `showSlide()` stage switch and filtered modal navigator. Do not mix anchor scrolling with the single-active-slide CSS.

## Do not "fix" the TOC with custom interception unless absolutely necessary

A previous regression looked like an anchor-scroll problem but was actually caused by slide-card geometry.

The reliable pattern is:

```css
html {
  scroll-behavior: smooth;
}

.slide-card {
  min-height: calc(100vh - 64px);
  scroll-margin-top: 72px;
  padding: 14px 4px 32px;
  border-top: 1px solid #1d2936;
  display: flex;
  flex-direction: column;
  justify-content: flex-start;
}
```

Use native anchors:

```html
<a class="toc-link" href="#slide-7">...</a>
```

Avoid replacing these with a custom TOC click handler unless the native behavior is demonstrably broken.

### Known bad pattern

Do not use this as the standard slide layout:

```css
.slide-card {
  height: calc(100vh - 64px);
  min-height: 620px;
  overflow: hidden;
}
```

That combination caused TOC links to land in poor frames / appear to scroll off target.

The important distinction is:

- **good:** `min-height`
- **risky:** fixed `height` + `overflow:hidden`

---

# Previous / Next Navigation

Use a simple current-slide model in both modes. The following example is **stacked-mode only**; stationary mode uses `showSlide()` from Design Pattern 1:

```javascript
const total = 24;
let current = 1;

function section(n) {
  return document.getElementById('slide-' + n);
}

function setCurrent(n) {
  current = Math.max(1, Math.min(total, n));
}

function go(n) {
  setCurrent(n);
  resetNoteScroll(current);
  section(current).scrollIntoView({
    behavior: 'smooth',
    block: 'start'
  });
  setTimeout(() => resetNoteScroll(current), 180);
}

function goPrev() { go(current - 1); }
function goNext() { go(current + 1); }

function goTOC() {
  document.getElementById('contents')
    .scrollIntoView({ behavior: 'smooth', block: 'start' });
}
```

In **stacked mode only**, use an `IntersectionObserver` to update `current` based on the slide nearest the viewport centre. In stationary mode, `current` changes only when the presenter explicitly selects or advances a slide; no scroll observer is needed.

Do not let arrow/page navigation fire while the presenter is typing **or while a navigation modal is open**:

```javascript
if (
  e.target &&
  (
    e.target.isContentEditable ||
    e.target.tagName === 'TEXTAREA' ||
    e.target.tagName === 'INPUT'
  )
) return;
```

---

# Notes Persistence

Use a stable prefix, for example:

```javascript
const keyPrefix = 'steercomm_sc03_notes_';
```

The exact prefix may differ by console, but once established it should not casually change.

Save on:

- input, with short debounce
- blur
- `beforeunload`

Example:

```javascript
function saveNote(el) {
  const key = el.dataset.noteKey || el.id;
  localStorage.setItem(keyPrefix + key, el.value);
}
```

When loading, apply this to **all registered textareas**, including hidden section-intro notes:

```javascript
const saved = localStorage.getItem(keyPrefix + key);

if (saved !== null) {
  el.value = htmlToPlainText(saved);
}
```

---

# Legacy Rich-Text Migration

Older console versions may have stored rich HTML.

Keep a migration helper:

```javascript
function htmlToPlainText(value) {
  if (!value) return '';
  if (!/[<>]/.test(value)) return value;

  const tmp = document.createElement('div');

  tmp.innerHTML = value
    .replace(/<br\s*\/?>/gi, '\n')
    .replace(/<\/p>\s*<p[^>]*>/gi, '\n\n')
    .replace(/<\/div>\s*<div[^>]*>/gi, '\n');

  return (tmp.textContent || tmp.innerText || '')
    .replace(/\u00a0/g, ' ');
}
```

Do not delete legacy saved keys as part of migration.

---

# Repeated Visits to the Same Slide

Sometimes one slide is intentionally used twice in the talk.

Example:

- Slide 4 Visit 1 = STATUS UPDATE
- Slide 4 Visit 2 = NEXT STEPS / CLOSE

Use separate keys:

```text
4_visit1
4_visit2
```

Do not split the slide into fake duplicate slide cards.

Use note tabs inside the same slide:

```html
<button data-visit="1">1 · STATUS UPDATE</button>
<button data-visit="2">2 · NEXT STEPS</button>
```

Migration behavior:

- preserve any original slide key such as `4`
- preserve older tab keys such as `4_t1` ... `4_t4`
- if `4_visit1` is absent, migrate old content into it
- never overwrite an existing `4_visit1` or `4_visit2`
- keep the original `4` key as a backup of Visit 1 if desired

This is a safety net, not housekeeping. Do not eagerly delete old keys.

---

# Slide Reordering

When slides are reordered:

- visible slide number may change
- persistence identity should follow the *content*, not automatically the new number

If an existing console already has custom mappings such as:

```html
data-note-key="20" id="notes-13"
```

that may be deliberate because the visible slide moved but the stored note belongs to the old semantic slide.

Do not "clean up" mismatched IDs and keys without understanding why they differ.

Before reorder:

1. build a map of:
   - visible slide
   - slide title
   - textarea ID
   - `data-note-key`
   - embedded note text
2. reorder slide cards
3. retain the original note key for each content slide
4. verify the map after the change

---

# Hiding Appendices From the Contents / Navigator

If the presenter says appendices will not be used:

- hide the **Appendices entry/group from the main contents only**, unless removal from all navigation is explicitly requested
- do not delete the appendix slide sections unless explicitly asked
- in stationary mode, decide whether a **Home → All Slides** navigator still exposes Q&A/appendix slides, even if shortcuts do not
- Previous / Next may still traverse appendices at the end of the main deck; this needs a deliberate policy, not an accidental side effect
- if appendices remain available for Q&A, retaining the underlying slide sections is preferable

For any contents list, keep items **vertically ordered within sections**, even when multiple sections are laid out side by side. Two-column *interleaving within a section* is not acceptable because it obscures the slide sequence.

Example readable TOC styling:

```css
.toc-section { display: flex; flex-direction: column; gap: 6px; }
.toc-link { font-size: 16px; line-height: 1.35; padding: 10px 7px; }
```

---

# Editing an Existing Console Safely

## Step 1 — Snapshot the source

Before any modification, extract:

- all slide IDs
- all slide titles
- all TOC hrefs
- all textarea IDs
- all `data-note-key` values
- all textarea text
- special visit/tab structures and **section-intro note fields**
- the stable section/group map, opener configuration and top-bar shortcuts
- `keyPrefix`
- navigation functions, active-stage mode and modal mechanics
- total slide count

Keep the source untouched.

---

## Step 2 — Make the smallest possible change

Do not rebuild the entire HTML to change one behavior.

Examples:

- TOC change → edit the TOC only
- larger TOC text → CSS only
- notes update → textarea content only
- section tabs → modify the section map / modal filters, not the slide or note identities
- intro note for a new section → add a separate keyed field and register it in exports
- slide order → reorder slide sections and TOC links while preserving keys
- navigation bug → first confirm whether this is stationary or stacked mode, then inspect the correct mechanics

Prefer surgical edits.

---

## Step 3 — Protect notes programmatically

Before saving an edited file, compare note maps.

Pseudo-check:

```python
before = {
    note_key(textarea): textarea_text(textarea)
    for textarea in source
}

after = {
    note_key(textarea): textarea_text(textarea)
    for textarea in edited
}

# Additive note editors are allowed, but none of the original notes may change.
assert all(k in after and after[k] == v for k, v in before.items())
assert len(after) == len(edited)  # catches duplicate note keys
```

For an intentional note update, compare everything except the explicitly changed keys.

Never hand back a file if unexpected note keys or note contents changed.

---

## Step 4 — Validate structural invariants

Check:

- every TOC `href="#slide-N"` points to an existing slide (when stacked TOC exists)
- every modal slide entry maps to exactly one existing slide; each group refers only to existing slide IDs
- section opener IDs exist, and each configured `introNoteKey` is unique
- slide IDs are unique and `.slide-card` count is expected
- `total` matches the highest intended navigable slide
- exactly one `.active-slide` is visible in stationary mode
- each editable note has a stable, unique `data-note-key`; all embedded note contents preserved
- special visit and section-intro notes exist and are independently keyed
- no duplicate element IDs
- no broken/remote image source for slide previews
- no malformed HTML around textareas
- keyboard listeners ignore textarea/input and suppress background slide navigation while a modal is open
- paste handler forces plain text across **all** note editors
- snapshot/JSON export discovers hidden note fields as well as active slide notes

---

# Acceptance Test Checklist

A console is not finished until all of these are checked.

## Notes

- [ ] Existing notes are present.
- [ ] Existing note keys are unchanged unless deliberately migrated.
- [ ] Typing a note survives moving to another slide.
- [ ] Pasting from rich text produces plain text only.
- [ ] Closing/reopening in the same browser restores localStorage notes.
- [ ] A fresh browser/file still shows embedded default notes.
- [ ] Browser-only notes have not been mistaken for embedded notes.
- [ ] If available, Export Snapshot successfully bakes **all** current notes (including hidden intro fields) into a new HTML.
- [ ] JSON export/import, if included, round-trips regular, intro and visit notes by unchanged key.
- [ ] Every note key is unique and a newly added note field has not replaced an existing one.

## Navigation

- [ ] TOC click lands with the slide title and working area comfortably framed.
- [ ] `Next` advances one slide.
- [ ] `Prev` moves back one slide.
- [ ] Arrow/Page keys work outside note fields.
- [ ] Keys do not change slide while typing.
- [ ] `T` returns to Contents.
- [ ] `F` toggles fullscreen.
- [ ] `Z` opens current slide image.
- [ ] `Esc` closes zoom (or modal if zoom is not open).
- [ ] In stationary mode, **Home / Contents** opens the full modal, and a section shortcut opens a filtered modal.
- [ ] Hover/focus shows the right preview **without changing the active slide**.
- [ ] Click/Enter on a modal row replaces the slide in the **same stage pane**, closing the modal.
- [ ] The modal is keyboard accessible and does not allow background next/previous shortcuts.
- [ ] Sections display their slides in vertical source order; all valid slides remain reachable.

## Layout

- [ ] Notes pane is larger/more important than slide image.
- [ ] Long notes scroll inside the notes pane.
- [ ] Entering a slide resets its note scroll to the top.
- [ ] Sticky top bar does not cover the slide title.
- [ ] TOC is readable at presentation distance.
- [ ] Mobile/narrow fallback does not corrupt desktop layout.
- [ ] Stationary mode shows exactly one slide card without forcing page scrolling on every navigation.
- [ ] Modal notes editor is large enough to edit, and toggling tabs does not remove or reset its text.

## Section-introduction notes

- [ ] Only configured section openers expose the **Image / Intro speaking notes** tabs.
- [ ] Each introduction uses its own stable semantic note key, distinct from normal opener-slide notes.
- [ ] Intro notes survive opening/closing the modal and switching the preview between slides.
- [ ] Intro notes are included in local autosave, HTML snapshot, JSON export and import.
- [ ] Changing slide order does not reassign introduction notes to the wrong section.

## Repeated-visit slides

- [ ] Visit 1 and Visit 2 show different note fields.
- [ ] Each visit saves independently.
- [ ] Old slide notes remain recoverable.
- [ ] Switching visits resets inner note scroll.

---

# Common Failure Modes

## Failure: part shortcut shows only the first divider slide

Cause: the part button jumps to the section opener instead of exposing the part's slide list.

Fix: have each part button open the **shared filtered navigator**. Keep the main presentation stage fixed; clicking a slide row selects it.

---

## Failure: user must scroll down to reach selected slides

Cause: mixed stacked-slide and stationary-stage mechanics, or `go()` still uses `scrollIntoView()` in stationary mode.

Fix: choose one mode. For stationary mode, toggle exactly one `.active-slide`, update progress and reset only its note scroll. Keep the rest in the DOM for persistence/export.

---

## Failure: section intro notes vanish from export or collide with slide notes

Possible causes:

1. intro field reused the opener's normal `data-note-key`
2. export scans only `.active-slide textarea`
3. an intro textarea is rebuilt each time the modal opens
4. section opener is identified solely by its current numerical position

Fix: use a separate stable intro key, preserve each intro editor in the DOM, enumerate **all** `textarea[data-note-key]` for every export and save, and associate the opener via section configuration.

---

## Failure: hovering a slide unexpectedly changes the main presenter pane

Cause: the preview handler calls the same function as explicit slide selection.

Fix: separate `previewNavSlide()` (preview only) from `chooseSlide()` (modal close + active-stage change). Never navigate on hover.

---

## Failure: TOC appears to scroll to the wrong place

Check slide geometry first.

Likely cause:

- fixed slide height
- `overflow:hidden`
- wrong `scroll-margin-top`

Do not immediately add custom anchor JavaScript.

---

## Failure: notes vanish after an HTML update

Possible causes:

1. editor rebuilt textareas rather than preserving them
2. note keys changed
3. the user had newer notes only in browser localStorage
4. a newly downloaded HTML is running under a different storage context
5. defaults were overwritten from an older file

Response:

- compare embedded notes before/after
- compare persistence keys
- do not claim recovery of browser-only notes unless they were exported or supplied
- restore from the newest known source or user-supplied note text

---

## Failure: pasted notes break following slides

Cause:

- `contenteditable` accepted rich HTML and changed DOM structure

Fix:

- use `<textarea>`
- force plain-text paste
- never return to rich `contenteditable` notes

---

## Failure: slide reorder causes the wrong notes to appear

Cause:

- storage keys were tied blindly to current slide number

Fix:

- retain semantic `data-note-key`
- map notes by content before reorder
- verify each slide title -> note key mapping after reorder

---

## Failure: "clean-up" destroys safety history

Do not delete:

- old localStorage keys
- migration aliases
- backup keys

unless the user specifically asks.

Storage is cheap. Lost presenter notes are expensive.

---

# Preferred Build Philosophy

The console should feel boringly reliable.

Use:

- **native anchors for stacked mode; a single active-slide toggle for stationary mode**
- native browser scrolling only where that mode intentionally needs it
- simple DOM
- plain `<textarea>` inputs
- localStorage as convenience, not as the only durable copy
- embedded defaults as a portable baseline
- minimal JavaScript
- explicit safety migration
- direct file-level verification before handoff

Avoid:

- complex SPA frameworks or duplicate per-section modals; a small stage toggle and one modal are enough
- rich text editors
- unnecessary libraries
- aggressive key renaming
- global rebuilds for small changes
- assuming the browser's state exists inside the HTML file
- section links that merely jump to a cover slide without exposing that section's slide list
- duplicating a slide to hold introduction notes

---

# Handoff Requirements

When returning a modified console:

1. Say exactly what changed.
2. Say explicitly whether notes were preserved.
3. If note preservation was verified programmatically, say so.
4. Do not say browser-local notes were preserved unless they were actually available.
5. Provide the new file with a distinct versioned filename.
6. Keep the prior version intact.
7. Describe the navigation mode and any new sections/intro-note keys.
8. If the user is about to present, stop making cosmetic changes once the acceptance checks pass.

Example handoff:

```text
Updated:
- Appendices removed from TOC only
- remaining TOC text enlarged
- appendix slides retained for Q&A

Safety check:
- 25/25 embedded note fields preserved exactly
- note keys unchanged
- timeline Visit 1 / Visit 2 keys unchanged
- native TOC navigation retained
```

---

# Reference Known-Good Geometry

The following is the **stacked/native-anchor baseline**. For the preferred stationary stage, retain the notes/sidebar sizing but **replace** the `.slide-card` geometry with the active-slide visibility switch from Design Pattern 1. Do not retain the stacked `min-height` / scroll-anchor assumptions in a stationary-only implementation.

Use this as the legacy desktop starting point:

```css
.topbar {
  position: sticky;
  top: 0;
  height: 64px;
  z-index: 100;
}

.deck {
  max-width: 1600px;
  margin: 0 auto;
  padding: 0 28px 80px;
}

.slide-card {
  min-height: calc(100vh - 64px);
  scroll-margin-top: 72px;
  padding: 14px 4px 32px;
  border-top: 1px solid #1d2936;
  display: flex;
  flex-direction: column;
  justify-content: flex-start;
}

.console-grid {
  display: grid;
  grid-template-columns:
    minmax(300px, .68fr)
    minmax(560px, 1.72fr);
  gap: 16px;
  align-items: start;
}

.slide-image {
  width: 100%;
  height: auto;
  max-height: 36vh;
  aspect-ratio: 16 / 9;
  object-fit: contain;
}

.notes-panel {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 138px);
  min-height: 520px;
}

.notes {
  flex: 1;
  min-height: 0;
  overflow-y: scroll;
  resize: none;
  white-space: pre-wrap;
}
```

---

# Version 2.0 — Design Decision Summary

When starting a *new* console:

1. If it will be presented live and has several named parts, default to **stationary stage + shared modal navigator**.
2. Build section shortcuts from metadata, not hardcoded "Part 1 / Part 2 / Part 3" assumptions.
3. Provide the **Image / Intro speaking notes** toggle for every named section opener that benefits from dedicated opening remarks; keep normal slide notes independent.
4. Register **all** note editors in one persistence/export pipeline.
5. Make **Export Snapshot** prominent, because browser autosave alone is not a portable file backup.

When modifying an *existing* working console, do not convert its navigation architecture or introduce new note keys unless the user asks. A small, proven repair is safer than redesign.

---

# Final Rule

**Never trade note safety for prettier code.**

If a console already works, preserve the working mechanics and make the smallest change required.
