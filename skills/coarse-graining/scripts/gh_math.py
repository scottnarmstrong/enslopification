#!/usr/bin/env python3
r"""Make the math in Markdown files render on GitHub.

GitHub's Markdown processing runs before MathJax and breaks some valid LaTeX:
  - `\#` inside $...$ loses its backslash and `#` is then a macro-parameter error: both `\#` and a bare `#`
    inside math become `\sharp ` (write \sharp A or \mathrm{card}\,A for a count);
  - `\operatorname{X}` (and `\operatorname*`) is not reliably supported: it becomes `\mathrm{X}`;
  - a `|` inside math in a table row ends the cell: it becomes `\vert `.
Code spans and fenced code blocks are left alone.

Usage:
  gh_math.py FILE.md ...            rewrite the files in place, report which changed
  gh_math.py --check FILE.md ...    report what would change; write nothing; exit 1 if anything would
"""
import argparse
import re
import sys

MATH = re.compile(r'\$\$(.+?)\$\$|\$([^$\n]+?)\$', re.S)
CODE = re.compile(r'(```.*?```|`[^`\n]*`)', re.S)


def _math(m):
    s = m.group(0)
    s = re.sub(r'\\#|(?<!\\)#', r'\\sharp ', s)
    s = re.sub(r'\\operatorname\*?\{([^}]*)\}', r'\\mathrm{\1}', s)
    return s


def _table_bars(text):
    """Inside Markdown table rows, a | in math ends the cell: write \\vert instead."""
    out = []
    for line in text.split('\n'):
        if line.lstrip().startswith('|'):
            line = re.sub(r'\$[^$\n]+?\$', lambda m: re.sub(r'(?<!\\)\|', r'\\vert ', m.group(0)), line)
        out.append(line)
    return '\n'.join(out)


def fix(text):
    parts = CODE.split(text)
    text = ''.join(p if i % 2 else MATH.sub(_math, p) for i, p in enumerate(parts))
    parts = CODE.split(text)
    return ''.join(p if i % 2 else _table_bars(p) for i, p in enumerate(parts))


def main():
    ap = argparse.ArgumentParser(
        description='Rewrite LaTeX math in Markdown so that GitHub renders it (\\# and # -> \\sharp, '
                    '\\operatorname -> \\mathrm, | in table math -> \\vert).',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='example:\n  gh_math.py --check outline/units/*.md     # report only\n'
               '  gh_math.py outline/units/*.md             # fix in place')
    ap.add_argument('files', nargs='+', help='Markdown files')
    ap.add_argument('--check', action='store_true', help='report the lines that would change; write nothing')
    a = ap.parse_args()
    changed = 0
    for f in a.files:
        try:
            with open(f, encoding='utf-8') as fh:
                t = fh.read()
        except OSError as e:
            print(f'gh_math.py: {e}', file=sys.stderr)
            return 2
        u = fix(t)
        if u == t:
            continue
        changed += 1
        if a.check:
            for i, (x, y) in enumerate(zip(t.split('\n'), u.split('\n')), 1):
                if x != y:
                    print(f'{f}:{i}: {x.strip()[:100]}')
        else:
            with open(f, 'w', encoding='utf-8') as fh:
                fh.write(u)
            print(f'fixed {f}')
    verb = 'would change' if a.check else 'changed'
    print(f'gh_math: {changed} of {len(a.files)} files {verb}')
    return 1 if (a.check and changed) else 0


if __name__ == '__main__':
    sys.exit(main())
