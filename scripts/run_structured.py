#!/usr/bin/env python3
"""Phase 0 Step C / Phase 1: run the structured DramAdapt checks over the sample.

    python scripts/run_structured.py
    python scripts/run_structured.py --checks timing --rate 4.2
    python scripts/run_structured.py --telugu-file data/telugu/first_pass_seeded.json --label structured_seeded
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.pipeline import ALL_CHECKS, run_structured, sample_lines, write_payload  # noqa: E402
from src.report import write_markdown, write_run_json  # noqa: E402
from src.console import force_utf8  # noqa: E402


def carry_over_errors(current: list[dict], prior: list[dict], reran: set[str], kept: list[str]) -> list[dict]:
    """A merge keeps the failures of every check it did not just re-run.

    Losing them is how "2 of 18 batches refused" disappears from an artifact while the summary that
    explains it survives: the report then has no *did not finish* section left to print.
    """
    return ([e for e in current if e.get("check") not in set(kept)]
            + [e for e in prior if e.get("check") not in reran])


def main() -> int:
    force_utf8()
    ap = argparse.ArgumentParser()
    ap.add_argument("--checks", default=",".join(ALL_CHECKS), help="comma separated subset of meaning,relationship,timing,naturalness,script")
    ap.add_argument("--telugu-file", default=None)
    ap.add_argument("--model", default=None)
    ap.add_argument("--rate", type=float, default=None, help="override the calibrated Telugu rate (akshara/s)")
    ap.add_argument("--max-lines-per-request", type=int, default=None)
    ap.add_argument("--label", default="structured", help="run name; results/<label>_flags.json")
    ap.add_argument("--merge", default=None, metavar="LABEL",
                    help="keep the flags of checks not re-run here from results/<LABEL>_flags.json. "
                         "Use it to re-price timing after calibration without paying for the LLM "
                         "checks a second time; tokens are never double counted.")
    ap.add_argument("--config", default=None)
    ap.add_argument("--fresh", action="store_true",
                    help="ignore the calls already logged for this label and pay for every batch again. "
                         "By default a batch whose exact prompt is already in the call log is reused, "
                         "which is what makes a throttled run finishable.")
    args = ap.parse_args()

    checks = tuple(c.strip() for c in args.checks.split(",") if c.strip())
    unknown = [c for c in checks if c not in ALL_CHECKS]
    if unknown:
        print(f"unknown checks: {unknown}", file=sys.stderr)
        return 2

    lines, meta = sample_lines(args.telugu_file)
    print(f"lines: {len(lines)} | telugu attached: {sum(1 for r in lines if r.telugu)} | checks: {','.join(checks)}")
    payload = run_structured(lines, checks, cfg_path=args.config, model=args.model,
                             max_lines_per_request=args.max_lines_per_request, phase=args.label,
                             rate_override=args.rate, reuse=not args.fresh)
    if payload["reused_requests"]:
        print(f"reused {payload['reused_requests']} batches from results/{args.label}_calls.jsonl; "
              "their tokens are counted once, in the run log, not again here")
    payload["source"] = {"telugu_file": meta.get("telugu_file"), "telugu_provenance": meta.get("telugu_provenance"),
                         "sample_seed": meta.get("seed")}

    if args.merge:
        prior_path = ROOT / "results" / f"{args.merge}_flags.json"
        if not prior_path.exists():
            print(f"--merge: results/{args.merge}_flags.json does not exist; writing this run alone",
                  file=sys.stderr)
        else:
            prior = json.loads(prior_path.read_text(encoding="utf-8"))
            keep = [f for f in prior.get("flags", []) if f["check"] not in checks]
            kept = sorted({f["check"] for f in keep})
            payload["flags"].extend(keep)
            for key in ("verdicts", "summaries"):
                for name, block in (prior.get(key) or {}).items():
                    payload[key].setdefault(name, block)
            payload["checks_run"] = list(checks) + kept
            payload["errors"] = carry_over_errors(payload["errors"], prior.get("errors") or [],
                                                  set(checks), kept)
            payload["merged_from"] = {"label": args.merge, "checks_kept": kept, "note": (
                "run_log for this label is cumulative across every invocation that wrote its call log, "
                "so the merged checks' requests already appear in these totals rather than being counted twice"
                if args.merge == args.label else
                f"run_log here counts only this label's own calls; the merged checks' requests stay in "
                f"results/{args.merge}_run.json and are not added to these totals")}
            print(f"merged {len(keep)} flags of checks {kept} from results/{args.merge}_flags.json")

    flags_path = write_payload(payload, ROOT / "results" / f"{args.label}_flags.json")
    write_run_json(payload, ROOT / "results" / f"{args.label}_run.json")
    write_markdown(payload, lines, ROOT / "results" / f"{args.label}_report.md")

    logt = payload["run_log"]
    per_check: dict[str, int] = {}
    for flag in payload["flags"]:
        per_check[flag["check"]] = per_check.get(flag["check"], 0) + 1
    print(f"batches(requests target): {len(payload['batches'])}")
    print(f"flags: {len(payload['flags'])} -> {per_check}")
    print(f"requests: {logt['requests_total']} measured: {logt['requests_measured']} "
          f"prompt_tokens: {logt['prompt_tokens']} completion_tokens: {logt['completion_tokens']} "
          f"cost_usd: {logt['cost_usd']}")
    print(f"batches reused from the call log (no new tokens): {payload['reused_requests']}")
    if payload["errors"]:
        print("CHECKS THAT FAILED (not clean passes):")
        for err in payload["errors"]:
            print(f"  {err['check']}: {err['error']}")
    print(f"wrote {flags_path.relative_to(ROOT)}, {args.label}_run.json, {args.label}_report.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
