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
import os
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


def apply_secrets() -> None:
    """A deployed app has no .env file. Streamlit Cloud secrets are the only place a key can live
    there, and they belong in the environment where src/config.py already looks for it."""
    try:
        secrets = st.secrets
        for name in ("GROQ_API_KEY", "OPENAI_API_KEY"):
            value = secrets.get(name)
            if value and not os.environ.get(name):
                os.environ[name] = str(value)
    except Exception:  # noqa: BLE001 - no secrets.toml raises here, and unset is the same as absent
        return


def key_available() -> bool:
    try:
        config_mod.api_key(config_mod.load(None))
        return True
    except Exception:  # noqa: BLE001 - any reason the key is missing is the same answer here
        return False


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


def attempt_write(action: str, fn, report) -> tuple[bool, object]:
    """A hosted demo usually has a read-only filesystem, and a saved editor decision is not the
    place to discover that with a traceback. Returns (ok, value); `report` gets the explanation."""
    try:
        return True, fn()
    except OSError as exc:
        report(f"Could not {action}: {exc}. This filesystem is read-only, so the change lives only in "
               "this browser session - use the Export panel to download the file and keep decisions "
               "locally, where they can be committed.")
        return False, None


def main() -> None:
    st.set_page_config(page_title="DramAdapt QA", layout="wide")
    apply_secrets()
    st.title("DramAdapt QA - pre-dubbing quality gate")
    st.caption(
        "Quality assurance, not translation. Every flag needs an editor action; nothing here is "
        "auto-approved, and no number in this UI is a confidence score about Telugu correctness."
    )

    st.markdown(
        "**What this page does.** Suppose a studio has an English microdrama script, a machine-made Telugu "
        "translation of it, and a dubbing artist booked at 10am. Someone has to read both scripts and find "
        "what is wrong before the artist is in the booth. That is this tool. It takes the English line and "
        "the Telugu line and returns a list of specific problems, each one pointing at a line id: a meaning "
        "that silently changed, the wrong form of address between two characters, a line that cannot be "
        "spoken inside its time slot, phrasing no Telugu speaker would actually say, Telugu typed in Latin "
        "letters. Five checks do that work: `meaning`, `relationship` and `naturalness` ask a model, `timing` "
        "and `script` are computed from the text and cost zero model calls. "
        "**It does not translate, does not dub, does not lip-sync, and does not clear a line.** Every row is "
        "a question for a human editor, and each row carries the evidence and a place to record what that "
        "human decided."
    )
    st.caption(
        "**The honest status of the `structured` run, stated before the numbers.** Against a 100-line sheet "
        "graded by hand, it put a flag on 80 of the 81 lines the reviewer marked as needing work, but only "
        "0.506 of its 174 flags were problems the reviewer agreed with, while one generic \"find the errors\" "
        "prompt got 0.897 of 58. The project's rule was written down before the run, and that rule returns "
        "**NO-GO**. The prototype is submitted carrying that verdict instead of a friendlier one. "
        "See `docs/phase0_results.md` and the expander below; other labels in the sidebar are subsets or "
        "re-pricings of these same 100 lines, not new evidence."
    )

    with st.expander("Why Telugu, and why this problem", expanded=True):
        st.markdown(
            "- **Because Telugu is my native language, I could be the evaluator myself.** No dubbing house, "
            "no studio, no interpreter: 100 lines graded by hand (81 `needs_revision`, 19 acceptable), 83 of "
            "them rewritten in my own Telugu, and 34 of the 174 flags put through a second pass that says "
            "accept, accept-with-an-edit or dismiss. The cost is just as real and is written down: one "
            "evaluator, one language, no inter-rater agreement, and the grades were recorded in batches with "
            "an AI assistant drafting some of them for review, which is human-reviewed AI-suggested "
            "annotation, not independent annotation.\n"
            "- **Because the models are weak here, in a measurable way.** TeluguEval (Gundam and Mamidi, "
            "LoResLM @ ACL 2026) has Llama-3.1-8B fall from 90.95 to 48.10 on GSM8K when the same questions "
            "are asked in Telugu instead of English. A cheap first-pass translation is exactly the input this "
            "tool is meant to catch, so a QA gate is not decorative in this language pair.\n"
            "- **Because Telugu makes error classes interesting that English does not.** Register lives in "
            "the pronoun and the verb ending, so నువ్వు and మీరు are not two spellings of \"you\" but two "
            "different relationships, and a model flips them between lines. Telugu is verb-final, so an "
            "English sentence cut into two lines often needs re-ordering or the punch lands on the wrong "
            "word. And a huge amount of machine Telugu comes back typed in Latin letters, which a voice "
            "artist cannot read aloud at all.\n"
            "- **Because of where the failure sits in the pipeline.** The translation is checked before the "
            "booth, not after the episode ships. A flag here costs one editor reading one line; the same "
            "defect found later costs a re-dub.\n"
            "\nWhat the checks actually flag is in `docs/solution_two_pager.md`, and every wrong turn this "
            "project took is numbered in `docs/failure_log.md`."
        )

    runs = available_runs()
    if not runs:
        st.warning("No run found. Run `python scripts/run_structured.py --label demo` first.")
        return

    preferred = [r for r in ("structured", "demo_timing_uncalibrated") if r in runs]
    label = st.sidebar.selectbox("Run", runs, index=runs.index(preferred[0]) if preferred else len(runs) - 1)
    payload = load_run(label)
    stored = payload.get("source", {}).get("telugu_file") or "data/telugu/first_pass.json"
    telugu_file = st.sidebar.text_input("Telugu draft file", str(stored).replace("\\", "/"))

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

    with st.expander("How to read the numbers above"):
        st.markdown(
            "- **Lines / With Telugu.** A line with no Telugu text is not a clean line, it is an unjudged "
            "one, which is why the gap is a warning rather than a metric.\n"
            "- **Lines flagged.** The five checks flag independently, so one line can carry three flags and "
            "still count once here. Flag count and line count answer different questions.\n"
            "- **Requests.** Only three checks call a model, and they are batched by scene, so requests "
            "scale with scenes rather than lines. `timing` and `script` are computed from the text: zero "
            "calls, zero cost, and they are the two checks that cannot change their mind between runs.\n"
            "- **The timing line.** The akshara-per-second rate in it is an assumption, not a measurement. "
            "Nothing has been hand-timed yet. Re-pricing the same draft at 5.83 akshara/s, a rate derived "
            "from the reviewer's own 83 corrected lines, moves the timing check's false positives from 50 to "
            "20 and whole-run precision from 0.506 to 0.606, so this number is the cheapest real result left "
            "in the project - see `docs/phase0_results_timing_derived583.md`.\n"
            "- **The script-form line.** Counted from Unicode blocks, not asked of a model. Lines with no "
            "Telugu letters are unreadable in the booth; mixed-script lines are unreadable in a different way.\n"
            "- **\"Sent to the model but not classified.\"** This is a coverage gap and deliberately not "
            "counted as clean. A batch the model refused to answer in full leaves those lines unjudged."
        )

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
                ok, _ = attempt_write(
                    f"record {flag['flag_id']} as {choice}",
                    lambda f=flag, c=choice, e=(edited if choice == "edited" else ""):
                        save_decision(f, c, e),
                    st.error)
                if ok:
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
                ok, _ = attempt_write("save the sheet confirmations",
                                      lambda: write_sheet_edits(edited.to_dict("records")), st.error)
                if ok:
                    st.success("saved data/relationship_sheet_edits.csv (the YAML sheet itself is untouched)")
                    st.rerun()
        else:
            st.write("no rows in data/relationship_sheet.yaml")
        block = sheet.get("telugu_register_standard", {})
        st.markdown(f"**Telugu register standard** - status: `{block.get('status', 'unset')}`. "
                    "The two reviewer decisions are recorded in `reviewer_decisions` below; the rest of "
                    "the paragraph is still unconfirmed against the episodes.")
        for decision in sheet.get("reviewer_decisions") or []:
            if not isinstance(decision, dict):
                continue
            line = decision.get("report_sentence") or ", ".join(
                f"{k}={v}" for k, v in decision.items() if k not in ("id", "decided", "note"))
            st.caption(f"decided {decision.get('decided', '?')} - {decision.get('id', '')}: {line}")
        status = st.text_input("status", block.get("status", ""))
        para = st.text_area("register standard", block.get("draft_paragraph", ""), height=180)
        if st.button("Sign off / save register standard"):
            ok, _ = attempt_write("save the register standard",
                                  lambda: sign_off_register_standard(para, status), st.error)
            if ok:
                st.success("saved data/register_standard_override.json")
                st.rerun()

    with st.expander("Run checks now"):
        st.caption("Model calls need a key: locally from `.env`, on a hosted app from Streamlit "
                   "secrets. `timing` and `script` need none and always run."
                   if key_available() else
                   "No API key is available here, so the three LLM checks will fail loudly. "
                   "`timing` and `script` need no key and always run.")
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
            ok, path = attempt_write("write the report file",
                                     lambda: write_markdown(payload, lines, RESULTS / f"{label}_report.md"),
                                     st.error)
            if ok:
                st.success(f"wrote {path.relative_to(ROOT)}")
        if st.button("Write run JSON (with counts)"):
            ok, path = attempt_write("write the run JSON",
                                     lambda: write_run_json(payload, RESULTS / f"{label}_run.json"),
                                     st.error)
            if ok:
                st.success(f"wrote {path.relative_to(ROOT)}")


def write_payload_ui(payload: dict) -> Path:
    path = RESULTS / "ui_run_flags.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


if __name__ == "__main__":
    main()
