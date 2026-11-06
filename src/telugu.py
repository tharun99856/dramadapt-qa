"""Telugu syllable (akshara) counting and the timing estimate.

An akshara is a spoken syllable: a consonant with its inherent or explicit vowel, with a
conjunct (consonant + virama + consonant) counting as one. Counting base letters and
subtracting viramas gives that directly, and needs no segmentation dictionary.
"""

from __future__ import annotations

import re
import unicodedata

TELUGU = (0x0C00, 0x0C7F)
VOWEL_BASE = (0x0C05, 0x0C14)
CONSONANT_BASE = (0x0C15, 0x0C39)
VIRAMA = 0x0C4D


def telugu_chars(text: str) -> list[str]:
    return [ch for ch in text if TELUGU[0] <= ord(ch) <= TELUGU[1]]


def akshara_count(text: str) -> int:
    letters = 0
    viramas = 0
    for ch in telugu_chars(text):
        code = ord(ch)
        if VOWEL_BASE[0] <= code <= VOWEL_BASE[1] or CONSONANT_BASE[0] <= code <= CONSONANT_BASE[1]:
            letters += 1
        elif code == VIRAMA:
            viramas += 1
    return max(letters - viramas, 0)


def latin_word_count(text: str) -> int:
    return len([w for w in re.split(r"\s+", text.strip()) if w])


def has_telugu(text: str) -> bool:
    return bool(telugu_chars(text))


def script_name(text: str) -> str:
    counts: dict[str, int] = {}
    for ch in text:
        if ch.isspace():
            continue
        name = unicodedata.name(ch, "OTHER").split(" ")[0]
        key = "TELUGU" if TELUGU[0] <= ord(ch) <= TELUGU[1] else ("LATIN" if "LATIN" in name else name)
        counts[key] = counts.get(key, 0) + 1
    if not counts:
        return "empty"
    return max(counts, key=counts.get)


def script_share(text: str) -> dict[str, float]:
    """Letter-class proportions over the letters that are words, not punctuation."""
    letters = [ch for ch in text if ch.isalpha()]
    if not letters:
        return {"telugu": 0.0, "latin": 0.0, "other": 0.0}
    telugu = sum(1 for ch in letters if TELUGU[0] <= ord(ch) <= TELUGU[1])
    latin = sum(1 for ch in letters if "LATIN" in unicodedata.name(ch, ""))
    n = len(letters)
    return {"telugu": telugu / n, "latin": latin / n, "other": (n - telugu - latin) / n}


def estimate_duration(telugu: str, syllables_per_second: float) -> float:
    if not syllables_per_second or syllables_per_second <= 0:
        raise ValueError("syllables_per_second is not calibrated")
    return akshara_count(telugu) / syllables_per_second
