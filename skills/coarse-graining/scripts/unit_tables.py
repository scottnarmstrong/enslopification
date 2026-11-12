#!/usr/bin/env python3
"""Unit tables from a declaration -> unit assignment and the declaration graph, with counting scopes stated.

Writes, in --out-dir:
  units.tsv        unit, part, title, lines, declarations, names, used_names, key_statements, builds_on, used_by
  unit-pairs.tsv   src_unit, dst_unit, pairs, statement_pairs: every pair of units with at least one reference
  unassigned.tsv   used declarations (used = 1) without a unit, largest first
  scopes.txt       what each count counts (also printed)

Counting rules (state them wherever the tables are published):
  lines          distinct source lines covered by the spans (path, line .. line_end) of the unit's assigned
                 names: the union, so a field or constructor inside its structure's span is not counted twice
                 (without paths in the database: the sum of spans). With --scope used, only names with
                 used = 1. Spans include statements, proofs and any comment lines inside them.
  declarations   assigned names with a positive span (line-counted declarations)
  names          all assigned names; used_names: those with used = 1
  builds_on      units b such that at least --threshold distinct declaration pairs (x -> y) have x in this unit
                 and y in b; each pair counted once, whatever the number of occurrences or the part (statement
                 or proof). used_by is the reverse. Order: decreasing pair count, then unit identifier.
With --canonical-col, only rows whose canonical name is the name itself count for lines, declarations and as
sources of references (folded names stay in the assignment but add nothing), as in the Yang-Mills tables.
These are code references between allocations, not mathematical prerequisites or a reading order; grouping
declarations into units can create apparent cycles that the declaration graph does not have.

Usage:
  unit_tables.py --db graph.sqlite --assign declaration-units.tsv --units catalogue.tsv --out-dir data
"""
import argparse
import collections
import csv
import os
import re
import sqlite3
import sys


def die(msg):
    print(f'unit_tables.py: {msg}', file=sys.stderr)
    sys.exit(2)


def natural(u):
    return [int(t) if t.isdigit() else t for t in re.split(r'(\d+)', u)]


def read_tsv(path):
    csv.field_size_limit(10 ** 9)
    with open(path, encoding='utf-8', newline='') as f:
        return list(csv.DictReader(f, delimiter='\t'))


def main():
    ap = argparse.ArgumentParser(
        description='Write units.tsv and cross-reference tables from a declaration-to-unit assignment.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='example:\n  unit_tables.py --db graph.sqlite --assign declaration-units.tsv --units catalogue.tsv \\\n'
               '      --key-statements key-statements.tsv --threshold 25 --out-dir data\n'
               'The Yang-Mills map: 32 units, 77,099 assigned names, 74,093 used declarations, threshold 25.')
    ap.add_argument('--db', required=True, help='SQLite graph (lean-dependency-graph schema); opened read-only')
    ap.add_argument('--assign', required=True, help='TSV assigning each declaration to one unit')
    ap.add_argument('--name-col', default='declaration', help='name column of --assign (default declaration)')
    ap.add_argument('--unit-col', default='unit', help='unit column of --assign and --units (default unit)')
    ap.add_argument('--canonical-col', help='optional column of --assign naming the canonical declaration of each row')
    ap.add_argument('--units', help='optional catalogue TSV with columns unit, part, title (order is kept)')
    ap.add_argument('--key-statements', help='optional TSV with one row per key statement and a unit column')
    ap.add_argument('--threshold', type=int, default=25, help='pairs needed for builds_on/used_by (default 25)')
    ap.add_argument('--scope', choices=('all', 'used'), default='all',
                    help='count lines and references over all assigned names (default) or used ones only')
    ap.add_argument('--out-dir', required=True, help='output directory')
    a = ap.parse_args()

    for p in (a.db, a.assign) + tuple(x for x in (a.units, a.key_statements) if x):
        if not os.path.isfile(p):
            die(f'no such file: {p}')
    con = sqlite3.connect(f'file:{a.db}?mode=ro', uri=True)
    ncols = {r[1] for r in con.execute('PRAGMA table_info(nodes)')}
    lines_expr = 'lines' if 'lines' in ncols else 'CASE WHEN line > 0 AND line_end >= line THEN line_end - line + 1 END'
    has_path = 'path' in ncols and 'line' in ncols
    rows = con.execute(f'SELECT name, kind, module, {lines_expr}, used, '
                       + ('path, line' if has_path else 'NULL, NULL') + ' FROM nodes').fetchall()
    node = {}
    for name, kind, mod, ln, used, path, line in rows:
        old = node.get(name)
        if old is None or (ln or 0) > old[2]:
            node[name] = (kind, mod, ln or 0, max(used or 0, old[3] if old else 0), path, line)
        else:
            node[name] = old[:3] + (max(used or 0, old[3]),) + old[4:]
    used_rows = sum(1 for r in rows if r[4])
    used = {n for n, v in node.items() if v[3]}

    assign = {}
    noncanon = set()
    conflicts = []
    arows = read_tsv(a.assign)
    need = [a.name_col, a.unit_col] + ([a.canonical_col] if a.canonical_col else [])
    if arows and any(c not in arows[0] for c in need):
        die(f'{a.assign} needs columns {", ".join(need)}')
    for r in arows:
        nm, u = r[a.name_col].strip(), r[a.unit_col].strip()
        if not nm or not u:
            continue
        if nm in assign and assign[nm] != u:
            conflicts.append(f'{nm}: {assign[nm]} / {u}')
        assign[nm] = u
        if a.canonical_col and r[a.canonical_col].strip() not in ('', nm):
            noncanon.add(nm)
    if conflicts:
        die(f'{len(conflicts)} names have two units, e.g. {conflicts[0]}')
    catalogue = read_tsv(a.units) if a.units else []
    order = [r[a.unit_col] for r in catalogue] if catalogue else []
    meta_u = {r[a.unit_col]: r for r in catalogue}
    for u in sorted(set(assign.values()) - set(order), key=natural):
        order.append(u)
    unknown = set(assign.values()) - set(meta_u) if catalogue else set()
    ks = collections.Counter()
    if a.key_statements:
        for r in read_tsv(a.key_statements):
            ks[r.get(a.unit_col, '').strip()] += 1

    def in_scope(nm):
        return nm in node and (a.scope == 'all' or nm in used)

    lines = collections.Counter()
    decls = collections.Counter()
    names = collections.Counter()
    unames = collections.Counter()
    spans = collections.defaultdict(lambda: collections.defaultdict(list))   # unit -> path -> [(a, b)]
    allspans = collections.defaultdict(list)
    for nm, u in assign.items():
        names[u] += 1
        if nm in used:
            unames[u] += 1
        if in_scope(nm) and nm not in noncanon and node[nm][2] > 0:
            decls[u] += 1
            path, line = node[nm][4], node[nm][5]
            if has_path and path and line:
                spans[u][path].append((line, line + node[nm][2] - 1))
                allspans[path].append((line, line + node[nm][2] - 1))
            else:
                lines[u] += node[nm][2]

    def union(ivs):
        tot, end = 0, None
        for x, y in sorted(ivs):
            if end is None or x > end:
                tot += y - x + 1
                end = y
            elif y > end:
                tot += y - end
                end = y
        return tot

    for u, byp in spans.items():
        lines[u] += sum(union(v) for v in byp.values())
    global_union = sum(union(v) for v in allspans.values())
    pairs = collections.Counter()
    spairs = collections.Counter()
    for s, d, part in con.execute('SELECT src, dst, part FROM edges'):
        us, ud = assign.get(s), assign.get(d)
        if us and ud and us != ud and in_scope(s) and in_scope(d) and s not in noncanon:
            pairs[(us, ud)] += 1
            if part in ('statement', 'both'):
                spairs[(us, ud)] += 1
    builds = collections.defaultdict(list)
    usedby = collections.defaultdict(list)
    for (x, y), c in pairs.items():
        if c >= a.threshold:
            builds[x].append((c, y))
            usedby[y].append((c, x))

    def fmt(lst):
        return ';'.join(u for c, u in sorted(lst, key=lambda t: (-t[0], natural(t[1]))))

    os.makedirs(a.out_dir, exist_ok=True)
    with open(os.path.join(a.out_dir, 'units.tsv'), 'w', encoding='utf-8') as f:
        f.write('unit\tpart\ttitle\tlines\tdeclarations\tnames\tused_names\tkey_statements\tbuilds_on\tused_by\n')
        for u in order:
            m = meta_u.get(u, {})
            f.write(f'{u}\t{m.get("part", "")}\t{m.get("title", "")}\t{lines[u]}\t{decls[u]}\t{names[u]}\t'
                    f'{unames[u]}\t{ks[u]}\t{fmt(builds[u])}\t{fmt(usedby[u])}\n')
    with open(os.path.join(a.out_dir, 'unit-pairs.tsv'), 'w', encoding='utf-8') as f:
        f.write('src_unit\tdst_unit\tpairs\tstatement_pairs\n')
        for (x, y), c in sorted(pairs.items(), key=lambda kv: (-kv[1], natural(kv[0][0]), natural(kv[0][1]))):
            f.write(f'{x}\t{y}\t{c}\t{spairs[(x, y)]}\n')
    unassigned = sorted((n for n in used if n not in assign), key=lambda n: (-node[n][2], n))
    with open(os.path.join(a.out_dir, 'unassigned.tsv'), 'w', encoding='utf-8') as f:
        f.write('name\tkind\tmodule\tlines\n')
        for n in unassigned:
            f.write(f'{n}\t{node[n][0]}\t{node[n][1] or ""}\t{node[n][2]}\n')
    recip = sorted({tuple(sorted((x, y), key=natural)) for (x, y), c in pairs.items()
                    if c >= a.threshold and pairs.get((y, x), 0) >= a.threshold}, key=lambda t: natural(t[0]))
    assigned_not_graph = sum(1 for n in assign if n not in node)
    scopes = [
        f'database rows in nodes: {len(rows)}; distinct names: {len(node)}',
        f'used rows: {used_rows}; distinct used names (the closure): {len(used)}',
        f'assigned names (the allocation): {len(assign)}; of them in the graph: {len(assign) - assigned_not_graph}; '
        f'used: {len(set(assign) & used)}; assigned but not used: {len(set(assign) - used)}',
        f'used names without a unit: {len(unassigned)} (unassigned.tsv)',
        f'scope of lines, declarations and references: {"all assigned names in the graph" if a.scope == "all" else "assigned names with used = 1"}',
        f'line weights: distinct source lines covered by declaration spans (statement, proof and comment lines '
        f'inside them); sum over units {sum(lines.values())} lines in {sum(decls.values())} line-counted '
        f'declarations; union over all units {global_union} lines'
        + (f'; {len(noncanon)} non-canonical names add nothing' if a.canonical_col else ''),
        f'builds_on/used_by: distinct declaration pairs, threshold {a.threshold}; {len(pairs)} unit pairs with at '
        f'least one reference, {sum(1 for c in pairs.values() if c >= a.threshold)} at or above the threshold',
        f'reciprocal unit pairs at the threshold (apparent cycles from grouping): '
        + (', '.join(f'{x}<->{y}' for x, y in recip) or 'none'),
        'references between units are code references, not mathematical prerequisites or a reading order',
    ]
    if unknown:
        scopes.append(f'units in the assignment but not in the catalogue: {", ".join(sorted(unknown, key=natural))}')
    with open(os.path.join(a.out_dir, 'scopes.txt'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(scopes) + '\n')
    print('Counting scopes:')
    for s in scopes:
        print('  ' + s)
    print(f'unit_tables: {len(order)} units, {len(assign)} assigned names, {len(unassigned)} used names without a '
          f'unit -> {a.out_dir}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
