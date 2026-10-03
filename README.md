# BolsaBuddy

A $0, fully-local tracker for the Mexican stock market (IPC index). Built for a friend who wanted an investing tool for the BMV — no paid data feeds, no cloud AI, nothing leaves the laptop.

## What it does

- **Fetches** free daily IPC prices (Yahoo Finance ^MXX, history back to 1991)
- **Analyzes** momentum: day change, 20/50/200-day averages, drawdown from 52-week high, streaks, all-time highs
- **Briefs** you in plain English via a local open-weight model (Ollama) — or a templated brief if the model is down
- **Surfaces** the latest BMV headlines (Google News RSS, free, no key)
- **Watches** your tickers against your own thesis and kill-triggers
- **Renders** a phone-readable daily page (`report.html`)

## Run it

```bash
python3 fetch.py      # download latest IPC data (uses cache offline)
python3 analyze.py    # -> data/stats.json
python3 brief.py      # -> data/brief.txt (local Ollama, falls back gracefully)
python3 news.py       # -> data/news.json (latest BMV headlines)
python3 report.py     # -> report.html
```

The AI brief needs Ollama running with an open-weight model
(e.g. `ollama serve`, model `llama3.2:3b`). If Ollama is down, `brief.py`
writes a templated brief instead — the pipeline never breaks.

Or the whole pipeline: `python3 fetch.py && python3 analyze.py && python3 brief.py && python3 report.py`

Smoke test (no network, no Ollama needed — uses cached data):

```bash
python3 test_smoke.py
```

Watchlist (theses + live prices, free Yahoo quotes, no key):

```bash
python3 watchlist.py add CEMEXCPO.MX "cement demand recovering" "breaks below 200-day avg"
python3 watchlist.py list
python3 watchlist.py check    # live price + day change next to each thesis
python3 watchlist.py remove CEMEXCPO.MX
```

## Why local

A closed AI API would charge per brief forever and send your watchlist and theses to someone else's server. The local model costs nothing, works offline, and keeps your financial thinking private. That's the whole point.

## Data sources

- IPC daily OHLC: Yahoo Finance chart API (`^MXX`, no key), https://query1.finance.yahoo.com/v8/finance/chart/%5EMXX

Not investment advice. For learning and tracking only.

## License

MIT
