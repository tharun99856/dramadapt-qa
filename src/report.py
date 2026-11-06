"""Report assembly: stable flag ids, editor decisions, JSON run artifact, Markdown report."""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path

from .flags import LLM_CHECKS, is_not_judged
from .parser import DialogueLine

ROOT = Path(__file__).resolve().parents[1]
DECISIONS = ROOT / "data" / "annotation" / "decisions.csv"

FLAG_COLUMNS = ["flag_id", "line_id", "episode", "speaker", "check", "severity", "verdict", "english",
                "telugu", "slot_seconds", "evidence", "suggestion", "note", "status", "edited_suggestion",
                "editor_action_ts"]


def flag_id(flag: dict) -> str:
    base = f"{flag['line_id']}_{flag['check']}"
    # timing can raise two flags on one line - its own slot and the chain it belongs to -
    # so its ids carry the verdict. The other checks produce at most one verdict per line.
    return f"{base}_{flag['verdict']}" if flag["check"] == "timing" else base


def with_ids(flags: list[dict]) -> list[dict]:
    out = []
    # sorting by check only: sorted() is stable, so a check that returns its flags worst-first
    # (timing does) keeps that order for the editor
    for flag in sorted(flags, key=lambda f: f["check"]):
        row = dict(flag)
        row["flag_id"] = flag_id(flag)
        row.setdefault("status", "pending")
        out.append(row)
    return out


def load_decisions(path: Path | None = None) -> dict[str, dict]:
    p = Path(path) if path else DECISIONS
    if not p.exists():
        return {}
    out: dict[str, dict] = {}
    with p.open(encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            if row.get("flag_id"):
                out[row["flag_id"]] = row
    return out


def apply_decisions(flags: list[dict], decisions: dict[str, dict]) -> list[dict]:
    out = []
    for flag in flags:
        row = dict(flag)
        decision = decisions.get(row["flag_id"])
        if decision:
            row["status"] = decision.get("status") or row["status"]
            if decision.get("edited_suggestion"):
                row["suggestion"] = decision["edited_suggestion"]
                row["edited"] = True
            row["editor_action_ts"] = decision.get("editor_action_ts") or decision.get("timestamp", "")
        out.append(row)
    return out


def empty_decisions_sheet(flags: list[dict], by_id: dict[str, DialogueLine], path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=FLAG_COLUMNS)
        writer.writeheader()
        for flag in flags:
            rec = by_id.get(flag["line_id"])
            writer.writerow({
                "flag_id": flag["flag_id"],
                "line_id": flag["line_id"],
                "episode": getattr(rec, "episode", ""),
                "speaker": getattr(rec, "canonical_speaker", ""),
                "check": flag["check"],
                "severity": flag["severity"],
                "verdict": flag["verdict"],
                "english": getattr(rec, "text", ""),
                "telugu": getattr(rec, "telugu", ""),
                "slot_seconds": getattr(rec, "tight_window", ""),
                "evidence": flag["evidence"],
                "suggestion": flag["suggestion"],
                "note": flag.get("note", ""),
                "status": "pending",
                "edited_suggestion": "",
                "editor_action_ts": "",
            })
    return path


def write_run_json(payload: dict, path: Path) -> Path:
    by_id = {rec["line_id"]: rec for rec in payload.get("lines", [])} if "lines" in payload else {}
    body = {
        "generated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "phase": payload.get("phase"),
        "model": payload.get("model"),
        "source": payload.get("source"),
        "batching": {"batches": len(payload.get("batches", [])), "requests": payload.get("run_log", {}).get("requests_total")},
        "run_log": payload.get("run_log"),
        "errors": payload.get("errors", []),
        "counts": {
            "lines": len(payload.get("lines", [])) or payload.get("meta", {}).get("lines"),
            "flags": len(payload.get("flags", [])),
            "by_check": _by_check(payload.get("flags", [])),
            "by_severity": _by_key(payload.get("flags", []), "severity"),
        },
        "flags": payload.get("flags", []),
        "verdicts": payload.get("verdicts", {}),
        "summaries": payload.get("summaries", {}),
        "stats": payload.get("stats", {}),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(body, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def _by_check(flags: list[dict]) -> dict:
    return _by_key(flags, "check")


def _by_key(flags: list[dict], key: str) -> dict:
    out: dict[str, int] = {}
    for flag in flags:
        out[flag.get(key, "?")] = out.get(flag.get(key, "?"), 0) + 1
    return out


def write_markdown(payload: dict, lines: list[DialogueLine], path: Path) -> Path:
    by_id = {rec.line_id: rec for rec in lines}
    flags = with_ids(payload.get("flags", []))
    flags = apply_decisions(flags, load_decisions())
    flagged = {f["line_id"] for f in flags}
    with_telugu = sum(1 for rec in lines if (rec.telugu or '').strip())
    no_telugu = [rec.line_id for rec in lines if not (rec.telugu or '').strip()]
    failed = sorted({e.get("check", "?") for e in payload.get("errors", []) if not e.get("partial")})
    partial = sorted({e.get("check", "?") for e in payload.get("errors", []) if e.get("partial")})
    ran = payload.get("checks_run")
    n_ran = len(ran) if isinstance(ran, (list, tuple)) else None
    completed = max(n_ran - len(failed) - len(partial), 0) if n_ran is not None else None

    lines_out = [
        f"# DramAdapt QA report - {payload.get('phase')}",
        "",
        f"Generated {datetime.now(timezone.utc).isoformat(timespec='seconds')}. Model: `{payload.get('model')}`.",
        "",
        "## Summary",
        "",
        f"- Lines reviewed: **{len(lines)}**",
        f"- Lines with Telugu attached: **{with_telugu}** of {len(lines)}"
        + ("" if with_telugu == len(lines) else "  *(the rest were not judged - see below)*"),
        f"- Checks completed: " + (
            f"**{completed}** of {n_ran}" + ("" if not failed else f"  *(failed: {', '.join(failed)})*")
            + ("" if not partial else f"  *(partially judged: {', '.join(partial)})*")
            if n_ran is not None else "n/a for this run"),
        f"- Lines flagged: **{len(flagged)}**"
        + ("  *(no check completed - this is not a clean pass)*" if n_ran and completed == 0 else ""),
        f"- Flags by check: " + ", ".join(f"{k}={v}" for k, v in sorted(_by_check(flags).items())),
        f"- Flags by severity: " + ", ".join(f"{k}={v}" for k, v in sorted(_by_key(flags, 'severity').items())),
        _coverage_line(payload),
        _timing_line(payload, len(lines)),
        f"- Requests: {payload.get('run_log', {}).get('requests_total')} for "
        f"{len(payload.get('batches', []))} scene batches "
        f"(prompt tokens {payload.get('run_log', {}).get('prompt_tokens')}, "
        f"completion tokens {payload.get('run_log', {}).get('completion_tokens')}, "
        f"cost {payload.get('run_log', {}).get('cost_usd')})",
        "",
    ]
    if with_telugu < len(lines):
        lines_out += [
            f"**Coverage warning:** {len(lines) - with_telugu} lines have no Telugu text, so no check could run on them. "
            "A missing line is not a clean line.",
            "",
        ]
    if payload.get("errors"):
        lines_out += ["## Checks that did not finish", ""]
        lines_out += [f"- **{e['check']}**{' (partial)' if e.get('partial') else ''}: {e['error']}"
                      for e in payload["errors"]]
        lines_out += ["", "These are failures or gaps, not clean passes. Lines a check never read were not judged.", ""]

    lines_out += [
        "## Flagged lines",
        "",
        "| flag | line | check | severity | verdict | English | Telugu | slot | evidence | suggestion | status |",
        "|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for flag in flags:
        rec = by_id.get(flag["line_id"])
        telugu = rec.telugu if rec else ""
        est = ""
        if rec and rec.telugu and payload.get("verdicts", {}).get("timing"):
            for row in payload["verdicts"]["timing"]:
                if row["line_id"] == rec.line_id:
                    est = f"~{row['estimated_seconds']}s/{row['akshara']}ak"
                    break
        lines_out.append(
            f"| {flag['flag_id']} | {flag['line_id']} | {flag['check']} | {flag['severity']} | {flag['verdict']} | "
            f"{_cell(rec.text if rec else '')} | {_cell(telugu)} {est} | {rec.tight_window if rec else ''} | "
            f"{_cell(flag['evidence'])} | {_cell(flag.get('suggestion', ''))} | {flag['status']} |"
        )
    if not flags:
        lines_out.append("| - | - | - | - | - | no flags | | | | | |")

    gap_ids = sorted({lid for ids in coverage_gaps(payload).values() for lid in ids})
    unread_ids = sorted({lid for s in (payload.get("summaries") or {}).values()
                         for b in (s.get("failed_batches") or []) for lid in b.get("lines", [])})
    parts = []
    if no_telugu:
        what = ("no line in this run has Telugu attached, so nothing was judged on it"
                if len(no_telugu) == len(lines)
                else f"{len(no_telugu)} line(s) had no Telugu text, so the checks that need it skipped them")
        parts.append(what)
    if gap_ids:
        parts.append(f"{len(gap_ids)} line(s) were sent to a model that declined to judge them")
    if unread_ids:
        parts.append(f"{len(unread_ids)} sat in a batch the model never answered")
    coverage_note = (
        "- Absent from the flag list is not the same as cleared: " + "; ".join(parts)
        + ". Check the coverage lines above before reading this as a pass."
        if parts else "- Every line was read by every check that could run on it."
    )
    # A line no check could read belongs under "never judged", not under "not flagged".
    never_judged = set(no_telugu) | set(gap_ids) | set(unread_ids)
    cleared = [rec.line_id for rec in lines if rec.line_id not in flagged and rec.line_id not in never_judged]
    untouched = [rec.line_id for rec in lines if rec.line_id not in flagged and rec.line_id in never_judged]
    lines_out += [
        "",
        "## Not flagged",
        "",
        ", ".join(cleared) or ("every line was flagged or was never judged"
                               if untouched else "every line was flagged"),
    ]
    if untouched:
        lines_out += ["", f"## Flagged by nothing because nothing read it ({len(untouched)} lines)",
                      "", ", ".join(untouched)]
    lines_out += [
        "",
        "## Reading this report",
        "",
        "- Timing flags are risk against the English performance window, not failure: dubbing can retime a line.",
        "- Naturalness flags are advisory only and carry no score.",
        "- Nothing here is auto-approved. Every flag needs an editor action.",
        "- Akshara counts in the timing column are machine counts of Telugu syllables by `src/telugu.py`: "
        "one per base letter, minus one per virama, so a conjunct counts once.",
        coverage_note,
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines_out), encoding="utf-8")
    return path


def coverage_gaps(payload: dict) -> dict[str, list[str]]:
    """Lines each LLM check was sent but could not classify, newest artifacts first.

    Read from the summary when the run recorded it, and otherwise recomputed from the verdict rows,
    so an artifact written before this accounting existed still reports its own gaps honestly.
    """
    out: dict[str, list[str]] = {}
    sums = payload.get("summaries") or {}
    for check in LLM_CHECKS:
        block = sums.get(check) or {}
        if isinstance(block.get("not_judged_line_ids"), list):
            if block["not_judged_line_ids"]:
                out[check] = list(block["not_judged_line_ids"])
            continue
        rows = (payload.get("verdicts") or {}).get(check) or []
        gaps = [r["line_id"] for r in rows if isinstance(r, dict) and is_not_judged(r)]
        if gaps:
            out[check] = gaps
    return out


def _coverage_line(payload: dict) -> str:
    gaps = coverage_gaps(payload)
    if not any((payload.get("summaries") or {}).get(c) or (payload.get("verdicts") or {}).get(c)
               for c in LLM_CHECKS):
        return "- Model coverage: no LLM check ran on this run"
    if not gaps:
        return "- Model coverage: every line sent to the model was given a verdict"
    return ("- Model coverage: lines sent but not classified - "
            + ", ".join(f"{c} {len(ids)}" for c, ids in sorted(gaps.items())) + ". "
            "For relationship this is usually no relationship-sheet row for the pair or an addressee "
            "that cannot be identified from the line; those lines are neither flagged nor cleared.")


def _timing_line(payload: dict, n_lines: int) -> str:
    tsum = (payload.get("summaries") or {}).get("timing")
    if not tsum:
        return "- Timing: not run"
    ratio = tsum.get("ratio_to_tight_slot") or {}
    share = tsum.get("share_over_tight_with_margin")
    return (
        f"- Timing: rate **{tsum.get('syllables_per_second')}** akshara/s "
        f"({tsum.get('rate_source', 'source not recorded')}), "
        f"median estimate/slot ratio **{ratio.get('median')}**, p90 {ratio.get('p90')}, "
        f"max {ratio.get('max')} - **{share:.0%}** of measured lines overrun their slot "
        f"by more than {tsum.get('margin', 0):.0%}. "
        "A share near 1.0 means this check is shortlisting nothing, so read the ratio before trusting the list."
        if isinstance(share, float) else
        f"- Timing: rate **{tsum.get('syllables_per_second')}** akshara/s, no lines measured"
    )


def _cell(text: str, limit: int = 90) -> str:
    flat = " ".join(str(text).split()).replace("|", "/")
    return flat if len(flat) <= limit else flat[: limit - 1] + "…"
