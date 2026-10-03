#!/usr/bin/env python3
"""watchlist.py — tiny JSON-backed watchlist with thesis + invalidation trigger.

Usage:
  watchlist.py add <TICKER> "<thesis>" "<invalidation trigger>"
  watchlist.py remove <TICKER>
  watchlist.py list
  watchlist.py check          # live prices + day change vs your triggers

Tickers are Yahoo Finance symbols (e.g. IPC -> ^MXX, CEMEXCPO.MX).
`check` pulls the latest quote for each holding — free, no key — and shows
it next to your thesis so the review is grounded in today's price.
The invalidation trigger itself is yours to judge, not the tool's.
"""

import json
import os
import sys
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
WATCH_PATH = os.path.join(HERE, "data", "watchlist.json")
USER_AGENT = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
              "AppleWebKit/537.36 (KHTML, like Gecko) "
              "Chrome/126.0.0.0 Safari/537.36")

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
WATCH_PATH = os.path.join(HERE, "data", "watchlist.json")


def load():
    if os.path.exists(WATCH_PATH):
        with open(WATCH_PATH) as f:
            return json.load(f)
    return []


def save(items):
    with open(WATCH_PATH, "w") as f:
        json.dump(items, f, indent=2)


def cmd_add(ticker, thesis, trigger):
    items = load()
    ticker = ticker.upper()
    items = [i for i in items if i["ticker"] != ticker]
    items.append({"ticker": ticker, "thesis": thesis, "trigger": trigger})
    save(items)
    print(f"watchlist: added {ticker}")


def cmd_remove(ticker):
    items = load()
    ticker = ticker.upper()
    items = [i for i in items if i["ticker"] != ticker]
    save(items)
    print(f"watchlist: removed {ticker}")


def cmd_list():
    items = load()
    if not items:
        print("watchlist: empty — add one with: watchlist.py add <TICKER> \"<thesis>\" \"<trigger>\"")
        return
    for i in items:
        print(f"- {i['ticker']}\n    thesis: {i['thesis']}\n    kill it if: {i['trigger']}")


def cmd_check():
    items = load()
    if not items:
        print("watchlist: nothing to check")
        return
    print("watchlist check — review each trigger honestly:\n")
    for i in items:
        quote = fetch_quote(i["ticker"])
        if quote is None:
            price_txt = "price unavailable (offline?)"
        else:
            price, chg = quote
            price_txt = f"{price:,.2f} ({chg:+.2f}% today)"
        print(f"[{i['ticker']}] {price_txt}\n"
              f"  thesis: {i['thesis']}\n"
              f"  invalidated if: {i['trigger']}\n")


# Map friendly names to Yahoo symbols; anything else passes through as-is.
SYMBOL_MAP = {"IPC": "^MXX"}


def fetch_quote(ticker):
    """Return (latest_close, day_change_pct) or None on any failure."""
    symbol = SYMBOL_MAP.get(ticker.upper(), ticker)
    url = ("https://query1.finance.yahoo.com/v8/finance/chart/"
           + urllib.parse.quote(symbol, safe="")
           + "?interval=1d&range=5d")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=20) as resp:
            payload = json.load(resp)
        result = (payload.get("chart") or {}).get("result")
        if not result:
            return None
        closes = (result[0].get("indicators") or {}).get("quote", [{}])[0].get("close") or []
        closes = [c for c in closes if c]
        if len(closes) < 2:
            return None
        chg = (closes[-1] - closes[-2]) / closes[-2] * 100
        return round(closes[-1], 2), round(chg, 2)
    except Exception:
        return None


def main(argv):
    os.makedirs(os.path.dirname(WATCH_PATH), exist_ok=True)
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__.strip().split("\n\n")[1])
        return 0
    cmd = argv[0]
    if cmd == "add" and len(argv) == 4:
        cmd_add(argv[1], argv[2], argv[3])
    elif cmd == "remove" and len(argv) == 2:
        cmd_remove(argv[1])
    elif cmd == "list" and len(argv) == 1:
        cmd_list()
    elif cmd == "check" and len(argv) == 1:
        cmd_check()
    else:
        print("usage: watchlist.py add|remove|list|check [...]", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
