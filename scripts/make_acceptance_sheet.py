#!/usr/bin/env python3
"""Build the reviewer acceptance sheet for the flags DramAdapt actually produced.

    python scripts/make_acceptance_sheet.py

Writes data/annotation/decisions.csv, one row per flag. Fill status with
approved / edited / dismissed and, for edited, put your own wording in edited_suggestion.
This sheet is the acceptance-rate metric (PRD §9): it asks whether a flag was useful, not
merely whether it fired. Rows you already filled survive a rebuild.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.report import DECISIONS, FLAG_COLUMNS, with_ids  # noqa: E402
from src.sample import load_sample  # noqa: E402
from src.console import force_utf8  # noqa: E402

STATUSES = ("pending", "approved", "edited", "dismissed")


def main() -> int:
    force_utf8()
    ap = argparse.ArgumentParser()
    ap.add_argument("--flags", default=str(ROOT / "results" / "structured_flags.json"))
    args = ap.parse_args()

    path = Path(args.flags)
    if not path.exists():
        print(f"{path} missing - run scripts/run_structured.py first", file=sys.stderr)
        return 1
    payload = json.loads(path.read_text(encoding="utf-8"))
    flags = with_ids(payload.get("flags", []))
    if not flags:
        print("that run produced no flags, so there is nothing to review")
        return 0

    lines, _ = load_sample()
    by_id = {rec.line_id: rec for rec in lines}

    existing: dict[str, dict] = {}
    if DECISIONS.exists():
        with DECISIONS.open(encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                if row.get("flag_id"):
                    existing[row["flag_id"]] = row

    DECISIONS.parent.mkdir(parents=True, exist_ok=True)
    with DECISIONS.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=FLAG_COLUMNS)
        writer.writeheader()
        for flag in flags:
            rec = by_id.get(flag["line_id"])
            prev = existing.get(flag["flag_id"], {})
            writer.writerow({
                "flag_id": flag["flag_id"],
                "line_id": flag["line_id"],
                "episode": getattr(rec, "episode", ""),
                "speaker": getattr(rec, "canonical_speaker", ""),
                "check": flag["check"],
                "severity": flag["severity"],
                "verdict": flag["verdict"],
                "english": getattr(rec, "text", ""),
                "telugu": getattr(rec, "telugu", ""),
                "slot_seconds": getattr(rec, "tight_window", ""),
                "evidence": flag["evidence"],
                "suggestion": flag.get("suggestion", ""),
                "note": flag.get("note", ""),
                "status": prev.get("status", "pending"),
                "edited_suggestion": prev.get("edited_suggestion", ""),
                "editor_action_ts": prev.get("editor_action_ts", ""),
            })

    kept = sum(1 for row in existing.values() if (row.get("status") or "pending") != "pending")
    print(f"wrote {DECISIONS.relative_to(ROOT)}: {len(flags)} flags, {kept} already decided")
    print(f"statuses allowed: {', '.join(STATUSES)}")
    print("then re-run: python scripts/score.py")
    print(json.dumps({"generated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                      "flags_file": path.name, "flags": len(flags)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
