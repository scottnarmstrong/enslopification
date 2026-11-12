#!/usr/bin/env python3
"""Cohen's kappa between two readers' labels, with raw agreement and the confusion table.

Input: one TSV with an item column and one label column per reader (--file), or each reader's labels in one or
more files (--a FILES --b FILES), joined on the item column. A file is a TSV or a reader's printed report that
contains one (as key-statement-reader.md asks for): lines before the header row (the first line holding the item
and label columns, separated by tabs), lines without a tab, and repeated header rows are skipped, so the reports
saved by the rollout driver can be given as they are (several batches: a shell glob).

Labels are compared after stripping spaces and, unless --case-sensitive, lower-casing. Items labelled by only one
reader are reported and left out. --collapse turns the labels into a binary split (the listed labels against all
others), as in "main or key" against "technical or bookkeeping". Checks (exit 1): --labels lists the allowed
labels and reports any other; --items names a TSV of the candidates (an item column, e.g. candidates.tsv of
inventory.py --candidates) and reports every candidate that a reader did not label.

kappa measures agreement between the two readers beyond chance. It is not accuracy: two readers can agree and
both be wrong. Measure accuracy separately, against a reference whose answer is known.

Usage:
  kappa.py --file labels.tsv --item-col name --a-col reader1 --b-col reader2 [--collapse main,key]
  kappa.py --a work/*/read/reader-a.md --b work/*/read/reader-b.md --labels main,key,technical,bookkeeping \\
      --collapse main,key --items batches/candidates.tsv
"""
import argparse
import collections
import sys


def die(msg):
    print(f'kappa.py: {msg}', file=sys.stderr)
    sys.exit(2)


def read_table(path, need):
    """Rows (dicts) of the first table in the file whose tab-separated header holds every column of `need`."""
    try:
        with open(path, encoding='utf-8') as f:
            lines = f.read().splitlines()
    except OSError as e:
        die(str(e))
    hdr = None
    rows = []
    for ln in lines:
        cells = [c.strip() for c in ln.split('\t')]
        if hdr is None:
            if '\t' in ln and all(c in cells for c in need):
                hdr = cells
            continue
        if '\t' not in ln or cells == hdr:
            continue
        rows.append(dict(zip(hdr, cells + [''] * (len(hdr) - len(cells)))))
    if hdr is None:
        die(f'no header line with the columns {", ".join(need)} (tab-separated) in {path}')
    return rows


def cohen(pairs):
    n = len(pairs)
    po = sum(1 for x, y in pairs if x == y) / n
    ca = collections.Counter(x for x, _ in pairs)
    cb = collections.Counter(y for _, y in pairs)
    pe = sum(ca[k] * cb[k] for k in set(ca) | set(cb)) / (n * n)
    kappa = (po - pe) / (1 - pe) if pe < 1 else 1.0
    return kappa, po, pe


def main():
    ap = argparse.ArgumentParser(
        description="Cohen's kappa, raw agreement and confusion table for two readers' labels.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='examples:\n'
               '  kappa.py --file readings.tsv --item-col name --a-col first --b-col second --collapse main,key\n'
               '  kappa.py --a work/*/read/reader-a.md --b work/*/read/reader-b.md \\\n'
               '      --labels main,key,technical,bookkeeping --collapse main,key --items batches/candidates.tsv\n'
               'The Yang-Mills selection: 2,424 statements, kappa = 0.72 on "main or key" against the rest.')
    ap.add_argument('--file', help='one TSV holding both readers\' labels')
    ap.add_argument('--a-col', help='label column of the first reader (with --file)')
    ap.add_argument('--b-col', help='label column of the second reader (with --file)')
    ap.add_argument('--a', nargs='+', metavar='FILE', help='TSV files or reports of the first reader (with --b)')
    ap.add_argument('--b', nargs='+', metavar='FILE', help='TSV files or reports of the second reader (with --a)')
    ap.add_argument('--label-col', default='label', help='label column in --a/--b files (default label)')
    ap.add_argument('--item-col', default='item', help='item identifier column (default item)')
    ap.add_argument('--collapse', help='comma-separated labels forming one class; every other label is "rest"')
    ap.add_argument('--labels', help='comma-separated allowed labels; any other label makes the exit status 1')
    ap.add_argument('--items', help='TSV of the candidates (with the item column); a candidate that a reader did '
                    'not label makes the exit status 1')
    ap.add_argument('--case-sensitive', action='store_true', help='do not lower-case labels')
    a = ap.parse_args()

    norm = (lambda s: s.strip()) if a.case_sensitive else (lambda s: s.strip().lower())
    la, lb = {}, {}
    twice = collections.Counter()
    if a.file:
        if not (a.a_col and a.b_col):
            die('--file needs --a-col and --b-col')
        for r in read_table(a.file, [a.item_col, a.a_col, a.b_col]):
            it = r[a.item_col]
            if r[a.a_col]:
                la[it] = norm(r[a.a_col])
            if r[a.b_col]:
                lb[it] = norm(r[a.b_col])
    elif a.a and a.b:
        for who, paths, dest in (('first', a.a, la), ('second', a.b, lb)):
            for path in paths:
                for r in read_table(path, [a.item_col, a.label_col]):
                    if r[a.item_col] and r[a.label_col]:
                        if r[a.item_col] in dest:
                            twice[who] += 1
                        dest[r[a.item_col]] = norm(r[a.label_col])
    else:
        die('give --file with --a-col/--b-col, or --a and --b')
    common = sorted(set(la) & set(lb))
    only = len(set(la) ^ set(lb))
    if not common:
        die('no item is labelled by both readers')
    failed = False
    for who, n in sorted(twice.items()):
        print(f'note: the {who} reader labelled {n} items more than once; the last label was kept')
    if a.labels:
        allowed = {norm(x) for x in a.labels.split(',') if x.strip()}
        other = collections.Counter(x for d in (la, lb) for x in d.values() if x not in allowed)
        if other:
            failed = True
            print('labels outside --labels: ' + ', '.join(f'{k!r} ({v})' for k, v in other.most_common()))
    if a.items:
        cand = [r[a.item_col] for r in read_table(a.items, [a.item_col]) if r[a.item_col]]
        miss_a = [x for x in cand if x not in la]
        miss_b = [x for x in cand if x not in lb]
        extra = sorted((set(la) | set(lb)) - set(cand))
        print(f'candidates: {len(cand)}; not labelled by the first reader: {len(miss_a)}, by the second: '
              f'{len(miss_b)}; labelled items that are not candidates: {len(extra)}'
              + (f' (e.g. {", ".join(list(dict.fromkeys(miss_a + miss_b + extra))[:3])})'
                 if miss_a or miss_b or extra else ''))
        failed = failed or bool(miss_a or miss_b)
    if a.collapse:
        pos = {norm(x) for x in a.collapse.split(',') if x.strip()}
        name = '|'.join(sorted(pos))

        def bucket(x):
            return name if x in pos else 'rest'
    else:
        def bucket(x):
            return x
    pairs = [(bucket(la[i]), bucket(lb[i])) for i in common]
    kappa, po, pe = cohen(pairs)
    labels = sorted({x for p in pairs for x in p})
    conf = collections.Counter(pairs)
    w = max(8, max(len(x) for x in labels) + 2)
    print(f'items labelled by both readers: {len(common)}; by one only (left out): {only}')
    print('confusion table (rows: first reader, columns: second reader)')
    print(' ' * w + ''.join(f'{x:>{w}}' for x in labels))
    for x in labels:
        print(f'{x:<{w}}' + ''.join(f'{conf[(x, y)]:>{w}}' for y in labels))
    print(f'raw agreement {po:.3f}; chance agreement {pe:.3f}')
    print(f'kappa: {kappa:.3f} on {len(common)} items' + (f' (collapsed: {a.collapse} vs rest)' if a.collapse else '')
          + '; agreement between readers, not accuracy')
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
