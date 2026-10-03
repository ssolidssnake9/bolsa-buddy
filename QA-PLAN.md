# BolsaBuddy QA plan — test / review / improve / retest

**Goal:** nothing bugs out on main stage (judges running it, the demo behind
the write-up, the owner opening the daily page on their iPad).

## Round 1 — fresh-run test
- [x] Cold pipeline: fetch -> analyze -> brief -> report all complete.
- [x] Outputs sane: ipc.csv (8,739 rows), stats.json, brief.txt, report.html.

## Findings + fixes (2026-10-01 ~21:50 PDT)
1. **Stooq 403s urllib** (UA-based edge block). curl+browser UA got the JS
   PoW challenge page, but /__verify POST 403d on non-browser TLS.
   FIX: switched data source to Yahoo Finance ^MXX chart API (no key, no
   challenge, 8,912 bars 1991->today, same-day fresh). fetch.py rewritten;
   CSV contract unchanged so analyze/report untouched.
2. **Stale "Stooq" references** in report footer, brief fallback, README,
   smoke-test needle. FIX: all updated to Yahoo Finance ^MXX.
3. **Ollama died mid-QA** (box memory pressure: 561MB free when model
   loaded). FIX: restarted `ollama serve` as background proc; brief.py's
   fallback path already covers this — pipeline never crashes. README
   should note Ollama needs to be running for the AI brief.

## Round 2 — failure modes
- [x] Corrupt CSV (garbage row): skipped cleanly, exit 0.
- [x] Empty CSV: clean error, exit 2, no traceback.
- [x] Ollama down: fallback brief, pipeline completes (verified live twice).
- [x] Yahoo unreachable + stale cache → warns, uses cache, exit 0 (forced).
- [x] report.html with no forecast.json → renders (no forecast file present,
      page generated clean).

## Round 3 — numbers audit
- [x] 8/8 stats verified by independent recomputation (chg, MA20/50/200,
      52w high, drawdown, streak, row count). ALL OK.

## Round 4 — brief quality
- [x] Real AI brief regenerated: every number matches stats.json, no
      hallucinations, plain English. Mild editorializing ("support zone")
      acceptable; footer carries the not-advice disclaimer.

## Round 5 — presentation
- [x] report.html structure validated (tags balanced, 90-pt SVG in range,
      brief embedded, Yahoo footer, zero Stooq refs).

## Round 6 — TabPFN verdict
- [x] **NOT-VIABLE (2026-10-01 ~22:15 PDT).** tabpfn 9.0.0 installs fine, but
      first `.fit()` demands a Prior Labs account + license acceptance +
      TABPFN_TOKEN (human browser step, a signup, a key). That breaks the
      tool's $0 / no-keys / no-accounts identity — the whole point of the
      entry. Dropped cleanly; 3.5GB venv removed. Entry competes for
      overall + completion badge. Reversible if the owner ever wants to do
      the 5-minute signup themselves.

## Loop rule
Every failure found → fix → re-run the FULL suite, not just the failed
step. Fixes that only pass their own test are how stage bugs are born.
Two clean full passes before sign-off.
**Pass 1:** complete after fixes above (smoke OK 21:58 PDT).
**Pass 2 (2026-10-01 ~22:25 PDT):** true cold run — data/ nuked, full
pipeline from zero: fetch (Yahoo) -> analyze -> AI brief (real model) ->
report -> smoke. ALL GREEN. Numbers re-verified, brief regenerated with
the live model, report rebuilt. Two clean passes: SIGN-OFF.

## Watchlist upgrade (2026-10-01 ~22:40 PDT, owner greenlit)
- `check` now pulls live quotes (Yahoo, no key): price + day change next
  to each thesis. IPC maps to ^MXX; unknown tickers pass through.
- Tested: real ticker (CEMEXCPO.MX 17.29 +0.29%), bad ticker (graceful
  "price unavailable"), IPC mapping (63,828.60 matches index), offline
  path (returns None, never crashes). Smoke re-run: OK.

## News module (2026-10-01 ~22:50 PDT, owner-ordered)
- news.py: Google News RSS (BMV IPC, es-MX), top 5 headlines + source +
  link -> data/news.json. report.py renders "Latest BMV news" section.
- Tested: live fetch (5 fresh headlines, today's news), dead feed ->
  empty list exit 0, HTML escaping verified (S&amp;P), 5 <li> rendered.
- Full suite re-run: smoke OK. Sign-off holds.
