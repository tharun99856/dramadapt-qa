#!/usr/bin/env python3
"""Phase 0 Step A: one fixed prompt, one pass, Telugu for every sampled line.

    python scripts/run_first_pass.py                     # uses config.yaml provider
    python scripts/run_first_pass.py --model gemini-2.0-flash --out data/telugu/first_pass_alt.json
    python scripts/run_first_pass.py --compare           # both models, two files, one report
    python scripts/run_first_pass.py --from-file X.json  # import an externally produced pass

The model output is stored untouched. The raw prompts and responses live in
results/first_pass_calls.jsonl, which is where the cost figures come from.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src import config as config_mod  # noqa: E402
from src.batching import scene_batches  # noqa: E402
from src.checks.relationship import relationship_sheet  # noqa: E402
from src.llm import LLM, LLMError  # noqa: E402
from src.parser import DialogueLine  # noqa: E402
from src.pipeline import register_standard, sample_lines, write_payload  # noqa: E402
from src.prompting import require_coverage  # noqa: E402
from src.runlog import RunLog  # noqa: E402
from src.telugu import has_telugu, script_name  # noqa: E402
from src.console import force_utf8  # noqa: E402

CONTRACT = (
    ' Reply JSON only: {"lines":[{"line_id":"","telugu":""}]}. Every input line_id appears '
    "exactly once, in the same order. Give Telugu text only - no notes, no alternates, no scores."
)


def build_system(cfg: dict) -> str:
    return cfg.get("first_pass", {}).get("instruction", "").strip() + CONTRACT


def build_user(batch: str, lines: list[DialogueLine], cfg: dict) -> str:
    items = []
    for rec in lines:
        items.append(
            {
                "line_id": rec.line_id,
                "speaker": rec.canonical_speaker,
                "emotion_or_delivery": rec.delivery_tag,
                "english": rec.text,
                "slot_seconds": rec.tight_window,
                "chain": rec.chain_id or None,
                "chain_position": rec.chain_position or None,
                "speech_mode": "voice-over" if rec.voice_over else ("off-screen" if rec.off_screen else "on-camera"),
                "scene": rec.scene_heading,
            }
        )
    chains = {}
    for rec in lines:
        if rec.chain_id:
            chains.setdefault(rec.chain_id, []).append(rec.line_id)
    speakers = {rec.canonical_speaker for rec in lines}
    rows = [row for row in relationship_sheet().get("relationships", []) if row["speaker"] in speakers]
    body = {
        "batch": batch,
        "register_standard": register_standard(),
        "relationship_rows": rows,
        "chain_instruction": (
            "Lines sharing a chain id are one English sentence cut in two for timing. Translate the "
            "combined sentence as one natural Telugu sentence, then split it into the same number of parts "
            "in the given order, so the meaning of the whole survives."
        ) if chains else None,
        "chains": chains or None,
        "items": items,
    }
    return json.dumps(body, ensure_ascii=False, indent=1)


def translate(lines: list[DialogueLine], cfg: dict, model: str | None, out_path: Path, phase: str,
              max_lines: int | None, seed=None, reuse: bool = True) -> dict:
    log = RunLog(phase, pricing=cfg.get("pricing", {}) or {})
    llm = LLM(cfg, log, model=model, reuse=reuse)
    batches = scene_batches(lines, max_lines or int(cfg.get("batching", {}).get("max_lines_per_request", 14)))
    system = build_system(cfg)
    rows: list[dict] = []
    errors: list[dict] = []
    for batch, chunk in batches:
        user = build_user(batch, chunk, cfg)
        try:
            data = llm.ask_json(system, user, kind="first_pass", batch=batch)
            covered = require_coverage("first_pass", data, chunk)
        except LLMError as exc:
            errors.append({"batch": batch, "error": str(exc), "lines": [r.line_id for r in chunk],
                           "note": "these lines have no Telugu; the run is not padded with guesses"})
            continue
        for rec, row in zip(chunk, covered):
            text = str(row.get("telugu", "")).strip()
            rows.append({
                "line_id": rec.line_id,
                "telugu": text,
                "script_detected": script_name(text),
                "is_telugu": has_telugu(text),
                "slot_seconds": rec.tight_window,
                "english": rec.text,
            })
    provenance = {
        "method": "api",
        "provider_base_url": cfg["provider"].get("base_url"),
        "model": llm.model,
        "temperature": cfg["provider"].get("temperature"),
        "generated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "sample_seed": seed,
        "measured": True,
        "note": "machine first pass - stand-in, not a human localization",
    }
    payload = {
        "provenance": provenance,
        "lines": rows,
        "errors": errors,
        "coverage": {"requested": len(lines), "returned": len(rows),
                     "not_telugu_script": [r["line_id"] for r in rows if not r["is_telugu"]]},
        "run_log": log.totals(),
    }
    write_payload(payload, out_path)
    log.save_summary()
    return payload


def import_external(path: Path, lines: list[DialogueLine], out_path: Path, note: str) -> dict:
    raw = json.loads(path.read_text(encoding="utf-8"))
    items = raw.get("lines") if isinstance(raw, dict) else raw
    by_id = {}
    for item in items or []:
        if isinstance(item, dict) and item.get("line_id"):
            by_id[str(item["line_id"])] = str(item.get("telugu", "")).strip()
    rows = []
    for rec in lines:
        text = by_id.get(rec.line_id, "")
        rows.append({"line_id": rec.line_id, "telugu": text, "script_detected": script_name(text),
                     "is_telugu": has_telugu(text), "slot_seconds": rec.tight_window, "english": rec.text})
    payload = {
        "provenance": {
            "method": "imported",
            "source_file": path.name,
            "generated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "measured": False,
            "request_count": None,
            "tokens": None,
            "cost_usd": None,
            "note": note or "produced outside this script, so no token or cost figures are claimed",
        },
        "lines": rows,
        "errors": [],
        "coverage": {"requested": len(lines), "returned": sum(1 for r in rows if r["telugu"]),
                     "missing": [r["line_id"] for r in rows if not r["telugu"]],
                     "not_telugu_script": [r["line_id"] for r in rows if r["telugu"] and not r["is_telugu"]]},
        "run_log": {"requests_total": 0, "note": "no API call was made by this script"},
    }
    write_payload(payload, out_path)
    return payload


def main() -> int:
    force_utf8()
    ap = argparse.ArgumentParser()
    ap.add_argument("--telugu-file", default=None, help="use a specific first-pass file as the input lines")
    ap.add_argument("--model", default=None)
    ap.add_argument("--out", default=str(ROOT / "data" / "telugu" / "first_pass.json"))
    ap.add_argument("--compare", action="store_true", help="run config provider plus first_pass.comparison_model")
    ap.add_argument("--from-file", default=None, help="import Telugu produced outside this script")
    ap.add_argument("--provenance-note", default="")
    ap.add_argument("--max-lines-per-request", type=int, default=None)
    ap.add_argument("--config", default=None)
    ap.add_argument("--fresh", action="store_true",
                    help="pay for every scene again instead of reusing the calls already logged for this phase")
    args = ap.parse_args()

    cfg = config_mod.load(args.config)
    lines, meta = sample_lines(args.telugu_file)
    print(f"sample: {len(lines)} lines, selection seed {meta.get('seed')}")

    if args.from_file:
        payload = import_external(Path(args.from_file), lines, Path(args.out), args.provenance_note)
        cov = payload["coverage"]
        print(f"imported {cov['returned']}/{cov['requested']} lines -> {args.out}")
        if cov["missing"]:
            print(f"  missing line_ids: {cov['missing'][:12]}")
        if cov["not_telugu_script"]:
            print(f"  not in Telugu script: {cov['not_telugu_script'][:12]}")
        return 0

    results = []
    out1 = Path(args.out)
    try:
        results.append((cfg["provider"].get("model"), translate(lines, cfg, args.model, out1, "first_pass",
                                                                args.max_lines_per_request, meta.get("seed"),
                                                                reuse=not args.fresh)))
    except Exception as exc:  # noqa: BLE001
        print(f"first pass failed: {exc}", file=sys.stderr)
        return 2

    comparison = cfg.get("telugu", {}).get("comparison_model") or (cfg.get("first_pass", {}).get("comparison_model"))
    if args.compare and comparison:
        alt = out1.with_name(out1.stem + "_alt.json")
        cfg2 = json.loads(json.dumps(cfg))
        cfg2["provider"]["model"] = comparison
        results.append((comparison, translate(lines, cfg2, None, alt, "first_pass_alt",
                                              args.max_lines_per_request, meta.get("seed"))))
        print(f"second model written to {alt}")
    elif args.compare:
        print("--compare asked for but telugu.comparison_model is not set in config.yaml; ran one model only")

    for model, payload in results:
        cov = payload["coverage"]
        logt = payload["run_log"]
        print(f"model={model} lines={cov['returned']}/{cov['requested']} requests={logt['requests_total']} "
              f"prompt_tokens={logt['prompt_tokens']} completion_tokens={logt['completion_tokens']} "
              f"cost_usd={logt['cost_usd']}")
        if payload["errors"]:
            print(f"  batches with no usable output: {len(payload['errors'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
