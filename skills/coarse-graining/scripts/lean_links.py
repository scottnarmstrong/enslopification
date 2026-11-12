#!/usr/bin/env python3
"""Pinned GitHub links to the exact lines of Lean declarations: <repo-url>/blob/<commit>/<path>#La-Lb.

Paths and lines come from the declaration graph (nodes.path, nodes.line, nodes.line_end). The commit must be
a hexadecimal commit id: a branch or tag name is refused, because the lines it points to change when the
branch moves. A declaration without a line range gets a link to its file (and a note); a name that is not in
the graph is reported and makes the exit code 1 unless --allow-missing.

Usage:
  lean_links.py --db graph.sqlite --repo-url https://github.com/ORG/REPO --commit 3456e5e7... Foo.bar Foo.baz
  lean_links.py ... --names names.txt --format md        Markdown links [`Foo.bar`](url)
  lean_links.py ... --all-used > lean-links.tsv          a lookup table (name, url, kind) for writers
"""
import argparse
import re
import sqlite3
import sys


def die(msg):
    print(f'lean_links.py: {msg}', file=sys.stderr)
    sys.exit(2)


def main():
    ap = argparse.ArgumentParser(
        description='Print pinned GitHub links to the exact line ranges of Lean declarations.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='example:\n  lean_links.py --db graph.sqlite --repo-url https://github.com/yang-mills-group/OpenAI-YM-20261028 \\\n'
               '      --commit 3456e5e75cf8d4cd558955a5c7638fba2d68f464 YangMills.WilsonFamily.Converges\n'
               '  -> .../blob/3456e5e75cf8d4cd558955a5c7638fba2d68f464/PublicWilson.lean#L85-L90')
    ap.add_argument('names', nargs='*', help='declaration names')
    ap.add_argument('--db', required=True, help='SQLite graph (lean-dependency-graph schema); opened read-only')
    ap.add_argument('--repo-url', required=True, help='https://github.com/ORG/REPO of the Lean source')
    ap.add_argument('--commit', required=True, help='commit id (hexadecimal; a branch or tag is refused)')
    ap.add_argument('--names', dest='names_file', help='file with one name per line')
    ap.add_argument('--all-used', action='store_true', help='every declaration with used = 1')
    ap.add_argument('--format', choices=('tsv', 'md', 'url'), default='tsv',
                    help='tsv: name, url, kind (default); md: [`name`](url); url: the URL only')
    ap.add_argument('--allow-missing', action='store_true', help='exit 0 even if some names are not found')
    a = ap.parse_args()

    if not re.fullmatch(r'[0-9a-fA-F]{7,40}', a.commit):
        die(f'refusing an unpinned reference {a.commit!r}: give a commit id, not a branch or tag name')
    if len(a.commit) < 40:
        print(f'lean_links.py: note: abbreviated commit {a.commit}; a full 40-digit id cannot become ambiguous',
              file=sys.stderr)
    repo = a.repo_url.rstrip('/')
    if repo.endswith('.git'):
        repo = repo[:-4]
    con = sqlite3.connect(f'file:{a.db}?mode=ro', uri=True)
    names = list(a.names)
    if a.names_file:
        with open(a.names_file, encoding='utf-8') as f:
            names += [ln.strip() for ln in f if ln.strip() and not ln.startswith('#')]
    if a.all_used:
        names += [r[0] for r in con.execute('SELECT DISTINCT name FROM nodes WHERE used = 1 ORDER BY name')]
    if not names:
        die('no names given (arguments, --names or --all-used)')
    info = {}
    for n, path, line, end, kind in con.execute('SELECT name, path, line, line_end, kind FROM nodes'):
        if n not in info or (line and not info[n][1]):
            info[n] = (path, line, end, kind)
    missing, nofile = [], 0
    seen = set()
    for n in names:
        if n in seen:
            continue
        seen.add(n)
        v = info.get(n)
        if not v or not v[0]:
            missing.append(n)
            continue
        path, line, end, kind = v
        url = f'{repo}/blob/{a.commit}/{path}'
        if line and end and end > line:
            url += f'#L{line}-L{end}'
        elif line:
            url += f'#L{line}'
        else:
            nofile += 1
        if a.format == 'tsv':
            print(f'{n}\t{url}\t{kind or ""}')
        elif a.format == 'md':
            print(f'[`{n}`]({url})')
        else:
            print(url)
    for n in missing:
        print(f'lean_links.py: not in the graph (or no source path): {n}', file=sys.stderr)
    print(f'lean_links: {len(seen) - len(missing)} links ({nofile} to a whole file, no line range), '
          f'{len(missing)} missing', file=sys.stderr)
    return 1 if (missing and not a.allow_missing) else 0


if __name__ == '__main__':
    sys.exit(main())
