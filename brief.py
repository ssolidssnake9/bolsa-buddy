#!/usr/bin/env python3
"""brief.py — ask the local Ollama model to write a plain-English market brief.

Reads data/stats.json, POSTs to http://127.0.0.1:11434/api/generate with
llama3.2:3b, saves the result to data/brief.txt.

Never crashes the pipeline: if Ollama is down or the model errors, falls
back to a templated text brief so the report still renders.
"""

import json
import os
import sys
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
STATS_PATH = os.path.join(HERE, "data", "stats.json")
BRIEF_PATH = os.path.join(HERE, "data", "brief.txt")
OLLAMA_URL = os.environ.get("BOLSABUDDY_OLLAMA_URL", "http://127.0.0.1:11434/api/generate")
MODEL = "llama3.2:3b"


def describe_stats(s):
    streak = s["streak_days"]
    streak_txt = (f"up {streak} days in a row" if streak > 0
                  else f"down {abs(streak)} days in a row" if streak < 0
                  else "flat")
    lines = [
        f"The Mexican IPC index closed at {s['latest_close']:,} on {s['latest_date']}, "
        f"{s['day_change_pct']:+.2f}% on the day.",
        f"It is {streak_txt}.",
        f"It sits {s['drawdown_from_52w_pct']:.2f}% below its 52-week high of {s['high_52w']:,}.",
    ]
    for key, label in (("ma20", "20-day"), ("ma50", "50-day"), ("ma200", "200-day")):
        if s.get(key):
            pos = "above" if s["latest_close"] > s[key] else "below"
            lines.append(f"Close is {pos} the {label} moving average ({s[key]:,}).")
    if s.get("all_time_high"):
        lines.append("That is a new all-time high.")
    return " ".join(lines)


def fallback_brief(stats):
    core = describe_stats(stats)
    return (f"IPC daily brief ({stats['latest_date']}) — auto-generated without the AI model:\n\n"
            f"{core}\n\n"
            f"No investment advice. Data: Yahoo Finance free daily feed (^MXX).")


def ai_brief(stats):
    facts = describe_stats(stats)
    prompt = (
        "You write a short daily market brief for a casual investor watching the "
        "Mexican stock market (IPC index). Write 5-8 sentences, plain English, "
        "casual tone, no jargon, no emojis. Do not give investment advice. "
        "Just describe what happened and what the numbers suggest about momentum.\n\n"
        f"Facts: {facts}\n\nBrief:"
    )
    payload = json.dumps({
        "model": MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.6, "num_predict": 220},
    }).encode()
    req = urllib.request.Request(OLLAMA_URL, data=payload,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=180) as resp:
        data = json.loads(resp.read().decode())
    text = data.get("response", "").strip()
    if not text:
        raise RuntimeError("empty response from model")
    return text


def main():
    if not os.path.exists(STATS_PATH):
        print("brief: data/stats.json missing — run analyze.py first", file=sys.stderr)
        return 2
    with open(STATS_PATH) as f:
        stats = json.load(f)
    try:
        text = ai_brief(stats)
        source = f"local {MODEL}"
    except Exception as exc:
        text = fallback_brief(stats)
        source = f"fallback template (Ollama unavailable: {exc})"
    with open(BRIEF_PATH, "w") as f:
        f.write(text + "\n")
    print(f"brief: wrote data/brief.txt via {source}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
