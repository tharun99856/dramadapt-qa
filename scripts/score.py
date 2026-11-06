#!/usr/bin/env python3
"""Phase 0 Step D: score both systems against the reviewer's annotation and apply the thresholds.

    python scripts/score.py
    python scripts/score.py --structured results/structured_seeded_flags.json --seeded only

Nothing here invents a number. If the annotation sheet is not filled in, the script says so
and stops, because every metric below depends on it.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src import metrics  # noqa: E402
from src.sample import ACCEPTANCE_CSV, load_annotations, load_sample  # noqa: E402
from src.console import force_utf8  # noqa: E402


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    force_utf8()
    ap = argparse.ArgumentParser()
    ap.add_argument("--annotations", default=str(ROOT / "data" / "annotation" / "blind_annotation.csv"))
    ap.add_argument("--structured", default=str(ROOT / "results" / "structured_flags.json"))
    ap.add_argument("--baseline", default=str(ROOT / "results" / "baseline_flags.json"))
    ap.add_argument("--seeded-manifest", default=str(ROOT / "results" / "seeded_manifest.json"))
    ap.add_argument("--seeded-flags", default=str(ROOT / "results" / "structured_seeded_flags.json"))
    ap.add_argument("--acceptance", default=str(ACCEPTANCE_CSV))
    ap.add_argument("--out", default=str(ROOT / "results" / "scores.json"))
    args = ap.parse_args()

    annotations = load_annotations(Path(args.annotations))
    unfilled = metrics.unfilled(annotations)
    if unfilled:
        print(
            f"BLOCKED: {len(unfilled)} of {len(annotations)} annotation rows have no verdict.\n"
            f"Fill in data/annotation/blind_annotation.csv (scripts/make_blind_sheet.py builds it) "
            f"before scoring. Scoring against a half-filled sheet would just print noise.",
            file=sys.stderr,
        )
        return 3

    structured = load_json(Path(args.structured))
    baseline = load_json(Path(args.baseline))
    if not structured and not baseline:
        print("BLOCKED: no check results found. Run scripts/run_structured.py and scripts/run_baseline.py first.",
              file=sys.stderr)
        return 3

    lines, meta = load_sample()
    chains: dict[str, list[str]] = {}
    for rec in lines:
        if rec.chain_id:
            chains.setdefault(rec.chain_id, []).append(rec.line_id)

    issues = metrics.human_issues(annotations)
    genuine = len(issues)

    s_flags = structured.get("flags", [])
    b_flags = baseline.get("flags", [])
    s_score = metrics.score(s_flags, issues, chains)
    b_score = metrics.score(b_flags, issues, chains)
    s_per_check = metrics.per_check(s_flags, issues, chains)
    sweep_s = metrics.severity_sweep(s_flags, issues, chains)
    sweep_b = metrics.severity_sweep(b_flags, issues, chains)
    beats = metrics.best_recall_at_precision(sweep_s, b_score["precision"])

    decisions = _decisions(Path(args.acceptance))
    acceptance = metrics.acceptance_rates(decisions)

    seeded = {}
    seed_manifest = load_json(Path(args.seeded_manifest))
    seeded_flags = load_json(Path(args.seeded_flags))
    if seed_manifest.get("edits"):
        seeded = metrics.seeded_recall(seed_manifest, seeded_flags.get("flags", []) or s_flags)

    thresholds = {
        "genuine_issues_at_least_10": {"value": genuine, "pass": genuine >= 10},
        "structured_recall_at_least_0_5": {"value": s_score["recall"], "pass": (s_score["recall"] or 0) >= 0.5},
        "structured_beats_baseline_at_similar_precision": {
            "baseline_precision": b_score["precision"],
            "baseline_recall": b_score["recall"],
            "structured_at_that_precision": beats,
            "pass": bool(beats.get("available")) and (beats.get("recall") or 0) > (b_score["recall"] or 0),
        },
        "false_positives_reported": {"structured": s_score["false_positive_flags"],
                                     "baseline": b_score["false_positive_flags"], "pass": True},
        "naturalness_precision_reported_separately": {"value": s_per_check.get("naturalness", {}).get("precision"),
                                                     "pass": "naturalness" in s_per_check},
        "acceptance_rate_available": {"checks_with_decisions": sorted(acceptance), "pass": bool(acceptance)},
    }
    core = ["genuine_issues_at_least_10", "structured_recall_at_least_0_5",
            "structured_beats_baseline_at_similar_precision"]
    decision = "GO" if all(thresholds[k]["pass"] for k in core) else "NO-GO"
    caveats = []
    if not decisions:
        caveats.append("acceptance rate not measured: no decisions recorded yet")
    if structured.get("errors") or baseline.get("errors"):
        caveats.append("at least one check failed to complete, so its lines were not judged")
    if not seed_manifest.get("edits"):
        caveats.append("seeded-error run not done")
    if s["flags"] == 0 and genuine:
        caveats.append("structured QA produced no flags at all against "
                       f"{genuine} human-confirmed issues")
    dropped = [check for check, res in s_per_check.items()
               if (res["precision"] is not None and res["precision"] < 0.25) or
               (acceptance.get(check, {}).get("acceptance_rate") is not None
                and acceptance[check]["acceptance_rate"] < 0.2)]

    out = {
        "generated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "inputs": {
            "annotations": Path(args.annotations).name,
            "annotated_lines": len(annotations),
            "structured_file": Path(args.structured).name,
            "baseline_file": Path(args.baseline).name,
            "structured_model": structured.get("model"),
            "baseline_model": baseline.get("model"),
            "sample_seed": meta.get("seed"),
            "telugu_provenance": meta.get("telugu_provenance"),
            "structured_run_log": structured.get("run_log"),
            "baseline_run_log": baseline.get("run_log"),
        },
        "reviewer": {
            "genuine_issue_lines": genuine,
            "issue_types": _type_counts(issues),
            "ambiguous_verdict_rows": metrics.ambiguous(annotations),
            "note": "one evaluator, one language, 100 lines - no inter-rater agreement is claimed",
        },
        "structured": {"overall": s_score, "per_check": s_per_check, "severity_sweep": sweep_s,
                       "errors": structured.get("errors", [])},
        "baseline": {"overall": b_score, "severity_sweep": sweep_b, "stats": baseline.get("stats", {}),
                      "errors": baseline.get("errors", [])},
        "comparison_at_similar_precision": beats,
        "acceptance_rate": acceptance,
        "seeded_errors": seeded,
        "thresholds": thresholds,
        "decision": decision,
        "caveats": caveats,
        "checks_to_drop": dropped,
    }
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    (ROOT / "docs" / "phase0_results.md").write_text(render(out, lines), encoding="utf-8")

    print(f"genuine issues found by the reviewer: {genuine}/100")
    print(f"structured: precision {s_score['precision']} recall {s_score['recall']} "
          f"({s_score['flags']} flags, {s_score['false_positive_flags']} false)")
    print(f"baseline  : precision {b_score['precision']} recall {b_score['recall']} ({b_score['flags']} flags)")
    print(f"structured at baseline precision: {beats}")
    print(f"decision: {decision}   checks to drop: {dropped or 'none'}")
    print(f"wrote {Path(args.out).name} and docs/phase0_results.md")
    return 0


def _decisions(path: Path) -> dict:
    import csv

    if not path.exists():
        return {}
    out = {}
    with path.open(encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            key = ((row.get("flag_id") or "").strip(), (row.get("line_id") or "").strip())
            if all(key):
                out[key] = row
    return out


def _type_counts(issues: dict[str, set[str]]) -> dict:
    counts: dict[str, int] = {}
    for types in issues.values():
        for t in types:
            counts[t] = counts.get(t, 0) + 1
    return counts


def render(out: dict, lines) -> str:
    s = out["structured"]["overall"]
    b = out["baseline"]["overall"]
    by_line = {rec.line_id: rec for rec in lines}
    head = [
        "# Phase 0 result",
        "",
        f"Written {out['generated']} by `scripts/score.py`. Every figure below is computed from "
        f"`{out['inputs']['annotations']}` (the reviewer's blind annotation) and the two run files.",
        "",
        "## What the reviewer found",
        "",
        f"- Lines needing revision: **{out['reviewer']['genuine_issue_lines']} of {out['inputs']['annotated_lines']}**",
        f"- Issue types: " + ", ".join(f"{k}={v}" for k, v in sorted(out["reviewer"]["issue_types"].items())),
        f"- Evaluator: one native Telugu reviewer (the builder). No inter-rater agreement is claimed.",
        "",
        "## The two systems on identical inputs",
        "",
        "| system | flags | precision | recall | false positives | missed |",
        "|---|---|---|---|---|---|",
        f"| DramAdapt structured | {s['flags']} | {s['precision']} | {s['recall']} | {s['false_positive_flags']} | {s['missed_human_issues']} |",
        f"| generic single-prompt baseline | {b['flags']} | {b['precision']} | {b['recall']} | {b['false_positive_flags']} | {b['missed_human_issues']} |",
        "",
        "## Per check",
        "",
        "| check | flags | precision | recall | false positives |",
        "|---|---|---|---|---|",
    ]
    for check, res in out["structured"]["per_check"].items():
        head.append(f"| {check} | {res['flags']} | {res['precision']} | {res['recall']} | {res['false_positive_flags']} |")
    head += [
        "",
        "## Comparison at similar precision",
        "",
        f"Baseline precision is {out['comparison_at_similar_precision'].get('target_precision')}. "
        f"At that precision or better, structured QA reaches recall "
        f"{out['comparison_at_similar_precision'].get('recall', 'n/a')} "
        f"(severity cut: {out['comparison_at_similar_precision'].get('at_least', 'n/a')}).",
        "",
        "Severity sweep, structured:",
        "",
        *[f"- keep >= {p['at_least']}: {p['flags']} flags, precision {p['precision']}, recall {p['recall']}"
          for p in out["structured"]["severity_sweep"]],
        "",
        "## Reviewer acceptance rate",
        "",
    ]
    if out["acceptance_rate"]:
        head += ["| check | accept | accept-but-modify | dismiss | acceptance rate |", "|---|---|---|---|---|"]
        for check, row in out["acceptance_rate"].items():
            head.append(f"| {check} | {row['accept']} | {row['accept_but_modify']} | {row['dismiss']} | "
                        f"{row['acceptance_rate']} |")
    else:
        head += ["Not measured yet: no acceptance decisions have been recorded. This is the metric that shows",
                 "whether a flag is *useful*, not just whether it fires - fill in the acceptance sheet and re-run.",
                 "", "Sheet: `python scripts/make_acceptance_sheet.py`"]
    head += ["", "## Seeded errors (separate from the main result)", ""]
    if out["seeded_errors"]:
        head += ["| expected check | seeded | detected | recall | which checks fired |", "|---|---|---|---|---|"]
        for check, row in out["seeded_errors"].items():
            head.append(f"| {check} | {row['seeded']} | {row['detected']} | {row['recall']} | "
                        + ", ".join(f"{k}={v}" for k, v in row["by_check"].items()) + " |")
        head += ["", "Seeded errors are blunter than real ones. They measure detection, not product value."]
    else:
        head.append("No seeded run recorded yet.")
    head += ["", "## Thresholds and decision", ""]
    for name, row in out["thresholds"].items():
        head.append(f"- **{name}**: {'PASS' if row['pass'] else 'FAIL'} - {json.dumps({k: v for k, v in row.items() if k != 'pass'}, ensure_ascii=False)}")
    head += ["", f"**Decision: {out['decision']}**", ""]
    if out.get("caveats"):
        head += ["## Caveats", ""] + [f"- {c}" for c in out["caveats"]] + [""]
    if out["checks_to_drop"]:
        head += [f"Checks to drop: {', '.join(out['checks_to_drop'])} (low precision, or the reviewer keeps dismissing them).", ""]
    if out["structured"]["errors"] or out["baseline"]["errors"]:
        head += ["## Runs that failed rather than came out clean", ""]
        for err in out["structured"]["errors"] + out["baseline"]["errors"]:
            head.append(f"- {err['check']}: {err['error']}")
        head.append("")
    head += [
        "## False positives, by hand",
        "",
        "Every flag below was judged as a false positive by the reviewer. Listing them is the honest part of the result.",
        "",
        "| line | speaker | English | Telugu |",
        "|---|---|---|---|",
    ]
    for line_id in s["fp_line_ids"][:40]:
        rec = by_line.get(line_id)
        if rec:
            head.append(f"| {line_id} | {rec.canonical_speaker} | {rec.text[:60]} | {rec.telugu[:60]} |")
    head += [
        "",
        "## Missed issues",
        "",
        *[f"- {line_id} ({etype})" for line_id, etype in s["missed"][:60]],
        "",
        "## Cost actually spent",
        "",
        f"- structured: {json.dumps(out['inputs']['structured_run_log'], ensure_ascii=False)}",
        f"- baseline: {json.dumps(out['inputs']['baseline_run_log'], ensure_ascii=False)}",
        "",
    ]
    return "\n".join(head)


if __name__ == "__main__":
    raise SystemExit(main())
