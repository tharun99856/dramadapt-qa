"""Check 4 - cultural naturalness. Advisory only, never a score (PRD §7.3)."""

from __future__ import annotations

from ..flags import make_flag
from ..llm import LLM, LLMError
from ..parser import DialogueLine
from ..prompting import NO_SCORE, require_coverage, require_llm, scene_payload

SYSTEM = (
    "You are a Telugu dialogue editor reading a period microdrama localization meant for "
    "dubbing. For every line decide whether a Telugu listener would hear it as something a "
    "person would actually say in that situation, at that register. Verdicts: natural, "
    "possibly_unnatural. Use possibly_unnatural when the phrasing is stiff, translated-feeling, "
    "idiom-by-idiom, or mixes registers inside one sentence - and say which. When genuinely "
    "unsure, say possibly_unnatural and say a human should review it. Never label a line wrong "
    "on cultural grounds without a reason a reviewer can check. " + NO_SCORE +
    ' Reply JSON only: {"lines":[{"line_id":"","verdict":"","note":""}]}. '
    "Every input line_id must appear exactly once."
)


def run(llm: LLM | None, batches: list[tuple[str, list[DialogueLine]]], register_standard: str = "") -> tuple[list[dict], list[dict], list[dict]]:
    llm = require_llm(llm, "naturalness")
    flags: list[dict] = []
    verdicts: list[dict] = []
    failed: list[dict] = []
    for batch, lines in batches:
        payload = scene_payload(batch, lines, extra={"register_standard": register_standard} if register_standard else None)
        try:
            data = llm.ask_json(SYSTEM, payload, kind="naturalness", batch=batch)
            rows = require_coverage("naturalness", data, lines)
        except LLMError as exc:
            failed.append({"batch": batch, "lines": [r.line_id for r in lines], "error": str(exc)})
            continue
        for rec, row in zip(lines, rows):
            verdict = str(row.get("verdict", "")).strip().lower()
            verdicts.append({"line_id": rec.line_id, "verdict": verdict or "blank",
                             "note": row.get("note", "")})
            if verdict == "natural":
                continue
            if not verdict:
                continue  # the model returned the row but said nothing: a line not judged
            flags.append(
                make_flag(
                    line_id=rec.line_id,
                    check="naturalness",
                    severity="low",
                    verdict="possibly_unnatural",
                    evidence=str(row.get("note", "") or "the model hesitated on this line"),
                    suggestion="",
                    note="advisory only, low confidence: human review recommended",
                )
            )
    return flags, verdicts, failed
