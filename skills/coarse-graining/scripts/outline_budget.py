#!/usr/bin/env python3
"""Measure Markdown outlines against a word allowance computed from the size of the Lean they describe.

Allowance: pages = the nearest whole number to lean_lines / lines-per-page, clamped to [min-pages, max-pages];
words = pages x words-per-page. Defaults: one page of about 500 words per 4,000
Lean lines, at least 3 and at most 10 pages. Words are whitespace-separated tokens after removing link URLs
(`[text](url)` counts as its text), autolinks and HTML comments; formulas count as their tokens.

Exit 1 if some file is over its allowance by more than --tolerance (default 10%), or misses a heading required
by --require-heading; this makes it usable as the `check` command of a rollout stage (the driver then retries
once with this output appended to the prompt).

Usage:
  outline_budget.py outline.md --lines 7215
  outline_budget.py short/*.md --units-tsv units.tsv            (unit = file name stem, '-' or '.' alike)
  outline_budget.py --units-tsv units.tsv --emit-units-json     (unit entries for a rollout config)
"""
import argparse
import csv
import json
import os
import re
import sys


def die(msg):
    print(f'outline_budget.py: {msg}', file=sys.stderr)
    sys.exit(2)


def count_words(text):
    text = re.sub(r'<!--.*?-->', ' ', text, flags=re.S)
    text = re.sub(r'\]\([^)]*\)', ']', text)
    text = re.sub(r'<https?://[^>]+>', ' ', text)
    return len(text.split())


def allowance(lines, a):
    pages = int(lines / a.lines_per_page + 0.5)
    pages = max(a.min_pages, min(a.max_pages, pages))
    return pages, pages * a.words_per_page


def key(u):
    return u.replace('-', '.').lower()


def main():
    ap = argparse.ArgumentParser(
        description='Measure Markdown outlines against a word allowance derived from Lean line counts.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='examples:\n  outline_budget.py short/III.9.md --lines 7215          # 3 pages, 1,500 words\n'
               '  outline_budget.py short/*.md --units-tsv data/units.tsv --tolerance 0.10\n'
               'Without a measured allowance the Yang-Mills outlines grew 4.4 times past their template.')
    ap.add_argument('files', nargs='*', help='Markdown files to measure')
    ap.add_argument('--lines', type=int, help='Lean lines described by the file(s)')
    ap.add_argument('--units-tsv', help='TSV with a unit column and a lines column (e.g. units.tsv)')
    ap.add_argument('--unit', help='unit key for a single file (default: the file name stem)')
    ap.add_argument('--key-col', default='unit', help='unit column of --units-tsv (default unit)')
    ap.add_argument('--lines-col', default='lines', help='lines column of --units-tsv (default lines)')
    ap.add_argument('--title-col', default='title', help='title column used by --emit-units-json')
    ap.add_argument('--words-per-page', type=int, default=500)
    ap.add_argument('--lines-per-page', type=int, default=4000)
    ap.add_argument('--min-pages', type=int, default=3)
    ap.add_argument('--max-pages', type=int, default=10)
    ap.add_argument('--tolerance', type=float, default=0.10, help='allowed overrun fraction (default 0.10)')
    ap.add_argument('--no-budget', action='store_true',
                    help='only check the required headings (for detailed notes, which have no allowance)')
    ap.add_argument('--require-heading', action='append', default=[],
                    help='regex that some Markdown heading line must match (repeatable)')
    ap.add_argument('--emit-units-json', action='store_true',
                    help='print {"<unit>": {"title", "pages", "vars": {"lean_lines", "words_max"}}} for a rollout config')
    a = ap.parse_args()

    table = {}
    titles = {}
    if a.units_tsv:
        try:
            with open(a.units_tsv, encoding='utf-8', newline='') as f:
                for r in csv.DictReader(f, delimiter='\t'):
                    if a.key_col not in r or a.lines_col not in r:
                        die(f'{a.units_tsv} needs columns {a.key_col} and {a.lines_col}')
                    table[key(r[a.key_col])] = (r[a.key_col], int(r[a.lines_col] or 0))
                    titles[r[a.key_col]] = r.get(a.title_col, '')
        except OSError as e:
            die(str(e))
    if a.emit_units_json:
        if not table:
            die('--emit-units-json needs --units-tsv')
        out = {}
        for unit, lines in table.values():
            p, w = allowance(lines, a)
            out[unit] = {'title': titles.get(unit, ''), 'pages': p,
                         'vars': {'lean_lines': str(lines), 'words_max': str(w)}}
        print(json.dumps(out, indent=1, ensure_ascii=False))
        return 0
    if not a.files:
        die('no files given')
    failed = 0
    for path in a.files:
        try:
            with open(path, encoding='utf-8') as f:
                text = f.read()
        except OSError as e:
            die(str(e))
        if a.no_budget:
            lines = 0
        elif a.lines is not None:
            lines = a.lines
        elif table:
            u = a.unit or os.path.splitext(os.path.basename(path))[0]
            if key(u) not in table:
                die(f'{path}: unit {u} not in {a.units_tsv}')
            lines = table[key(u)][1]
        else:
            die('give --lines or --units-tsv')
        pages, wmax = allowance(lines, a)
        w = count_words(text)
        heads = [ln for ln in text.split('\n') if ln.lstrip().startswith('#')]
        missing = [rx for rx in a.require_heading if not any(re.search(rx, h) for h in heads)]
        over = (not a.no_budget) and w > wmax * (1 + a.tolerance)
        status = 'OVER' if over else 'OK'
        if a.no_budget:
            msg = f'{path}: {w} words (no allowance)'
        else:
            msg = (f'{path}: {w} words; allowance {wmax} ({pages} pages for {lines} Lean lines); {status}'
                   + (f' by {100 * (w - wmax) / wmax:.0f}%: shorten to at most {wmax} words' if over else ''))
        if missing:
            msg += '; missing headings: ' + ', '.join(missing)
        print(msg)
        failed += 1 if (over or missing) else 0
    print(f'outline_budget: {len(a.files)} files, {failed} failing')
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
