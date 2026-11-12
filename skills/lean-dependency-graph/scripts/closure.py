#!/usr/bin/env python3
"""Mark the closure of the headline roots in the declaration graph (nodes.used = 1), or list a statement closure.

The closure is the union of everything reachable from the roots along `edges` (src uses dst), roots included.
With several roots it is the union of their closures, counted once: do not add the sizes of separate
closures. The roots are recorded in the `roots` table and in `meta` (count, SHA-256 of the sorted list).

Checks: every root must be a node (exit 2 otherwise); a declaration of the set that relies on `sorryAx`
(nodes.sorry = 1; in a statement closure, a definition whose body does) makes the run fail with exit 1 after
writing, so that it cannot be overlooked.

--statement-closure lists what is needed to *state* the roots, and never writes the database: from every
declaration reached it follows the statement references (edges with part statement or both), and from a
definition (kinds given by --definition-kinds: def, abbrev, opaque, instance, field, structure, inductive, ctor)
also its proof references, which for a definition are its body; a structure or inductive type also brings its
constructors (nodes whose parent is the type). A theorem reached this way contributes its statement only.
`--parts statement,both` is not the statement closure: it follows only statement references from every node, so a
definition used only inside another definition's body is missed (theorem -> Def -> Inner omits Inner).

Usage:
  closure.py --db graph.sqlite --roots-file headlines.txt [--export used.txt]
  closure.py --db graph.sqlite YangMills.constructed --dry-run      (print the size, write nothing)
  closure.py --db graph.sqlite --why Some.Declaration                 (a chain from a root to it)
  closure.py --db graph.sqlite --statement-closure --export statement-closure.txt   (roots from the roots table)
"""
import argparse
import collections
import datetime
import hashlib
import sqlite3
import sys

ALL_PARTS = ('statement', 'proof', 'both')
DEFINITION_KINDS = 'def,abbrev,opaque,instance,field,structure,inductive,ctor'


def die(msg):
    print(f'closure.py: {msg}', file=sys.stderr)
    sys.exit(2)


def read_roots(path):
    out = []
    with open(path, encoding='utf-8') as f:
        for line in f:
            line = line.split('#', 1)[0].strip()
            if line:
                out.append(line.split()[0])
    return out


def main():
    ap = argparse.ArgumentParser(
        description='Mark the closure of the roots (used = 1) in a graph built by build_graph_db.py,\n'
                    'or list the statement closure of the roots (--statement-closure, read-only).',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='examples:\n'
               '  closure.py --db graph.sqlite --roots-file verification/joint-headlines.txt --export used.txt\n'
               '  closure.py --db graph.sqlite --statement-closure --export statement-closure.txt\n'
               'The Yang-Mills campaign used the 17 names of the release\'s headline list: 74,093 declarations.')
    ap.add_argument('roots', nargs='*', help='root declaration names (default: --roots-file, else the roots table)')
    ap.add_argument('--db', required=True, help='SQLite graph (lean-dependency-graph schema)')
    ap.add_argument('--roots-file', help='file with one root name per line (# starts a comment)')
    ap.add_argument('--parts', default=None,
                    help='edge parts followed from every node (default: all three). A partial list is not the '
                         'statement closure (it misses definitions used inside definition bodies; use '
                         '--statement-closure), and it may not write used = 1: combine it with --dry-run')
    ap.add_argument('--statement-closure', action='store_true',
                    help='list what is needed to state the roots: statement references of every node, and also '
                         'the body (proof references) of definitions; never writes the database')
    ap.add_argument('--definition-kinds', default=DEFINITION_KINDS,
                    help=f'kinds whose body is followed by --statement-closure (default {DEFINITION_KINDS})')
    ap.add_argument('--export', help='write the names of the set, one per line, sorted')
    ap.add_argument('--why', help='print one shortest chain of references from a root to this declaration')
    ap.add_argument('--dry-run', action='store_true', help='compute and print; do not write the database')
    a = ap.parse_args()

    if a.statement_closure and a.parts is not None:
        die('--statement-closure chooses the edges itself; do not combine it with --parts')
    roots = list(a.roots)
    if a.roots_file:
        roots += read_roots(a.roots_file)
    con = sqlite3.connect(a.db)
    if not roots:
        roots = [r[0] for r in con.execute('SELECT name FROM roots ORDER BY name')]
    if not roots:
        die('no roots given (arguments, --roots-file, or the roots table)')
    roots = sorted(set(roots))
    names = {r[0]: r[1] for r in con.execute('SELECT name, kind FROM nodes')}
    missing = [r for r in roots if r not in names]
    if missing:
        die(f'{len(missing)} roots are not nodes of the graph: {", ".join(missing[:10])}')
    parts = ALL_PARTS if a.parts is None else tuple(p.strip() for p in a.parts.split(',') if p.strip())
    bad = set(parts) - set(ALL_PARTS)
    if bad:
        die(f'unknown parts: {", ".join(sorted(bad))}')
    partial = set(parts) != set(ALL_PARTS)
    writes = not (a.dry_run or a.statement_closure or a.why)
    if partial and writes:
        die(f'--parts {",".join(parts)} would set used = 1 on a partial closure; add --dry-run (with --export), '
            f'or use --statement-closure for what the statements need')

    succ = collections.defaultdict(list)
    def_kinds = {k.strip() for k in a.definition_kinds.split(',') if k.strip()}
    if a.statement_closure:
        for s, d, part in con.execute('SELECT src, dst, part FROM edges'):
            if part != 'proof' or names.get(s) in def_kinds:
                succ[s].append(d)
        ctors = collections.defaultdict(list)
        cols = {r[1] for r in con.execute('PRAGMA table_info(nodes)')}
        if 'parent' in cols:
            for n, par in con.execute("SELECT name, parent FROM nodes WHERE kind = 'ctor' AND parent IS NOT NULL"):
                ctors[par].append(n)
        for t, cs in ctors.items():
            if names.get(t) in def_kinds:
                succ[t].extend(cs)
        mode = (f'followed: statement references of every declaration, bodies of kinds '
                f'{",".join(sorted(def_kinds))}, constructors of reached types')
    else:
        q = 'SELECT src, dst FROM edges WHERE part IN (%s)' % ','.join('?' * len(parts))
        for s, d in con.execute(q, parts):
            succ[s].append(d)
        mode = f'parts {",".join(parts)}'
    seen = set(roots)
    parent = {r: None for r in roots}
    queue = collections.deque(roots)
    while queue:
        x = queue.popleft()
        for y in succ.get(x, ()):
            if y not in seen and y in names:
                seen.add(y)
                parent[y] = x
                queue.append(y)
    if a.why:
        if a.why not in seen:
            print(f'{a.why} is not in the {"statement closure" if a.statement_closure else "closure"} of these roots')
        else:
            chain, x = [], a.why
            while x is not None:
                chain.append(x)
                x = parent[x]
            print(' -> '.join(reversed(chain)))
        return 0

    kinds = collections.Counter(names[n] for n in seen)
    lines = 0
    sorry = []
    for n, ln, so in con.execute('SELECT name, lines, sorry FROM nodes'):
        if n in seen:
            lines += ln or 0
            # in a statement closure a theorem contributes its statement only, so its proof's sorry is not counted
            if so and not (a.statement_closure and names[n] not in def_kinds):
                sorry.append(n)
    digest = hashlib.sha256('\n'.join(roots).encode()).hexdigest()
    print(f'roots: {len(roots)} (sha256 of sorted list {digest[:16]}...)')
    print('by kind: ' + ', '.join(f'{k} {v}' for k, v in kinds.most_common()))
    if writes:
        con.execute('UPDATE nodes SET used = 0')
        con.executemany('UPDATE nodes SET used = 1 WHERE name = ?', ((n,) for n in seen))
        con.execute('DELETE FROM roots')
        con.executemany('INSERT INTO roots VALUES (?)', ((r,) for r in roots))
        now = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
        con.executemany('INSERT OR REPLACE INTO meta VALUES (?,?)', [
            ('closure_roots', str(len(roots))), ('closure_roots_sha256', digest), ('closure_parts', ','.join(parts)),
            ('closure_size', str(len(seen))), ('closure_created_utc', now)])
        con.commit()
    if a.export:
        with open(a.export, 'w', encoding='utf-8') as f:
            f.writelines(n + '\n' for n in sorted(seen))
    if sorry:
        print(f'WARNING: {len(sorry)} declarations of this set rely on sorry: {", ".join(sorted(sorry)[:10])}',
              file=sys.stderr)
    what = 'statement closure' if a.statement_closure else 'closure'
    if a.statement_closure:
        unused = [n for n, u in con.execute('SELECT name, used FROM nodes') if n in seen and not u]
        if len(unused) < len(seen):     # used = 1 is set: report members outside the closure
            print(f'note: {len(unused)} of these have used = 0 (e.g. constructors, and the types of their fields, '
                  f'that no proof reaches; build_graph_db.py --link-ctors counts them in the closure)'
                  + (f': {", ".join(sorted(unused)[:5])}' if unused else ''))
    print(f'{what}: {len(seen)} declarations (distinct names) from {len(roots)} roots, {lines} lines in their '
          f'source ranges; {mode}' + ('' if writes else '; database unchanged'))
    return 1 if sorry else 0


if __name__ == '__main__':
    sys.exit(main())
