#!/usr/bin/env python3
"""analyze.py — compute headline stats from data/ipc.csv into data/stats.json.

Stats: latest close, day change %, 20/50/200-day moving averages,
distance from 52-week high (drawdown %), current up/down streak,
all-time-high flag.
"""

import csv
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(HERE, "data", "ipc.csv")
STATS_PATH = os.path.join(HERE, "data", "stats.json")


def load_rows(path):
    rows = []
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            try:
                rows.append({
                    "date": row["Date"].strip(),
                    "open": float(row["Open"]),
                    "high": float(row["High"]),
                    "low": float(row["Low"]),
                    "close": float(row["Close"]),
                })
            except (KeyError, ValueError):
                continue
    rows.sort(key=lambda r: r["date"])
    return rows


def moving_average(closes, n):
    if len(closes) < n:
        return None
    return sum(closes[-n:]) / n


def current_streak(closes):
    """Consecutive up/down days ending today. Positive = up streak."""
    if len(closes) < 2:
        return 0
    direction = 1 if closes[-1] > closes[-2] else -1
    n = 1
    for i in range(len(closes) - 2, 0, -1):
        d = 1 if closes[i + 1] > closes[i] else -1
        if d == direction:
            n += 1
        else:
            break
    return direction * n


def analyze(rows):
    closes = [r["close"] for r in rows]
    latest = rows[-1]
    prev = rows[-2] if len(rows) > 1 else latest

    year_rows = rows[-252:] if len(rows) >= 252 else rows
    high_52w = max(r["high"] for r in year_rows)
    all_time_high = max(r["high"] for r in rows)

    day_change_pct = (latest["close"] - prev["close"]) / prev["close"] * 100
    drawdown_pct = (latest["close"] - high_52w) / high_52w * 100

    return {
        "latest_date": latest["date"],
        "latest_close": round(latest["close"], 2),
        "day_change_pct": round(day_change_pct, 2),
        "ma20": round(moving_average(closes, 20), 2) if moving_average(closes, 20) else None,
        "ma50": round(moving_average(closes, 50), 2) if moving_average(closes, 50) else None,
        "ma200": round(moving_average(closes, 200), 2) if moving_average(closes, 200) else None,
        "high_52w": round(high_52w, 2),
        "drawdown_from_52w_pct": round(drawdown_pct, 2),
        "streak_days": current_streak(closes),
        "all_time_high": latest["high"] >= all_time_high,
        "rows": len(rows),
    }


def main():
    if not os.path.exists(CSV_PATH):
        print("analyze: data/ipc.csv missing — run fetch.py first", file=sys.stderr)
        return 2
    rows = load_rows(CSV_PATH)
    if len(rows) < 2:
        print("analyze: not enough rows in ipc.csv", file=sys.stderr)
        return 2
    stats = analyze(rows)
    with open(STATS_PATH, "w") as f:
        json.dump(stats, f, indent=2)
    print(f"analyze: {stats['latest_date']} close {stats['latest_close']:,} "
          f"({stats['day_change_pct']:+.2f}%) -> data/stats.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
