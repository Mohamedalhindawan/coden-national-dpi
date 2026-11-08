# CODEN Architecture Boards — Visual QA Standard

**Scope:** 15 SVG architecture boards in `design-system/boards/`.
**Branch:** `feat/coden-visual-documentation-skills`
**Status:** Typography and contrast refinement applied; final rendered review remains required.
**Truth label:** All architecture boards describe a conceptual target state unless a board explicitly says otherwise.

## Non-negotiable acceptance criteria

### 1. Brand and system consistency
- Canvas is 1920 × 1080 with a consistent 16:9 composition.
- Navy, blue, turquoise and pale-neutral palette is consistent across all boards.
- Title, subtitle, section headers, cards, connectors, status label and footer follow one design system.
- No unofficial logo is presented as an approved CODEN mark. A lighthouse placeholder must be labelled as provisional until the approved asset is supplied.

### 2. Typography and legibility
- Main title is visually dominant and remains on one line where possible.
- Section headings are distinct from card titles and body copy.
- Body copy is readable at presentation size; secondary labels must not become the only carrier of critical meaning.
- Avoid tiny text. Any text below 13 px requires explicit justification and must remain legible in the rendered board.
- Use sufficient contrast for secondary text and connector labels.
- Avoid long all-caps phrases where sentence case improves scanning.

### 3. Layout and diagram quality
- No text, cards, arrows, labels or decorative shapes overlap unintentionally.
- No content is clipped by the canvas or card boundaries.
- Connectors terminate at the intended components and do not cross labels.
- Alignment, gutters, card padding and corner radii are consistent.
- Each board has a clear reading order and one primary visual focus.
- Reduce or split content rather than shrinking text to fit.

### 4. Architecture semantics
- Distinguish conceptual, proposed, validated, implemented and production states.
- Do not imply that integrations, teams, controls, platforms or government partnerships are live unless supported by evidence.
- Show human accountability and approval gates for high-impact actions.
- Use consistent names for shared platform capabilities across the 15 boards.
- Arrows must communicate a defined relationship (flow, dependency, governance or feedback), not decoration.

### 5. Accessibility and output
- Meaning is not conveyed by colour alone; labels and shapes provide redundant cues.
- Text/background contrast should meet WCAG 2.2 AA where applicable (4.5:1 for normal text; 3:1 for large text).
- SVGs must remain editable and include a meaningful title/description where practical.
- Verify SVG rendering in a browser and a vector editor.
- Export a 1920 × 1080 PNG preview for screen review and a print-ready PDF/A4 proof; inspect both at 100% zoom.

## Final review procedure

For each of the 15 boards:
1. Open the SVG in a standards-compliant browser or vector editor.
2. Inspect the full canvas at fit-to-screen.
3. Inspect dense regions at 100% zoom.
4. Check every text block against card boundaries and canvas edges.
5. Check arrow routing, hierarchy, contrast and consistency with related boards.
6. Export a PNG and an A4 proof; inspect line weights and smallest text.
7. Record pass/fail and a specific defect for every failed criterion.

## Current change log

- Increased small typography in the 15 SVGs to improve presentation-size readability.
- Darkened secondary text colours for stronger contrast.
- Added text-rendering hints for more consistent SVG output.
- Preserved the existing canvas geometry and conceptual-state labels.

## Release gate

Do **not** label the set “10/10”, “final”, or “print-approved” until all 15 rendered boards pass the procedure above. Source-level checks alone cannot detect every font substitution, text collision, clipping issue or printer-specific problem.

