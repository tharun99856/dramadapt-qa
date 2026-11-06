"""Windows consoles default to cp1252 and cannot print Telugu. Call this first in every script."""

from __future__ import annotations

import sys


def force_utf8() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass
