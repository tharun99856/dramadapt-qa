"""Check 5 - script form. Pure Python, no model calls.

A dubbing artist reads Telugu script. A line of transliterated Telugu - "Meeru mee lampu
neeku pettukondi" - is the right words in the wrong alphabet: it cannot be read on a studio floor,
it cannot be timed by akshara count, and a general-purpose QA prompt rarely mentions it because the
sentence *is* Telugu to a language model. In our own Step A run this was not hypothetical:
gpt-oss-120b returned 20 of 100 lines in Latin script, while qwen/qwen3.8-27b returned none. The
failure is a property of the model, not of the screenplay, and the only reason it is visible is that
something counted letters.

Two verdicts:
  not_in_telugu_script - no Telugu letters at all. High: unusable as recorded.
  mixed_script         - Telugu and Latin both carrying words. Medium: readable but the Latin part
                         needs a decision (keep the English term or write it in Telugu).
"""

from __future__ import annotations

from ..flags import make_flag
from ..parser import DialogueLine
from ..telugu import latin_word_count, script_name, script_share

MIXED_MIN_LATIN = 0.25


def run(lines: list[DialogueLine]) -> tuple[list[dict], list[dict], dict]:
    flags: list[dict] = []
    table: list[dict] = []
    missing = 0
    letterless = 0

    for rec in lines:
        text = (rec.telugu or "").strip()
        if not text:
            missing += 1
            continue
        if not any(ch.isalpha() for ch in text):
            letterless += 1  # digits or stage noise: there is no script to judge, so no flag
            table.append({"line_id": rec.line_id, "script": "no_letters",
                          "telugu_letter_share": 0.0, "latin_words": 0})
            continue
        share = script_share(text)
        row = {"line_id": rec.line_id, "script": script_name(text),
               "telugu_letter_share": round(share["telugu"], 3),
               "latin_words": latin_word_count(text)}
        table.append(row)

        if share["telugu"] == 0.0:
            flags.append(make_flag(
                line_id=rec.line_id,
                check="script",
                severity="high",
                verdict="not_in_telugu_script",
                evidence=(f"no Telugu letters; {row['latin_words']} Latin words, detected script "
                          f"{row['script']}: {text[:60]!r}"),
                suggestion="re-render this line in Telugu script before it goes to the studio",
                note=("transliteration is readable to a language model and unreadable to a voice "
                      "artist; the timing check cannot measure it either"),
            ))
        elif share["latin"] >= MIXED_MIN_LATIN:
            flags.append(make_flag(
                line_id=rec.line_id,
                check="script",
                severity="medium",
                verdict="mixed_script",
                evidence=(f"{share['latin']:.0%} Latin letters against {share['telugu']:.0%} Telugu: "
                          f"{text[:60]!r}"),
                suggestion="decide each English term on purpose - write it in Telugu or keep it "
                           "in English everywhere, not line by line",
                note="loanwords are a legitimate choice; a draft that varies them per line is not",
            ))

    summary = {
        "lines_checked": len(table),
        "lines_without_telugu": missing,
        "lines_without_letters": letterless,
        "not_in_telugu_script": sum(1 for f in flags if f["verdict"] == "not_in_telugu_script"),
        "mixed_script": sum(1 for f in flags if f["verdict"] == "mixed_script"),
        "mixed_min_latin_share": MIXED_MIN_LATIN,
        "note": ("zero model calls; this check exists because Step A really did return 20 "
                 "Latin-script lines out of 100 on the default model and none on the comparison model"),
    }
    return flags, table, summary
