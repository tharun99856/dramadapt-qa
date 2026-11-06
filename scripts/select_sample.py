#!/usr/bin/env python3
"""Pick the Phase 0 sample from our own corpus with a recorded seed and stratified minimums.

    python scripts/select_sample.py                 # uses data/selection_plan.yaml
    python scripts/select_sample.py --seed 42 --show

Writes:
  data/annotation/sample_lines.json   stored order, full context
  data/annotation/sample_lines.csv
  data/annotation/blind_order.json    the randomized order used for annotation
  results/selection_manifest.json     seed, quotas, minimums met or not
  docs/category_audit.md              every line with its category tags, for review
"""

from __future__ import annotations

import argparse
import csv
import json
import random
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.corpus import categories_for, context_for, corpus, register_expectation  # noqa: E402
from src.parser import to_dict  # noqa: E402
from src.console import force_utf8  # noqa: E402

MINIMUM_UNITS = {"chain_member": "chains", "short_slot": "lines", "voice_or_offscreen": "lines",
                 "address_shift": "lines", "threat_or_accusation": "lines",
                 "tender_or_intimate": "lines", "long_line": "lines"}


def unit_of(rec, category: str):
    if category == "chain_member":
        return rec.chain_id
    return rec.line_id


def main() -> int:
    force_utf8()
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", default=str(ROOT / "data" / "selection_plan.yaml"))
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--show", action="store_true", help="print the selected lines")
    args = ap.parse_args()

    plan = yaml.safe_load(Path(args.plan).read_text(encoding="utf-8"))
    seed = int(args.seed if args.seed is not None else plan["seed"])
    rng = random.Random(seed)
    target = int(plan["target_lines"])
    cap = int(plan["per_episode_max"])
    minimums = dict(plan["minimums"])

    records = corpus()
    tagged = {rec.line_id: categories_for(rec) for rec in records}
    by_line = {rec.line_id: rec for rec in records}

    pool_by_cat: dict[str, list[str]] = {}
    for cat in minimums:
        pool_by_cat[cat] = [rec.line_id for rec in records if cat in tagged[rec.line_id]]

    chosen: list[str] = []
    chosen_set: set[str] = set()
    per_ep: dict[int, int] = {}
    relaxations: list[str] = []

    def units_in(cat: str, ids: list[str]) -> set:
        return {unit_of(by_line[i], cat) for i in ids if cat in tagged[i]}

    def add(line_id: str) -> None:
        rec = by_line[line_id]
        if line_id in chosen_set:
            return
        chosen.append(line_id)
        chosen_set.add(line_id)
        per_ep[rec.episode] = per_ep.get(rec.episode, 0) + 1
        # keep whole chains together, even if that nudges the total past target
        if rec.chain_id:
            for partner in by_line.values():
                if partner.chain_id == rec.chain_id and partner.line_id not in chosen_set:
                    chosen.append(partner.line_id)
                    chosen_set.add(partner.line_id)
                    per_ep[partner.episode] = per_ep.get(partner.episode, 0) + 1

    order = sorted(minimums, key=lambda c: len(pool_by_cat[c])) if plan.get("scarce_first", True) else list(minimums)

    for cat in order:
        need = int(minimums[cat])
        have = len(units_in(cat, chosen))
        pool = [i for i in pool_by_cat[cat] if i not in chosen_set]
        rng.shuffle(pool)
        for line_id in pool:
            if have >= need:
                break
            rec = by_line[line_id]
            if per_ep.get(rec.episode, 0) >= cap:
                continue
            add(line_id)
            have = len(units_in(cat, chosen))

    # fill to target, episode-capped, seeded random over everything not yet chosen
    rest = [rec.line_id for rec in records if rec.line_id not in chosen_set]
    rng.shuffle(rest)
    for line_id in rest:
        if len(chosen) >= target:
            break
        rec = by_line[line_id]
        if per_ep.get(rec.episode, 0) >= cap:
            continue
        add(line_id)

    # last pass: if a minimum is still short, drop the cap and say so in the manifest
    for cat in order:
        need = int(minimums[cat])
        have = len(units_in(cat, chosen))
        if have >= need:
            continue
        pool = [i for i in pool_by_cat[cat] if i not in chosen_set]
        rng.shuffle(pool)
        for line_id in pool:
            if have >= need:
                break
            add(line_id)
            relaxations.append(f"{cat}: per-episode cap relaxed for {line_id}")
            have = len(units_in(cat, chosen))

    chosen_records = sorted((by_line[i] for i in chosen), key=lambda r: (r.source_file, r.start, r.line_id))

    cat_counts = {}
    for cat in minimums:
        cat_counts[cat] = {
            "in_corpus": len(pool_by_cat[cat]),
            "in_sample_lines": sum(1 for r in chosen_records if cat in tagged[r.line_id]),
            "in_sample_units": len(units_in(cat, [r.line_id for r in chosen_records])),
            "unit": MINIMUM_UNITS.get(cat, "lines"),
            "minimum": int(minimums[cat]),
        }
        cat_counts[cat]["met"] = cat_counts[cat]["in_sample_units"] >= cat_counts[cat]["minimum"]

    blind_ids = [r.line_id for r in chosen_records]
    blind_rng = random.Random(seed + 1)
    blind_rng.shuffle(blind_ids)
    anon_map = {line_id: f"A{n:03d}" for n, line_id in enumerate(blind_ids, start=1)}

    out_dir = ROOT / "data" / "annotation"
    out_dir.mkdir(parents=True, exist_ok=True)

    rows = []
    for rec in chosen_records:
        rows.append(
            {
                **to_dict(rec),
                "categories": tagged[rec.line_id],
                "context": context_for(rec),
                "register_expectation": register_expectation(rec),
                "blind_order": anon_map[rec.line_id],
            }
        )
    (out_dir / "sample_lines.json").write_text(
        json.dumps({"seed": seed, "target": target, "n": len(rows), "lines": rows}, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    fieldnames = ["blind_order", "line_id", "episode", "scene", "canonical_speaker", "delivery_tag",
                  "start", "end", "tight_window", "loose_window", "word_count", "text", "chain_id",
                  "chain_kind", "voice_over", "off_screen", "categories", "register_expectation", "context"]
    with (out_dir / "sample_lines.csv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            row = dict(row)
            row["categories"] = ";".join(sorted(row["categories"]))
            writer.writerow(row)
    (out_dir / "blind_order.json").write_text(json.dumps({"seed": seed + 1, "order": blind_ids, "anon": anon_map}, indent=2), encoding="utf-8")

    manifest = {
        "seed": seed,
        "plan_file": str(Path(args.plan).relative_to(ROOT)),
        "target": target,
        "selected": len(chosen_records),
        "per_episode": {str(ep): sum(1 for r in chosen_records if r.episode == ep) for ep in sorted({r.episode for r in chosen_records})},
        "categories": cat_counts,
        "all_minimums_met": all(v["met"] for v in cat_counts.values()),
        "cap_relaxations": relaxations,
        "note": "Sample comes from data/screenplay/, written by the builder. No Kuku pack content.",
    }
    (ROOT / "results" / "selection_manifest.json").parent.mkdir(parents=True, exist_ok=True)
    (ROOT / "results" / "selection_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    audit = ["# Category audit", "", "Which rule matched which line, over the whole corpus.",
            "Correct `data/category_rules.yaml` if a match looks wrong, then re-run.", ""]
    for cat in minimums:
        audit.append(f"## {cat} (corpus {len(pool_by_cat[cat])}, sample {cat_counts[cat]['in_sample_lines']}, minimum {minimums[cat]})")
        audit.append("")
        for rec in records:
            if cat in tagged[rec.line_id]:
                mark = "S" if rec.line_id in chosen_set else " "
                audit.append(f"- [{mark}] `{rec.line_id}` {rec.canonical_speaker} ({rec.delivery_tag}): {rec.text[:90]} -> {tagged[rec.line_id][cat]}")
        audit.append("")
    (ROOT / "docs" / "category_audit.md").write_text("\n".join(audit), encoding="utf-8")

    print(f"seed={seed} selected={len(chosen_records)} target={target}")
    print(f"per episode: {manifest['per_episode']}")
    for cat, v in cat_counts.items():
        print(f"  {cat}: {v['in_sample_units']}/{v['minimum']} {v['unit']} (corpus pool {v['in_corpus']}) {'OK' if v['met'] else 'SHORT'}")
    print(f"all minimums met: {manifest['all_minimums_met']}")
    if relaxations:
        print(f"cap relaxations: {len(relaxations)}")
    if args.show:
        for rec in chosen_records:
            print(f"  {rec.line_id} {rec.canonical_speaker}: {rec.text[:70]}")
    return 0 if manifest["all_minimums_met"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
