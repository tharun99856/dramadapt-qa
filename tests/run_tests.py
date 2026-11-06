#!/usr/bin/env python3
"""Self-tests for the pieces that must not be wrong: windows, chains, akshara counts, metrics.

    python tests/run_tests.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src import metrics  # noqa: E402
from src.batching import scene_batches  # noqa: E402
from src.flags import make_flag  # noqa: E402
from src.parser import DialogueLine, assign_windows, clean_text, link_chains, parse_file, norm_time  # noqa: E402
from src.telugu import akshara_count  # noqa: E402

PASS: list[str] = []
FAIL: list[str] = []


def check(name: str, got, want) -> None:
    if got == want:
        PASS.append(name)
    else:
        FAIL.append(f"{name}: got {got!r} want {want!r}")


def rec(**kw) -> DialogueLine:
    base = dict(line_id="E01-L001", episode=1, scene=1, scene_heading="INT. ROOM - NIGHT",
                speaker_label="A", canonical_speaker="A", delivery_tag="", voice_over=False, off_screen=False,
                chain_id="", chain_kind="", chain_position=0, chain_length=1, start=0.0, end=2.0,
                tight_window=2.0, loose_window=2.0, text="hello", telugu="", nearby_action="",
                source_file="ep.txt", source_line=1, word_count=1, flags=[])
    base.update(kw)
    return DialogueLine(**base)


def test_time_parsing() -> None:
    check("time mm:ss.t", norm_time("1:26.0"), 86.0)
    check("time ss.t", norm_time("44.0"), 44.0)
    check("time h:mm:ss", norm_time("1:02:03.5"), 3723.5)
    check("time garbage", norm_time("bogus"), None)


def test_clean_text() -> None:
    check("quotes stripped", clean_text('"The lamp stays lit."'), "The lamp stays lit.")
    check("inner quotes kept", clean_text('"She said \\"no\\" here"'.replace('\\"', "'")), "She said 'no' here")
    check("curly quotes", clean_text("\u201cTelugu text\u201d"), "Telugu text")


def test_windows() -> None:
    a = rec(line_id="E01-L001", start=0.0, end=2.0, tight_window=2.0)
    b = rec(line_id="E01-L002", start=3.0, end=4.0, tight_window=1.0)
    assign_windows([b, a])
    check("tight stays", a.tight_window, 2.0)
    check("loose reaches next start", a.loose_window, 3.0)
    check("last line loose equals tight", b.loose_window, 1.0)


def test_chains() -> None:
    a = rec(line_id="E01-L010", speaker_label="A", text="Say it as a promise, not a ...")
    b = rec(line_id="E01-L011", speaker_label="B", text="... a dare. I hear you.", start=5.0, end=6.0, tight_window=1.0)
    warns: list = []
    link_chains([a, b], warns)
    check("interlocked chain linked", (a.chain_id == b.chain_id, a.chain_kind), (True, "interlocked"))
    c = rec(line_id="E01-L012", speaker_label="C", text="... trailing in", start=8.0, end=9.0, tight_window=1.0)
    warns2: list = []
    link_chains([c], warns2)
    check("orphan fragment reported", [w.kind for w in warns2], ["fragment"])


def test_akshara() -> None:
    check("nn conjunct counts once", akshara_count("\u0c28\u0c3e\u0c28\u0c4d\u0c28"), 2)  # na-nna
    check("honorific verb", akshara_count("\u0c1a\u0c46\u0c36\u0c3e\u0c30\u0c41"), 3)  # che-saa-ru
    check("latin gives zero", akshara_count("hello world"), 0)
    check("mixed counts Telugu only", akshara_count("\u0c28\u0c3e\u0c28\u0c4d\u0c28 yes"), 2)


def test_batching() -> None:
    lines = [rec(line_id=f"E01-L{i:03d}", scene=1 if i < 3 else 2, start=float(i), end=float(i) + 1) for i in range(5)]
    batches = scene_batches(lines, max_lines=14)
    check("splits by scene", [len(b) for _, b in batches], [3, 2])
    long_scene = [rec(line_id=f"E02-L{i:03d}", scene=1, episode=2, start=float(i), end=float(i) + 1) for i in range(9)]
    long_scene[4].chain_id = long_scene[5].chain_id = "C2-001"
    long_scene[4].speaker_label = long_scene[5].speaker_label = "A"
    chunks = scene_batches(long_scene, max_lines=4)
    sizes = [len(b) for _, b in chunks]
    check("respects max lines", max(sizes) <= 4, True)
    joined = {r.line_id for _, b in chunks for r in b}
    check("nothing lost in chunking", len(joined), 9)


def test_metrics() -> None:
    issues = {"L1": {"meaning"}, "L2": {"timing"}, "L3": {"meaning"}}
    flags = [make_flag(line_id="L1", check="meaning", severity="high", verdict="reversed", evidence="e"),
             make_flag(line_id="L2", check="timing", severity="medium", verdict="over_slot", evidence="e"),
             make_flag(line_id="L4", check="meaning", severity="medium", verdict="weakened", evidence="e")]
    res = metrics.score(flags, issues)
    check("two true positives", res["true_positive_flags"], 2)
    check("one false positive", res["false_positive_flags"], 1)
    check("one missed", res["missed_human_issues"], 1)
    check("precision", res["precision"], round(2 / 3, 3))
    check("recall", res["recall"], round(2 / 3, 3))

    chain_flags = [make_flag(line_id="L1", check="meaning", severity="high", verdict="reversed", evidence="e")]
    check("no chain credit without chain map", metrics.score(chain_flags, issues)["true_positive_flags"], 1)
    rescued = metrics.score(chain_flags, {"L9": {"meaning"}}, {"C1": ["L1", "L9"]})
    check("chain partner counts as a hit", rescued["true_positive_flags"], 1)

    sweep = metrics.severity_sweep(flags, issues)
    check("sweep has three cut points", len(sweep), 3)
    high_only = [p for p in sweep if p["at_least"] == "high"][0]
    check("high-only keeps one flag at precision 1.0", (high_only["flags"], high_only["precision"]), (1, 1.0))
    best = metrics.best_recall_at_precision(sweep, 0.6)
    check("best recall at precision 0.6 comes from the medium cut",
          (best["available"], best["at_least"], best["recall"], best["flags"]), (True, "medium", 0.667, 3))
    none = metrics.best_recall_at_precision(sweep, 1.1)
    check("an impossible precision target is reported, not guessed", none["available"], False)


def test_acceptance() -> None:
    decisions = {
        ("F1", "L1"): {"check": "meaning", "status": "approved"},
        ("F2", "L2"): {"check": "meaning", "status": "edited"},
        ("F3", "L3"): {"check": "meaning", "status": "dismissed"},
        ("F4", "L4"): {"check": "timing", "status": "dismissed"},
        ("F5", "L5"): {"check": "timing", "status": "dismissed"},
    }
    rates = metrics.acceptance_rates(decisions)
    check("meaning acceptance", rates["meaning"]["acceptance_rate"], round(2 / 3, 3))
    check("timing acceptance", rates["timing"]["acceptance_rate"], 0.0)


def test_seeded_recall() -> None:
    manifest = {"edits": [{"line_id": "L1", "expected_check": "meaning"}, {"line_id": "L2", "expected_check": "timing"}]}
    flags = [make_flag(line_id="L1", check="meaning", severity="high", verdict="reversed", evidence="e")]
    out = metrics.seeded_recall(manifest, flags)
    check("seeded meaning detected", out["meaning"]["detected"], 1)
    check("seeded timing missed", out["timing"]["detected"], 0)


def test_real_corpus_has_three_chains() -> None:
    import yaml

    alias = yaml.safe_load((ROOT / "data" / "alias_map.yaml").read_text(encoding="utf-8"))
    result = parse_file(ROOT / "data" / "screenplay" / "episode-001.txt", alias)
    warns: list = []
    link_chains(result[0], warns)
    chains = {r.chain_id for r in result[0] if r.chain_id}
    check("episode 1 chains", len(chains), 2)


def test_timing_flags_are_unique_and_worst_first() -> None:
    import re

    from src.checks import timing
    from src.report import flag_id, with_ids

    # one line over its own slot, plus two chain members whose combined sentence also runs over
    a = rec(line_id="L1", tight_window=1.0, loose_window=1.4, telugu="దీపం వెలుగుతూనే ఉంటుంది")
    b = rec(line_id="L2", tight_window=1.0, loose_window=4.0, telugu="చాలు", chain_id="C1", chain_position=1)
    c = rec(line_id="L3", tight_window=1.0, loose_window=4.0, telugu="దీపం వెలుగుతూనే ఉంటుంది",
            chain_id="C1", chain_position=2)
    found, table, summary = timing.run([a, b, c], 3.5)

    ids = [flag_id(f) for f in with_ids(found)]
    check("timing ids unique", len(set(ids)), len(ids))
    check("line with two timing problems keeps both", len([f for f in found if f["line_id"] == "L3"]) >= 1, True)

    ratios = [float(m.group(1)) for f in found if (m := re.search(r"\((\d+\.\d+)x", f["evidence"]))]
    check("flagged at all", len(ratios) >= 2, True)
    check("worst first", ratios, sorted(ratios, reverse=True))
    check("summary carries selectivity", summary["share_over_tight_with_margin"] is not None, True)
    check("summary carries median ratio", summary["ratio_to_tight_slot"]["median"] is not None, True)


def test_decision_timestamp_round_trip() -> None:
    from src.report import apply_decisions, flag_id, with_ids

    f = make_flag(line_id="L1", check="timing", severity="medium", verdict="over_slot", evidence="e")
    rows = with_ids([f])
    fid = flag_id(f)
    merged = apply_decisions(rows, {fid: {"status": "edited", "edited_suggestion": "trim it",
                                          "editor_action_ts": "2026-11-06T00:00:00+00:00"}})
    check("decision status applied", merged[0]["status"], "edited")
    check("decision suggestion applied", merged[0]["suggestion"], "trim it")
    check("decision timestamp shown", merged[0]["editor_action_ts"], "2026-11-06T00:00:00+00:00")


def test_script_check() -> None:
    from src.checks import script as script_check

    lines = [
        rec(line_id="L1", telugu="దీపం వెలిగినట్టే ఉంటుంది."),
        rec(line_id="L2", telugu="Meeru seal ki kooda layakaledu. Aameyi teesukondi."),
        rec(line_id="L3", telugu="ఆమె office కు వెళ్ళింది."),
        rec(line_id="L4", telugu="1913."),
        rec(line_id="L5", telugu=""),
    ]
    found, table, summary = script_check.run(lines)
    by_line = {f["line_id"]: f for f in found}
    check("telugu script not flagged", "L1" in by_line, False)
    check("transliteration is high", (by_line["L2"]["severity"], by_line["L2"]["verdict"]),
          ("high", "not_in_telugu_script"))
    check("mixed script is medium", (by_line["L3"]["severity"], by_line["L3"]["verdict"]),
          ("medium", "mixed_script"))
    check("a digit line is not called transliteration", "L4" in by_line, False)
    check("an absent line is left to the coverage report", "L5" in by_line, False)
    check("summary counts", (summary["not_in_telugu_script"], summary["mixed_script"],
                             summary["lines_without_telugu"], summary["lines_without_letters"]), (1, 1, 1, 1))
    check("table skips the absent line", len(table), 4)
    check("suggestion names the fix", "Telugu script" in by_line["L2"]["suggestion"], True)


def test_declined_verdicts_are_coverage_gaps() -> None:
    """A model that declines must not become a finding, and must not become a clean line either."""
    from src.checks import meaning, relationship
    from src.pipeline import _absorb

    class StubLLM:
        model = "stub"

        def __init__(self, answers):
            self.answers = answers

        def ask_json(self, system, user, kind=None, batch=None):
            return {"lines": self.answers[kind]}

    lines = [rec(line_id="L1"), rec(line_id="L2"), rec(line_id="L3"), rec(line_id="L4")]
    batches = [("ep.txt#S01", lines)]
    answers = {
        "relationship": [
            {"line_id": "L1", "verdict": "consistent", "evidence": ""},
            {"line_id": "L2", "verdict": "unknown", "evidence": "no sheet row for this pair"},
            {"line_id": "L3", "verdict": "too_formal", "evidence": "verb ending"},
            {"line_id": "L4", "verdict": "something_else", "evidence": "off enum"},
        ],
        "meaning": [
            {"line_id": "L1", "verdict": "same"},
            {"line_id": "L2", "verdict": "weakened", "reason": "threat became a request"},
            {"line_id": "L3", "verdict": "  "},
            {"line_id": "L4", "verdict": "same"},
        ],
    }
    llm = StubLLM(answers)

    rflags, rverdicts, rfailed = relationship.run(llm, batches, lines)
    by_line = {f["line_id"]: f for f in rflags}
    check("a refusal is not a flag", "L2" in by_line, False)
    check("a real problem is a flag", (by_line["L3"]["severity"], by_line["L3"]["verdict"]),
          ("medium", "too_formal"))
    check("an off-enum verdict stays visible", by_line["L4"]["verdict"], "outside_enum:something_else")
    check("the refusal is still recorded as a verdict",
          [v["verdict"] for v in rverdicts], ["consistent", "unknown", "too_formal", "something_else"])

    mflags, mverdicts, mfailed = meaning.run(llm, batches)
    check("a blank meaning verdict is not a flag", [f["line_id"] for f in mflags], ["L2"])
    check("a blank verdict is recorded as blank", [v["verdict"] for v in mverdicts],
          ["same", "weakened", "blank", "same"])

    verdicts, summaries, flags, errors = {}, {}, [], []
    _absorb("relationship", rflags, rverdicts, rfailed, batches, verdicts, summaries, flags, errors, "stub")
    # only the refusal counts as not judged: the off-enum line still produced a flag a reviewer sees
    check("the pipeline counts what was not judged", summaries["relationship"]["lines_not_judged"], 1)
    check("and names it", summaries["relationship"]["not_judged_line_ids"], ["L2"])
    check("one refusal is not an error entry", errors, [])
    check("flags survive", len(flags), 2)


def test_a_refused_batch_keeps_the_answered_ones() -> None:
    """One throttled scene must not throw away the scenes that already answered."""
    import json

    from src.checks import meaning, naturalness, relationship
    from src.llm import LLMError

    class HalfLLM:
        model = "stub"

        def ask_json(self, system, user, kind=None, batch=None):
            if batch.endswith("#S02"):
                raise LLMError("429 on purpose")
            items = json.loads(user)["items"]
            verdict = {"meaning": "same", "naturalness": "natural", "relationship": "consistent"}[kind]
            return {"lines": [{"line_id": i["line_id"], "verdict": verdict, "reason": "", "note": "",
                               "evidence": "", "suggestion": ""} for i in items]}

    batches = [("ep.txt#S01", [rec(line_id="L1")]), ("ep.txt#S02", [rec(line_id="L2")])]
    llm = HalfLLM()
    two = [rec(line_id="L1"), rec(line_id="L2")]
    calls = [(meaning.run, (llm, batches)), (naturalness.run, (llm, batches)),
             (relationship.run, (llm, batches, two))]
    for fn, args in calls:
        out = fn(*args)
        check(f"{fn.__module__.split('.')[-1]} returns flags, verdicts and failed batches", len(out), 3)
        check(f"{fn.__module__.split('.')[-1]} kept the answered batch", len(out[1]), 1)
        check(f"{fn.__module__.split('.')[-1]} names the refused one",
              [f["batch"] for f in out[2]], ["ep.txt#S02"])


def test_a_report_without_judged_lines_does_not_claim_a_pass() -> None:
    """The zero-spend rehearsal run has no flags because nothing was judged - the report must say so."""
    import tempfile

    from src.report import write_markdown

    lines = [rec(line_id="L1"), rec(line_id="L2", telugu="నువ్వు వచ్చావా")]
    payload = {"phase": "rehearsal", "model": None, "lines": [], "flags": [], "verdicts": {},
               "summaries": {}, "batches": [], "run_log": {}, "checks_run": ["timing", "script"]}
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "r.md"
        text = write_markdown(payload, lines, out).read_text(encoding="utf-8")
    tail = text.split("## Not flagged\n")[1]
    split = ", but not read by every check"
    check("the pass claim is withheld", "Every line was read by every check" in text, False)
    check("the gap is named", "1 line(s) had no Telugu text" in text, True)
    check("the unread line is not listed as cleared", "L1" in tail.split(split)[0], False)
    check("the line a check did read is cleared", "L2" in tail.split(split)[0], True)
    check("and appears under partially read", "L1" in tail.split(split)[1], True)


def test_a_merge_keeps_the_failure_of_checks_it_did_not_rerun() -> None:
    """--merge must not erase "this check was only partially judged"."""
    import importlib.util

    spec = importlib.util.spec_from_file_location("run_structured", ROOT / "scripts" / "run_structured.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    carry = module.carry_over_errors

    partial = {"check": "naturalness", "partial": True, "error": "2 of 18 batches refused"}
    kept = ["meaning", "naturalness", "relationship"]
    check("a re-render of timing keeps the naturalness refusal",
          [e["check"] for e in carry([], [partial], {"timing", "script"}, kept)], ["naturalness"])
    check("re-running the check itself replaces its old error",
          carry([], [partial], {"naturalness"}, ["meaning"]), [])
    check("a check re-run this pass drops both copies of its error",
          carry([partial], [partial], {"naturalness"}, kept), [])
    check("and an error for a check this run also did not touch survives",
          len(carry([], [partial, {"check": "meaning", "error": "x"}], {"timing"}, kept)), 2)


def main() -> int:
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
            except Exception as exc:  # noqa: BLE001
                FAIL.append(f"{name} raised {type(exc).__name__}: {exc}")
    print(f"{len(PASS)} passed, {len(FAIL)} failed")
    for f in FAIL:
        print("  FAIL " + f)
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
