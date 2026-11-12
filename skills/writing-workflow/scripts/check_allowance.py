#!/usr/bin/env python3
"""Measure a deliverable against its allowance: pages of a compiled PDF, or words of text files.

Over the allowance means not done. Used as a `check` of rollout.py write stages: a failing check sends the
writer one retry with this output quoted, so the message says what was measured and what is allowed.

Pages come from the LaTeX log next to the PDF ("Output written on X.pdf (N pages"), else from pdfinfo, else from
counting page objects in an uncompressed PDF. Words are whitespace-separated tokens, as `wc -w` counts them.

Usage:
  check_allowance.py --pdf standalone.pdf --pages 12 [--tolerance 0] [--report-only]
  check_allowance.py --words 2500 outline.md [more.md ...] [--report-only]
--report-only prints the measurement and exits 0 (for sections whose page figures the author made guides).
Exit status: 0 within the allowance (or --report-only), 1 over it, 2 usage or input error (cannot measure).
"""
from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path


def pdf_pages(pdf: Path) -> tuple[int, str]:
    log = pdf.with_suffix(".log")
    if log.is_file() and log.stat().st_mtime >= pdf.stat().st_mtime - 5:
        m = re.findall(r"Output written on .*?\((\d+) pages?", log.read_text(encoding="utf-8", errors="replace"))
        if m:
            return int(m[-1]), f"LaTeX log {log.name}"
    if shutil.which("pdfinfo"):
        r = subprocess.run(["pdfinfo", str(pdf)], capture_output=True, text=True)
        m = re.search(r"^Pages:\s+(\d+)", r.stdout, re.M)
        if r.returncode == 0 and m:
            return int(m.group(1)), "pdfinfo"
    n = len(re.findall(rb"/Type\s*/Page(?![a-zA-Z])", pdf.read_bytes()))
    if n:
        return n, "page objects (uncompressed PDF)"
    raise ValueError(f"cannot count the pages of {pdf} (no LaTeX log, no pdfinfo, compressed page objects)")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="Check a deliverable against its allowance (pages of a PDF or words of text). "
                    "Over the allowance = not done.",
        epilog="examples:\n  check_allowance.py --pdf standalone.pdf --pages 12\n"
               "  check_allowance.py --words 2500 outline.md",
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pdf", help="compiled PDF to measure")
    ap.add_argument("--pages", type=float, help="page allowance")
    ap.add_argument("--words", type=int, help="word allowance for the text files given")
    ap.add_argument("files", nargs="*", help="text files for --words")
    ap.add_argument("--tolerance", type=float, default=0, help="allowed excess (pages or words), default 0")
    ap.add_argument("--report-only", action="store_true", help="print the measurement, never fail")
    a = ap.parse_args(argv)
    try:
        if a.pdf is not None:
            if a.pages is None:
                ap.error("--pdf needs --pages")
            pdf = Path(a.pdf)
            if not pdf.is_file():
                raise ValueError(f"{pdf} does not exist (compile the standalone wrapper first)")
            measured, how = pdf_pages(pdf)
            allowed, unit = a.pages, "pages"
            what = f"{pdf.name}: {measured} pages (from {how})"
        elif a.words is not None:
            if not a.files:
                ap.error("--words needs at least one file")
            measured = sum(len(Path(f).read_text(encoding="utf-8", errors="replace").split()) for f in a.files)
            allowed, unit = a.words, "words"
            what = f"{', '.join(Path(f).name for f in a.files)}: {measured} words"
        else:
            ap.error("give --pdf with --pages, or --words with files")
    except (OSError, ValueError) as e:
        print(f"check_allowance: error: {e}", file=sys.stderr)
        return 2
    limit = allowed + a.tolerance
    over = measured > limit
    if over and not a.report_only:
        print(f"OVER THE ALLOWANCE: {what}; allowed {allowed:g} {unit}"
              + (f" (+{a.tolerance:g} tolerance)" if a.tolerance else "")
              + f". Over the allowance = not done: cut {measured - allowed:g} {unit}; do not explain the overrun.")
    print(f"check_allowance: {what}; allowance {allowed:g} {unit}; "
          + ("over (report only)" if over and a.report_only else "OVER" if over else "within"))
    return 1 if over and not a.report_only else 0


if __name__ == "__main__":
    sys.exit(main())
