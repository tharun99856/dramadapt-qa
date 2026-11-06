"""Check 2 - relationship and address. Rules narrow it down, the model judges the Telugu.

No find-and-replace on Telugu honorifics: the rules only work on the English side and only
to decide which lines are worth asking about.
"""

from __future__ import annotations

import json

from ..corpus import address_terms_in, relationship_sheet
from ..flags import make_flag
from ..llm import LLM, LLMError
from ..parser import DialogueLine
from ..prompting import NO_SCORE, require_coverage, require_llm, scene_payload

SYSTEM = (
    "You are checking whether a Telugu microdrama localization keeps relationships intact. "
    "For every line, judge the Telugu against the relationship sheet: the expected register "
    "between these two people, the forms of address the English uses, the delivery tag, and "
    "what the same speaker said to the same listener earlier in the scene. Verdicts: "
    "consistent, too_formal, too_informal, honorific_dropped, address_mismatch, unknown. "
    "too_formal or too_informal means the Telugu verb endings and pronouns do not match the "
    "relationship. honorific_dropped means the English marked respect and the Telugu lost it. "
    "address_mismatch means the Telugu uses a name or title the sheet does not predict. A "
    "shift that the sheet itself predicts at this moment is consistent - say so in the note. "
    + NO_SCORE +
    ' Reply JSON only: {"lines":[{"line_id":"","verdict":"","evidence":"","suggestion":""}]}. '
    "Every input line_id must appear exactly once."
)

BAD = {"too_formal": "medium", "too_informal": "medium", "honorific_dropped": "medium", "address_mismatch": "high"}


def rows_for(speaker: str) -> list[dict]:
    return [row for row in relationship_sheet().get("relationships", []) if row["speaker"] == speaker]


def best_row(rec: DialogueLine) -> dict | None:
    rows = rows_for(rec.canonical_speaker)
    if not rows:
        return None
    for row in rows:
        head = row["listener"].split(" (")[0].lower()
        if head and head.split()[0] in rec.text.lower():
            return row
    return rows[0]


def rule_candidates(lines: list[DialogueLine]) -> dict[str, list[str]]:
    """English-side hints: which used address terms the sheet does not predict for this pair."""
    out: dict[str, list[str]] = {}
    lowered_sheet_terms = {
        term.lower()
        for row in relationship_sheet().get("relationships", [])
        for term in (row.get("expected_address_terms") or [])
    }
    for rec in lines:
        row = best_row(rec)
        if row is None:
            out.setdefault(rec.line_id, []).append("no relationship-sheet row for this speaker")
            continue
        expected = {t.lower() for t in (row.get("expected_address_terms") or [])}
        predicted = {m.lower() for m in _shift_markers(rec)}
        for term in address_terms_in(rec.text):
            t = term.lower()
            if t in expected or t in predicted:
                continue
            if any(t in other for other in lowered_sheet_terms):
                out.setdefault(rec.line_id, []).append(f"'{term}' belongs to another relationship on the sheet")
            else:
                out.setdefault(rec.line_id, []).append(f"'{term}' is not predicted for {row['listener']}")
    return out


def _shift_markers(rec: DialogueLine) -> list[str]:
    terms = []
    for row in rows_for(rec.canonical_speaker):
        for shift in row.get("address_shifts", []) or []:
            marker = (shift.get("text_marker") or "").lower()
            if marker and marker in rec.text.lower():
                terms.extend(t.lower() for t in marker.split())
    return terms


def earlier_context(rec: DialogueLine, all_lines: list[DialogueLine]) -> list[str]:
    """The speaker's own recent lines, so a register drift inside one scene is visible."""
    out = []
    for other in all_lines:
        if other.episode != rec.episode or other.start >= rec.start:
            continue
        if other.canonical_speaker != rec.canonical_speaker:
            continue
        out.append(f"{other.line_id}: EN {other.text} / TE {other.telugu}")
    return out[-3:]


def run(llm: LLM | None, batches: list[tuple[str, list[DialogueLine]]], all_lines: list[DialogueLine],
        register_standard: str = "") -> tuple[list[dict], list[dict], list[dict]]:
    llm = require_llm(llm, "relationship")
    flags: list[dict] = []
    verdicts: list[dict] = []
    failed: list[dict] = []
    for batch, lines in batches:
        # One sheet row per line, guessed by best_row: a screenplay block never records who is being
        # addressed, so this is a guess and the model is told so. Widening it to every row for the
        # speakers in the scene was measured as unaffordable on the daily token budget, so the
        # artifact below and this prompt still agree with each other.
        sheet_rows = []
        for rec in lines:
            row = best_row(rec)
            if row and row not in sheet_rows:
                sheet_rows.append(row)
        candidates = rule_candidates(lines)
        history = {}
        for rec in lines:
            hist = earlier_context(rec, all_lines)
            if hist:
                history[rec.line_id] = hist
        payload = scene_payload(
            batch,
            lines,
            extra={
                "relationship_sheet": json.dumps(sheet_rows, ensure_ascii=False),
                "english_side_rule_hints": json.dumps(candidates, ensure_ascii=False),
                "speaker_history": json.dumps(history, ensure_ascii=False),
                "register_standard": register_standard,
            },
        )
        try:
            data = llm.ask_json(SYSTEM, payload, kind="relationship", batch=batch)
            rows = require_coverage("relationship", data, lines)
        except LLMError as exc:
            failed.append({"batch": batch, "lines": [r.line_id for r in lines], "error": str(exc)})
            continue
        for rec, row in zip(lines, rows):
            verdict = str(row.get("verdict", "")).strip().lower()
            verdicts.append({"line_id": rec.line_id, "verdict": verdict or "blank",
                             "evidence": row.get("evidence", "")})
            if verdict == "consistent":
                continue
            if verdict in ("unknown", "blank", ""):
                # The sheet has no row for this pair, or the addressee is not identifiable from
                # the line. That is a gap in what we can check, not a defect in the translation,
                # so it is recorded as a line not judged instead of being padded into the flags.
                continue
            severity = BAD.get(verdict, "low")
            hint = "; ".join(candidates.get(rec.line_id, []))
            flags.append(
                make_flag(
                    line_id=rec.line_id,
                    check="relationship",
                    severity=severity,
                    verdict=verdict if verdict in BAD else f"outside_enum:{verdict}",
                    evidence=str(row.get("evidence", "") or "") + (f" | rules: {hint}" if hint else ""),
                    suggestion=str(row.get("suggestion", "") or ""),
                    note="medium confidence, sheet plus model judgement",
                )
            )
    return flags, verdicts, failed
