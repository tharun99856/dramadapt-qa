#!/usr/bin/env python3
"""Render the submitted two-page solution doc to PDF.

    python scripts/make_pdf.py            # writes docs/DramAdapt_QA_solution.pdf
    python scripts/make_pdf.py --keep     # leave build/two_pages.html behind

Needs pandoc and Chrome (or Chromium) on PATH; both are already used by the build. The page budget is
the point of the exercise, so the script fails if the result is longer than two pages - a doc that
quietly grows to five is not the two-page doc the brief asks for.
"""

from __future__ import annotations

import argparse
import glob
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "docs" / "solution_two_pages.md"
STYLE = ROOT / "build" / "print_style.html"
HTML = ROOT / "build" / "two_pages.html"
OUT = ROOT / "docs" / "DramAdapt_QA_solution.pdf"
MAX_PAGES = 2


def chrome() -> str:
    for name in ("chrome", "chromium", "google-chrome", "chromium-browser"):
        if shutil.which(name):
            return name
    hits = glob.glob(r"C:/Program Files*/Google/Chrome/Application/chrome.exe")
    hits += glob.glob(r"C:/Program Files*/Microsoft/Edge/Application/msedge.exe")
    if hits:
        return hits[0].replace("\\", "/")
    sys.exit("no Chrome/Chromium/Edge found; install one or print docs/solution_two_pages.md by hand")


def count_pages(pdf: Path) -> int:
    """Page count without a PDF library: the /Pages object carries /Count."""
    import re
    counts = [int(m) for m in re.findall(rb"/Type\s*/Pages[^>]*?/Count\s+(\d+)", pdf.read_bytes())]
    if not counts:
        sys.exit(f"could not read a page count out of {pdf}; open it and check the length by eye")
    return max(counts)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--keep", action="store_true", help="keep the intermediate HTML")
    args = ap.parse_args()

    if not SRC.exists():
        sys.exit(f"missing source: {SRC}")
    STYLE.parent.mkdir(parents=True, exist_ok=True)
    STYLE.write_text(STYLE_CSS, encoding="utf-8")

    subprocess.run(["pandoc", str(SRC), "--standalone", f"--include-in-header={STYLE}",
                    "--metadata", "title=DramAdapt QA - solution summary", "-o", str(HTML)],
                   check=True)
    subprocess.run([chrome(), "--headless", "--disable-gpu", "--no-pdf-header-footer",
                    f"--print-to-pdf={OUT}", HTML.as_uri()], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    pages = count_pages(OUT)
    if not args.keep:
        HTML.unlink(missing_ok=True)
    if pages > MAX_PAGES:
        print(f"FAIL: {pages} pages, the brief asks for {MAX_PAGES}. Cut text; do not shrink the font"
              " below 8pt.", file=sys.stderr)
        return 1
    print(f"wrote {OUT.relative_to(ROOT)} ({pages} pages, {OUT.stat().st_size:,} bytes)")
    return 0


STYLE_CSS = """<style>
@page { size: A4; margin: 12mm 13mm; }
html { font-family: "Segoe UI", "Nirmala UI", sans-serif; }
body { font-size: 8.2pt; line-height: 1.32; color: #111; margin: 0; max-width: none; }
h1 { font-size: 13pt; margin: 0 0 4pt; }
h2 { font-size: 9.6pt; margin: 9pt 0 3pt; border-bottom: 0.6pt solid #999; padding-bottom: 1.5pt; }
h3 { font-size: 8.8pt; margin: 6pt 0 2pt; }
p, li { margin: 2pt 0; }
ul, ol { margin: 2pt 0 2pt 14pt; padding: 0; }
blockquote { margin: 4pt 0; padding: 3pt 7pt; background: #f4f4f4; border-left: 2pt solid #888; }
table { border-collapse: collapse; width: 100%; font-size: 7.6pt; margin: 4pt 0; }
th, td { border: 0.4pt solid #bbb; padding: 1.6pt 3pt; text-align: left; vertical-align: top; }
th { background: #eee; }
code, pre { font-family: "Consolas", monospace; font-size: 7.4pt; }
pre { background: #f6f6f6; padding: 3pt; white-space: pre-wrap; }
h2, h3 { page-break-after: avoid; }
table, blockquote { page-break-inside: avoid; }
header#title-block-header { display: none; }
</style>
"""

if __name__ == "__main__":
    raise SystemExit(main())
