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
    ap.add_argument("--overrides", default=str(ROOT / "data" / "check_overrides.json"))
    ap.add_argument("--out", default=str(ROOT / "results" / "scores.json"))
    ap.add_argument("--report", default=str(ROOT / "docs" / "phase0_results.md"))
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
    seeded_flags_path = Path(args.seeded_flags)
    seeded_flags = load_json(seeded_flags_path)
    if seed_manifest.get("edits"):
        # This used to fall back to the clean run's flags. That scored the seeded lines against a
        # draft that never contained the seeded errors and printed 1.0 recalls, so it now refuses.
        if seeded_flags.get("flags"):
            seeded = metrics.seeded_recall(seed_manifest, seeded_flags["flags"])
        else:
            seeded = {
                "status": "not measured",
                "reason": f"{seeded_flags_path.name} does not exist, so nothing here was run against "
                          f"the seeded draft. The {len(seed_manifest['edits'])} edits in "
                          f"{Path(args.seeded_manifest).name} were never scored.",
                "command": "python scripts/run_seeded.py && python scripts/run_structured.py "
                           "--telugu-file data/telugu/first_pass_seeded.json --label structured_seeded",
            }

    thresholds = {
        "genuine_issues_at_least_10": {"value": genuine, "pass": genuine >= 10},
        "structured_recall_at_least_0_5": {
            "value": s_score["recall"],
            "basis": "reviewer (line, type) instances credited / instances the reviewer reported",
            "value_legacy_flagcount": s_score["recall_legacy_flagcount"],
            "pass": (s_score["recall"] or 0) >= 0.5,
        },
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
    thresholds["line_level_reported"] = {
        "structured": s_score["line_level"], "baseline": b_score["line_level"], "pass": True,
        "note": "did the system put any flag on a line the reviewer marked, and how many of the "
                "lines it touched were ones the reviewer marked - the operational reading",
    }
    thresholds["instance_coverage_reported"] = {
        "structured": f"{s_score['instances_found']}/{s_score['instances_total']}",
        "baseline": f"{b_score['instances_found']}/{b_score['instances_total']}",
        "pass": True,
        "note": "one untyped baseline flag credits every type the reviewer named on that line, so "
                "the baseline leads on this row while flagging fewer issue lines",
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
    elif seeded.get("status") == "not measured":
        caveats.append("seeded errors not measured: no run against the seeded draft exists, "
                       "so any seeded number in a document is unsupported")
    if s_score["flags"] == 0 and genuine:
        caveats.append("structured QA produced no flags at all against "
                       f"{genuine} human-confirmed issues")
    dropped = [check for check, res in s_per_check.items()
               if (res["precision"] is not None and res["precision"] < 0.25) or
               (acceptance.get(check, {}).get("acceptance_rate") is not None
                and acceptance[check]["acceptance_rate"] < 0.2)]

    # A pre-registered rule and a human decision are different kinds of thing, so both stay in the
    # output. Overrides never edit `dropped`: they sit beside it, with the reason and the n.
    overrides = [o for o in _overrides(Path(args.overrides)) if o["check"] in dropped]
    if overrides:
        caveats.append(
            "checks the rule says to drop and the builder decided to keep: "
            + "; ".join(f"{o['check']} ({o['evidence']})" for o in overrides)
            + ". The threshold was not moved to match the decision.")

    reviewer_std = _register_standard()

    out = {
        "generated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "inputs": {
            "annotations": Path(args.annotations).name,
            "annotated_lines": len(annotations),
            "structured_file": Path(args.structured).name,
            "baseline_file": Path(args.baseline).name,
            "structured_model": structured.get("model")
                                or (structured.get("run_log") or {}).get("models"),
            "baseline_model": baseline.get("model")
                              or (baseline.get("run_log") or {}).get("models"),
            "sample_seed": meta.get("seed"),
            "telugu_provenance": meta.get("telugu_provenance"),
            "structured_run_log": structured.get("run_log"),
            "baseline_run_log": baseline.get("run_log"),
            "seeded_flags_file": (seeded_flags_path.name if seeded_flags.get("flags") else None),
        },
        "reviewer": {
            "genuine_issue_lines": genuine,
            "issue_types": _type_counts(issues),
            "ambiguous_verdict_rows": metrics.ambiguous(annotations),
            "note": (
                "one Telugu evaluator (the builder), one language, 100 lines. No inter-rater "
                "agreement is claimed. Provenance of these verdicts, stated plainly because it "
                "affects how much weight they carry: they were recorded in ten batches in a chat "
                "session with an AI assistant, and a share of them were recorded against a grade "
                "the assistant drafted and the reviewer then reviewed, changed or accepted. The "
                "reviewer approved every row, so the judgement on the sheet is the reviewer's, but "
                "this is human-reviewed AI-suggested annotation, not independent human annotation, "
                "and it must not be described as that. One block (rows 61-70) was first graded "
                "against ten lines the assistant invented and has been re-graded against the file; "
                "see docs/failure_log.md entry 22."
            ),
            "address_rule": reviewer_std["address_rule"],
            "name_spellings": reviewer_std["name_spellings"],
            "register_standard_status": reviewer_std["status"],
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
        "checks_retained_by_override": overrides,
    }
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    report_path = Path(args.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(render(out, lines), encoding="utf-8")

    print(f"genuine issues found by the reviewer: {genuine}/100")
    print(f"structured: precision {s_score['precision']} recall {s_score['recall']} "
          f"({s_score['instances_found']}/{s_score['instances_total']} instances, "
          f"{s_score['line_level']['issue_lines_found']}/{s_score['line_level']['issue_lines_total']} lines, "
          f"{s_score['flags']} flags, {s_score['false_positive_flags']} false)")
    print(f"baseline  : precision {b_score['precision']} recall {b_score['recall']} "
          f"({b_score['instances_found']}/{b_score['instances_total']} instances, "
          f"{b_score['line_level']['issue_lines_found']}/{b_score['line_level']['issue_lines_total']} lines, "
          f"{b_score['flags']} flags)")
    print(f"structured at baseline precision: {beats}")
    print(f"decision: {decision}   checks to drop: {dropped or 'none'}")
    print(f"wrote {Path(args.out).name} and {report_path.name}")
    return 0


def _overrides(path: Path) -> list[dict]:
    """Decisions to keep a check the rule would drop. Data, not prose, so the reason is attributable.

    Each entry needs `check`, `evidence` and `decided_by`. A run with no such file simply has no
    overrides, which is the honest default: silence is not a decision to keep.
    """
    if not path.exists():
        return []
    entries = json.loads(path.read_text(encoding="utf-8"))
    bad = [e for e in entries if not {"check", "evidence", "decided_by"} <= set(e)]
    if bad:
        sys.exit(f"{path.name}: every override needs check, evidence and decided_by")
    return entries


def _register_standard() -> dict:
    """The reviewer's sign-off decisions, read from the sheet the relationship check also reads.

    These are printed into the generated report from data rather than pasted by hand, because a
    hand-written line in docs/phase0_results.md is deleted by the next run of this script.
    """
    from src.corpus import relationship_sheet

    block = relationship_sheet().get("telugu_register_standard") or {}
    decided = [d for d in (block.get("reviewer_decisions") or []) if isinstance(d, dict)]
    by_id = {d.get("id"): d for d in decided}
    spellings = {k: v for d in decided for k, v in d.items() if k in ("caine", "halloran")}
    return {"address_rule": (by_id.get("joss_addresses_edda") or {}).get("report_sentence", ""),
            "name_spellings": spellings,
            "status": block.get("status", "")}


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
        f"- Evaluator: {out['reviewer']['note']}",
        "",
        "## Reviewer standard, as decided (data/relationship_sheet.yaml, read at run time)",
        "",
        f"- Status: {out['reviewer']['register_standard_status']}",
        f"- {out['reviewer']['address_rule']}",
        "- Name spellings: " + ", ".join(f"{k}={v}" for k, v in sorted(out["reviewer"]["name_spellings"].items())),
        "- The Step A draft column keeps its own variants on purpose: it is byte-identical to "
        "`data/telugu/first_pass.json`, and saved flags quote it, three of them `script` flags that "
        "exist only because the draft left a name in Latin script. Normalising it there would break "
        "that evidence, so the standard is recorded as a decision, not written over the output.",
        "",
        "## The two systems on identical inputs",
        "",
        "Two readings are given because they answer different questions. Instance coverage asks how "
        "much of what the reviewer found each system named; line level asks whether the system put a "
        "flag on a line the reviewer marked, which is what a dubbing director actually experiences.",
        "",
        "| system | flags | precision | instances credited | recall (instances) | issue lines found | line recall | line precision | false positives |",
        "|---|---|---|---|---|---|---|---|---|",
        f"| DramAdapt structured | {s['flags']} | {s['precision']} | {s['instances_found']}/{s['instances_total']} "
        f"| {s['recall']} | {s['line_level']['issue_lines_found']}/{s['line_level']['issue_lines_total']} "
        f"| {s['line_level']['recall']} | {s['line_level']['precision']} | {s['false_positive_flags']} |",
        f"| generic single-prompt baseline | {b['flags']} | {b['precision']} | {b['instances_found']}/{b['instances_total']} "
        f"| {b['recall']} | {b['line_level']['issue_lines_found']}/{b['line_level']['issue_lines_total']} "
        f"| {b['line_level']['recall']} | {b['line_level']['precision']} | {b['false_positive_flags']} |",
        "",
        f"Recall here is instances credited over instances reported. The figure previously submitted as "
        f"\"recall\" divided a flag count by a mixed denominator and read {s['recall_legacy_flagcount']} "
        f"for structured and {b['recall_legacy_flagcount']} for baseline against a true instance count of "
        f"{s['instances_total']}; both arms' old denominators ({s['legacy_denominator_was']} and "
        f"{b['legacy_denominator_was']}) counted something other than reviewer issues.",
        "",
        "## Per check",
        "",
        "| check | flags | precision | of its own type | type recall | overall recall | false positives |",
        "|---|---|---|---|---|---|---|",
    ]
    for check, res in out["structured"]["per_check"].items():
        head.append(f"| {check} | {res['flags']} | {res['precision']} | "
                    f"{res.get('type_instances_found', '?')}/{res.get('type_instances_total', '?')} "
                    f"| {res.get('type_recall')} | {res['recall']} | {res['false_positive_flags']} |")
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
    seeded = out["seeded_errors"]
    if seeded.get("status") == "not measured":
        head += [f"**Not measured.** {seeded['reason']}", "",
                 f"To run it for real: `{seeded['command']}`", ""]
    elif seeded:
        head += [f"From `{out['inputs']['seeded_flags_file']}`.", "",
                 "| expected check | seeded | caught by that check | recall (that check) "
                 "| caught by any check | which checks fired |", "|---|---|---|---|---|---|"]
        for check, row in seeded.items():
            head.append(f"| {check} | {row['seeded']} | {row['detected_by_expected_check']} | "
                        f"{row['recall']} | {row['detected_by_any_check']} | "
                        + ", ".join(f"{k}={v}" for k, v in row["by_check"].items()) + " |")
        head += ["", "Seeded errors are blunter than real ones. They measure detection, not product value.",
                 "The two recall columns differ on purpose: a flag from the wrong check is not the "
                 "check working, it is the line being noisy."]
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
    if out.get("checks_retained_by_override"):
        head += ["Checks the rule names for dropping that the builder decided to keep, with the "
                 "evidence on each side:", ""]
        for o in out["checks_retained_by_override"]:
            head += [f"- **{o['check']}** - decided by {o['decided_by']}: {o['evidence']}"]
        head += ["", "The threshold itself was not moved to fit this decision.", ""]
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
