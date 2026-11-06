"""Check 3 - timing. Pure Python, no model calls.

An estimate is compared against two windows: the tight slot (this line's own
Start..End) and the loose window (up to the next line's Start). Over the tight slot is a
medium flag; over the loose window means it would collide with the next line, which is high.
Flags come back worst-first: the editor is meant to read the top of the list, not all of it.
"""

from __future__ import annotations

from ..flags import make_flag
from ..parser import DialogueLine
from ..telugu import akshara_count, estimate_duration, has_telugu, script_name


def _fmt_ratio(ratio: float | None) -> str:
    return f"{ratio:.2f}x the slot" if ratio else "n/a"


def run(lines: list[DialogueLine], syllables_per_second: float, margin: float = 0.15,
        english_words_per_second: float | None = None) -> tuple[list[dict], list[dict], dict]:
    """Returns flags, the per-line measurement table, and run statistics."""
    ranked: list[tuple[float, dict]] = []
    table: list[dict] = []
    skipped_no_telugu = 0
    skipped_not_telugu_script = []

    for rec in lines:
        telugu = (rec.telugu or "").strip()
        if not telugu:
            skipped_no_telugu += 1
            continue
        if not has_telugu(telugu):
            skipped_not_telugu_script.append((rec.line_id, script_name(telugu)))
            continue
        akshara = akshara_count(telugu)
        est = estimate_duration(telugu, syllables_per_second)
        over_tight = est - rec.tight_window * (1 + margin)
        over_loose = est - rec.loose_window
        ratio = est / rec.tight_window if rec.tight_window else None
        rate_text = f"{akshara} akshara at {syllables_per_second}/s"
        row = {
            "line_id": rec.line_id,
            "akshara": akshara,
            "estimated_seconds": round(est, 3),
            "tight_window": rec.tight_window,
            "loose_window": rec.loose_window,
            "telugu_to_slot_ratio": round(ratio, 3) if ratio else None,
            "english_words_per_second": (
                round(rec.word_count / rec.tight_window, 3) if rec.tight_window and rec.word_count else None
            ),
        }
        table.append(row)

        if over_loose > 0 and rec.loose_window > rec.tight_window:
            ranked.append((ratio or 0.0, make_flag(
                line_id=rec.line_id,
                check="timing",
                severity="high",
                verdict="overlaps_next_line",
                evidence=(
                    f"estimate {est:.2f}s > loose window {rec.loose_window:.2f}s "
                    f"(tight slot {rec.tight_window:.2f}s, {_fmt_ratio(ratio)}, {rate_text})"
                ),
                suggestion=f"cut about {max(1, round(over_loose * syllables_per_second))} akshara",
                note="risk, not failure: the window describes the English performance",
            )))
        elif over_tight > 0:
            ranked.append((ratio or 0.0, make_flag(
                line_id=rec.line_id,
                check="timing",
                severity="medium",
                verdict="over_slot",
                evidence=(
                    f"estimate {est:.2f}s exceeds the {rec.tight_window:.2f}s slot by more than "
                    f"{margin:.0%} ({_fmt_ratio(ratio)}, {rate_text})"
                ),
                suggestion=f"trim to {int(rec.tight_window * (1 + margin) * syllables_per_second)} akshara or less",
                note="risk, not failure: dubbing can retime or trim a line",
            )))

    # chain totals: a sentence split over two slots must fit the combined window
    chains: dict[str, list[DialogueLine]] = {}
    for rec in lines:
        if rec.chain_id:
            chains.setdefault(rec.chain_id, []).append(rec)
    for chain_id, recs in sorted(chains.items()):
        total_est = 0.0
        total_slot = 0.0
        parts = []
        for rec in recs:
            if not rec.telugu or not has_telugu(rec.telugu):
                continue
            total_est += estimate_duration(rec.telugu, syllables_per_second)
            total_slot += rec.tight_window
            parts.append(rec.line_id)
        if not parts or not total_slot:
            continue
        chain_ratio = total_est / total_slot
        if chain_ratio > 1 + margin:
            ranked.append((chain_ratio, make_flag(
                line_id=parts[0],
                check="timing",
                severity="medium",
                verdict="chain_over_slot",
                evidence=(
                    f"chain {chain_id} ({', '.join(parts)}) estimated {total_est:.2f}s against "
                    f"{total_slot:.2f}s of combined slot ({chain_ratio:.2f}x)"
                ),
                suggestion="translate the whole chain as one Telugu sentence, then split it at a natural break",
                note="verb-final Telugu cannot be built fragment by fragment",
            )))

    ranked.sort(key=lambda pair: pair[0], reverse=True)
    flags = [flag for _, flag in ranked]

    ratios = sorted(row["telugu_to_slot_ratio"] for row in table if row["telugu_to_slot_ratio"])

    def pct(p: float) -> float | None:
        if not ratios:
            return None
        return ratios[min(len(ratios) - 1, int(len(ratios) * p))]

    summary = {
        "syllables_per_second": syllables_per_second,
        "margin": margin,
        "lines_checked": len(table),
        "lines_without_telugu": skipped_no_telugu,
        "lines_not_in_telugu_script": skipped_not_telugu_script,
        "chains_checked": len(chains),
        "english_baseline_words_per_second": english_words_per_second,
        "ratio_to_tight_slot": {
            "median": pct(0.5),
            "p75": pct(0.75),
            "p90": pct(0.9),
            "max": ratios[-1] if ratios else None,
        },
        "share_over_tight_with_margin": (
            round(sum(1 for r in ratios if r > 1 + margin) / len(ratios), 3) if ratios else None
        ),
        "selectivity_note": (
            "A share near 1.0 means this check is shortlisting nothing: either the rate is not calibrated "
            "for this show yet, or the draft really does overrun every slot. Read the median ratio before "
            "trusting the flag list."
        ),
    }
    return flags, table, summary
