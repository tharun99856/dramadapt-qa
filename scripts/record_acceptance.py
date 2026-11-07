#!/usr/bin/env python3
"""Record a batch of the reviewer's own acceptance decisions into data/annotation/decisions.csv.

    python scripts/record_acceptance.py data/annotation/acceptance_batches/2026-11-07_relationship_batch1.tsv

The batch file is a TSV: flag_id, status, edited_suggestion, reason. Status is the reviewer's word -
accept, modify or dismiss - which maps onto the UI's approved / edited / dismissed. The reason column
is not written to the decisions file, because it has no column there; it stays in the batch file, so
the reviewer's reasoning is in the repo next to the verdict it produced.

Everything in that CSV comes from a batch file like this one or from the UI. Nothing here decides
whether a flag is real: a status derived from scores.json is the scorer's own verdict relabelled as
the metric PRD section 9 uses to drop a check, and that is failure log entry 27.
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

from src.console import force_utf8  # noqa: E402
from src.report import DECISIONS, FLAG_COLUMNS, load_decisions, with_ids  # noqa: E402

STATUSES = {"accept": "approved", "approved": "approved",
            "modify": "edited", "edited": "edited",
            "dismiss": "dismissed", "dismissed": "dismissed"}


def read_batch(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh, delimiter="\t"))
    if not rows:
        sys.exit(f"{path} has no data rows")
    for row in rows:
        if not row.get("flag_id"):
            sys.exit(f"{path} has a row with no flag_id")
        if (row.get("status") or "").strip().lower() not in STATUSES:
            sys.exit(f"{path}: flag {row['flag_id']} has status {row.get('status')!r}, "
                     "expected accept / modify / dismiss")
    return rows


def main() -> int:
    force_utf8()
    ap = argparse.ArgumentParser()
    ap.add_argument("batch", type=Path)
    ap.add_argument("--flags", default=str(ROOT / "results" / "structured_flags.json"))
    args = ap.parse_args()

    batch = read_batch(args.batch)
    payload = json.loads(Path(args.flags).read_text(encoding="utf-8"))
    by_id = {f["flag_id"]: f for f in with_ids(payload["flags"])}
    existing = load_decisions()

    already = [r["flag_id"] for r in batch
               if (existing.get(r["flag_id"]) or {}).get("status") not in (None, "", "pending")]
    if already:
        sys.exit(f"these flags already carry a decision, so this batch would overwrite history: "
                 f"{', '.join(already)}")

    unknown = [r["flag_id"] for r in batch if r["flag_id"] not in by_id]
    if unknown:
        sys.exit(f"no such flag in {Path(args.flags).name}: {', '.join(unknown)}")

    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    rows = {flag_id: row for flag_id, row in existing.items()}

    written = []
    for entry in batch:
        flag = by_id[entry["flag_id"]]
        status = STATUSES[entry["status"].strip().lower()]
        edited = (entry.get("edited_suggestion") or "").strip()
        if status == "edited" and not edited:
            sys.exit(f"{flag['flag_id']} is marked modify but the batch carries no replacement text")
        if status != "edited" and edited:
            sys.exit(f"{flag['flag_id']} is marked {status} but the batch carries replacement text")
        row = {col: flag.get(col, "") for col in FLAG_COLUMNS}
        row.update({
            "flag_id": flag["flag_id"],
            "line_id": flag["line_id"],
            "check": flag["check"],
            "severity": flag["severity"],
            "verdict": flag["verdict"],
            "english": flag.get("english", ""),
            "telugu": flag.get("telugu", ""),
            "slot_seconds": flag.get("slot_seconds", ""),
            "evidence": flag.get("evidence", ""),
            "suggestion": flag.get("suggestion", ""),
            "note": flag.get("note", ""),
            "status": status,
            "edited_suggestion": edited,
            "editor_action_ts": now,
        })
        rows[flag["flag_id"]] = row
        written.append(row)

    DECISIONS.parent.mkdir(parents=True, exist_ok=True)
    with DECISIONS.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=FLAG_COLUMNS)
        writer.writeheader()
        for key in sorted(rows):
            writer.writerow({col: rows[key].get(col, "") for col in FLAG_COLUMNS})

    tally = {s: sum(1 for r in written if r["status"] == s) for s in ("approved", "edited", "dismissed")}
    print(f"recorded {len(written)} decisions from {args.batch.name}: "
          f"{tally['approved']} approved, {tally['edited']} edited, {tally['dismissed']} dismissed")
    for row in written:
        shown = row["edited_suggestion"] if row["status"] == "edited" else (
            row["suggestion"] if row["status"] == "approved" else "")
        print(f"  {row['status']:<10} {row['flag_id']}" + (f"  -> {shown}" if shown else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
