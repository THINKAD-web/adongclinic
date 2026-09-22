#!/usr/bin/env python3
"""Generate community archive HTML from legacy-board-data.json."""

from __future__ import annotations

import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "legacy-board-data.json"

ARCHIVE_META = {
    "activities": {
        "file": "community-activities.html",
        "title": "대외활동",
        "eyebrow": "Activities",
        "heading": "대외활동 아카이브",
        "desc": "교육·복지·학교 등에서 이어온 강의와 대외 활동 기록입니다.",
    },
    "Press": {
        "file": "community-press.html",
        "title": "방송 및 보도자료",
        "eyebrow": "Press",
        "heading": "방송 및 보도자료",
        "desc": "방송 출연 및 언론 보도 자료를 모았습니다.",
    },
    "writing": {
        "file": "community-writing.html",
        "title": "저술 및 연구활동",
        "eyebrow": "Writing",
        "heading": "저술 및 연구활동",
        "desc": "저서·논문·학술 발표 및 연구 활동 기록입니다.",
        "crosslink": (
            '<p class="archive-crosslink">'
            '<a href="specialty-borderline.html">경계성 지능 특화클리닉 — 연구의 선두기관</a>'
            " 페이지에서도 관련 연구를 소개합니다."
            "</p>"
        ),
    },
}


def excerpt(text: str, limit: int = 120) -> str:
    t = re.sub(r"\s+", " ", text or "").strip()
    if len(t) <= limit:
        return t
    return t[: limit - 1] + "…"


def nav_shell(title: str, body: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{html.escape(title)} | 한국아동상담센터</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Nanum+Myeongjo:wght@700;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable.min.css">
<link rel="stylesheet" href="styles/archive.css">
</head>
<body>
<header class="archive-header">
  <a href="index.html" class="archive-logo">한국아동상담센터</a>
  <a href="index.html#community" class="archive-back">← 메인으로</a>
</header>
<main class="archive-main">
{body}
</main>
<footer class="archive-footer">
  <p>© 한국아동상담센터 · 마이그레이션 아카이브</p>
</footer>
</body>
</html>
"""


def list_page(board: str, posts: list[dict]) -> str:
    meta = ARCHIVE_META[board]
    items = []
    for p in posts:
        date = html.escape(p.get("list_date") or "—")
        title = html.escape(p.get("title") or "")
        summary = html.escape(excerpt(p.get("content_text", "")))
        href = f"community-post.html?board={board}&wr_id={html.escape(p['wr_id'], quote=True)}"
        items.append(
            f"""<a class="archive-item" href="{href}">
  <span class="archive-date">{date}</span>
  <span class="archive-body">
    <span class="archive-title">{title}</span>
    <span class="archive-excerpt">{summary}</span>
  </span>
</a>"""
        )
    cross = meta.get("crosslink", "")
    body = f"""
<section class="archive-hero">
  <p class="archive-eyebrow">{html.escape(meta['eyebrow'])}</p>
  <h1>{html.escape(meta['heading'])}</h1>
  <p class="archive-lead">{html.escape(meta['desc'])}</p>
  {cross}
  <p class="archive-count">총 {len(posts)}건</p>
</section>
<div class="archive-list">
{''.join(items)}
</div>
"""
    return nav_shell(meta["title"], body)


def post_page_template() -> str:
    return nav_shell(
        "게시글",
        """
<section class="archive-hero">
  <p class="archive-eyebrow" id="postEyebrow">Archive</p>
  <h1 id="postTitle">불러오는 중…</h1>
  <p class="archive-meta" id="postMeta"></p>
</section>
<article class="archive-article" id="postContent"></article>
<p class="archive-back-inline"><a id="postBack" href="#">← 목록으로</a></p>
<script src="scripts/community-post.js"></script>
""",
    )


def patch_index_snippets(data: dict) -> None:
    index_path = ROOT / "index.html"
    text = index_path.read_text(encoding="utf-8")

    act = data.get("activities", [])[:4]
    press = data.get("Press", [])[:4]
    writing = data.get("writing", [])[:7]

    def li_items(posts: list[dict]) -> str:
        lines = []
        for p in posts:
            t = html.escape(p.get("title", ""))
            lines.append(f"          <li>{t}</li>")
        return "\n".join(lines)

    text = re.sub(
        r'(<a href=")http://www\.adongclinic\.co\.kr/bbs/board\.php\?bo_table=activities(" target="_blank" rel="noopener" class="community-card community-card--link reveal">)',
        r'\1community-activities.html\2',
        text,
        count=1,
    )
    text = re.sub(
        r'(<ul class="community-list">\n)(.*?)(\n        </ul>\n        <span class="community-link">대외활동)',
        lambda m: m.group(1) + li_items(act) + m.group(3),
        text,
        count=1,
        flags=re.S,
    )

    text = re.sub(
        r'(<a href=")http://www\.adongclinic\.co\.kr/bbs/board\.php\?bo_table=Press(" target="_blank" rel="noopener" class="community-card community-card--link reveal reveal-d1">)',
        r'\1community-press.html\2',
        text,
        count=1,
    )
    text = re.sub(
        r'(<h3>방송 및 보도자료</h3>\n        <p>.*?</p>\n        <ul class="community-list">\n)(.*?)(\n        </ul>\n        <span class="community-link">방송 및 보도자료)',
        lambda m: m.group(1) + li_items(press) + m.group(3),
        text,
        count=1,
        flags=re.S,
    )

    text = re.sub(
        r'(<a href=")http://www\.adongclinic\.co\.kr/bbs/board\.php\?bo_table=writing(" target="_blank" rel="noopener" class="community-card community-card--link reveal reveal-d2">)',
        r'\1community-writing.html\2',
        text,
        count=1,
    )
    text = re.sub(
        r'(<h3>저술 및 연구활동</h3>\n        <p>.*?</p>\n        <ul class="community-list">\n)(.*?)(\n        </ul>\n        <span class="community-link">저술)',
        lambda m: m.group(1) + li_items(writing) + m.group(3),
        text,
        count=1,
        flags=re.S,
    )

    # Media section: link + featured from latest Press
    if press:
        latest = data["Press"][0]
        featured_title = html.escape(latest.get("title", ""))
        featured_date = html.escape(latest.get("list_date") or "")
        text = re.sub(
            r'(<p class="media-featured-meta">)EBS 심층취재 · 2014(</p>\s*<h3 class="media-featured-title">).*?(</h3>\s*<p class="media-featured-meta">).*?(</p>)',
            rf"\1{featured_date}\2{featured_title}\3{featured_date}\4",
            text,
            count=1,
            flags=re.S,
        )
    text = re.sub(
        r'(<section id="media">[\s\S]*?</div>\n    </div>\n  </div>\n</section>)',
        lambda m: m.group(0).replace(
            "</section>",
            '\n    <p style="margin-top:24px;text-align:center;"><a href="community-press.html" class="community-link">방송 및 보도자료 전체 보기 →</a></p>\n  </div>\n</section>',
            1,
        )
        if "community-press.html" not in m.group(0)
        else m.group(0),
        text,
        count=1,
    )

    index_path.write_text(text, encoding="utf-8")


def main() -> None:
    data = json.loads(DATA.read_text(encoding="utf-8"))
    for board, posts in data.items():
        meta = ARCHIVE_META[board]
        out = ROOT / meta["file"]
        out.write_text(list_page(board, posts), encoding="utf-8")
        print(f"Wrote {out} ({len(posts)} items)")

    (ROOT / "community-post.html").write_text(post_page_template(), encoding="utf-8")
    print("Wrote community-post.html (run scripts/patch_index_community.py for index updates)")


if __name__ == "__main__":
    main()
