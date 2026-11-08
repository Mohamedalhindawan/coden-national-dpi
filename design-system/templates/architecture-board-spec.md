# CODEN Architecture Board Template 1.0

## Purpose
A reusable, editable 16:9 SVG board for architecture diagrams in the CODEN Enterprise Operating & Engineering Playbook.

## Files
- `architecture-board.svg`: vector template; edit labels, shapes, connectors, and metadata in an SVG-capable editor.
- `architecture-board.mmd`: source-level Mermaid starter for logic and relationships.

## Layout specification
- Canvas: 1920 × 1080 (16:9).
- Header: CODEN identity lockup placeholder, board version, architecture status.
- Title block: diagram title and one-sentence purpose.
- Main canvas: system boundary, architecture layers, components, and directional flows.
- Cross-cutting controls: identity, security, privacy, data governance, observability, human approval.
- Footer: legend, owner, date, figure number, document/version note.

## Production rules
1. Replace placeholders with verified architecture content; do not leave bracketed placeholders in released boards.
2. Use the approved source logo asset. The lighthouse-like mark in the SVG is a neutral placeholder only and must not be represented as official logo artwork.
3. Palette values are provisional; verify against approved brand source files before final publication.
4. Use actual vector shapes and editable text; do not rasterize the complete board.
5. Add legends and label all important flows. Never use color as the only signal.
6. Label diagrams as Current State, Target State, or Conceptual.
7. Add sources, assumptions, and limitations where the diagram depends on external systems or proposed integrations.
8. Export PNG at 2× or 3× only for previews; retain SVG/Mermaid source as the editable master.

## Review checklist
- Technical relationships and arrow direction verified by architecture owner.
- Names match the relevant CODEN architecture documentation.
- No unverified integrations or implementation claims.
- Text legible at presentation size.
- Arabic RTL and English LTR render correctly.
- Logo and colors approved.
- Figure number, owner, date, and version completed.
