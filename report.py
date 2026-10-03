#!/usr/bin/env python3
"""report.py — generate report.html: headline stats, 90-day SVG sparkline,
AI brief, watchlist status. Phone-readable, no JS, no external assets."""

import csv
import html
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(HERE, "data", "ipc.csv")
STATS_PATH = os.path.join(HERE, "data", "stats.json")
BRIEF_PATH = os.path.join(HERE, "data", "brief.txt")
WATCH_PATH = os.path.join(HERE, "data", "watchlist.json")
FORECAST_PATH = os.path.join(HERE, "data", "forecast.json")
NEWS_PATH = os.path.join(HERE, "data", "news.json")
OUT_PATH = os.path.join(HERE, "report.html")


def load_closes(n=90):
    closes = []
    with open(CSV_PATH, newline="") as f:
        for row in csv.DictReader(f):
            try:
                closes.append(float(row["Close"]))
            except (KeyError, ValueError):
                continue
    return closes[-n:]


def sparkline_svg(values, width=340, height=90):
    """Inline SVG polyline. Green if up over the window, red if down."""
    if len(values) < 2:
        return ""
    lo, hi = min(values), max(values)
    span = hi - lo if hi > lo else 1.0
    pts = []
    for i, v in enumerate(values):
        x = i / (len(values) - 1) * (width - 8) + 4
        y = height - 6 - (v - lo) / span * (height - 16)
        pts.append(f"{x:.1f},{y:.1f}")
    color = "#2e9e5b" if values[-1] >= values[0] else "#d64545"
    return (
        f'<svg viewBox="0 0 {width} {height}" width="100%" '
        f'style="max-width:{width}px;display:block" role="img" aria-label="90-day trend">'
        f'<polyline points="{" ".join(pts)}" fill="none" stroke="{color}" stroke-width="2"/>'
        "</svg>"
    )


def fmt(x):
    return f"{x:,.2f}" if isinstance(x, (int, float)) else "—"


def main():
    for p in (CSV_PATH, STATS_PATH):
        if not os.path.exists(p):
            print(f"report: {p} missing — run fetch.py and analyze.py first", file=sys.stderr)
            return 2
    with open(STATS_PATH) as f:
        s = json.load(f)
    brief = open(BRIEF_PATH).read().strip() if os.path.exists(BRIEF_PATH) else "No brief yet — run brief.py."
    watch = json.load(open(WATCH_PATH)) if os.path.exists(WATCH_PATH) else []
    forecast = json.load(open(FORECAST_PATH)) if os.path.exists(FORECAST_PATH) else None
    news = json.load(open(NEWS_PATH)) if os.path.exists(NEWS_PATH) else []

    closes = load_closes(90)
    chg = s["day_change_pct"]
    chg_cls = "up" if chg >= 0 else "down"

    stat_rows = [
        ("Day change", f"{chg:+.2f}%"),
        ("20-day avg", fmt(s.get("ma20"))),
        ("50-day avg", fmt(s.get("ma50"))),
        ("200-day avg", fmt(s.get("ma200"))),
        ("52-week high", fmt(s.get("high_52w"))),
        ("Below 52w high", f"{s['drawdown_from_52w_pct']:.2f}%"),
        ("Streak", f"{abs(s['streak_days'])}d {'up' if s['streak_days'] > 0 else 'down' if s['streak_days'] < 0 else 'flat'}"),
    ]
    if s.get("all_time_high"):
        stat_rows.append(("All-time high", "YES"))

    stats_html = "".join(
        f"<tr><td>{html.escape(k)}</td><td class='num'>{html.escape(v)}</td></tr>"
        for k, v in stat_rows
    )

    if watch:
        watch_html = "".join(
            f"<li><b>{html.escape(w['ticker'])}</b> — {html.escape(w['thesis'])}"
            f"<br><span class='trig'>Kill it if: {html.escape(w['trigger'])}</span></li>"
            for w in watch
        )
        watch_html = f"<ul>{watch_html}</ul>"
    else:
        watch_html = "<p class='dim'>Watchlist empty. Add one:<br><code>python3 watchlist.py add CEMEXCPO.MX \"thesis\" \"kill trigger\"</code></p>"

    if news:
        items = "".join(
            f"<li><a href=\"{html.escape(n['link'])}\">{html.escape(n['title'])}</a>"
            f"<br><span class='dim'>{html.escape(n['source'])}</span></li>"
            for n in news if n.get("title")
        )
        news_html = f"<h2>Latest BMV news</h2><ul class='news'>{items}</ul>" if items else ""
    else:
        news_html = "<h2>Latest BMV news</h2><p class='dim'>News feed unavailable.</p>"

    forecast_html = ""
    if forecast:
        pts = "".join(
            f"<tr><td>{html.escape(d)}</td><td class='num'>{x:,.2f}</td></tr>"
            for d, x in forecast.get("points", [])
        )
        forecast_html = (
            "<h2>7-day forecast <span class='tag'>TabPFN</span></h2>"
            f"<table>{pts}</table>"
            "<p class='dim'>Experimental local forecast — not advice.</p>"
        )

    page = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>BolsaBuddy — IPC {html.escape(s['latest_date'])}</title>
<style>
body{{font-family:-apple-system,system-ui,sans-serif;margin:0 auto;max-width:560px;padding:16px;line-height:1.5;color:#1a1a1a}}
h1{{font-size:1.4rem;margin:0}} h2{{font-size:1.05rem;margin-top:1.6em;border-bottom:1px solid #eee;padding-bottom:4px}}
.price{{font-size:2rem;font-weight:700}} .up{{color:#2e9e5b}} .down{{color:#d64545}}
.dim{{color:#666;font-size:.9rem}} table{{width:100%;border-collapse:collapse}}
td{{padding:6px 4px;border-bottom:1px solid #f0f0f0}} td.num{{text-align:right;font-variant-numeric:tabular-nums}}
ul{{padding-left:1.2em}} ul.news li{{margin-bottom:.7em}} ul.news a{{color:#1a1a1a;text-decoration:none}} ul.news a:active{{color:#666}} .trig{{color:#8a5a00;font-size:.9rem}} .tag{{font-size:.7rem;background:#eef;border-radius:4px;padding:2px 6px;color:#446}}
code{{font-size:.85rem;background:#f5f5f5;padding:2px 5px;border-radius:4px}}
.brief{{background:#fafafa;border-left:3px solid #2e9e5b;padding:10px 12px;white-space:pre-wrap}}
footer{{margin-top:2em;font-size:.8rem;color:#999}}
h2,.brief,table{{break-inside:avoid}}
</style>
</head>
<body>
<h1>&#x1f4c8; BolsaBuddy</h1>
<p class="dim">Mexican IPC index &middot; {html.escape(s['latest_date'])} &middot; free data, local AI, $0</p>
<div class="price">{fmt(s['latest_close'])} <span class="{chg_cls}">{chg:+.2f}%</span></div>
{sparkline_svg(closes)}
<p class="dim">Last 90 closes</p>
<h2>Stats</h2>
<table>{stats_html}</table>
<h2>Daily brief</h2>
<div class="brief">{html.escape(brief)}</div>
<h2>Watchlist</h2>
{watch_html}
{news_html}
{forecast_html}
<footer>Data: Yahoo Finance free daily feed (^MXX). Brief: local open-weight model. Not investment advice.</footer>
</body>
</html>"""

    with open(OUT_PATH, "w") as f:
        f.write(page)
    print(f"report: wrote {OUT_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
