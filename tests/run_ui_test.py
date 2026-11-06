#!/usr/bin/env python3
"""Exercise the review UI the way an editor would, instead of reading it.

    python tests/run_ui_test.py

`AppTest` is the only check that catches what the UI actually does: it raised
`StreamlitDuplicateElementKey` when two timing problems on one line shared a flag id, which no amount
of reading the report had shown. This script is separate from `run_tests.py` because it needs
`streamlit` installed and a `results/<label>_flags.json` to exist.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.console import force_utf8  # noqa: E402
from src.report import flag_id, with_ids  # noqa: E402

FAIL: list[str] = []
PASS: list[str] = []


def check(name: str, got, want) -> None:
    (PASS if got == want else FAIL).append(name if got == want else f"{name}: got {got!r} want {want!r}")


def main() -> int:
    force_utf8()
    runs = sorted(p.name[:-len("_flags.json")] for p in (ROOT / "results").glob("*_flags.json"))
    if not runs:
        print("no results/*_flags.json yet - run scripts/run_structured.py first")
        return 2
    label = "structured" if "structured" in runs else runs[-1]
    payload = json.loads((ROOT / "results" / f"{label}_flags.json").read_text(encoding="utf-8"))
    flags = payload.get("flags", [])
    check("flag ids unique before the UI sees them", len({flag_id(f) for f in with_ids(flags)}), len(flags))

    from streamlit.testing.v1 import AppTest

    at = AppTest.from_file(str(ROOT / "app.py"), default_timeout=180).run()
    check("app renders without an exception", at.exception, [])
    check("summary subheader present", any("Summary" in s.value for s in at.subheader), True)

    radios = [r for r in at.radio if r.key.endswith("_status")]
    check("every flag has its own decision control", len(radios), len(flags))
    check("decision keys are unique", len({r.key for r in radios}), len(radios))

    if flags:
        decisions = ROOT / "data" / "annotation" / "decisions.csv"
        backup = decisions.read_bytes() if decisions.exists() else None
        try:
            radios[0].set_value("dismissed").run()
            check("app survives a dismissal", at.exception, [])
            rows = [line for line in decisions.read_text(encoding="utf-8").splitlines() if line.strip()]
            check("the dismissal was written down", len(rows) >= 2, True)
            dismissed = [line for line in rows[1:] if ",dismissed," in line]
            check("a dismissal reached the file", len(dismissed) >= 1, True)
        finally:
            # this test must not leave a decision the builder never made
            if backup is not None:
                decisions.write_bytes(backup)
            elif decisions.exists():
                decisions.unlink()

    print(f"run under test: {label} ({len(flags)} flags)")
    print(f"{len(PASS)} passed, {len(FAIL)} failed")
    for f in FAIL:
        print("  FAIL " + f)
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
