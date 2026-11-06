"""Check 1 - meaning preservation. One request per scene, verdict per line."""

from __future__ import annotations

from ..flags import make_flag
from ..llm import LLM, LLMError
from ..parser import DialogueLine
from ..prompting import NO_SCORE, require_coverage, require_llm, scene_payload

SYSTEM = (
    "You are a bilingual (English to Telugu) script supervisor checking a microdrama "
    "localization before dubbing. For every item, compare the English line with the Telugu "
    "line using the speaker, the delivery tag and the action context. Decide whether the "
    "meaning survived. Verdicts, exactly one per line: same, weakened, strengthened, reversed, "
    "missing. Weakened means the force dropped (a threat becomes a request). Strengthened means "
    "it rose. Reversed means the polarity or the actor changed. Missing means the Telugu does "
    "not carry the content at all. For any verdict other than same, give a one-line reason and, "
    "when you can, a corrected Telugu line. " + NO_SCORE +
    ' Reply JSON only: {"lines":[{"line_id":"","verdict":"","reason":"","suggestion":""}]}. '
    "Every input line_id must appear exactly once."
)


def run(llm: LLM | None, batches: list[tuple[str, list[DialogueLine]]], register_standard: str = "") -> tuple[list[dict], list[dict], list[dict]]:
    llm = require_llm(llm, "meaning")
    flags: list[dict] = []
    verdicts: list[dict] = []
    failed: list[dict] = []
    severity = {"reversed": "high", "missing": "high", "strengthened": "medium", "weakened": "medium"}
    for batch, lines in batches:
        payload = scene_payload(batch, lines, extra={"register_standard": register_standard} if register_standard else None)
        try:
            data = llm.ask_json(SYSTEM, payload, kind="meaning", batch=batch)
            rows = require_coverage("meaning", data, lines)
        except LLMError as exc:
            # a refused batch must not throw away the batches that already answered
            failed.append({"batch": batch, "lines": [r.line_id for r in lines], "error": str(exc)})
            continue
        for rec, row in zip(lines, rows):
            verdict = str(row.get("verdict", "")).strip().lower()
            if not verdict:
                # the model returned the line but declined to classify it: a line not judged,
                # not a clean line and not a finding
                verdicts.append({"line_id": rec.line_id, "verdict": "blank"})
                continue
            if verdict not in severity and verdict != "same":
                # unrecognised verdict is kept visible, not quietly treated as clean
                verdict = f"outside_enum:{verdict}"
            verdicts.append({"line_id": rec.line_id, "verdict": verdict, "reason": row.get("reason", "")})
            if verdict == "same":
                continue
            flags.append(
                make_flag(
                    line_id=rec.line_id,
                    check="meaning",
                    severity=severity.get(verdict, "medium"),
                    verdict=verdict,
                    evidence=f"English: {rec.text} / Telugu: {rec.telugu} / reason: {row.get('reason', '')}",
                    suggestion=str(row.get("suggestion", "") or ""),
                    note="medium confidence, model judgement",
                )
            )
    return flags, verdicts, failed
