#!/usr/bin/env python3
"""Scrape legacy GNU Board posts from adongclinic.co.kr (addendum-12)."""

from __future__ import annotations

import json
import re
import time
from pathlib import Path
from urllib.parse import urljoin, urlparse, parse_qs

import requests
from bs4 import BeautifulSoup

BASE = "http://www.adongclinic.co.kr/bbs/board.php"
G5 = "http://www.adongclinic.co.kr"
ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
PUBLIC_BOARDS = ["activities", "Press", "writing"]
PRIVATE_BOARDS = ["qa"]
DELAY_SEC = 1.0
SESSION = requests.Session()
SESSION.headers.update(
    {
        "User-Agent": "KCCCLegacyMigration/1.0 (+internal site migration; contact kidclinic@naver.com)",
        "Accept-Language": "ko-KR,ko;q=0.9",
    }
)


def fetch_html(url: str, params: dict | None = None) -> str:
    resp = SESSION.get(url, params=params, timeout=20)
    resp.raise_for_status()
    if resp.encoding and resp.encoding.lower() in ("iso-8859-1", "ascii"):
        resp.encoding = resp.apparent_encoding or "utf-8"
    return resp.text


def absolutize_url(href: str) -> str:
    if not href:
        return href
    return urljoin(G5 + "/", href)


def parse_wr_id(url: str) -> str | None:
    q = parse_qs(urlparse(url).query)
    wr = q.get("wr_id")
    return wr[0] if wr else None


def parse_list_page(html: str, bo_table: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    rows: list[dict] = []
    seen: set[str] = set()

    for link in soup.select("#bo_list a[href*='wr_id']"):
        href = absolutize_url(link.get("href", ""))
        wr_id = parse_wr_id(href)
        if not wr_id or wr_id in seen:
            continue
        title = link.get_text(strip=True)
        if not title:
            continue
        seen.add(wr_id)

        list_date = None
        row = link.find_parent("tr")
        if row:
            date_el = row.select_one("td.td_datetime")
            if date_el:
                list_date = date_el.get_text(strip=True)
        if not list_date:
            container = link.find_parent("div", class_=re.compile("webzine|subject"))
            if container:
                date_el = container.select_one(".webzine_date")
                if date_el:
                    list_date = re.sub(
                        r".*Date\s*",
                        "",
                        date_el.get_text(" ", strip=True),
                        flags=re.I,
                    ).strip()

        rows.append(
            {
                "wr_id": wr_id,
                "title": title,
                "url": href,
                "list_date": list_date,
                "bo_table": bo_table,
            }
        )
    return rows


def max_page(html: str) -> int:
    pages = [1]
    for a in BeautifulSoup(html, "html.parser").select("a.pg_page[href*='page=']"):
        m = re.search(r"page=(\d+)", a.get("href", ""))
        if m:
            pages.append(int(m.group(1)))
    return max(pages)


def rewrite_content_html(content_el) -> tuple[str, list[str]]:
    image_urls: list[str] = []
    if content_el is None:
        return "", image_urls
    for img in content_el.select("img"):
        src = img.get("src") or img.get("data-src")
        if src:
            abs_src = absolutize_url(src)
            img["src"] = abs_src
            image_urls.append(abs_src)
    for a in content_el.select("a[href]"):
        a["href"] = absolutize_url(a.get("href", ""))
    return str(content_el), image_urls


def fetch_post_detail(post: dict) -> dict:
    html = fetch_html(post["url"])
    soup = BeautifulSoup(html, "html.parser")
    title_el = soup.select_one("#bo_v_title .bo_v_tit") or soup.select_one("#bo_v_title")
    content_el = soup.select_one("#bo_v_con")
    content_html, inline_images = rewrite_content_html(content_el)
    gallery_images = [
        absolutize_url(img.get("src"))
        for img in soup.select("#bo_v_img img[src]")
        if img.get("src")
    ]
    return {
        **post,
        "title": title_el.get_text(strip=True) if title_el else post["title"],
        "content_html": content_html,
        "content_text": content_el.get_text("\n", strip=True) if content_el else "",
        "images": list(dict.fromkeys(gallery_images + inline_images)),
    }


def scrape_board(bo_table: str) -> list[dict]:
    first_html = fetch_html(BASE, params={"bo_table": bo_table})
    last_page = max_page(first_html)
    all_posts: list[dict] = []
    seen_ids: set[str] = set()

    for page in range(1, last_page + 1):
        html = first_html if page == 1 else fetch_html(BASE, params={"bo_table": bo_table, "page": page})
        batch = parse_list_page(html, bo_table)
        if not batch:
            break
        for item in batch:
            if item["wr_id"] in seen_ids:
                continue
            seen_ids.add(item["wr_id"])
            detail = fetch_post_detail(item)
            all_posts.append(detail)
            time.sleep(DELAY_SEC)
        time.sleep(DELAY_SEC)
        print(f"  [{bo_table}] page {page}/{last_page} — total {len(all_posts)} posts", flush=True)

    return all_posts


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    public: dict[str, list] = {}
    for board in PUBLIC_BOARDS:
        print(f"Scraping {board}...", flush=True)
        public[board] = scrape_board(board)

    out_public = DATA_DIR / "legacy-board-data.json"
    out_public.write_text(json.dumps(public, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {out_public} ({sum(len(v) for v in public.values())} posts)", flush=True)

    private: dict[str, list] = {}
    for board in PRIVATE_BOARDS:
        print(f"Scraping private {board}...", flush=True)
        private[board] = scrape_board(board)
    out_private = DATA_DIR / "qa-archive-private.json"
    out_private.write_text(json.dumps(private, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {out_private} ({len(private.get('qa', []))} posts) — NOT for public site", flush=True)


if __name__ == "__main__":
    main()
