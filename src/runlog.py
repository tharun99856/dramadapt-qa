"""Run log: measured request counts, token usage and cost, plus the raw prompt/response archive.

PRD §8 makes this file the source of the cost figures in the doc. Anything not measured by
an actual API call is written with measured=false and an explanation, never as a number.
"""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class RunLog:
    def __init__(self, phase: str, out_dir: Path | None = None, pricing: dict | None = None):
        self.phase = phase
        self.dir = Path(out_dir) if out_dir else ROOT / "results"
        self.dir.mkdir(parents=True, exist_ok=True)
        self.calls_path = self.dir / f"{phase}_calls.jsonl"
        self.pricing = pricing or {}
        self.entries: list[dict] = []
        if self.calls_path.exists():
            for line in self.calls_path.read_text(encoding="utf-8").splitlines():
                try:
                    self.entries.append(json.loads(line))
                except json.JSONDecodeError:
                    continue

    def record(self, *, kind: str, batch: str, model: str, prompt: dict, response_text: str,
               usage: dict | None = None, measured: bool = True, note: str = "", error: str | None = None) -> dict:
        usage = usage or {}
        prompt_tokens = int(usage.get("prompt_tokens") or 0)
        completion_tokens = int(usage.get("completion_tokens") or 0)
        price_in = self.pricing.get("usd_per_million_prompt")
        price_out = self.pricing.get("usd_per_million_completion")
        cost = None
        if measured and price_in is not None and price_out is not None:
            cost = round((prompt_tokens / 1e6) * float(price_in) + (completion_tokens / 1e6) * float(price_out), 6)
        entry = {
            "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "phase": self.phase,
            "kind": kind,
            "batch": batch,
            "model": model,
            "measured": measured,
            "prompt_tokens": prompt_tokens if measured else None,
            "completion_tokens": completion_tokens if measured else None,
            "cost_usd": cost,
            "system": prompt.get("system", ""),
            "user": prompt.get("user", ""),
            "response": response_text,
            "error": error,
            "note": note,
        }
        self.entries.append(entry)
        with self.calls_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
        return entry

    def totals(self) -> dict:
        measured = [e for e in self.entries if e.get("measured")]
        priced = [e for e in self.entries if e.get("cost_usd") is not None]
        by_kind: dict[str, int] = {}
        for e in self.entries:
            by_kind[e["kind"]] = by_kind.get(e["kind"], 0) + 1
        return {
            "requests_total": len(self.entries),
            "requests_measured": len(measured),
            "requests_unmeasured_provenance": len(self.entries) - len(measured),
            "by_kind": by_kind,
            "prompt_tokens": sum(e["prompt_tokens"] or 0 for e in measured),
            "completion_tokens": sum(e["completion_tokens"] or 0 for e in measured),
            "cost_usd": round(sum(e["cost_usd"] or 0 for e in priced), 6) if priced else None,
            "priced": bool(priced),
            "models": sorted({e["model"] for e in self.entries}),
        }

    def save_summary(self) -> Path:
        path = self.dir / "run_log.json"
        payload = {}
        if path.exists():
            payload = json.loads(path.read_text(encoding="utf-8"))
        payload[self.phase] = self.totals()
        payload["_updated"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
        payload["_aggregate"] = _aggregate(payload)
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        return path


def _aggregate(payload: dict) -> dict:
    phases = {k: v for k, v in payload.items() if not k.startswith("_")}
    return {
        "requests_total": sum(v.get("requests_total", 0) for v in phases.values()),
        "prompt_tokens": sum(v.get("prompt_tokens", 0) for v in phases.values()),
        "completion_tokens": sum(v.get("completion_tokens", 0) for v in phases.values()),
        "cost_usd": (
            round(sum(v.get("cost_usd") or 0 for v in phases.values()), 6)
            if any(v.get("cost_usd") is not None for v in phases.values())
            else None
        ),
    }


def started() -> float:
    return time.time()
