#!/usr/bin/env python3
"""test_smoke.py — end-to-end smoke test on cached data (no network, no Ollama needed).

Runs analyze -> brief (fallback path forced) -> report and checks the
artifacts exist and look sane. Exit 0 = pipeline healthy.
"""

import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def run(script, *args, env_extra=None):
    env = dict(os.environ)
    if env_extra:
        env.update(env_extra)
    r = subprocess.run([sys.executable, os.path.join(HERE, script), *args],
                       capture_output=True, text=True, env=env, timeout=120)
    return r


def main():
    failures = []

    csv_path = os.path.join(HERE, "data", "ipc.csv")
    if not os.path.exists(csv_path):
        print("SMOKE FAIL: data/ipc.csv missing — run fetch.py once with network first")
        return 1

    r = run("analyze.py")
    print(r.stdout.strip())
    if r.returncode != 0:
        failures.append(f"analyze.py exited {r.returncode}: {r.stderr.strip()}")
    else:
        stats = json.load(open(os.path.join(HERE, "data", "stats.json")))
        for key in ("latest_close", "day_change_pct", "ma20", "drawdown_from_52w_pct"):
            if key not in stats:
                failures.append(f"stats.json missing key {key}")

    # Force the fallback path: point brief.py at a dead Ollama port.
    import brief as _  # noqa: F401  (ensures module imports cleanly)
    r = run("brief.py", env_extra={"BOLSABUDDY_OLLAMA_URL": "http://127.0.0.1:1"})
    print(r.stdout.strip())
    if r.returncode != 0:
        failures.append(f"brief.py exited {r.returncode}: {r.stderr.strip()}")
    elif not os.path.exists(os.path.join(HERE, "data", "brief.txt")):
        failures.append("brief.txt not written")

    r = run("report.py")
    print(r.stdout.strip())
    if r.returncode != 0:
        failures.append(f"report.py exited {r.returncode}: {r.stderr.strip()}")
    else:
        html = open(os.path.join(HERE, "report.html")).read()
        for needle in ("<svg", "Daily brief", "Watchlist", "Yahoo Finance"):
            if needle not in html:
                failures.append(f"report.html missing {needle!r}")

    # watchlist round-trip
    for args in (["add", "SMOKETEST", "smoke thesis", "smoke trigger"],
                 ["list"], ["check"], ["remove", "SMOKETEST"]):
        r = run("watchlist.py", *args)
        if r.returncode != 0:
            failures.append(f"watchlist.py {' '.join(args)} exited {r.returncode}")

    if failures:
        print("SMOKE FAIL:")
        for f in failures:
            print(" -", f)
        return 1
    print("SMOKE OK: pipeline healthy on cached data")
    return 0


if __name__ == "__main__":
    sys.exit(main())
