#!/usr/bin/env python3
"""Parse every screenplay file in data/screenplay/ and run the addendum §7 acceptance tests.

    python scripts/parse_corpus.py            # parse + write data/parsed/ + tests
    python scripts/parse_corpus.py --quiet
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.parser import load_corpus, to_dict, write_csv, write_json  # noqa: E402
from src.console import force_utf8  # noqa: E402


def independent_dialogue_count(path: Path) -> int:
    """Deliberately dumb second count for acceptance test 1: labeled block + quoted text."""
    lines = path.read_text(encoding="utf-8").splitlines()
    count = 0
    for i, line in enumerate(lines):
        s = line.strip()
        if not s.endswith(":") or s.startswith("["):
            continue
        label = re.split(r"[\(:]", s)[0].strip().upper()
        if label in {"CAMERA", "ACTION", "SOUND FX"} or label.startswith(("EPISODE", "CONTINUITY")):
            continue
        nxt = lines[i + 1].strip() if i + 1 < len(lines) else ""
        after = lines[i + 2].strip() if i + 2 < len(lines) else ""
        if re.match(r"^\[.*\]$", nxt) and (after.startswith('"') or after.startswith("“")):
            count += 1
    return count


def main() -> int:
    force_utf8()
    ap = argparse.ArgumentParser()
    ap.add_argument("--screenplay-dir", default=str(ROOT / "data" / "screenplay"))
    ap.add_argument("--out-dir", default=str(ROOT / "data" / "parsed"))
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    alias_path = ROOT / "data" / "alias_map.yaml"
    alias_map = yaml.safe_load(alias_path.read_text(encoding="utf-8")) if alias_path.exists() else []

    screenplay_dir = Path(args.screenplay_dir)
    result = load_corpus(screenplay_dir, alias_map)

    out_dir = Path(args.out_dir)
    write_json(result, out_dir / "corpus.json")
    write_csv(result, out_dir / "corpus.csv")

    failures: list[str] = []
    report: list[str] = []

    # Test 1 - count against an independent pass over the raw files.
    per_file: dict[str, int] = {}
    for rec in result.records:
        per_file[rec.source_file] = per_file.get(rec.source_file, 0) + 1
    for path in sorted(screenplay_dir.glob("*.txt")):
        mine = independent_dialogue_count(path)
        theirs = per_file.get(path.name, 0)
        report.append(f"count {path.name}: parser={theirs} independent={mine}")
        if mine != theirs:
            failures.append(f"count mismatch in {path.name}: {theirs} vs {mine}")

    # Test 2 - window sanity.
    bad = [r for r in result.records if r.end <= r.start]
    report.append(f"end>start for all lines: {'PASS' if not bad else 'FAIL ' + str([b.line_id for b in bad])}")
    if bad:
        failures.append(f"{len(bad)} lines with end <= start")

    # Test 3 - no empty speaker or text.
    empty = [r for r in result.records if not r.canonical_speaker or not r.text]
    report.append(f"no empty speaker/text: {'PASS' if not empty else 'FAIL ' + str([e.line_id for e in empty])}")
    if empty:
        failures.append(f"{len(empty)} lines with empty speaker or text")

    # Test 4 - silent drops.
    drops = [w for w in result.warnings if w.kind in ("stray", "label", "unquoted", "empty")]
    alias_warns = [w for w in result.warnings if w.kind == "alias"]
    report.append(f"silent drops: {len(drops)} | alias-map misses: {len(alias_warns)} | total warnings: {len(result.warnings)}")
    if drops:
        failures.append(f"{len(drops)} blocks dropped or unquoted")

    # Test 5 - header drift: episode 4 uses en dashes in times and headings.
    ep4 = [r for r in result.records if r.source_file == "episode-004.txt"]
    heading_ok = any("–" in r.scene_heading for r in ep4)
    report.append(f"header drift (episode-004 en dash heading parsed): {'PASS' if heading_ok and ep4 else 'FAIL'}")
    if not (heading_ok and ep4):
        failures.append("episode-004 heading drift not handled")

    # Test 6 - unknown format must report, not crash.
    fixture = ROOT / "data" / "format_drift_fixture.txt"
    if fixture.exists():
        try:
            from src.parser import parse_file

            frecs, fwarns, _ = parse_file(fixture, alias_map)
            report.append(f"new-format fixture: parsed={len(frecs)} reported_warnings={len(fwarns)} (no crash)")
            if not fwarns:
                failures.append("format fixture produced no report entries")
        except Exception as exc:  # noqa: BLE001
            failures.append(f"format fixture crashed: {exc!r}")
    else:
        report.append("new-format fixture: data/format_drift_fixture.txt missing")

    chains = {r.chain_id for r in result.records if r.chain_id}
    summary = {
        "files": len(result.files),
        "blocks": result.block_count,
        "non_dialogue_blocks": result.non_dialogue_count,
        "dialogue_lines": len(result.records),
        "chains": len(chains),
        "voice_over": sum(1 for r in result.records if r.voice_over),
        "off_screen": sum(1 for r in result.records if r.off_screen),
        "canonical_speakers": len({r.canonical_speaker for r in result.records}),
    }

    if not args.quiet:
        print("=== parse report ===")
        for line in report:
            print(" ", line)
        print("=== summary ===")
        for k, v in summary.items():
            print(f"  {k}: {v}")
        if result.warnings:
            print("=== warnings (first 20) ===")
            for w in result.warnings[:20]:
                print(f"  {w.file}:{w.line} [{w.kind}] {w.detail}")
        print("=== acceptance tests ===")
        print("  " + ("ALL PASS" if not failures else "FAILURES:\n  " + "\n  ".join(failures)))

    (out_dir / "validation_report.md").write_text(
        "\n".join(
            [
                "# Parser validation report",
                "",
                "## Summary",
                "",
                *[f"- {k}: {v}" for k, v in summary.items()],
                "",
                "## Acceptance tests",
                "",
                *[f"- {line}" for line in report],
                "",
                "## Result",
                "",
                "PASS" if not failures else "FAIL\n\n" + "\n".join(f"- {f}" for f in failures),
                "",
                "## Warnings",
                "",
                *(
                    [f"- `{w.file}:{w.line}` [{w.kind}] {w.detail}" for w in result.warnings]
                    or ["none"]
                ),
                "",
            ]
        ),
        encoding="utf-8",
    )
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
