#!/usr/bin/env python3
"""fetch.py — download free daily OHLC for the Mexican IPC index (^MXX).

Source: Yahoo Finance chart API (no key, no signup).
  https://query1.finance.yahoo.com/v8/finance/chart/%5EMXX?interval=1d&period1=..&period2=..

Why Yahoo and not Stooq: Stooq's free CSV sits behind a JS proof-of-work
challenge whose /__verify endpoint 403s non-browser TLS fingerprints from
this environment (QA 2026-10-01: browser-UA curl got the challenge page,
verify POST 403d). Yahoo's API answers plain JSON with the same data
(8,912 daily bars, 1991-11-11 -> present, verified same-day).

Output: data/ipc.csv with columns Date,Open,High,Low,Close,Volume
(Volume is 0 for indices). Same contract the old Stooq fetcher kept, so
analyze.py / report.py are untouched.

Behavior:
  - Skips the download when the cached file already holds today's date.
  - On network failure, keeps the cached copy and exits 0 (never crash).
  - If no cache exists at all and the network fails, exits 2 (fail loudly).
"""

import csv
import datetime as dt
import json
import os
import sys
import time
import urllib.request

YAHOO_URL = ("https://query1.finance.yahoo.com/v8/finance/chart/%5EMXX"
             "?interval=1d&period1=689827200&period2=9999999999")
USER_AGENT = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
              "AppleWebKit/537.36 (KHTML, like Gecko) "
              "Chrome/126.0.0.0 Safari/537.36")
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
CSV_PATH = os.path.join(DATA_DIR, "ipc.csv")


def latest_date_in_csv(path):
    """Return the max Date found in a cached CSV, or None."""
    latest = None
    try:
        with open(path, newline="") as f:
            for row in csv.DictReader(f):
                d = row.get("Date", "").strip()
                if d and (latest is None or d > latest):
                    latest = d
    except (OSError, csv.Error):
        return None
    return latest


def download(url, path):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=60) as resp:
        payload = json.loads(resp.read().decode())

    result = (payload.get("chart") or {}).get("result")
    if not result:
        err = (payload.get("chart") or {}).get("error") or {}
        raise RuntimeError(f"Yahoo returned no data: {err.get('description', err)}")
    result = result[0]

    stamps = result.get("timestamp") or []
    quote = (result.get("indicators") or {}).get("quote", [{}])[0]
    opens = quote.get("open") or []
    highs = quote.get("high") or []
    lows = quote.get("low") or []
    closes = quote.get("close") or []
    volumes = quote.get("volume") or []

    rows = []
    for i, ts in enumerate(stamps):
        c = closes[i] if i < len(closes) else None
        if c is None:
            continue  # Yahoo nulls out non-trading days; skip them
        # The live bar sometimes reports 0.0 for O/H/L; fall back to close.
        o = opens[i] if i < len(opens) and opens[i] else c
        h = highs[i] if i < len(highs) and highs[i] else c
        l = lows[i] if i < len(lows) and lows[i] else c
        v = volumes[i] if i < len(volumes) and volumes[i] else 0
        date = time.strftime("%Y-%m-%d", time.gmtime(ts))
        rows.append((date, o, h, l, c, int(v)))

    if not rows:
        raise RuntimeError("Yahoo returned zero usable bars")

    tmp = path + ".tmp"
    with open(tmp, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Date", "Open", "High", "Low", "Close", "Volume"])
        w.writerows([(d, f"{o:.2f}", f"{h:.2f}", f"{l:.2f}", f"{c:.2f}", v)
                     for d, o, h, l, c, v in rows])
    os.replace(tmp, path)
    return path


def main():
    os.makedirs(DATA_DIR, exist_ok=True)
    today = dt.date.today().isoformat()

    cached = latest_date_in_csv(CSV_PATH)
    if cached and cached >= today:
        print(f"fetch: cache already has {cached}; skipping download")
        return 0

    try:
        download(YAHOO_URL, CSV_PATH)
    except Exception as exc:  # network failure -> fall back to cache
        if cached:
            print(f"fetch: download failed ({exc}); using cached data through {cached}")
            return 0
        print(f"fetch: download failed and no cache exists: {exc}", file=sys.stderr)
        return 2

    fresh = latest_date_in_csv(CSV_PATH)
    print(f"fetch: downloaded ipc.csv (^MXX via Yahoo), latest row {fresh}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
