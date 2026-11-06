"""Flag objects shared by every check.

A flag is a row in the report. Nothing here stores numeric model confidence, because the
product rule is that the tool never claims a number for Telugu correctness (PRD §8).
"""

from __future__ import annotations

SEVERITIES = ("high", "medium", "low", "info")
CHECKS = ("meaning", "relationship", "timing", "naturalness", "script", "baseline")
STATUS_ORDER = {"high": 3, "medium": 2, "low": 1, "info": 0}


class FlagError(ValueError):
    pass


def make_flag(*, line_id: str, check: str, severity: str, verdict: str, evidence: str,
              suggestion: str = "", status: str = "pending", note: str = "") -> dict:
    if check not in CHECKS:
        raise FlagError(f"unknown check {check!r}")
    if severity not in SEVERITIES:
        severity = "low"
    if not line_id:
        raise FlagError("a flag needs a line_id")
    return {
        "line_id": line_id,
        "check": check,
        "severity": severity,
        "verdict": verdict,
        "evidence": evidence,
        "suggestion": suggestion,
        "status": status,
        "note": note,
    }


def severity_rank(flag: dict) -> int:
    return STATUS_ORDER.get(flag.get("severity", "low"), 0)


def group_by_line(flags: list[dict]) -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = {}
    for flag in flags:
        out.setdefault(flag["line_id"], []).append(flag)
    return out


def flagged_ids(flags: list[dict]) -> set[str]:
    return {f["line_id"] for f in flags}


LLM_CHECKS = ("meaning", "relationship", "naturalness")


def is_not_judged(row: dict) -> bool:
    """A row the model returned but could not classify: a gap in coverage, never a clean line.

    `unknown` is the relationship prompt's honest I-cannot-tell; a blank is a refusal that did not
    even say so; `outside_enum:` is a verdict the prompt never offered, so it cannot be trusted as
    either a finding or a clearance.
    """
    verdict = str(row.get("verdict", "")).strip().lower()
    return verdict in ("", "blank", "unknown") or verdict.startswith("outside_enum:")
