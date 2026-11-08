#!/usr/bin/env python3
"""Deterministic quality gate for CODEN's architecture-board SVGs.

This validates SVG source structure and measurable design constraints.
It does not replace human inspection of rendered PNG/PDF output.
"""
from __future__ import annotations

import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BOARD_DIR = ROOT / "design-system" / "boards"
EXPECTED = 15
SVG_NS = "{http://www.w3.org/2000/svg}"
MIN_FONT = 13.0


def fail(errors: list[str], board: str, message: str) -> None:
    errors.append(f"{board}: {message}")


def inspect(path: Path) -> list[str]:
    errors: list[str] = []
    name = path.name
    try:
        tree = ET.parse(path)
    except (ET.ParseError, OSError) as exc:
        return [f"{name}: invalid XML/SVG ({exc})"]

    root = tree.getroot()
    if root.tag != f"{SVG_NS}svg":
        fail(errors, name, "root element is not SVG")
    if root.attrib.get("viewBox") != "0 0 1920 1080":
        fail(errors, name, "viewBox must be exactly 0 0 1920 1080")
    if root.attrib.get("role") != "img":
        fail(errors, name, 'root must declare role="img"')

    labelled = root.attrib.get("aria-labelledby", "").split()
    ids = {node.attrib["id"] for node in root.iter() if "id" in node.attrib}
    if len(labelled) != 2 or any(item not in ids for item in labelled):
        fail(errors, name, "aria-labelledby must reference an existing title and description")
    else:
        title = next((n for n in root.iter(f"{SVG_NS}title") if n.attrib.get("id") == labelled[0]), None)
        desc = next((n for n in root.iter(f"{SVG_NS}desc") if n.attrib.get("id") == labelled[1]), None)
        if title is None or not (title.text or "").strip():
            fail(errors, name, "accessible title is missing or empty")
        if desc is None or not (desc.text or "").strip():
            fail(errors, name, "accessible description is missing or empty")

    all_ids = [node.attrib["id"] for node in root.iter() if "id" in node.attrib]
    if len(all_ids) != len(set(all_ids)):
        fail(errors, name, "duplicate SVG id values")

    text_nodes = list(root.iter(f"{SVG_NS}text"))
    if not text_nodes:
        fail(errors, name, "no text nodes found")
    for node in text_nodes:
        raw = node.attrib.get("font-size")
        if raw is None:
            continue
        match = re.fullmatch(r"([0-9]+(?:\.[0-9]+)?)(?:px)?", raw.strip())
        if match and float(match.group(1)) < MIN_FONT:
            fail(errors, name, f"text size below {MIN_FONT:g}px: {raw}")
            break

    # External images/stylesheets can break portability and expose unexpected dependencies.
    for node in root.iter():
        href = node.attrib.get("href") or node.attrib.get("{http://www.w3.org/1999/xlink}href")
        if href and re.match(r"^https?://", href, re.I):
            fail(errors, name, "external HTTP(S) asset reference found")
            break

    return errors


def main() -> int:
    boards = sorted(BOARD_DIR.glob("[0-9][0-9]-*.svg"))
    errors: list[str] = []
    if len(boards) != EXPECTED:
        errors.append(f"Expected exactly {EXPECTED} numbered SVG boards; found {len(boards)}")
    for board in boards:
        errors.extend(inspect(board))

    if errors:
        print("ARCHITECTURE SVG QUALITY GATE: FAIL")
        print("\n".join(f"- {item}" for item in errors))
        return 1

    print(f"ARCHITECTURE SVG QUALITY GATE: PASS ({len(boards)} boards)")
    print("- SVG XML parses successfully")
    print("- 1920×1080 viewBox is consistent")
    print("- accessible title/description references are valid")
    print("- IDs are unique; explicit text sizes meet the 13px minimum")
    print("- no external HTTP(S) image dependencies found")
    print("NOTE: rendered-layout and A4 print inspection remain separate release checks.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
