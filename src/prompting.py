"""Prompt building and response validation shared by the three LLM checks."""

from __future__ import annotations

import json

from .config import ConfigError
from .llm import LLM, LLMError
from .parser import DialogueLine

NO_SCORE = "Never output a numeric score, percentage or confidence value."


def item(rec: DialogueLine, *, include_telugu: bool = True) -> dict:
    out = {
        "line_id": rec.line_id,
        "speaker": rec.canonical_speaker,
        "label_as_written": rec.speaker_label,
        "emotion_or_delivery": rec.delivery_tag,
        "english": rec.text,
        "tight_slot_seconds": rec.tight_window,
        "flags": ";".join(rec.flags),
    }
    if include_telugu:
        out["telugu"] = rec.telugu
    return out


def scene_payload(batch: str, lines: list[DialogueLine], *, extra: dict | None = None) -> str:
    body = {"batch": batch, "items": [item(rec) for rec in lines]}
    chain_groups: dict[str, list[str]] = {}
    for rec in lines:
        if rec.chain_id:
            chain_groups.setdefault(rec.chain_id, []).append(rec.line_id)
    if chain_groups:
        body["split_sentence_chains"] = chain_groups
        body["chain_note"] = (
            "Lines inside one chain are a single sentence that was cut in two for timing. "
            "Judge the chain as one utterance: Telugu is verb-final."
        )
    if extra:
        body.update(extra)
    return json.dumps(body, ensure_ascii=False, indent=1)


def require_coverage(kind: str, data: dict, lines: list[DialogueLine]) -> list[dict]:
    """Every requested line must come back. A short answer is an error, not a clean pass."""
    rows = data.get("lines") or data.get("items") or data.get("results")
    if not isinstance(rows, list):
        raise LLMError(f"{kind}: response has no 'lines' array")
    seen: dict[str, dict] = {}
    for row in rows:
        if isinstance(row, dict) and row.get("line_id"):
            seen[str(row["line_id"])] = row
    missing = [rec.line_id for rec in lines if rec.line_id not in seen]
    if missing:
        raise LLMError(f"{kind}: model skipped {len(missing)} lines: {missing[:8]}")
    return [seen[rec.line_id] for rec in lines]


def require_llm(llm: LLM | None, check: str) -> LLM:
    if llm is None:
        raise ConfigError(f"{check} needs a model: set the API key in the environment and re-run")
    return llm
