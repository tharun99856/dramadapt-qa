"""Shared corpus access: parsed lines + category tags + relationship-sheet expectations."""

from __future__ import annotations

import csv
import json
import re
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path

import yaml

from .parser import DialogueLine, load_parsed

ROOT = Path(__file__).resolve().parents[1]
SHEET_EDITS = ROOT / "data" / "relationship_sheet_edits.csv"
STANDARD_OVERRIDE = ROOT / "data" / "register_standard_override.json"
SHEET_COLUMNS = ["speaker", "listener", "episodes", "expected_register", "confirmed", "editor_note"]


def _sheet_key(speaker: object, listener: object, episodes: object) -> str:
    return f"{speaker}|{listener}|{episodes}"


def read_sheet_edits() -> dict[str, dict]:
    if not SHEET_EDITS.exists():
        return {}
    out: dict[str, dict] = {}
    with SHEET_EDITS.open(encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            key = _sheet_key(row.get("speaker"), row.get("listener"), row.get("episodes"))
            if key.count("|") == 2:
                out[key] = row
    return out


def write_sheet_edits(rows: list[dict]) -> None:
    """The YAML sheet stays the curated source; editor changes live beside it as an overlay,
    so saving from the UI cannot destroy the comments or the address_shift structure."""
    SHEET_EDITS.parent.mkdir(parents=True, exist_ok=True)
    with SHEET_EDITS.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=SHEET_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow({col: row.get(col, "") for col in SHEET_COLUMNS})
    relationship_sheet.cache_clear()


@lru_cache(maxsize=1)
def rules() -> dict:
    return yaml.safe_load((ROOT / "data" / "category_rules.yaml").read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def relationship_sheet() -> dict:
    sheet = yaml.safe_load((ROOT / "data" / "relationship_sheet.yaml").read_text(encoding="utf-8"))
    edits = read_sheet_edits()
    for row in sheet.get("relationships", []):
        edit = edits.get(_sheet_key(row.get("speaker"), row.get("listener"), row.get("episodes")))
        if not edit:
            continue
        if (edit.get("expected_register") or "").strip():
            row["expected_register"] = edit["expected_register"].strip()
        row["confirmed"] = (edit.get("confirmed") or "").strip().lower() in ("true", "yes", "1")
        if (edit.get("editor_note") or "").strip():
            row["editor_note"] = edit["editor_note"].strip()
    block = sheet.get("telugu_register_standard")
    if isinstance(block, dict) and STANDARD_OVERRIDE.exists():
        override = json.loads(STANDARD_OVERRIDE.read_text(encoding="utf-8"))
        sheet["telugu_register_standard"] = {**block, **override}
    return sheet


def sign_off_register_standard(paragraph: str, status: str, by: str = "builder") -> None:
    """Open item 3 in the addendum: the Telugu register standard needs a human sign-off.
    The UI writes an override rather than rewriting the YAML draft, so the original draft stays on disk."""
    STANDARD_OVERRIDE.write_text(json.dumps({
        "status": status,
        "draft_paragraph": paragraph,
        "signed_off_by": by,
        "signed_off_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    relationship_sheet.cache_clear()


@lru_cache(maxsize=1)
def loglines() -> dict:
    out = {}
    for path in sorted((ROOT / "data" / "screenplay").glob("*.txt")):
        num = None
        logline = ""
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.startswith("EPISODE NUMBER:"):
                num = int(re.sub(r"\D", "", line.split(":", 1)[1]) or 0)
            elif line.startswith("EPISODE LOGLINE:") and num is not None:
                logline = line.split(":", 1)[1].strip()
        if num:
            out[num] = logline
    return out


def _delivery_matches(delivery: str, words: list[str]) -> str | None:
    d = (delivery or "").lower()
    for word in words or []:
        if word.lower() in d:
            return word
    return None


def _pattern_matches(text: str, patterns: list[str]) -> str | None:
    for pat in patterns or []:
        if re.search(pat, text, re.I):
            return pat
    return None


def address_terms_in(text: str) -> list[str]:
    found = []
    for term in rules().get("address_terms", []):
        if re.search(r"(?<![\w])" + re.escape(term) + r"(?![\w])", text):
            if term not in found:
                found.append(term)
    return found


def sheet_markers(rec: DialogueLine) -> list[str]:
    """Relationship-sheet shift markers that this line's text actually contains."""
    hits = []
    lowered = rec.text.lower()
    for row in relationship_sheet().get("relationships", []):
        if row["speaker"] != rec.canonical_speaker:
            continue
        for shift in row.get("address_shifts", []) or []:
            marker = (shift.get("text_marker") or "").lower()
            if marker and marker in lowered:
                hits.append(f"{row['listener']}: {shift.get('text_marker')}")
    return hits


def categories_for(rec: DialogueLine) -> dict:
    r = rules()
    tags: dict[str, str] = {}
    if rec.tight_window < float(r.get("short_slot_seconds", 1.5)):
        tags["short_slot"] = f"slot {rec.tight_window}s < {r.get('short_slot_seconds', 1.5)}s"
    if rec.word_count >= int(r.get("long_line_words", 12)):
        tags["long_line"] = f"{rec.word_count} words"
    if rec.chain_id:
        tags["chain_member"] = f"{rec.chain_id} ({rec.chain_kind})"
    if rec.voice_over or rec.off_screen:
        tags["voice_or_offscreen"] = "voice-over" if rec.voice_over else "off-screen"
    terms = address_terms_in(rec.text)
    markers = sheet_markers(rec)
    if markers:
        tags["address_shift"] = "; ".join(markers)
    elif terms:
        tags["address_term"] = ", ".join(terms)
    tender_pat = _pattern_matches(rec.text, r.get("tender_text", []))
    threat_pat = _pattern_matches(rec.text, r.get("threat_text", []))
    tender_tag = _delivery_matches(rec.delivery_tag, r.get("tender_delivery", []))
    threat_tag = _delivery_matches(rec.delivery_tag, r.get("threat_delivery", []))
    if tender_pat or tender_tag:
        tags["tender_or_intimate"] = tender_pat or f"delivery: {tender_tag}"
    if threat_pat or threat_tag:
        tags["threat_or_accusation"] = threat_pat or f"delivery: {threat_tag}"
    if "threat_or_accusation" in tags and "tender_or_intimate" in tags:
        tags["ambiguous_register"] = "matched both threat and tender rules"
    if not tags:
        tags["general"] = "no category rule matched"
    return tags


def register_expectation(rec: DialogueLine) -> str:
    """The sheet rows that apply to this line's speaker, as one short string."""
    rows = [row for row in relationship_sheet().get("relationships", []) if row["speaker"] == rec.canonical_speaker]
    if not rows:
        return ""
    listeners = {row["listener"]: row for row in rows}
    for listener, row in listeners.items():
        if listener.split(" (")[0].lower() in rec.text.lower():
            terms = ", ".join(row.get("expected_address_terms", []) or []) or "(none listed)"
            return f"to {listener}: {row.get('expected_register', '')} | terms: {terms}"
    parts = []
    for row in rows:
        terms = ", ".join(row.get("expected_address_terms", []) or []) or "-"
        parts.append(f"to {row['listener']}: {row.get('expected_register', '')} ({terms})")
    return " || ".join(parts)


@lru_cache(maxsize=1)
def corpus() -> list[DialogueLine]:
    parsed = ROOT / "data" / "parsed" / "corpus.json"
    if not parsed.exists():
        raise SystemExit("data/parsed/corpus.json missing - run scripts/parse_corpus.py first")
    return load_parsed(parsed)


def by_id() -> dict[str, DialogueLine]:
    return {rec.line_id: rec for rec in corpus()}


def context_for(rec: DialogueLine) -> str:
    parts = [rec.scene_heading, rec.nearby_action, loglines().get(rec.episode, "")]
    return " | ".join(p for p in parts if p)
