"""The generic control used in Phase 0 Step C: one prompt, no sheets, no windows, no structure.

This is deliberately not DramAdapt. It is what a person gets from "is this translation
accurate and natural? list the problems".
"""

from __future__ import annotations

import json

from ..flags import make_flag
from ..llm import LLM
from ..parser import DialogueLine
from ..prompting import require_llm

SYSTEM = (
    "You are reviewing an English to Telugu translation of a microdrama scene. Is the "
    "translation accurate and natural? List the problems you find. For each one give the "
    "line_id and say what is wrong. If a line is fine, do not mention it. "
    'Reply JSON only: {"problems":[{"line_id":"","issue":""}]}'
)


def payload(batch: str, lines: list[DialogueLine]) -> str:
    return json.dumps(
        {
            "batch": batch,
            "lines": [{"line_id": rec.line_id, "speaker": rec.canonical_speaker,
                       "english": rec.text, "telugu": rec.telugu} for rec in lines],
        },
        ensure_ascii=False,
        indent=1,
    )


def run(llm: LLM | None, batches: list[tuple[str, list[DialogueLine]]]) -> tuple[list[dict], dict]:
    llm = require_llm(llm, "baseline")
    flags: list[dict] = []
    known = {rec.line_id for _, lines in batches for rec in lines}
    raw_problems: list[dict] = []
    empty_batches = 0
    for batch, lines in batches:
        data = llm.ask_json(SYSTEM, payload(batch, lines), kind="baseline", batch=batch)
        problems = data.get("problems")
        if not isinstance(problems, list):
            problems = []
        if not problems:
            empty_batches += 1
        for item in problems:
            if not isinstance(item, dict):
                continue
            line_id = str(item.get("line_id", "")).strip()
            if line_id not in known:
                # the model invented an id: keep it visible instead of dropping it
                raw_problems.append({"line_id": line_id, "issue": item.get("issue", ""), "hallucinated_id": True})
                continue
            raw_problems.append({"line_id": line_id, "issue": item.get("issue", ""), "hallucinated_id": False})
            flags.append(
                make_flag(
                    line_id=line_id,
                    check="baseline",
                    severity="medium",
                    verdict="reported_problem",
                    evidence=str(item.get("issue", "")),
                    suggestion="",
                    note="generic single-prompt QA, Phase 0 control only",
                )
            )
    stats = {"batches": len(batches), "batches_with_no_problems": empty_batches,
             "problems_reported": len(raw_problems), "unknown_ids": sum(1 for r in raw_problems if r["hallucinated_id"])}
    return flags, {"raw_problems": raw_problems, **stats}
