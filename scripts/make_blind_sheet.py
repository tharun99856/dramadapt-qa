#!/usr/bin/env python3
"""Build the blind annotation sheet for Phase 0 Step B.

    python scripts/make_blind_sheet.py

Rows come out in the randomized blind order (data/annotation/blind_order.json). The sheet
contains no DramAdapt output of any kind, because the annotation has to happen before the
reviewer ever sees a flag. Re-running keeps any verdicts you already typed.
"""

from __future__ import annotations

import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.sample import ANNOTATION_CSV, TELUGU_JSON, load_sample  # noqa: E402
from src.console import force_utf8  # noqa: E402

COLUMNS = [
    "anon_id", "line_id", "episode", "speaker", "delivery", "slot_seconds",
    "english", "telugu", "verdict", "error_types", "severity", "corrected_line", "reviewer_confidence",
]

HEADERS = [
    "# Phase 0 blind annotation sheet",
    "#",
    "# Fill in: verdict, error_types, severity, corrected_line, reviewer_confidence.",
    "# verdict      : acceptable | needs_revision",
    "# error_types  : any of meaning;relationship;timing;naturalness;script (semicolon separated, blank if acceptable)",
    "# severity     : high | medium | low  (high = would wreck the scene if dubbed as it is)",
    "# corrected    : your own Telugu line for that slot, not the machine's",
    "# confidence   : high | medium | low  (how sure you are about your own judgement)",
    "#",
    "# Do NOT open results/structured_flags.json or results/baseline_flags.json before you finish this file.",
    "# Judge the Telugu against the English and the slot. A line that is merely 'not how you would write it'",
    "# but would play fine on screen is acceptable.",
    "#",
]


def main() -> int:
    force_utf8()
    force_utf8()
    telugu_path = Path(sys.argv[1]) if len(sys.argv) > 1 else TELUGU_JSON
    lines, meta = load_sample(telugu_path)
    if not any(rec.telugu for rec in lines):
        print("No Telugu attached. Run scripts/run_first_pass.py first, or pass a first-pass file.", file=sys.stderr)
        return 1

    order_path = ROOT / "data" / "annotation" / "blind_order.json"
    order = json.loads(order_path.read_text(encoding="utf-8")) if order_path.exists() else None
    if order:
        anon = order["anon"]
        seq = order["order"]
    else:
        anon = {rec.line_id: f"A{i + 1:03d}" for i, rec in enumerate(lines)}
        seq = [rec.line_id for rec in lines]

    existing: dict[str, dict] = {}
    if ANNOTATION_CSV.exists():
        with ANNOTATION_CSV.open(encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                existing[row.get("line_id", "")] = row

    by_id = {rec.line_id: rec for rec in lines}
    missing = [lid for lid in seq if lid not in by_id]
    extra = [lid for lid in by_id if lid not in seq]

    with ANNOTATION_CSV.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=COLUMNS)
        writer.writeheader()
        for line_id in seq + extra:
            rec = by_id.get(line_id)
            if rec is None:
                continue
            prev = existing.get(line_id, {})
            writer.writerow({
                "anon_id": anon.get(line_id, f"A{seq.index(line_id) + 1:03d}"),
                "line_id": line_id,
                "episode": rec.episode,
                "speaker": rec.canonical_speaker,
                "delivery": rec.delivery_tag,
                "slot_seconds": rec.tight_window,
                "english": rec.text,
                "telugu": rec.telugu,
                "verdict": prev.get("verdict", ""),
                "error_types": prev.get("error_types", ""),
                "severity": prev.get("severity", ""),
                "corrected_line": prev.get("corrected_line", ""),
                "reviewer_confidence": prev.get("reviewer_confidence", ""),
            })

    filled = sum(1 for row in existing.values() if (row.get("verdict") or "").strip())
    stamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    (ROOT / "data" / "annotation" / "blind_annotation_README.md").write_text(
        "\n".join(HEADERS)
        + f"\n# generated: {stamp}\n# sample seed: {meta.get('seed')}\n"
        + f"# telugu file: {meta.get('telugu_file')}\n"
        + f"# telugu provenance: {json.dumps(meta.get('telugu_provenance'), ensure_ascii=False)}\n"
        + f"# lines: {len(by_id)} | already filled when this sheet was rebuilt: {filled}\n",
        encoding="utf-8",
    )
    print(f"wrote {ANNOTATION_CSV.relative_to(ROOT)}: {len(by_id)} rows in blind order")
    if filled:
        print(f"  kept {filled} rows you had already annotated")
    if missing:
        print(f"  WARNING: {len(missing)} blind-order ids are not in the sample: {missing[:5]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
