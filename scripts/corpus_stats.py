#!/usr/bin/env python3
"""Measured statistics for our own screenplay corpus (data/parsed/corpus.json).

These are the numbers the docs are allowed to quote. The two figures that came from
Kuku's confidential pack are not used anywhere (PRD §10).
"""

from __future__ import annotations

import json
import statistics as st
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.parser import DialogueLine, load_parsed  # noqa: E402
from src.console import force_utf8  # noqa: E402


def pct(xs: list[float], q: float) -> float:
    if not xs:
        return 0.0
    ordered = sorted(xs)
    idx = min(len(ordered) - 1, max(0, int(round(q * (len(ordered) - 1)))))
    return ordered[idx]


def describe(values: list[float]) -> dict:
    if not values:
        return {"n": 0}
    return {
        "n": len(values),
        "median": round(st.median(values), 3),
        "mean": round(st.mean(values), 3),
        "min": round(min(values), 3),
        "max": round(max(values), 3),
        "p90": round(pct(values, 0.9), 3),
    }


def main() -> int:
    force_utf8()
    force_utf8()
    parsed = ROOT / "data" / "parsed" / "corpus.json"
    if not parsed.exists():
        print("run scripts/parse_corpus.py first", file=sys.stderr)
        return 1

    records: list[DialogueLine] = load_parsed(parsed)
    payload = json.loads(parsed.read_text(encoding="utf-8"))

    slots = [r.tight_window for r in records]
    words = [float(r.word_count) for r in records]
    long_enough = [r for r in records if r.tight_window >= 1.0]
    rate = [r.word_count / r.tight_window for r in long_enough]
    gaps: list[float] = []
    overlaps = 0
    by_ep: dict[int, list[DialogueLine]] = {}
    for rec in records:
        by_ep.setdefault(rec.episode, []).append(rec)
    for ep, recs in by_ep.items():
        recs.sort(key=lambda r: (r.source_file, r.start))
        for a, b in zip(recs, recs[1:]):
            if a.source_file != b.source_file:
                continue
            gap = b.start - a.end
            gaps.append(gap)
            if gap < 0:
                overlaps += 1

    short_slots = [s for s in slots if s < 1.5]
    stats = {
        "source": "data/screenplay/ (original, written by the builder)",
        "files": payload["files"],
        "dialogue_lines": len(records),
        "per_episode": {str(ep): len(recs) for ep, recs in sorted(by_ep.items())},
        "tight_slot_seconds": describe(slots),
        "slots_under_1_5s": {"count": len(short_slots), "share": round(len(short_slots) / len(slots), 3)},
        "word_count": describe(words),
        "english_words_per_second": describe(rate),
        "gap_between_lines_seconds": describe(gaps),
        "consecutive_overlaps": overlaps,
        "chains": len({r.chain_id for r in records if r.chain_id}),
        "chain_kinds": {
            kind: sum(1 for r in records if r.chain_kind == kind)
            for kind in sorted({r.chain_kind for r in records if r.chain_kind})
        },
        "voice_over": sum(1 for r in records if r.voice_over),
        "off_screen": sum(1 for r in records if r.off_screen),
        "distinct_speaker_labels": len({r.speaker_label.upper() for r in records}),
        "canonical_speakers": sorted({r.canonical_speaker for r in records}),
        "loose_minus_tight_seconds": describe([r.loose_window - r.tight_window for r in records]),
        "long_lines_12_words_or_more": sum(1 for r in records if r.word_count >= 12),
    }

    out_json = ROOT / "data" / "parsed" / "stats.json"
    out_json.write_text(json.dumps(stats, indent=2, ensure_ascii=False), encoding="utf-8")

    slot = stats["tight_slot_seconds"]
    wps = stats["english_words_per_second"]
    gap = stats["gap_between_lines_seconds"]
    wc = stats["word_count"]
    lines = [
        "# Corpus statistics (our own screenplay)",
        "",
        f"Measured by `scripts/corpus_stats.py` over {len(stats['files'])} episode files in `data/screenplay/`.",
        f"Every figure here is ours; none of it comes from Kuku's confidential input pack.",
        "",
        f"- Dialogue lines: **{stats['dialogue_lines']}** (per episode: "
        + ", ".join(f"ep{k}={v}" for k, v in stats["per_episode"].items())
        + ")",
        f"- Tight slot per line: median **{slot['median']} s**, mean {slot['mean']} s, "
        f"min {slot['min']} s, max {slot['max']} s",
        f"- Lines in slots under 1.5 s: **{stats['slots_under_1_5s']['count']} "
        f"({round(100 * stats['slots_under_1_5s']['share'])}%)**",
        f"- English line length: median {wc['median']} words, mean {wc['mean']}, max {wc['max']}",
        f"- English speaking rate (slots >= 1 s): median **{wps['median']} words/s**, "
        f"p90 {wps['p90']}, max {wps['max']}",
        f"- Gap between one line's end and the next start: median {gap['median']} s, p90 {gap['p90']} s; "
        f"consecutive overlaps: {stats['consecutive_overlaps']}",
        f"- Split-sentence chains: **{stats['chains']}** ({', '.join(f'{k}={v}' for k, v in stats['chain_kinds'].items())})",
        f"- Voice-over lines: {stats['voice_over']} | off-screen lines: {stats['off_screen']}",
        f"- Speaker labels as written: {stats['distinct_speaker_labels']} | canonical characters after the alias map: {len(stats['canonical_speakers'])}",
        f"- Lines of 12 words or more: {stats['long_lines_12_words_or_more']}",
        f"- Loose window minus tight window: median {stats['loose_minus_tight_seconds']['median']} s "
        f"(this is the slack a dubbing line can borrow before it collides with the next line)",
        "",
        "## Canonical characters",
        "",
        *[f"- {s}" for s in stats["canonical_speakers"]],
        "",
        "## What these numbers are used for",
        "",
        "- The slot distribution sets the timing thresholds: with "
        f"{round(100 * stats['slots_under_1_5s']['share'])}% of lines under 1.5 s, short slots are over-sampled in Phase 0.",
        "- The speaking rate is the English baseline the Telugu/English duration ratio is reported against.",
        "- The overlap count is why the timing check reports risk against two windows instead of one.",
        "- The chain count is why the meaning check runs on chains, not fragments.",
        "",
    ]
    (ROOT / "docs" / "corpus_statistics.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
