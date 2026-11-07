"""Loading the Phase 0 sample as parsed lines with the Telugu first pass attached."""

from __future__ import annotations

import json
from pathlib import Path

from .parser import DialogueLine

ROOT = Path(__file__).resolve().parents[1]
SAMPLE_JSON = ROOT / "data" / "annotation" / "sample_lines.json"
TELUGU_JSON = ROOT / "data" / "telugu" / "first_pass.json"
ANNOTATION_CSV = ROOT / "data" / "annotation" / "blind_annotation.csv"
ACCEPTANCE_CSV = ROOT / "data" / "annotation" / "decisions.csv"


class SampleError(RuntimeError):
    pass


def load_sample(telugu_path: Path | None = None) -> tuple[list[DialogueLine], dict]:
    if not SAMPLE_JSON.exists():
        raise SampleError("data/annotation/sample_lines.json missing - run scripts/select_sample.py")
    payload = json.loads(SAMPLE_JSON.read_text(encoding="utf-8"))
    path = Path(telugu_path) if telugu_path else TELUGU_JSON
    # Run artifacts written on Windows store "data\\telugu\\first_pass.json"; on Linux that is one
    # filename with backslashes in it, so a hosted clone would silently load zero Telugu lines.
    if "\\" in str(path):
        path = Path(str(path).replace("\\", "/"))
    if not path.is_absolute():
        path = ROOT / path
    meta = {"seed": payload.get("seed"), "telugu_file": None, "telugu_provenance": None}
    telugu: dict[str, str] = {}
    if path.exists():
        tp = json.loads(path.read_text(encoding="utf-8"))
        telugu = {item["line_id"]: item.get("telugu", "") for item in tp.get("lines", [])}
        meta["telugu_file"] = str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path)
        meta["telugu_provenance"] = tp.get("provenance")
    records: list[DialogueLine] = []
    for item in payload["lines"]:
        data = {k: v for k, v in item.items() if k in DialogueLine.__dataclass_fields__}
        data["telugu"] = telugu.get(item["line_id"], "")
        records.append(DialogueLine(**data))
    if not telugu:
        meta["telugu_note"] = "no Telugu attached yet - run scripts/run_first_pass.py"
    return records, meta


def load_annotations(path: Path | None = None) -> dict[str, dict]:
    import csv

    p = Path(path) if path else ANNOTATION_CSV
    if not p.exists():
        raise SampleError(f"{p.relative_to(ROOT)} missing - fill in the blind annotation sheet")
    out: dict[str, dict] = {}
    with p.open(encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            line_id = (row.get("line_id") or "").strip()
            if line_id:
                out[line_id] = row
    return out


def load_acceptance(path: Path | None = None) -> dict[tuple[str, str], dict]:
    import csv

    p = Path(path) if path else ACCEPTANCE_CSV
    if not p.exists():
        return {}
    out: dict[tuple[str, str], dict] = {}
    with p.open(encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            key = ((row.get("flag_id") or "").strip(), (row.get("line_id") or "").strip())
            if all(key):
                out[key] = row
    return out
