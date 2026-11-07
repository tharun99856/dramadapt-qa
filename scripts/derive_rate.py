#!/usr/bin/env python3
"""Derive a speaking rate from the files already in the repo - and say loudly that it is derived.

    python scripts/derive_rate.py

This is NOT the calibration PRD section 6 Step D asks for. That one is `scripts/calibrate_rate.py`:
ten lines read aloud, timed by hand, in data/calibration_readings.csv, and only the reviewer can
produce it. What this script can do is bound the plausible range while those ten cells are empty:
the rate a voice artist must hold to fit a given Telugu text into a given slot is akshara / slot,
and the reviewer's own corrected lines are accepted text. So their median required rate is the
fastest honest interim - and it is circular in one specific way worth naming: setting the rate from
corrected lines makes those lines fit by construction, so it can judge the draft, never the
reviewer's own text.

Writes data/calibration_derived.json. src/config.py does not read that file, and must not:
data/calibration.json is the hand-measured one, and this script never writes it.
"""

from __future__ import annotations

import csv
import json
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from collections import Counter  # noqa: E402
from src.checks.timing import run as timing_run  # noqa: E402
from src.console import force_utf8  # noqa: E402
from src.pipeline import sample_lines  # noqa: E402
from src.telugu import akshara_count  # noqa: E402

ANNOTATION = ROOT / "data" / "annotation" / "blind_annotation.csv"
READINGS = ROOT / "data" / "calibration_readings.csv"
OUT = ROOT / "data" / "calibration_derived.json"


def margin() -> float:
    import yaml
    cfg = yaml.safe_load((ROOT / "config.yaml").read_text(encoding="utf-8")) or {}
    return float((cfg.get("telugu") or {}).get("over_tight_margin", 0.15))


def seconds(value: str) -> float | None:
    try:
        n = float(value)
    except (TypeError, ValueError):
        return None
    return n if n > 0 else None


def required_rate(text: str, slot: float | None) -> tuple[int, float] | None:
    """(akshara, slot) for a line short enough to measure a rate from; under 3 akshara a line is a
    breath, not a measurement, and dividing it by a slot invents a number."""
    if not slot:
        return None
    n = akshara_count(text or "")
    return (n, slot) if n >= 3 else None


def describe(pairs: list[tuple[int, float]]) -> dict:
    v = sorted(n / slot for n, slot in pairs)
    if not v:
        return {"n": 0}
    q = statistics.quantiles(v, n=4, method="inclusive") if len(v) >= 2 else [v[0], v[0], v[0]]
    return {
        "n": len(v),
        "median": round(statistics.median(v), 2),
        "q1": round(q[0], 2),
        "q3": round(q[2], 2),
        "p90": round(v[int(0.9 * (len(v) - 1))], 2),
        "max": round(v[-1], 2),
    }


def flag_list(lines, rate: float, margin: float) -> dict:
    """The real check, not a reimplementation: src/checks/timing.run at one assumed rate."""
    flags, _table, summary = timing_run(lines, rate, margin=margin)
    return {"flags": len(flags),
            "lines_flagged": len({f["line_id"] for f in flags}),
            "lines_checked": summary["lines_checked"],
            **dict(Counter(f["verdict"] for f in flags))}


def main() -> None:
    force_utf8()
    with ANNOTATION.open(encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))

    corrected, draft = [], []
    for row in rows:
        slot = seconds(row.get("slot_seconds"))
        for key, bucket in (("corrected_line", corrected), ("telugu", draft)):
            rate = required_rate(row.get(key), slot)
            if rate:
                bucket.append(rate)

    measured = []
    if READINGS.exists():
        with READINGS.open(encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                # Here the denominator is the reviewer's own stopwatch, not a slot - this is the only
                # line of this script that can produce a measured rate instead of a derived one.
                timing = seconds(row.get("seconds_read_aloud"))
                pair = required_rate(row.get("telugu"), timing)
                if pair:
                    measured.append(pair)

    print("Rate per second of speech (akshara/s):")
    print(f"  DERIVED, reviewer's corrected lines vs their slot : {describe(corrected)}")
    print(f"  DERIVED, the draft vs its slot                    : {describe(draft)}")
    print(f"  MEASURED, hand-timed readings                     : {describe(measured) if measured else 'none yet'}")
    print()
    lines, _meta = sample_lines(ROOT / "data" / "telugu" / "first_pass.json")
    sweep = {f"{rate}": flag_list(lines, rate, margin()) for rate in (3.0, 3.5, 4.0, 5.0, 6.0, 6.5, 7.0)}
    print("What the assumed rate does to the flag list (the real check, so both windows count):")
    for rate, stats in sweep.items():
        print(f"  at {rate}: {stats['flags']:3d} flags over {stats['lines_flagged']:3d} of "
              f"{stats['lines_checked']} lines checked "
              f"(over_slot {stats.get('over_slot', 0)}, overlaps_next_line "
              f"{stats.get('overlaps_next_line', 0)}, chain {stats.get('chain_over_slot', 0)})")

    interim = statistics.median([n / slot for n, slot in corrected]) if corrected else None
    OUT.write_text(json.dumps({
        "provenance": "DERIVED from data/annotation/blind_annotation.csv, not measured from a speaker",
        "not_the_same_as": "data/calibration.json (hand-timed readings; does not exist yet)",
        "circularity": "a rate derived from the reviewer's corrected lines makes those lines fit by "
                       "construction; it may judge the draft, not the corrections",
        "required_rate_corrected_lines": describe(corrected),
        "required_rate_draft": describe(draft),
        "measured_rate_hand_timed": describe(measured) if measured else None,
        "hand_timed_readings_filled": len(measured),
        "interim_rate_akshara_per_second": round(interim, 2) if interim else None,
        "rate_sweep": sweep,
    }, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nwrote {OUT.relative_to(ROOT)} - interim {interim and round(interim, 2)} akshara/s, DERIVED, "
          f"{len(measured)} hand-timed readings")


if __name__ == "__main__":
    main()
