"""Runs the checks over a set of lines and writes the artifacts Phase 0 and the demo need."""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path

from . import config as config_mod
from .batching import scene_batches
from .checks import baseline as baseline_check
from .checks import meaning, naturalness, relationship, timing
from .checks import script as script_check
from .flags import is_not_judged
from .llm import LLM, LLMError
from .parser import DialogueLine
from .runlog import RunLog
from .sample import load_sample

ROOT = Path(__file__).resolve().parents[1]
ALL_CHECKS = ("meaning", "relationship", "timing", "naturalness", "script")


def register_standard() -> str:
    sheet = relationship.relationship_sheet()
    block = sheet.get("telugu_register_standard", {}) or {}
    text = " ".join(str(block.get("draft_paragraph", "")).split())
    status = block.get("status", "UNDOCUMENTED")
    return f"[{status}] {block.get('decision', '')} {text}".strip()


def _absorb(check: str, found: list[dict], rows: list[dict], failed: list[dict],
            batches: list, verdicts: dict, summaries: dict, flags: list[dict], errors: list[dict],
            confidence_note: str) -> None:
    """Keep the batches that answered even when a later one is refused, and name the lines not judged."""
    not_judged = [r["line_id"] for r in rows if is_not_judged(r)]
    verdicts[check] = rows
    summaries[check] = {
        "batches_requested": len(batches),
        "batches_completed": len(batches) - len(failed),
        "lines_judged": len(rows),
        "lines_not_judged": len(not_judged),
        "not_judged_line_ids": not_judged,
        "confidence": confidence_note,
        "failed_batches": failed,
    }
    flags.extend(found)
    if not failed:
        return
    missed = sorted({lid for b in failed for lid in b["lines"]})
    if rows:
        errors.append({"check": check, "partial": True,
                       "error": f"{len(failed)} of {len(batches)} batches refused; {len(rows)} lines "
                                f"judged, {len(missed)} not",
                       "lines_affected": len(missed),
                       "note": "the flags below cover only the batches that answered"})
    else:
        errors.append({"check": check, "error": failed[0]["error"], "lines_affected": len(missed),
                       "note": "this check produced no flags; it is recorded as failed, not as clean"})


def run_structured(lines: list[DialogueLine], checks=ALL_CHECKS, *, cfg_path=None, model: str | None = None,
                   max_lines_per_request: int | None = None, phase: str = "structured",
                   rate_override: float | None = None, reuse: bool = True) -> dict:
    cfg = config_mod.load(cfg_path)
    pricing = cfg.get("pricing", {}) or {}
    log = RunLog(phase, pricing=pricing)
    per_request, token_cap = config_mod.batch_caps(cfg)
    per_request = max_lines_per_request or per_request
    batches = scene_batches(lines, per_request, token_cap)
    llm = LLM(cfg, log, model=model, reuse=reuse) if set(checks) - {"timing", "script"} else None
    margin = float(cfg["telugu"].get("over_tight_margin", 0.15))
    rate = rate_override or config_mod.syllables_per_second(cfg)

    started = time.time()
    flags: list[dict] = []
    verdicts: dict[str, list] = {}
    summaries: dict[str, dict] = {}
    errors: list[dict] = []

    for check in checks:
        try:
            if check == "timing":
                if not rate:
                    raise RuntimeError(
                        "Telugu speaking rate is not calibrated: run scripts/calibrate_rate.py "
                        "or pass --syllables-per-second. The timing check refuses to guess."
                    )
                found, table, tsum = timing.run(lines, float(rate), margin)
                tsum["rate_source"] = ("override passed on the command line - not calibrated"
                                       if rate_override else "data/calibration.json")
                verdicts["timing"] = table
                summaries["timing"] = tsum
                flags.extend(found)
            elif check == "script":
                found, table, ssum = script_check.run(lines)
                verdicts["script"] = table
                summaries["script"] = ssum
                flags.extend(found)
            elif check == "meaning":
                found, rows, failed = meaning.run(llm, batches, register_standard())
                _absorb(check, found, rows, failed, batches, verdicts, summaries, flags, errors,
                        "medium confidence, model judgement")
            elif check == "relationship":
                found, rows, failed = relationship.run(llm, batches, lines, register_standard())
                _absorb(check, found, rows, failed, batches, verdicts, summaries, flags, errors,
                        "sheet plus model judgement")
            elif check == "naturalness":
                found, rows, failed = naturalness.run(llm, batches, register_standard())
                _absorb(check, found, rows, failed, batches, verdicts, summaries, flags, errors,
                        "advisory, low confidence")
            else:
                raise RuntimeError(f"unknown check {check!r}")
        except (LLMError, RuntimeError) as exc:
            errors.append({"check": check, "error": str(exc), "lines_affected": len(lines),
                           "note": "this check produced no flags; it is recorded as failed, not as clean"})

    out = {
        "phase": phase,
        "generated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "model": llm.model if llm else None,
        "checks_run": list(checks),
        "requests_per_batch_target": per_request,
        "batches": [{"batch": b, "lines": [r.line_id for r in l]} for b, l in batches],
        "flags": flags,
        "verdicts": verdicts,
        "summaries": summaries,
        "errors": errors,
        # batches answered by an earlier, already-counted request to the identical prompt: the
        # tokens are in run_log once, and these requests spent nothing extra
        "reused_requests": llm.reused if llm else 0,
        "meta": {"lines": len(lines), "elapsed_seconds": round(time.time() - started, 2)},
    }
    out["run_log"] = log.totals()
    log.save_summary()
    return out


def run_baseline_control(lines: list[DialogueLine], *, cfg_path=None, model: str | None = None,
                         max_lines_per_request: int | None = None) -> dict:
    cfg = config_mod.load(cfg_path)
    log = RunLog("baseline", pricing=cfg.get("pricing", {}) or {})
    per_request = max_lines_per_request or int(cfg.get("batching", {}).get("max_lines_per_request", 14))
    batches = scene_batches(lines, per_request)
    llm = LLM(cfg, log, model=model)
    started = time.time()
    errors: list[dict] = []
    try:
        flags, stats = baseline_check.run(llm, batches)
    except (LLMError, RuntimeError) as exc:
        flags = []
        stats = {}
        errors.append({"check": "baseline", "error": str(exc), "lines_affected": len(lines)})
    out = {
        "phase": "baseline",
        "generated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "model": llm.model,
        "batches": [{"batch": b, "lines": [r.line_id for r in l]} for b, l in batches],
        "flags": flags,
        "stats": stats,
        "errors": errors,
        "meta": {"lines": len(lines), "elapsed_seconds": round(time.time() - started, 2)},
    }
    out["run_log"] = log.totals()
    log.save_summary()
    return out


def sample_lines(telugu_file: Path | str | None = None) -> tuple[list[DialogueLine], dict]:
    lines, meta = load_sample(Path(telugu_file) if telugu_file else None)
    return lines, meta


def write_payload(payload: dict, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return path
