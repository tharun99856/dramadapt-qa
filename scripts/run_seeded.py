#!/usr/bin/env python3
"""Phase 0 Step E: inject 10 known errors into a copy of the Telugu first pass.

    python scripts/run_seeded.py

Writes data/telugu/first_pass_seeded.json plus results/seeded_manifest.json, which lists
every edit before and after. Run the checks on the seeded file with:

    python scripts/run_structured.py --telugu-file data/telugu/first_pass_seeded.json --label structured_seeded

Seeded errors are blunter than real ones. They are reported by type only and never mixed
into the main precision/recall numbers.
"""

from __future__ import annotations

import argparse
import json
import random
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.checks.relationship import best_row  # noqa: E402
from src.corpus import categories_for  # noqa: E402
from src.pipeline import sample_lines, write_payload  # noqa: E402
from src.telugu import akshara_count, script_name  # noqa: E402
from src.console import force_utf8  # noqa: E402

OPS = [
    ("negation", "meaning", "threat_or_accusation"),
    ("honorific_downgrade", "relationship", "address_shift"),
    ("untranslated_left", "meaning", None),
    ("slot_padding", "timing", "short_slot"),
    ("address_swap", "relationship", "tender_or_intimate"),
]


def apply_op(op: str, rec, telugu: str, cfg: dict, used_prefixes: list[str]) -> str | None:
    if op == "negation":
        tail = cfg["negation"]["tail"]
        return None if tail.strip() in telugu else telugu.rstrip() + tail
    if op == "honorific_downgrade":
        for find, replace in cfg["honorific_downgrade"]["patterns"]:
            if find in telugu:
                return telugu.replace(find, replace, 1)
        return None
    if op == "untranslated_left":
        return None if telugu.strip() == rec.text.strip() else rec.text.strip()
    if op == "slot_padding":
        tail = cfg["slot_padding"]["tail"]
        return None if tail.strip() in telugu else telugu.rstrip() + tail
    if op == "address_swap":
        for prefix in cfg["address_swap"]["prefixes"]:
            if prefix.strip(" ,") in telugu or prefix in used_prefixes:
                continue
            row = best_row(rec)
            expected = " ".join(row.get("expected_address_terms", []) or []).lower() if row else ""
            if prefix.strip(" ,").lower() in expected:
                continue
            used_prefixes.append(prefix)
            return prefix + telugu.lstrip()
        return None
    raise ValueError(f"unknown seed op {op}")


def main() -> int:
    force_utf8()
    ap = argparse.ArgumentParser()
    ap.add_argument("--telugu-file", default=None)
    ap.add_argument("--seed", type=int, default=20261106)
    ap.add_argument("--out", default=str(ROOT / "data" / "telugu" / "first_pass_seeded.json"))
    args = ap.parse_args()

    cfg_ops = yaml.safe_load((ROOT / "data" / "seed_ops.yaml").read_text(encoding="utf-8"))
    counts = cfg_ops["counts"]
    lines, meta = sample_lines(args.telugu_file)
    if not any(rec.telugu for rec in lines):
        print("no Telugu attached - run scripts/run_first_pass.py first", file=sys.stderr)
        return 1

    rng = random.Random(args.seed)
    telugu_by_id = {rec.line_id: rec.telugu for rec in lines}
    tags = {rec.line_id: categories_for(rec) for rec in lines}
    edits: list[dict] = []
    used: set[str] = set()
    used_prefixes: list[str] = []
    unseedable: list[dict] = []

    for op, expected_check, prefer in OPS:
        need = int(counts.get(op, 0))
        pool = [rec for rec in lines if rec.line_id not in used and rec.telugu.strip()]
        preferred = [rec for rec in pool if prefer and prefer in tags[rec.line_id]]
        candidates = (preferred or pool)[:]
        rng.shuffle(candidates)
        made = 0
        for rec in candidates:
            if made >= need:
                break
            before = telugu_by_id[rec.line_id]
            after = apply_op(op, rec, before, cfg_ops, used_prefixes)
            if not after or after == before:
                continue
            edits.append({
                "op": op,
                "line_id": rec.line_id,
                "expected_check": expected_check,
                "before": before,
                "after": after,
                "english": rec.text,
                "slot_seconds": rec.tight_window,
                "akshara_before": akshara_count(before),
                "akshara_after": akshara_count(after),
                "categories": sorted(tags[rec.line_id]),
            })
            telugu_by_id[rec.line_id] = after
            used.add(rec.line_id)
            made += 1
        if made < need:
            unseedable.append({"op": op, "wanted": need, "made": made,
                               "reason": "no candidate line contained a fragment this op could change"})

    rows = [
        {
            "line_id": rec.line_id,
            "telugu": telugu_by_id[rec.line_id],
            "script_detected": script_name(telugu_by_id[rec.line_id]),
            "is_telugu": bool(akshara_count(telugu_by_id[rec.line_id])),
            "english": rec.text,
            "slot_seconds": rec.tight_window,
            "seeded": rec.line_id in used,
        }
        for rec in lines
    ]
    payload = {
        "provenance": {
            "method": "seeded_copy",
            "base_file": meta.get("telugu_file"),
            "base_provenance": meta.get("telugu_provenance"),
            "seed": args.seed,
            "ops_file": "data/seed_ops.yaml",
            "generated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "measured": False,
            "note": "known errors injected into a copy; blunter than real localization errors",
        },
        "lines": rows,
        "errors": [],
        "coverage": {"requested": len(lines), "returned": len(rows), "seeded_lines": len(used)},
        "run_log": {"requests_total": 0, "note": "no model call; edits are mechanical"},
    }
    out_path = write_payload(payload, Path(args.out))

    by_type: dict[str, int] = {}
    for e in edits:
        by_type[e["op"]] = by_type.get(e["op"], 0) + 1
    manifest = {
        "seed": args.seed,
        "edits": edits,
        "edits_by_op": by_type,
        "edits_total": len(edits),
        "could_not_seed": unseedable,
        "caveat": "seeded errors are easier to detect than natural ones; reported by type only (PRD §6 Step E)",
        "telugu_fragments_status": "machine-drafted, reviewer sign-off still open (data/seed_ops.yaml)",
    }
    (ROOT / "results").mkdir(exist_ok=True)
    (ROOT / "results" / "seeded_manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"wrote {out_path.relative_to(ROOT)} with {len(edits)} seeded edits across {len(used)} lines")
    for op, n in sorted(by_type.items()):
        print(f"  {op}: {n}")
    for miss in unseedable:
        print(f"  COULD NOT SEED {miss['op']}: wanted {miss['wanted']}, made {miss['made']} - {miss['reason']}")
    print("next: python scripts/run_structured.py --telugu-file "
          f"{out_path.relative_to(ROOT)} --label structured_seeded")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
