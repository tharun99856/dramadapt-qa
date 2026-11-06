"""Scene batching: requests scale with scenes, not lines (PRD §8, §11).

A scene is one request, but a free-tier key caps tokens per minute, so a scene can also be
split when the estimated payload gets big. Lines are cheap to count; chains are not splittable.
"""

from __future__ import annotations

from .parser import DialogueLine

SYSTEM_OVERHEAD_TOKENS = 1200   # instruction + register standard + relationship rows + JSON scaffold


def batch_key(rec: DialogueLine) -> str:
    return f"{rec.source_file}#S{rec.scene:02d}"


def payload_tokens(chunk: list[DialogueLine], extra_chars: int = 0) -> int:
    """Rough token count of what a request would actually carry: the text plus JSON keys."""
    chars = sum(len((rec.text or "") + (rec.telugu or "")) + 60 for rec in chunk)
    return SYSTEM_OVERHEAD_TOKENS + extra_chars // 4 + (chars + 3) // 4


def scene_batches(lines: list[DialogueLine], max_lines: int = 14,
                  max_prompt_tokens: int | None = None) -> list[tuple[str, list[DialogueLine]]]:
    """Group by scene, then split long scenes without ever cutting a chain in half."""
    groups: dict[str, list[DialogueLine]] = {}
    for rec in lines:
        groups.setdefault(batch_key(rec), []).append(rec)
    out: list[tuple[str, list[DialogueLine]]] = []
    for key in sorted(groups):
        recs = sorted(groups[key], key=lambda r: (r.start, r.line_id))
        chunks: list[list[DialogueLine]] = []
        current: list[DialogueLine] = []
        for rec in recs:
            too_many_lines = current and len(current) >= max_lines
            too_many_tokens = bool(current) and max_prompt_tokens and \
                payload_tokens([*current, rec]) > max_prompt_tokens
            if current and (too_many_lines or too_many_tokens):
                # only break here if this line does not continue the previous fragment
                if not rec.chain_id or rec.chain_id != current[-1].chain_id:
                    chunks.append(current)
                    current = []
            current.append(rec)
        if current:
            chunks.append(current)
        for n, chunk in enumerate(chunks, start=1):
            label = key if len(chunks) == 1 else f"{key}#part{n}"
            out.append((label, chunk))
    return out


def chain_members(lines: list[DialogueLine], chain_id: str) -> list[DialogueLine]:
    return [rec for rec in lines if rec.chain_id == chain_id]


def with_chain_partners(lines: list[DialogueLine], pool: list[DialogueLine]) -> list[DialogueLine]:
    """Return lines plus any pool member needed to keep a chain whole."""
    have = {rec.line_id for rec in lines}
    out = list(lines)
    for rec in lines:
        if not rec.chain_id:
            continue
        for other in pool:
            if other.chain_id == rec.chain_id and other.line_id not in have:
                out.append(other)
                have.add(other.line_id)
    return out
