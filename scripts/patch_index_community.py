#!/usr/bin/env python3
"""Safely refresh index.html community card lists from legacy-board-data.json.

Does NOT modify the #media section (edit that manually or via a dedicated script).
"""

from __future__ import annotations

import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "legacy-board-data.json"
INDEX = ROOT / "index.html"


def li_items(posts: list[dict]) -> str:
    lines = []
    for p in posts:
        t = html.escape(p.get("title", ""))
        lines.append(f"          <li>{t}</li>")
    return "\n".join(lines)


def main() -> None:
    data = json.loads(DATA.read_text(encoding="utf-8"))
    text = INDEX.read_text(encoding="utf-8")

    act = data.get("activities", [])[:4]
    press = data.get("Press", [])[:4]
    writing = data.get("writing", [])[:7]

    replacements = [
        (
            r'(<a href="community-activities\.html" class="community-card community-card--link reveal">\s*<h3>대외활동</h3>\s*<p>.*?</p>\s*<ul class="community-list">\n)(.*?)(\n        </ul>)',
            lambda m: m.group(1) + li_items(act) + m.group(3),
        ),
        (
            r'(<a href="community-press\.html" class="community-card community-card--link reveal reveal-d1">\s*<h3>방송 및 보도자료</h3>\s*<p>.*?</p>\s*<ul class="community-list">\n)(.*?)(\n        </ul>)',
            lambda m: m.group(1) + li_items(press) + m.group(3),
        ),
        (
            r'(<a href="community-writing\.html" class="community-card community-card--link reveal reveal-d2">\s*<h3>저술 및 연구활동</h3>\s*<p>.*?</p>\s*<ul class="community-list">\n)(.*?)(\n        </ul>)',
            lambda m: m.group(1) + li_items(writing) + m.group(3),
        ),
    ]

    for pattern, repl in replacements:
        new_text, n = re.subn(pattern, repl, text, count=1, flags=re.S)
        if n != 1:
            raise SystemExit(f"Expected 1 match for community block, got {n}: {pattern[:60]}…")
        text = new_text

    # Ensure internal links (no target=_blank on archive cards)
    text = text.replace(
        'href="community-activities.html" target="_blank" rel="noopener" class="community-card',
        'href="community-activities.html" class="community-card',
    )
    text = text.replace(
        'href="community-press.html" target="_blank" rel="noopener" class="community-card',
        'href="community-press.html" class="community-card',
    )
    text = text.replace(
        'href="community-writing.html" target="_blank" rel="noopener" class="community-card',
        'href="community-writing.html" class="community-card',
    )

    INDEX.write_text(text, encoding="utf-8")
    print("Updated index.html community snippets only.")


if __name__ == "__main__":
    main()
