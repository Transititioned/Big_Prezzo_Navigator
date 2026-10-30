# Big Prezo — Product Brief

**Status:** MVP definition  
**Product:** Workfriend.ai / Big Prezo  
**Audience:** People who need to present an existing PowerPoint deck confidently, especially in executive meetings, steering committees, training and project updates.

## 1. Product idea

Big Prezo turns an existing PowerPoint presentation into a more usable *presentation kit*: a navigable PPTX with a table of contents and Home links, plus a separate browser-based speaking-notes console. Optional AI helps the presenter tell a coherent story without rewriting or rearranging their slides.

**Promise:** Keep your slides. Find your way around. Tell the story better.

Big Prezo is not a slide-generation tool or a presentation-design replacement.

## 2. Problem to solve

Presenters often inherit or build long, imperfect decks. During a live presentation they need to jump between sections, recover from questions, keep track of their narrative and consult notes without showing those notes to the audience. Conventional speaker notes and presenter views can be awkward with multiple screens or Teams screen sharing. AI slide tools often want to rebuild the deck rather than help deliver the one that exists.

## 3. Target use cases

- Executive and Steering Committee updates with sections and appendices.
- Project, programme and business transformation presentations.
- Training or briefing decks that need non-linear navigation.
- Existing slide decks that would benefit from concise speaker cues and transitions.

A five-slide deck may not need Big Prezo. Value grows with deck complexity, navigation needs and presentation stakes.

## 4. Core user journey

1. Upload an existing `.pptx`.
2. Optionally answer three quick questions: **What is the purpose? Who is the audience? What is the main takeaway or story?**
3. Review automatically detected sections and correct them if necessary.
4. Generate a downloadable navigable PPTX with a TOC and native PowerPoint internal links.
5. Open or download a separate HTML speaking-notes console for use on another screen.
6. Optionally choose an AI delivery style and improve the narrative notes.
7. Present using PowerPoint as usual, keeping the notes console private.

## 5. Product principles

1. **Deterministic first.** Use Python and `python-pptx` for extraction, section heuristics, TOC creation, links and slide mapping. Do not spend LLM tokens on mechanical document operations.
2. **Respect the source.** Preserve existing slide order, content and formatting as far as technically feasible. Never silently reorder slides.
3. **AI for narrative, not mechanics.** Use AI only for speaker notes, transitions, tone and storytelling.
4. **Human control.** Section detection is reviewable; notes can be edited. Avoid black-box restructuring.
5. **Presentation-safe.** The notes console is a separate local HTML/browser view, not part of the PPTX or the Teams-shared presentation window.
6. **Simple and economical.** Minimal dependencies, no mandatory sign-in, no agent framework, no subscription or payments in the MVP.
7. **Graceful degradation.** A useful deterministic tool must still work with no AI API key or if AI generation fails.

## 6. MVP scope

### A. Deterministic PowerPoint engine — essential

- Read `.pptx` and extract slide numbers, slide titles and compact text into a structured slide manifest.
- Detect probable section slides with transparent, adjustable heuristics.
- Let the user confirm or correct section choices.
- Add a navigable TOC and native internal hyperlinks to sections.
- Add unobtrusive Home navigation links where appropriate.
- Preserve the original input file; produce a new output PPTX.
- Maintain an accurate mapping between original slides, output slides and console notes, including any inserted TOC.
- Avoid duplicate TOCs or navigation elements if processing a previously processed file; handle repeat runs predictably.

### B. Speaking-notes console — essential

- Separate, downloadable HTML file that can open locally in a browser.
- Current slide title/number, notes, previous/next controls and keyboard navigation.
- Readable at a glance on a second monitor; no presenter-mode takeover.
- Basic deterministic speaker cues derived from slide titles/text and optional user answers.
- Reuse the existing speaking-notes console design and skill file if present in the repo; do not rebuild working features unnecessarily.
- Clearly label basic cues versus AI-generated notes.

### C. Optional AI narrative — follow-on

- Three context inputs: purpose, audience, main takeaway/story.
- Follow the **existing slide order**, inferring the narrative rather than imposing a template.
- Generate concise per-slide speaking notes, useful transitions and clear takeaways where supported.
- Four styles: **Natural**, **Executive**, **Storyteller**, **Explainer**.
- Do not invent outcomes, decisions, statistics or unsupported facts.
- Validate structured responses and preserve slide alignment.
- Allow editing/regenerating notes without regenerating the PPTX.
- Cache repeat requests and log usage/cost when available; send compact slide text, not entire PPTX binaries.

## 7. Out of scope for MVP

- Creating an entire presentation from a prompt.
- Automatically rearranging or redesigning slides.
- Live PowerPoint synchronisation or automatic slide detection.
- Sending notes to Teams or controlling Teams screen sharing.
- Accounts, payment flows, credit wallets, subscriptions or analytics infrastructure.
- Complex agent orchestration, multiple-model debates or autonomous research.
- Full PowerPoint feature parity across all layouts, animations and embedded objects.

## 8. Technical direction

- **Backend:** Python, `python-pptx`, small testable modules.
- **Interface:** Lightweight Gradio on a Hugging Face Space if practical; use limited HTML/CSS/JS to improve usability without a wholesale React rewrite.
- **Output:** Modified `.pptx`, standalone notes `.html`, structured JSON slide manifest as an internal/debug artifact.
- **AI:** Optional configurable provider. One or a small number of batched requests per deck; validate returned JSON.
- **Deployment:** Aim for low-cost/free hosting initially. Avoid persistent storage of user decks unless explicitly needed.
- **Future commercial model:** Free deterministic functions; AI-intensive features may later consume shared Workfriend.ai prepaid credits. Leave a clean integration point but do not implement monetisation yet.

## 9. Acceptance criteria

A successful deterministic MVP can:

- Process a representative existing deck without altering the original file.
- Produce a usable TOC and Home links that **actually work in Microsoft PowerPoint slideshow mode**, not just pass Python-level assertions.
- Preserve slide order and important content.
- Keep slide numbers and titles consistent between the generated deck and notes console.
- Handle missing slide titles, no obvious section slides and repeated processing without crashing or corrupting the deck.
- Open the notes console separately in a browser, navigate it by keyboard, and keep it out of the shared presentation window.
- Run with no LLM configured.

For the AI follow-on: notes should track the source slides, respect the selected style, include useful transitions, avoid invented facts and fail back safely to deterministic cues.

## 10. Build sequence

**Pass 1 — PowerPoint engine:** Inspect repo and skill file; extract manifest; detect sections; create TOC/Home navigation; write tests and CLI/callable interface.

**Pass 2 — Usable MVP:** Add upload/review/download flow and standalone notes console; reuse existing console assets; deploy and perform real PowerPoint smoke tests.

**Pass 3 — AI polish:** Add optional narrative notes, four styles, compact batching, validation, caching and cost instrumentation.

Do not combine all three passes into one large speculative rewrite. Each pass should leave working, testable software.

## 11. Risks and open decisions

- `python-pptx` has limitations around slide insertion and some PowerPoint features. Prefer robust, documented behavior over clever hacks.
- Internal hyperlinks must be validated in desktop PowerPoint, including slideshow mode.
- Decks with complex masters, existing links, animations, grouped shapes or unusual layouts may need conservative handling.
- Section-detection heuristics will be imperfect; provide a review step rather than claiming certainty.
- Privacy: treat uploaded decks as potentially confidential; do not send them to an LLM unless the user explicitly invokes AI notes.
- AI provider, pricing and credit model are intentionally undecided.

## 12. Product positioning

**Short description:** Make your existing PowerPoint easier to navigate and easier to present — with a clickable contents page, a private speaking-notes console and optional AI storytelling help.

**Workfriend.ai tools listing:** *Big Prezo — Keep the deck you've got. Make it easier to present.*
