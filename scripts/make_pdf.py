#!/usr/bin/env python3
"""Render the submitted two-page solution doc to PDF.

    python scripts/make_pdf.py            # writes DramAdapt_QA_solution.pdf at the repository root
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
PAGE = ROOT / "build" / "two_pages.html"
OUT = ROOT / "DramAdapt_QA_solution.pdf"
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


def build(font_pt: float, out: Path) -> int:
    STYLE.write_text(STYLE_CSS.replace("__BASE__", f"{font_pt:g}"), encoding="utf-8")
    subprocess.run(["pandoc", str(SRC), "--standalone", f"--include-in-header={STYLE}",
                    "--metadata", "title=DramAdapt QA - solution summary", "-o", str(PAGE)],
                   check=True)
    subprocess.run([chrome(), "--headless", "--disable-gpu", "--no-pdf-header-footer",
                    f"--print-to-pdf={out}", PAGE.as_uri()], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return count_pages(out)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--keep", action="store_true", help="keep the intermediate HTML")
    ap.add_argument("--font-pt", type=float, default=None,
                    help="base type size; default searches downward from 10pt for the largest "
                         "size that still prints in the page budget")
    ap.add_argument("--sweep", action="store_true", help="print the page count at each size, fit or not")
    args = ap.parse_args()

    if not SRC.exists():
        sys.exit(f"missing source: {SRC}")
    STYLE.parent.mkdir(parents=True, exist_ok=True)

    if args.font_pt:
        sizes = [args.font_pt]
    elif args.sweep:
        sizes = [round(10 - 0.2 * i, 1) for i in range(11)]
    else:
        sizes = [round(10 - 0.1 * i, 1) for i in range(21)]

    chosen, pages = None, None
    for size in sizes:
        pages = build(size, OUT)
        if args.sweep:
            print(f"{size:4.1f}pt -> {pages} page{'s' if pages > 1 else ''}"
                  f"{', within budget' if pages <= MAX_PAGES else ''}")
            if pages <= MAX_PAGES and chosen is None:
                chosen = size
            continue
        if pages <= MAX_PAGES:
            chosen = size
            break

    if chosen is None:
        print(f"FAIL: {pages} pages even at {sizes[-1]:g}pt; the brief asks for {MAX_PAGES}."
              " Cut text - do not buy pages with an 8pt font.", file=sys.stderr)
        return 1
    if args.sweep:
        return 0
    if not args.keep:
        STYLE.unlink(missing_ok=True)
        PAGE.unlink(missing_ok=True)
    print(f"wrote {OUT.relative_to(ROOT)} at {chosen:g}pt base, {MAX_PAGES} pages,"
          f" {OUT.stat().st_size:,} bytes")
    return 0


STYLE_CSS = """<style>
@page { size: A4; margin: 10mm 12mm 10mm 12mm; }
:root { --ink: #14181c; --muted: #4a5560; --accent: #0f4c5c; --rule: #ccd6da; --band: #eef3f5; }
html { font-family: "Segoe UI", "Nirmala UI", "Noto Sans Telugu", sans-serif; }
body { font-size: __BASE__pt; line-height: 1.34; color: var(--ink); margin: 0; max-width: none;
       hyphens: none; text-wrap: pretty; }
h1 { font-size: 1.62em; font-weight: 700; letter-spacing: -0.3pt; line-height: 1.12;
     margin: 0 0 2.5pt; color: var(--accent); }
h1 + p { font-size: 0.92em; color: var(--muted); margin: 0 0 5.5pt; padding-bottom: 4pt;
         border-bottom: 2pt solid var(--accent); }
h2 { font-size: 1.04em; font-weight: 700; letter-spacing: 0.5pt; text-transform: uppercase;
     margin: 7.5pt 0 3pt; color: var(--accent); break-after: avoid; }
h3 { font-size: 1.0em; font-weight: 700; margin: 5pt 0 1.5pt; break-after: avoid; }
p, li { margin: 2.2pt 0; orphans: 2; widows: 2; }
ul, ol { margin: 2.4pt 0 2.4pt 12pt; padding: 0; }
li { margin: 1.8pt 0; }
li::marker { color: var(--accent); }
strong { color: #000; }
blockquote { margin: 4pt 0; padding: 3.5pt 8pt; background: var(--band);
             border-left: 3pt solid var(--accent); border-radius: 1.5pt; break-inside: avoid; }
blockquote p { margin: 0.5pt 0; }
table { border-collapse: collapse; width: 100%; font-size: 0.9em; margin: 4pt 0 5pt; }
th, td { border: 0; padding: 2pt 7pt 2pt 0; text-align: left; vertical-align: top;
         border-bottom: 0.4pt solid var(--rule); }
th { font-size: 0.92em; font-weight: 700; letter-spacing: 0.4pt; text-transform: uppercase;
     color: var(--accent); border-bottom: 1pt solid var(--accent); padding-bottom: 2.4pt; }
tbody tr:nth-child(even) td { background: #f7fafb; }
td:last-child, th:last-child { padding-right: 0; }
code { font-family: "Consolas", monospace; font-size: 0.88em; background: #f1f4f5; padding: 0 1.2pt;
       border-radius: 1.5pt; }
pre { background: #f6f6f6; padding: 3pt; white-space: pre-wrap; font-size: 0.88em; }
hr { border: 0; border-top: 0.6pt solid var(--rule); margin: 6pt 0; }
header#title-block-header { display: none; }
@media print { body { -webkit-print-color-adjust: exact; print-color-adjust: exact; } }
</style>
"""

if __name__ == "__main__":
    raise SystemExit(main())
