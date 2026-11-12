#!/usr/bin/env python3
"""Compare the closure (nodes.used = 1) with a usage record published by the authors of the development.

The record is a list of constant names: one per line, or one column of a TSV file, optionally filtered by
other columns (e.g. status = used or headline). Header row: --header or --no-header; without either, the first
line is a header when --column/--filter name a column; otherwise it is taken as a header when it contains a tab or
is a usual header word (name, declaration, constant, ...), and a note on stderr says which was done. The names are
attributed to owning declarations with the rule of the graph (the `aux` table, then the auxiliary-name and
private-prefix patterns stored in `meta`), so that `foo._proof_3`, `foo.eq_1` and `_private.M.0.foo` all count
as `foo`. The output of ClosureCheck.lean is such a record (one name per line).

Differences are classified:
  in the record only:  constructor whose inductive type is in the closure (records that count constructors
                       through recursors put them here); other declaration of the graph not reached;
  in the closure only: reached only through auxiliary constants (every edge into it from a used declaration
                       comes through an auxiliary); constructor or field; other.
Names of the record that the graph does not contain are counted apart (metaprogramming, auxiliaries without a
project owner, names absent from the graph).

What this does not check: individual edges, mathematical necessity, or any English text.

Usage:
  compare_usage.py --db graph.sqlite --record declaration-usage.tsv --column declaration \
      --filter status=used,headline [--out-dir cmp/] [--examples 10] [--max-diff 100]
"""
import argparse
import collections
import csv
import os
import re
import sqlite3
import sys


def die(msg):
    print(f'compare_usage.py: {msg}', file=sys.stderr)
    sys.exit(2)


def split_name(n):
    out, cur, depth = [], [], 0
    for ch in n:
        if ch == '«':
            depth += 1
        elif ch == '»':
            depth = max(0, depth - 1)
        if ch == '.' and depth == 0:
            out.append(''.join(cur))
            cur = []
        else:
            cur.append(ch)
    out.append(''.join(cur))
    return out


HEADER_WORDS = {'name', 'names', 'declaration', 'declarations', 'decl', 'decls', 'constant', 'constants',
                'const', 'lean_name', 'full_name', 'fullname', 'item', 'id', 'symbol'}


def detect_header(first, column, filters):
    """(has_header, reason of the guess, or '' when there is nothing to guess) when no --header/--no-header."""
    named = [c for c in [column] + [f.split('=', 1)[0] for f in filters] if c and not c.isdigit()]
    if named:
        return True, ''      # a column given by name needs the header row: no guess, no note
    if len(first) > 1:
        return True, 'it contains a tab'
    if first and first[0].strip().lower() in HEADER_WORDS:
        return True, f'{first[0].strip()!r} is a usual header word'
    return False, 'it has no tab and is not a usual header word'


def read_record(path, column, filters, header):
    csv.field_size_limit(10 ** 9)
    with open(path, encoding='utf-8', newline='') as f:
        rows = list(csv.reader(f, delimiter='\t'))
    if not rows:
        die(f'empty record: {path}')
    if header is None:
        header, why = detect_header(rows[0], column, filters)
        if why:     # a guess: say what was done
            shown = '\t'.join(rows[0])
            shown = shown if len(shown) <= 60 else shown[:57] + '...'
            print(f'compare_usage.py: note: first line {shown!r} of {path} read as '
                  + (f'a header ({why}); pass --no-header if it is data' if header else
                     f'data ({why}); pass --header if it is a header'), file=sys.stderr)
    if not header:
        hdr = [str(i + 1) for i in range(len(rows[0]))]
        body = rows
    else:
        hdr, body = rows[0], rows[1:]

    def col(c):
        if c in hdr:
            return hdr.index(c)
        if c.isdigit() and 1 <= int(c) <= len(hdr):
            return int(c) - 1
        die(f'no column {c!r} in {path} (columns: {", ".join(hdr)})')

    ci = col(column) if column else 0
    flt = []
    for fs in filters:
        if '=' not in fs:
            die(f'--filter needs COL=VALUE[,VALUE]: {fs}')
        k, v = fs.split('=', 1)
        flt.append((col(k), set(v.split(','))))
    out = []
    for r in body:
        if len(r) <= ci:
            continue
        if all(len(r) > i and r[i] in vs for i, vs in flt):
            if r[ci].strip():
                out.append(r[ci].strip())
    return out


def main():
    ap = argparse.ArgumentParser(
        description='Compare the closure (used = 1) with a usage record published by the authors.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='example (the Yang-Mills release: 74,093 vs 74,115 declarations, 50 differences):\n'
               '  compare_usage.py --db graph.sqlite --record verification/declaration-usage.tsv \\\n'
               '      --column declaration --filter status=used,headline --out-dir cmp\n'
               'without a published record, the names written by ClosureCheck.lean (a cross-check, not a proof):\n'
               '  compare_usage.py --db graph.sqlite --record closure-check.txt --no-header --out-dir cmp')
    ap.add_argument('--db', required=True, help='SQLite graph with used = 1 set by closure.py')
    ap.add_argument('--record', required=True, help='usage record: names one per line, or a TSV file')
    ap.add_argument('--column', help='column holding the names (header name or 1-based index; default: first)')
    ap.add_argument('--filter', action='append', default=[],
                    help='keep rows whose COL is one of the values: COL=V1,V2 (repeatable)')
    hg = ap.add_mutually_exclusive_group()
    hg.add_argument('--header', dest='header', action='store_true', default=None,
                    help='the first line of the record is a header row')
    hg.add_argument('--no-header', dest='header', action='store_false', default=None,
                    help='the record has no header row (default: detect it, with a note on stderr)')
    ap.add_argument('--examples', type=int, default=8, help='examples printed per class (default 8)')
    ap.add_argument('--out-dir', help='write record-only.tsv, closure-only.tsv and unattributed.tsv here')
    ap.add_argument('--max-diff', type=int, help='exit 1 if the symmetric difference is larger than this')
    a = ap.parse_args()

    if not os.path.isfile(a.record):
        die(f'no such file: {a.record}')
    con = sqlite3.connect(f'file:{a.db}?mode=ro', uri=True)
    meta = dict(con.execute('SELECT key, value FROM meta'))
    aux_re = re.compile(r'^(?:%s)$' % meta.get('aux_component_regex', r'(?!)'))
    priv_re = re.compile(meta.get('private_prefix_regex', r'^_private\.(.+?)\.0\.'))
    node = {n: (k, m, p) for n, k, m, p in con.execute('SELECT name, kind, module, parent FROM nodes')}
    used = {r[0] for r in con.execute('SELECT name FROM nodes WHERE used = 1')}
    if not used:
        die('no declaration has used = 1: run closure.py first')
    aux = {}
    for n, s, o, st in con.execute('SELECT name, short, owner, status FROM aux'):
        aux[n] = (o, st)
        aux.setdefault(s, (o, st))

    def attribute(n):
        """(owner or None, reason when None)."""
        if n in node:
            return n, None
        if n in aux:
            o, st = aux[n]
            return (o, None) if o else (None, 'metaprogramming' if st == 'meta' else 'auxiliary without project owner')
        nn = priv_re.sub('', n, count=1) if n.startswith('_private.') else n
        if nn in node:
            return nn, None
        cs = split_name(nn)
        while len(cs) > 1 and (aux_re.match(cs[-1]) or cs[-1] == 'eq'):
            cs = cs[:-1]
            c = '.'.join(cs)
            if c in node:
                return c, None
        return None, 'not in the graph'

    names = read_record(a.record, a.column, a.filter, a.header)
    owners = set()
    unattributed = collections.defaultdict(list)
    for n in sorted(set(names)):
        o, why = attribute(n)
        if o:
            owners.add(o)
        else:
            unattributed[why].append(n)
    rec_only = sorted(owners - used)
    clo_only = sorted(used - owners)
    both = len(used & owners)

    # classify
    def cls_record_only(n):
        k, _, par = node[n][0], node[n][1], node[n][2]
        if k == 'ctor' and par in used:
            return 'constructor whose inductive type is in the closure'
        if k == 'ctor':
            return 'constructor, inductive type not reached'
        return 'declaration of the graph not reached'

    into = collections.defaultdict(list)
    q = 'SELECT e.src, e.dst, e.direct FROM edges e JOIN nodes s ON s.name = e.src WHERE s.used = 1'
    clo_only_set = set(clo_only)
    for s, d, direct in con.execute(q):
        if d in clo_only_set:
            into[d].append(direct)

    def cls_closure_only(n):
        k = node[n][0]
        if into[n] and not any(into[n]):
            return 'reached only through auxiliary constants'
        if k in ('ctor', 'field'):
            return 'constructor or field'
        return 'other'

    groups = (('in the record only', rec_only, cls_record_only), ('in the closure only', clo_only, cls_closure_only))
    print(f'record: {len(names)} rows kept, {len(set(names))} distinct names -> {len(owners)} declarations after '
          f'attribution to owners; {sum(map(len, unattributed.values()))} names not attributed')
    for why, ns in sorted(unattributed.items()):
        print(f'  not attributed ({why}): {len(ns)}; e.g. {", ".join(ns[:3])}')
    print(f'closure: {len(used)} declarations; both: {both}; closure only: {len(clo_only)}; '
          f'record only: {len(rec_only)}; symmetric difference: {len(clo_only) + len(rec_only)}')
    classified = {}
    for title, ns, f in groups:
        c = collections.defaultdict(list)
        for n in ns:
            c[f(n)].append(n)
        classified[title] = c
        for k, v in sorted(c.items(), key=lambda kv: -len(kv[1])):
            ex = ', '.join(f'{n} ({node[n][0]})' for n in v[:a.examples])
            print(f'{title}: {k}: {len(v)}' + (f'; e.g. {ex}' if ex else ''))
    if a.out_dir:
        os.makedirs(a.out_dir, exist_ok=True)
        for fname, title in (('record-only.tsv', 'in the record only'), ('closure-only.tsv', 'in the closure only')):
            with open(os.path.join(a.out_dir, fname), 'w', encoding='utf-8') as f:
                f.write('name\tkind\tmodule\tclass\n')
                for k, v in sorted(classified[title].items()):
                    for n in v:
                        f.write(f'{n}\t{node[n][0]}\t{node[n][1]}\t{k}\n')
        with open(os.path.join(a.out_dir, 'unattributed.tsv'), 'w', encoding='utf-8') as f:
            f.write('name\treason\n')
            for why, ns in sorted(unattributed.items()):
                f.writelines(f'{n}\t{why}\n' for n in ns)
    print('scope: this compares reached-name sets; it does not check individual edges, mathematical necessity, '
          'or any English text.')
    diff = len(clo_only) + len(rec_only)
    print(f'compare_usage: closure {len(used)}, record {len(owners)}, intersection {both}, difference {diff}')
    return 1 if (a.max_diff is not None and diff > a.max_diff) else 0


if __name__ == '__main__':
    sys.exit(main())
