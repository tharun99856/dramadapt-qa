#!/usr/bin/env python3
"""Phase 0 Step C: the generic single-prompt control, on the same lines and the same model."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.pipeline import run_baseline_control, sample_lines, write_payload  # noqa: E402
from src.report import write_run_json  # noqa: E402
from src.console import force_utf8  # noqa: E402


def main() -> int:
    force_utf8()
    ap = argparse.ArgumentParser()
    ap.add_argument("--telugu-file", default=None)
    ap.add_argument("--model", default=None)
    ap.add_argument("--max-lines-per-request", type=int, default=None)
    ap.add_argument("--label", default="baseline")
    ap.add_argument("--config", default=None)
    args = ap.parse_args()

    lines, meta = sample_lines(args.telugu_file)
    print(f"lines: {len(lines)} | telugu attached: {sum(1 for r in lines if r.telugu)}")
    payload = run_baseline_control(lines, cfg_path=args.config, model=args.model,
                                   max_lines_per_request=args.max_lines_per_request)
    payload["source"] = {"telugu_file": meta.get("telugu_file"), "telugu_provenance": meta.get("telugu_provenance"),
                         "sample_seed": meta.get("seed")}
    write_payload(payload, ROOT / "results" / f"{args.label}_flags.json")
    write_run_json(payload, ROOT / "results" / f"{args.label}_run.json")

    logt = payload["run_log"]
    stats = payload.get("stats", {})
    print(f"batches: {len(payload['batches'])} problems reported: {stats.get('problems_reported', 0)} "
          f"batches with nothing found: {stats.get('batches_with_no_problems', 0)} "
          f"unknown ids: {stats.get('unknown_ids', 0)}")
    print(f"requests: {logt['requests_total']} prompt_tokens: {logt['prompt_tokens']} "
          f"completion_tokens: {logt['completion_tokens']} cost_usd: {logt['cost_usd']}")
    for err in payload["errors"]:
        print(f"  FAILED: {err['check']}: {err['error']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
