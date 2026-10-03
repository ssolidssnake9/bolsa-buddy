#!/usr/bin/env python3
"""news.py — latest BMV/IPC headlines via Google News RSS (free, no key).

Writes data/news.json: [{title, source, link, published}]. Never crashes
the pipeline: on any failure it writes an empty list and exits 0, so the
report simply shows "news unavailable".
"""

import json
import os
import sys
import urllib.request
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
NEWS_PATH = os.path.join(HERE, "data", "news.json")
RSS_URL = ("https://news.google.com/rss/search"
           "?q=Bolsa%20Mexicana%20de%20Valores%20IPC"
           "&hl=es-419&gl=MX&ceid=MX%3Aes-419")
USER_AGENT = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
              "AppleWebKit/537.36 (KHTML, like Gecko) "
              "Chrome/126.0.0.0 Safari/537.36")
MAX_ITEMS = 5


def fetch_headlines():
    req = urllib.request.Request(RSS_URL, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as resp:
        root = ET.fromstring(resp.read())
    items = []
    for it in root.findall(".//item")[:MAX_ITEMS]:
        raw_title = (it.findtext("title") or "").strip()
        # Google News titles end with " - Source Name"
        title, _, source = raw_title.rpartition(" - ")
        if not source:
            title, source = raw_title, ""
        items.append({
            "title": title.strip(),
            "source": source.strip(),
            "link": (it.findtext("link") or "").strip(),
            "published": (it.findtext("pubDate") or "").strip(),
        })
    return items


def main():
    os.makedirs(os.path.dirname(NEWS_PATH), exist_ok=True)
    try:
        items = fetch_headlines()
    except Exception as exc:
        print(f"news: feed failed ({exc}); writing empty list")
        items = []
    with open(NEWS_PATH, "w") as f:
        json.dump(items, f, indent=2, ensure_ascii=False)
    print(f"news: wrote data/news.json ({len(items)} headlines)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
