#!/usr/bin/env python3
"""Minimal review UI. Cut this before the checks, never the other way round (PRD section 13).

    streamlit run app.py

Reads results/<label>_flags.json produced by scripts/run_structured.py, shows one row per
flagged line with evidence and a suggested correction, and records approve / edit / dismiss in
data/annotation/decisions.csv with a timestamp. Nothing is auto-approved: a flag stays pending
until the editor acts on it.
"""

from __future__ import annotations

import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from src import config as config_mod  # noqa: E402
from src.checks.relationship import relationship_sheet  # noqa: E402
from src.console import force_utf8  # noqa: E402
from src.corpus import sign_off_register_standard, write_sheet_edits  # noqa: E402
from src.pipeline import ALL_CHECKS, run_structured, sample_lines  # noqa: E402
from src.report import (DECISIONS, FLAG_COLUMNS, apply_decisions, coverage_gaps, load_decisions,  # noqa: E402
                        with_ids, write_markdown, write_run_json)

force_utf8()
RESULTS = ROOT / "results"


def available_runs() -> list[str]:
    return sorted(p.stem[: -len("_flags")] for p in RESULTS.glob("*_flags.json"))


def load_run(label: str) -> dict:
    return json.loads((RESULTS / f"{label}_flags.json").read_text(encoding="utf-8"))


def save_decision(flag: dict, status: str, edited: str) -> None:
    """Upsert one row in the decisions file. Editors work line by line, not in batches."""
    rows = {}
    if DECISIONS.exists():
        with DECISIONS.open(encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                if row.get("flag_id"):
                    rows[row["flag_id"]] = row
    row = {col: flag.get(col, "") for col in FLAG_COLUMNS}
    row.update({
        "flag_id": flag["flag_id"],
        "line_id": flag["line_id"],
        "check": flag["check"],
        "severity": flag["severity"],
        "verdict": flag["verdict"],
        "english": flag.get("english", ""),
        "telugu": flag.get("telugu", ""),
        "slot_seconds": flag.get("slot_seconds", ""),
        "evidence": flag.get("evidence", ""),
        "suggestion": flag.get("suggestion", ""),
        "note": flag.get("note", ""),
        "status": status,
        "edited_suggestion": edited,
        "editor_action_ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    })
    rows[flag["flag_id"]] = row
    DECISIONS.parent.mkdir(parents=True, exist_ok=True)
    with DECISIONS.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=FLAG_COLUMNS)
        writer.writeheader()
        for key in sorted(rows):
            writer.writerow({col: rows[key].get(col, "") for col in FLAG_COLUMNS})


def main() -> None:
    st.set_page_config(page_title="DramAdapt QA", layout="wide")
    st.title("DramAdapt QA - pre-dubbing quality gate")
    st.caption(
        "Quality assurance, not translation. Every flag needs an editor action; nothing here is "
        "auto-approved, and no number in this UI is a confidence score about Telugu correctness."
    )

    runs = available_runs()
    if not runs:
        st.warning("No run found. Run `python scripts/run_structured.py --label demo` first.")
        return

    preferred = [r for r in ("structured", "demo_timing_uncalibrated") if r in runs]
    label = st.sidebar.selectbox("Run", runs, index=runs.index(preferred[0]) if preferred else len(runs) - 1)
    payload = load_run(label)
    telugu_file = st.sidebar.text_input("Telugu draft file", payload.get("source", {})
                                        .get("telugu_file") or "data/telugu/first_pass.json")

    lines, meta = sample_lines(Path(telugu_file))
    by_id = {rec.line_id: rec for rec in lines}
    decisions = load_decisions()
    flags = apply_decisions(with_ids(payload.get("flags", [])), decisions)

    with_telugu = sum(1 for rec in lines if (rec.telugu or "").strip())
    ran = payload.get("checks_run")
    failed = sorted({e.get("check", "?") for e in payload.get("errors", []) if not e.get("partial")})
    partial = sorted({e.get("check", "?") for e in payload.get("errors", []) if e.get("partial")})
    st.subheader("Summary")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Lines", len(lines))
    c2.metric("With Telugu", with_telugu)
    c3.metric("Lines flagged", len({f["line_id"] for f in flags}))
    c4.metric("Requests", payload.get("run_log", {}).get("requests_total", 0))
    if ran is not None and failed:
        st.error(f"Checks that did not complete: {', '.join(failed)}. "
                 "Lines they covered were not judged - this is not a clean pass.")
    if partial:
        gap = next((e for e in payload.get("errors", []) if e.get("partial")), {})
        st.warning(f"Partially judged: {', '.join(partial)}. {gap.get('error', '')} "
                   "Lines a refused batch never read are not clean lines.")
    if with_telugu < len(lines):
        st.warning(f"{len(lines) - with_telugu} lines have no Telugu text. A missing line is not a clean line.")
    tsum = (payload.get("summaries") or {}).get("timing")
    if tsum:
        r = tsum.get("ratio_to_tight_slot") or {}
        st.info(f"Timing at {tsum.get('syllables_per_second')} akshara/s: median estimate/slot ratio "
                f"{r.get('median')}, p90 {r.get('p90')}, "
                f"{(tsum.get('share_over_tight_with_margin') or 0):.0%} of lines over the slot.")
    ssum = (payload.get("summaries") or {}).get("script")
    if ssum:
        st.info(f"Script form: {ssum.get('not_in_telugu_script')} lines with no Telugu letters, "
                f"{ssum.get('mixed_script')} mixing scripts past "
                f"{(ssum.get('mixed_min_latin_share') or 0):.0%} Latin - counted, not asked, so zero "
                "model calls. A voice artist cannot read the first group and the timing check cannot "
                "measure it either.")
    gaps = coverage_gaps(payload)
    if gaps:
        st.warning("Sent to the model but not classified: "
                   + ", ".join(f"{c} {len(ids)} line{'s' if len(ids) != 1 else ''}"
                               for c, ids in sorted(gaps.items()))
                   + ". These lines are neither flagged nor cleared - for relationship that is "
                   "usually no sheet row for the pair or an addressee the line never names.")

    st.subheader("Flagged lines")
    st.caption("Worst first within each check. Timing flags are risk against the English window, not failure.")
    if not flags:
        st.write("This run produced no flags.")
    for flag in flags:
        rec = by_id.get(flag["line_id"])
        with st.container(border=True):
            head = st.columns([2, 1, 1, 4])
            head[0].markdown(f"**{flag['line_id']}** - {rec.canonical_speaker if rec else ''}")
            head[1].markdown(f"check: `{flag['check']}`")
            head[2].markdown(f"severity: `{flag['severity']}`")
            head[3].markdown(f"verdict: `{flag['verdict']}`")
            st.markdown(f"**EN** {rec.text if rec else ''}")
            st.markdown(f"**TE** {rec.telugu if rec else ''}"
                        + (f"  |  slot {rec.tight_window}s" if rec else ""))
            st.caption(f"evidence: {flag['evidence']}")
            if flag.get("note"):
                st.caption(flag["note"])
            st.markdown(f"suggested: {flag.get('suggestion') or '_none offered_'}")

            current = (flag.get("status") or "pending")
            choice = st.radio(
                "editor action", ["pending", "approved", "edited", "dismissed"],
                index=["pending", "approved", "edited", "dismissed"].index(current)
                if current in ("pending", "approved", "edited", "dismissed") else 0,
                horizontal=True, key=f"{flag['flag_id']}_status",
            )
            edited = st.text_input("edited correction", value=flag.get("suggestion", "") if current == "edited" else "",
                                   key=f"{flag['flag_id']}_edit")
            if choice != current or (choice == "edited" and edited and not flag.get("edited")):
                save_decision(flag, choice, edited if choice == "edited" else "")
                st.toast(f"{flag['flag_id']} -> {choice}")
                st.rerun()
            if flag.get("editor_action_ts"):
                st.caption(f"last editor action: {flag['editor_action_ts']}")

    with st.expander("Relationship and address sheet (model pre-filled, editor confirms)"):
        sheet = relationship_sheet()
        rows = sheet.get("relationships", [])
        df = pd.DataFrame([{k: v for k, v in r.items() if k in
                            ("speaker", "listener", "episodes", "expected_register", "confirmed", "editor_note")}
                           for r in rows])
        if not df.empty:
            df["confirmed"] = df["confirmed"].astype(bool)
            edited = st.data_editor(df, hide_index=True, width="stretch",
                                    column_config={"confirmed": st.column_config.CheckboxColumn("confirmed")})
            if st.button("Save confirmations"):
                write_sheet_edits(edited.to_dict("records"))
                st.success("saved data/relationship_sheet_edits.csv (the YAML sheet itself is untouched)")
                st.rerun()
        else:
            st.write("no rows in data/relationship_sheet.yaml")
        block = sheet.get("telugu_register_standard", {})
        st.markdown("**Telugu register standard** — "
                    "addendum open item 3: this paragraph is a draft until the builder signs it off.")
        status = st.text_input("status", block.get("status", ""))
        para = st.text_area("register standard", block.get("draft_paragraph", ""), height=180)
        if st.button("Sign off / save register standard"):
            sign_off_register_standard(para, status)
            st.success("saved data/register_standard_override.json")
            st.rerun()

    with st.expander("Run checks now"):
        checks = st.multiselect("checks", list(ALL_CHECKS), default=list(ALL_CHECKS))
        rate = st.text_input("Telugu rate (akshara/s) - blank uses data/calibration.json", "")
        model = st.text_input("model override (blank uses config.yaml)", "")
        if st.button("Run"):
            try:
                cfg = config_mod.load(None)
                use_rate = float(rate) if rate else config_mod.syllables_per_second(cfg)
                out = run_structured(lines, tuple(checks), phase="ui_run",
                                     model=model or None, rate_override=use_rate)
                write_payload_ui(out)
                st.success(f"wrote results/ui_run_flags.json - {len(out['flags'])} flags")
                st.rerun()
            except Exception as exc:  # noqa: BLE001 - the UI must show the failure, not swallow it
                st.error(str(exc))

    with st.expander("Export"):
        st.download_button("run JSON", json.dumps(payload, ensure_ascii=False, indent=2),
                           file_name=f"{label}_run.json", mime="application/json")
        st.download_button("decisions CSV", DECISIONS.read_text(encoding="utf-8")
                           if DECISIONS.exists() else "", file_name="decisions.csv", mime="text/csv")
        if st.button("Write Markdown report from this run"):
            path = write_markdown(payload, lines, RESULTS / f"{label}_report.md")
            st.success(f"wrote {path.relative_to(ROOT)}")
        if st.button("Write run JSON (with counts)"):
            path = write_run_json(payload, RESULTS / f"{label}_run.json")
            st.success(f"wrote {path.relative_to(ROOT)}")


def write_payload_ui(payload: dict) -> Path:
    path = RESULTS / "ui_run_flags.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


if __name__ == "__main__":
    main()
