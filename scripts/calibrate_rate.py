#!/usr/bin/env python3
"""Calibrate the Telugu speaking rate by timing yourself reading lines aloud.

    python scripts/calibrate_rate.py --template   # write data/calibration_readings.csv
    python scripts/calibrate_rate.py              # turn those readings into a rate

The timing check refuses to run until this exists, because an uncalibrated rate is a guess.
"""

from __future__ import annotations

import argparse
import csv
import json
import statistics as st
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.sample import load_sample  # noqa: E402
from src.telugu import akshara_count  # noqa: E402
from src.console import force_utf8  # noqa: E402

READINGS = ROOT / "data" / "calibration_readings.csv"
OUT = ROOT / "data" / "calibration.json"


def pick_template(n: int = 10) -> list:
    """Ten lines that actually differ: short slot, long slot, one chain, one voice-over."""
    lines, _ = load_sample()
    with_telugu = [rec for rec in lines if rec.telugu]
    pool = with_telugu or lines
    chosen: list = []
    seen_akshara = set()
    ordered = sorted(pool, key=lambda r: r.tight_window)
    steps = [0, len(ordered) - 1] + [int(i * (len(ordered) - 1) / (n - 1)) for i in range(1, n - 1)]
    for idx in steps:
        rec = ordered[min(max(idx, 0), len(ordered) - 1)]
        if rec.line_id not in seen_akshara:
            seen_akshara.add(rec.line_id)
            chosen.append(rec)
        if len(chosen) >= n:
            break
    vo = [rec for rec in pool if (rec.voice_over or rec.off_screen) and rec.line_id not in seen_akshara]
    if vo and len(chosen) < n + 2:
        chosen.append(vo[0])
    chains = [rec for rec in pool if rec.chain_id and rec.line_id not in seen_akshara]
    if chains and len(chosen) < n + 3:
        chosen.append(chains[0])
    return chosen[: max(n, len(chosen))]


def main() -> int:
    force_utf8()
    ap = argparse.ArgumentParser()
    ap.add_argument("--template", action="store_true")
    ap.add_argument("--telugu-file", default=None)
    args = ap.parse_args()

    if args.template:
        chosen = pick_template(10)
        if not chosen:
            print("no sample lines yet - run scripts/select_sample.py", file=sys.stderr)
            return 1
        with READINGS.open("w", newline="", encoding="utf-8") as fh:
            writer = csv.writer(fh)
            writer.writerow(["line_id", "telugu", "seconds_read_aloud", "notes"])
            for rec in chosen:
                writer.writerow([rec.line_id, rec.telugu or rec.text, "", "read at the show's delivery pace"])
        print(f"wrote {READINGS.relative_to(ROOT)} with {len(chosen)} lines.")
        print("Read each Telugu line aloud at the pace the show uses, time it, put the seconds in column 3,")
        print("then run: python scripts/calibrate_rate.py")
        return 0

    if not READINGS.exists():
        print("no readings file - run: python scripts/calibrate_rate.py --template", file=sys.stderr)
        return 1

    rates = []
    rows_used = []
    rows_skipped = []
    with READINGS.open(encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            seconds = float(row.get("seconds_read_aloud") or 0)
            text = (row.get("telugu") or "").strip()
            if seconds <= 0 or not text:
                rows_skipped.append(row.get("line_id", "?"))
                continue
            akshara = akshara_count(text)
            if akshara <= 0:
                rows_skipped.append(f"{row.get('line_id')}(no Telugu letters)")
                continue
            rates.append(akshara / seconds)
            rows_used.append({"line_id": row.get("line_id"), "akshara": akshara, "seconds": seconds,
                              "rate": round(akshara / seconds, 3)})

    if not rates:
        print("no usable readings - fill in seconds_read_aloud and re-run", file=sys.stderr)
        return 1

    payload = {
        "telugu_syllables_per_second": round(st.median(rates), 3),
        "n_readings": len(rates),
        "min": round(min(rates), 3),
        "max": round(max(rates), 3),
        "mean": round(st.mean(rates), 3),
        "readings": rows_used,
        "skipped": rows_skipped,
        "method": "median of akshara count divided by hand-timed reading, one reviewer",
        "caveat": "one reviewer, ten lines, read not performed; treat the timing flag as risk, not failure",
        "generated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    OUT.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"calibrated rate: {payload['telugu_syllables_per_second']} akshara/s "
          f"from {payload['n_readings']} readings (range {payload['min']}-{payload['max']})")
    print(f"wrote {OUT.relative_to(ROOT)}")
    if rows_skipped:
        print(f"skipped: {rows_skipped}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
