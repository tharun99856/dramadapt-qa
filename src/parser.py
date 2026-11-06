"""Screenplay parser for the pack block format used by data/screenplay/.

Never silently drops a block: anything unrecognised is returned in `warnings`
with file name and line number.
"""

from __future__ import annotations

import csv
import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path

NON_DIALOGUE_LABELS = {"CAMERA", "ACTION", "SOUND FX"}
VO_RE = re.compile(r"\bV\.?\s*O\.?\b|\bVOICE-?OVER\b", re.I)
OS_RE = re.compile(r"\bO\.?\s*S\.?\b|\bOFF-?SCREEN\b", re.I)
LABEL_RE = re.compile(r"^(?P<label>[^(\[:]+?)(?:\s*\((?P<delivery>[^)]*)\))?\s*:\s*$")
RANGE_RE = re.compile(r"^\[(?P<a>[\d:.,]+)\s*(?:-|\u2013|\u2014|\u2212)\s*(?P<b>[\d:.,]+)\]$")
SCENE_TIME_RE = re.compile(
    r"^\[\s*Scene\s*(?P<what>Start|End)\s*:\s*(?P<a>[\d:.,]+)(?:\s*(?:-|\u2013|\u2014|\u2212)\s*(?P<b>[\d:.,]+))?\s*\]$",
    re.I,
)
SCENE_RE = re.compile(r"^SCENE\s+(?P<n>\d+)\s*$", re.I)
HEADER_RE = re.compile(r"^(?P<key>EPISODE NUMBER|EPISODE LOGLINE|CONTINUITY NOTES)\s*:\s*(?P<val>.*)$", re.I)
QUOTE_PAIRS = [('"', '"'), ("\u201c", "\u201d")]


def norm_time(raw: str) -> float | None:
    text = raw.strip().replace(",", ".").rstrip(".")
    if not text:
        return None
    parts = text.split(":")
    try:
        nums = [float(p) for p in parts]
    except ValueError:
        return None
    if len(nums) == 1:
        return nums[0]
    if len(nums) == 2:
        return nums[0] * 60 + nums[1]
    if len(nums) == 3:
        return nums[0] * 3600 + nums[1] * 60 + nums[2]
    return None


def clean_text(text: str) -> str:
    out = " ".join(text.split())
    for open_q, close_q in QUOTE_PAIRS:
        stripped = out.strip()
        if stripped.startswith(open_q) and stripped.endswith(close_q):
            return stripped[len(open_q):len(stripped) - len(close_q) or None].strip()
    return out.strip().strip('"').strip()


def ends_with_ellipsis(text: str) -> bool:
    return text.rstrip().endswith(("...", "\u2026"))


def starts_with_ellipsis(text: str) -> bool:
    return text.lstrip().startswith(("...", "\u2026"))


@dataclass
class Warning:
    file: str
    line: int
    kind: str
    detail: str


@dataclass
class DialogueLine:
    line_id: str
    episode: int
    scene: int
    scene_heading: str
    speaker_label: str
    canonical_speaker: str
    delivery_tag: str
    voice_over: bool
    off_screen: bool
    chain_id: str
    chain_kind: str
    chain_position: int
    chain_length: int
    start: float
    end: float
    tight_window: float
    loose_window: float
    text: str
    telugu: str
    nearby_action: str
    source_file: str
    source_line: int
    word_count: int = 0
    flags: list[str] = field(default_factory=list)


@dataclass
class ParseResult:
    records: list[DialogueLine]
    warnings: list[Warning]
    episode_count: int = 0
    block_count: int = 0
    non_dialogue_count: int = 0
    unparsed_blocks: int = 0
    files: list[str] = field(default_factory=list)


def parse_file(path: Path, alias_map: list[dict] | None = None) -> tuple[list[DialogueLine], list[Warning], dict]:
    warnings: list[Warning] = []
    raw = path.read_text(encoding="utf-8").splitlines()
    fname = path.name

    episode = 0
    logline = ""
    continuity = ""
    scene = 0
    scene_heading = ""
    scene_start: float | None = None
    scene_end: float | None = None

    blocks: list[dict] = []
    current: dict | None = None

    for idx, rawline in enumerate(raw, start=1):
        line = rawline.rstrip()
        stripped = line.strip()
        if not stripped:
            continue

        m = HEADER_RE.match(stripped)
        if m:
            key = m.group("key").upper()
            val = m.group("val").strip()
            if key == "EPISODE NUMBER":
                num = norm_time(val)
                if num is None:
                    warnings.append(Warning(fname, idx, "header", f"unparsable EPISODE NUMBER: {val!r}"))
                else:
                    episode = int(num)
            elif key == "EPISODE LOGLINE":
                logline = val
            else:
                continuity = val
            continue

        if stripped.upper() in ("[SCRIPT START]", "[SCRIPT END]"):
            continue

        if SCENE_RE.match(stripped):
            if current:
                blocks.append(current)
                current = None
            scene = int(SCENE_RE.match(stripped).group("n"))
            scene_heading = ""
            scene_start = scene_end = None
            continue

        m = SCENE_TIME_RE.match(stripped)
        if m:
            a = norm_time(m.group("a"))
            b = norm_time(m.group("b")) if m.group("b") else None
            what = m.group("what").lower()
            if what == "start":
                scene_start = a
                if b is not None:
                    scene_end = b
            else:
                scene_end = a
                if b is not None:
                    scene_start = a
                    scene_end = b
            continue

        if current is None and not stripped.startswith("[") and not stripped.endswith(":"):
            if re.match(r"^(INT\.|EXT\.|I/E\.|INT/EXT\.)", stripped, re.I) and not scene_heading:
                scene_heading = stripped
                continue

        if stripped.endswith(":") and not stripped.startswith("["):
            lm = LABEL_RE.match(stripped)
            if lm:
                if current:
                    blocks.append(current)
                current = {
                    "label": lm.group("label").strip(),
                    "delivery": (lm.group("delivery") or "").strip(),
                    "start": None,
                    "end": None,
                    "text": [],
                    "line": idx,
                    "scene": scene,
                    "heading": scene_heading,
                    "scene_end": scene_end,
                }
                continue
            warnings.append(Warning(fname, idx, "label", f"block label not recognised: {stripped!r}"))
            continue

        if current is not None and stripped.startswith("[") and stripped.endswith("]"):
            rm = RANGE_RE.match(stripped)
            if rm:
                current["start"] = norm_time(rm.group("a"))
                current["end"] = norm_time(rm.group("b"))
                continue
            warnings.append(Warning(fname, idx, "time", f"time range not parsable: {stripped!r}"))
            continue

        if current is not None:
            current["text"].append(stripped)
            continue

        warnings.append(Warning(fname, idx, "stray", f"text outside any block: {stripped!r}"))

    if current:
        blocks.append(current)

    records: list[DialogueLine] = []
    non_dialogue = 0
    dialogue_no = 0
    recent_scene_blocks: list[tuple[str, str]] = []

    for block in blocks:
        label_key = re.sub(r"\s+", " ", block["label"].strip().upper())
        if label_key in NON_DIALOGUE_LABELS:
            non_dialogue += 1
            recent_scene_blocks.append((label_key, clean_text(" ".join(block["text"]))))
            recent_scene_blocks = recent_scene_blocks[-3:]
            continue

        body = " ".join(block["text"]).strip()
        if not body:
            warnings.append(Warning(fname, block["line"], "empty", f"block {block['label']!r} has no text"))
            continue
        quoted = body.startswith(tuple(q for q, _ in QUOTE_PAIRS)) or body.endswith(tuple(q for _, q in QUOTE_PAIRS))
        if not quoted:
            warnings.append(
                Warning(
                    fname,
                    block["line"],
                    "unquoted",
                    f"speaker block {block['label']!r} is not quoted, so it is not treated as dialogue: {body[:60]!r}",
                )
            )
            continue
        if block["start"] is None or block["end"] is None:
            warnings.append(Warning(fname, block["line"], "time", f"speaker block {block['label']!r} has no usable time range"))
            continue
        if block["end"] <= block["start"]:
            warnings.append(
                Warning(fname, block["line"], "badwindow", f"end {block['end']} <= start {block['start']} for {block['label']!r}")
            )

        label_base, vo_label, os_label = strip_speech_tags(block["label"])
        tag_text = block["delivery"]
        vo = vo_label or bool(VO_RE.search(tag_text))
        os_ = os_label or bool(OS_RE.search(tag_text))

        dialogue_no += 1
        records.append(
            DialogueLine(
                line_id=f"E{episode:02d}-L{dialogue_no:03d}",
                episode=episode,
                scene=block["scene"],
                scene_heading=block["heading"],
                speaker_label=block["label"].strip(),
                canonical_speaker=resolve_speaker(block["label"].strip(), episode, alias_map, warnings, fname, block["line"]),
                delivery_tag=block["delivery"],
                voice_over=vo,
                off_screen=os_,
                chain_id="",
                chain_kind="",
                chain_position=0,
                chain_length=1,
                start=block["start"],
                end=block["end"],
                tight_window=round(block["end"] - block["start"], 3),
                loose_window=round(block["end"] - block["start"], 3),
                text=clean_text(body),
                telugu="",
                nearby_action=" | ".join(t for _, t in recent_scene_blocks[-2:]),
                source_file=fname,
                source_line=block["line"],
                word_count=len([w for w in re.split(r"\s+", body.strip('"')) if w]),
                flags=["voice-over"] if vo else (["off-screen"] if os_ else []),
            )
        )
        recent_scene_blocks.append(("SPEAKER", clean_text(body)))

    meta = {
        "episode": episode,
        "logline": logline,
        "continuity": continuity,
        "blocks": len(blocks),
        "non_dialogue": non_dialogue,
    }
    return records, warnings, meta


def strip_speech_tags(label: str) -> tuple[str, bool, bool]:
    """Return (label without V.O./O.S. noise, voice_over, off_screen)."""
    vo = bool(VO_RE.search(label))
    os_ = bool(OS_RE.search(label))
    base = OS_RE.sub(" ", VO_RE.sub(" ", label))
    base = re.sub(r"[(),]", " ", base)
    base = re.sub(r"\s+", " ", base).strip(" .-")
    return base.upper(), vo, os_


def resolve_speaker(label: str, episode: int, alias_map: list[dict] | None, warnings: list[Warning], fname: str, lineno: int) -> str:
    base, _, _ = strip_speech_tags(label)
    for entry in alias_map or []:
        if entry["label"].upper() != base:
            continue
        if in_range(episode, entry.get("episodes", "")):
            return entry["canonical"]
    warnings.append(Warning(fname, lineno, "alias", f"speaker label {label!r} not in alias map; kept as written"))
    return base


def in_range(episode: int, spec: object) -> bool:
    spec = str(spec if spec is not None else "").strip()
    if not spec or spec == "*":
        return True
    for part in spec.split(","):
        part = part.strip()
        if "-" in part:
            a, b = part.split("-", 1)
            try:
                if int(a) <= episode <= int(b):
                    return True
            except ValueError:
                return False
        elif part.isdigit() and episode == int(part):
            return True
    return False


def link_chains(records: list[DialogueLine], warnings: list[Warning]) -> None:
    """Group split sentences. Telugu is verb-final, so a fragment cannot be judged alone.

    A chain is a line ending in an ellipsis followed by a line starting with one. Two
    speakers can share a chain when one finishes the other's sentence; that is recorded
    as an interlocked chain rather than dropped.
    """
    by_episode: dict[int, list[DialogueLine]] = {}
    for rec in records:
        by_episode.setdefault(rec.episode, []).append(rec)
    chain_no = 0
    for episode, recs in sorted(by_episode.items()):
        for i, rec in enumerate(recs):
            if rec.chain_id or not ends_with_ellipsis(rec.text):
                continue
            nxt = recs[i + 1] if i + 1 < len(recs) else None
            if nxt is None or nxt.source_file != rec.source_file or not starts_with_ellipsis(nxt.text):
                rec.flags.append("trails-off")
                warnings.append(
                    Warning(rec.source_file, rec.source_line, "fragment", f"{rec.line_id} trails off with no following fragment")
                )
                continue
            chain_no += 1
            cid = f"C{episode:02d}-{chain_no:03d}"
            same_speaker = rec.speaker_label.strip().upper() == nxt.speaker_label.strip().upper()
            kind = "same-speaker" if same_speaker else "interlocked"
            rec.chain_id, nxt.chain_id = cid, cid
            rec.chain_kind, nxt.chain_kind = kind, kind
            rec.chain_length = nxt.chain_length = 2
            rec.chain_position, nxt.chain_position = 1, 2
            rec.flags.append("chain")
            nxt.flags.append("chain")
    for rec in records:
        if not rec.chain_id and starts_with_ellipsis(rec.text):
            rec.flags.append("continues-in")
            warnings.append(
                Warning(rec.source_file, rec.source_line, "fragment", f"{rec.line_id} starts mid-sentence with no previous fragment")
            )


def assign_windows(records: list[DialogueLine]) -> None:
    by_ep: dict[int, list[DialogueLine]] = {}
    for rec in records:
        by_ep.setdefault(rec.episode, []).append(rec)
    for recs in by_ep.values():
        recs.sort(key=lambda r: (r.source_file, r.start, r.line_id))
        for i, rec in enumerate(recs):
            nxt = recs[i + 1] if i + 1 < len(recs) else None
            if nxt and nxt.source_file == rec.source_file:
                loose = nxt.start - rec.start
            else:
                loose = rec.tight_window
            loose = max(loose, rec.tight_window)
            rec.loose_window = round(min(loose, 600.0), 3)


def parse_screenplay(path: Path, alias_map: list[dict] | None = None) -> ParseResult:
    """One screenplay file or a whole directory of them.

    The interview rerun hands us a new input (PRD 7.1, brief: "you'll run your solution on a new
    input"), so this is the single entry point that does not care which it got.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"no screenplay at {path}")
    files = sorted(p for p in path.glob("*.txt")) if path.is_dir() else [path]
    if not files:
        raise FileNotFoundError(f"{path} is a directory with no .txt files in it")
    return load_files(files, alias_map)


def load_files(files: list[Path], alias_map: list[dict] | None = None) -> ParseResult:
    all_records: list[DialogueLine] = []
    all_warnings: list[Warning] = []
    blocks = non_dialogue = 0
    for path in files:
        recs, warns, meta = parse_file(path, alias_map)
        all_records.extend(recs)
        all_warnings.extend(warns)
        blocks += meta["blocks"]
        non_dialogue += meta["non_dialogue"]
    link_chains(all_records, all_warnings)
    assign_windows(all_records)
    all_records.sort(key=lambda r: (r.source_file, r.start, r.line_id))
    unparsed = [w for w in all_warnings if w.kind in ("stray", "label", "time", "empty", "unquoted", "badwindow")]
    return ParseResult(
        records=all_records,
        warnings=all_warnings,
        episode_count=len(files),
        block_count=blocks,
        non_dialogue_count=non_dialogue,
        unparsed_blocks=len(unparsed),
        files=[p.name for p in files],
    )


def load_corpus(screenplay_dir: Path, alias_map: list[dict] | None = None) -> ParseResult:
    return load_files(sorted(p for p in Path(screenplay_dir).glob("*.txt")), alias_map)


def to_dict(rec: DialogueLine) -> dict:
    return asdict(rec)


def write_json(result: ParseResult, path: Path) -> None:
    payload = {
        "files": result.files,
        "episode_files": result.episode_count,
        "blocks": result.block_count,
        "non_dialogue_blocks": result.non_dialogue_count,
        "dialogue_lines": len(result.records),
        "records": [to_dict(r) for r in result.records],
        "warnings": [asdict(w) for w in result.warnings],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


CSV_FIELDS = [
    "line_id", "episode", "scene", "scene_heading", "speaker_label", "canonical_speaker", "delivery_tag",
    "voice_over", "off_screen", "chain_id", "chain_kind", "chain_position", "chain_length", "start", "end",
    "tight_window", "loose_window", "text", "telugu", "nearby_action", "source_file", "source_line",
    "word_count", "flags",
]


def write_csv(result: ParseResult, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=CSV_FIELDS)
        writer.writeheader()
        for rec in result.records:
            row = to_dict(rec)
            row["flags"] = ";".join(rec.flags)
            writer.writerow({k: row[k] for k in CSV_FIELDS})


def load_parsed(path: Path) -> list[DialogueLine]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    out = []
    for item in payload["records"]:
        item = dict(item)
        item["flags"] = list(item.get("flags") or [])
        out.append(DialogueLine(**item))
    return out
