#!/usr/bin/env python3
"""Run the whole gate on any screenplay: the interview rerun the brief describes.

    python scripts/run_qa.py --input data/screenplay
    python scripts/run_qa.py --input /path/to/new_show/ep1.txt --telugu their_draft.json
    python scripts/run_qa.py --input /path/to/new_show --rate 3.9 --label new_input

A directory of .txt files or a single file both work. If no Telugu draft is supplied, Step A
generates one from the configured model and every artifact labels it as a machine stand-in.
Nothing here reads the Phase 0 sample, so a new show cannot inherit the old sample's numbers.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import yaml  # noqa: E402

from run_first_pass import translate  # noqa: E402
from src import config as config_mod  # noqa: E402
from src.parser import parse_screenplay  # noqa: E402
from src.pipeline import ALL_CHECKS, run_structured, write_payload  # noqa: E402
from src.report import write_markdown, write_run_json  # noqa: E402
from src.console import force_utf8  # noqa: E402


def attach_from_payload(lines, payload) -> int:
    """Put a generated or supplied Telugu draft back onto the records every check reads.

    Step A used to write its answers to disk and stop there. The checks then saw an empty Telugu
    field on lines that had just been translated: timing and script reported nothing to read, and
    the meaning check called 14 of them "missing" at high severity. Only overwrite where there is
    something to write, so a partial draft cannot blank out a line another source already filled.
    """
    items = payload.get("lines") if isinstance(payload, dict) else payload
    by_id = {str(i["line_id"]): str(i.get("telugu", "")).strip() for i in items or [] if i.get("line_id")}
    for rec in lines:
        if text := by_id.get(rec.line_id, ""):
            rec.telugu = text
    return sum(1 for rec in lines if rec.telugu)


def attach_telugu(lines, telugu_file: Path):
    payload = json.loads(Path(telugu_file).read_text(encoding="utf-8"))
    matched = attach_from_payload(lines, payload)
    provenance = payload.get("provenance") if isinstance(payload, dict) else None
    return matched, provenance


def main() -> int:
    force_utf8()
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, help="screenplay .txt file or a folder of them")
    ap.add_argument("--telugu", default=None, help="localized draft JSON; Step A runs if omitted")
    ap.add_argument("--skip-step-a", action="store_true",
                    help="check the parse and the coverage report without generating anything: "
                         "no Telugu is attached, so the lines arrive with nothing to compare. "
                         "Use it to see what a new input costs before spending a token on it.")
    ap.add_argument("--checks", default=",".join(ALL_CHECKS))
    ap.add_argument("--rate", type=float, default=None, help="Telugu akshara/s if not calibrated yet")
    ap.add_argument("--model", default=None, help="override config.yaml for the Step A pass")
    ap.add_argument("--label", default="new_input", help="artifact prefix under results/")
    ap.add_argument("--config", default=None)
    ap.add_argument("--fresh", action="store_true",
                    help="pay for every batch again instead of reusing the calls already logged for this label")
    args = ap.parse_args()
    ap_label = args.label

    cfg = config_mod.load(args.config)
    alias_path = ROOT / "data" / "alias_map.yaml"
    alias_map = yaml.safe_load(alias_path.read_text(encoding="utf-8")) if alias_path.exists() else []

    try:
        parsed = parse_screenplay(Path(args.input), alias_map)
    except FileNotFoundError as exc:
        print(f"cannot read the input: {exc}", file=sys.stderr)
        return 2

    print(f"input: {args.input}")
    print(f"episodes: {parsed.episode_count} | dialogue blocks: {parsed.block_count} | "
          f"lines: {len(parsed.records)} | non-dialogue blocks: {parsed.non_dialogue_count} | "
          f"blocks the parser could not read: {parsed.unparsed_blocks}")
    if parsed.unparsed_blocks:
        for w in parsed.warnings[:12]:
            if w.kind in ("stray", "label", "time", "empty", "unquoted"):
                print(f"  {w.kind}: {w.file}:{w.line} {w.detail}")
        print("  the parser kept every block it could not read visible instead of dropping it.")

    if not parsed.records:
        print("no dialogue lines were parsed - the gate has nothing to check.", file=sys.stderr)
        return 2

    telugu_file = args.telugu
    if telugu_file:
        matched, prov = attach_telugu(parsed.records, Path(telugu_file))
        print(f"telugu attached: {matched}/{len(parsed.records)} lines from {telugu_file}")
        if matched == 0:
            print("  no line ids matched the draft, so only timing-free checks could have anything to read.",
                  file=sys.stderr)
    else:
        telugu_file = ROOT / "data" / "telugu" / f"{ap_label}.json"
        if args.skip_step_a:
            print("no --telugu draft and --skip-step-a: nothing is attached, so every line will be "
                  "reported as unjudged. This run spent zero requests and proves the parse only.")
            telugu_file = None
        else:
            print("no --telugu draft: running Step A to produce a machine first pass ...")
            fp = translate(parsed.records, cfg, args.model, Path(telugu_file), f"{ap_label}_first_pass",
                           None, seed=None, reuse=not args.fresh)
            cov = fp["coverage"]
            logt = fp["run_log"]
            print(f"step A: {cov['returned']}/{cov['requested']} lines | requests {logt['requests_total']} "
                  f"prompt {logt['prompt_tokens']} completion {logt['completion_tokens']} "
                  f"| model {fp['provenance']['model']}")
            matched = attach_from_payload(parsed.records, fp)
            print(f"telugu attached from step A: {matched}/{len(parsed.records)} lines")
            if cov.get("not_telugu_script"):
                print(f"  {len(cov['not_telugu_script'])} lines came back with no Telugu letters "
                      f"(the script check flags these)")

    checks = tuple(c.strip() for c in args.checks.split(",") if c.strip())
    if unknown := [c for c in checks if c not in ALL_CHECKS]:
        print(f"unknown checks: {unknown}", file=sys.stderr)
        return 2

    payload = run_structured(parsed.records, checks, cfg_path=args.config, model=None,
                             max_lines_per_request=None, phase=ap_label, rate_override=args.rate,
                             reuse=not args.fresh)
    payload["source"] = {"input": str(args.input), "files": parsed.files,
                         "telugu_file": str(telugu_file), "unparsed_blocks": parsed.unparsed_blocks,
                         "parse_warnings": len(parsed.warnings)}
    flags_path = write_payload(payload, ROOT / "results" / f"{ap_label}_flags.json")
    write_run_json(payload, ROOT / "results" / f"{ap_label}_run.json")
    write_markdown(payload, parsed.records, ROOT / "results" / f"{ap_label}_report.md")

    per_check: dict[str, int] = {}
    for flag in payload["flags"]:
        per_check[flag["check"]] = per_check.get(flag["check"], 0) + 1
    logt = payload["run_log"]
    print(f"flags: {len(payload['flags'])} -> {per_check}")
    print(f"requests: {logt['requests_total']} measured: {logt['requests_measured']} "
          f"prompt_tokens: {logt['prompt_tokens']} completion_tokens: {logt['completion_tokens']} "
          f"cost_usd: {logt['cost_usd']}")
    if payload["reused_requests"]:
        print(f"batches reused from the call log (already paid for): {payload['reused_requests']}")
    for name, block in (payload.get("summaries") or {}).items():
        if block.get("lines_not_judged"):
            print(f"  {name}: {block['lines_not_judged']} lines sent but not classified "
                  f"({','.join(block.get('not_judged_line_ids', [])[:6])}...) - neither flagged nor cleared")
    for err in payload["errors"]:
        print(f"  CHECK FAILED {err['check']}: {err['error']}")
    print(f"wrote {flags_path.name}, {ap_label}_run.json, {ap_label}_report.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
