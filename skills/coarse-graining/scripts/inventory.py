#!/usr/bin/env python3
"""Source inventories of the units for the outline writers, and key-statement candidate batches for the readers.

Inputs: the declaration graph (SQLite, lean-dependency-graph schema, with used = 1 and the roots set by
closure.py), a declaration -> unit TSV (declaration-units.tsv), and the Lean source checked out at the pinned
commit (--src: only read; an --out-dir inside it is refused, and so is a git checkout at another commit). Links are
pinned: <repo-url>/blob/<commit>/<path>#La-Lb (defaults: source_url and commit recorded in the graph's meta table).

Inventory mode (default) writes <out-dir>/<unit>.md for every unit:
  size            lines (union of the spans of the unit's declarations, per file, as unit_tables.py computes them)
                  and declarations; the unit's declarations in the closure by kind; its largest source files
  results         the unit's results in the closure (kinds --result-kinds) by mass: their lines plus the lines of
                  everything they dominate (every chain of references from the roots to it passes through them),
                  read from own_and_scale.py's dominators.tsv (--dominators) or computed the same way; each with
                  its pinned link, the first line of its docstring, its immediate dominator, and an excerpt of its
                  statement read from the source at the recorded lines, cut at the first `:=` outside brackets
                  (or at `where`, or before a pattern-matching line) and labelled as an excerpt
  definitions     the definitions, structures and inductive types the unit introduces (--definition-kinds), most
                  used first (number of declarations of the closure that reference them)
  inputs          declarations of other units that the unit's declarations reference, ranked by the number of the
                  unit's declarations that reference them (and how many of these references are in statements),
                  with totals per unit
  used by         the unit's declarations most referenced from other units, and totals per unit
  key statements  with --key-statements, the unit's rows of key-statements.tsv
Apart from the size line, only declarations in the closure of the roots (used = 1) are listed.

Candidates mode (--candidates) writes key-statement candidates for two independent readers, in <out-dir>:
  candidates.tsv  item, batch, unit, kind, lines, mass, link, doc (first line)
  B001.md, ...    batches of at most --batch-size candidates (default 25), one unit at a time, in source order,
                  each candidate with its pinned link, docstring and statement excerpt
  batches.json    the "units" entries for rollout.key-statements.example.json
Candidates: the roots, and every result of the closure with mass >= --min-mass (default 100 lines), that is the
results that own_and_scale.py retains at that scale.

What it does not do: decide which statements matter (the readers do); give the elaborated statement (an excerpt is
source text cut by a simple rule: open the link); check that a link supports any sentence.

Usage:
  inventory.py --db graph.sqlite --assign declaration-units.tsv --src lean-src --out-dir map/inventories \\
      [--units catalogue.tsv] [--dominators coarse/dominators.tsv] [--key-statements key-statements.tsv]
  inventory.py --candidates --db graph.sqlite --assign declaration-units.tsv --src lean-src --out-dir batches
"""
import argparse
import collections
import csv
import importlib.util
import json
import math
import os
import re
import sqlite3
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
UNIT_RE = re.compile(r'[A-Za-z0-9][A-Za-z0-9_.-]*\Z')
OPEN, CLOSE = '([{⦃⟨⟦', ')]}⦄⟩⟧'
NOUNIT = '(no unit)'


def die(msg):
    print(f'inventory.py: {msg}', file=sys.stderr)
    sys.exit(2)


def natural(u):
    return [int(t) if t.isdigit() else t for t in re.split(r'(\d+)', u)]


def read_tsv(path):
    csv.field_size_limit(10 ** 9)
    with open(path, encoding='utf-8', newline='') as f:
        return list(csv.DictReader(f, delimiter='\t'))


def read_roots(path):
    out = []
    with open(path, encoding='utf-8') as f:
        for line in f:
            line = line.split('#', 1)[0].strip()
            if line:
                out.append(line.split()[0])
    return out


def num(x):
    return f'{x:,}'


def pl(x, word, words=None):
    return f'{x:,} ' + (word if x == 1 else (words or word + 's'))


def cell(s):
    return (s or '').replace('\n', ' ').replace('|', '\\|').strip()


def first_line(doc):
    for ln in (doc or '').strip().split('\n'):
        if ln.strip():
            return ln.strip()
    return ''


def load_sibling(name):
    """Import a script of this directory (python3 -I does not put it on sys.path); write no bytecode here."""
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location(f'enslop_{name}', os.path.join(HERE, name + '.py'))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def compute_mass(con, node, roots):
    """mass and immediate dominator of every declaration reached from the roots, as own_and_scale.py computes
    them with its defaults (all edge parts; used declarations only, unless none is marked)."""
    osc = load_sibling('own_and_scale')
    has_used = any(v['used'] for v in node.values())
    keep = sorted({n for n, v in node.items() if v['used'] or not has_used} | set(roots))
    idx = {n: i for i, n in enumerate(keep)}
    n = len(keep)
    succ = [[] for _ in range(n + 1)]
    pred = [[] for _ in range(n + 1)]
    seen = set()
    for s, d in con.execute('SELECT src, dst FROM edges'):
        i, j = idx.get(s), idx.get(d)
        if i is None or j is None or i == j:
            continue
        k = i * (n + 1) + j
        if k in seen:
            continue
        seen.add(k)
        succ[i].append(j)
        pred[j].append(i)
    del seen
    rix = [idx[r] for r in roots]
    succ[n] = rix
    for r in rix:
        pred[r].append(n)
    idom, rpo = osc.dominators(n, succ, pred, rix)
    mass = [node[x]['lines'] for x in keep] + [0]
    for v in reversed(rpo):
        if v != n:
            mass[idom[v]] += mass[v]
    return ({keep[v]: mass[v] for v in rpo if v != n},
            {keep[v]: (keep[idom[v]] if idom[v] != n else '') for v in rpo if v != n})


def cut_point(text):
    """(index, rule) where the statement ends: the first `:=` outside brackets, strings and comments, a `where`,
    or the line break before a line starting with `|` that contains `=>` (pattern matching); (None, '') if none."""
    i, n, depth = 0, len(text), 0
    while i < n:
        c = text[i]
        if c == '\n':
            if depth == 0:
                j = i + 1
                while j < n and text[j] in ' \t':
                    j += 1
                eol = text.find('\n', j)
                eol = n if eol < 0 else eol
                if j < n and text[j] == '|' and '=>' in text[j:eol]:
                    return i, 'before the first pattern-matching line'
            i += 1
            continue
        if text.startswith('--', i):
            j = text.find('\n', i)
            i = n if j < 0 else j
            continue
        if text.startswith('/-', i):
            d, i = 1, i + 2
            while i < n and d:
                if text.startswith('/-', i):
                    d, i = d + 1, i + 2
                elif text.startswith('-/', i):
                    d, i = d - 1, i + 2
                else:
                    i += 1
            continue
        if c == '"':
            i += 1
            while i < n and text[i] != '"':
                i += 2 if text[i] == '\\' else 1
            i += 1
            continue
        if c in OPEN:
            depth += 1
        elif c in CLOSE:
            depth = max(0, depth - 1)
        elif depth == 0:
            if text.startswith(':=', i):
                return i, 'at the first `:=`'
            if (text.startswith('where', i) and (i == 0 or not (text[i - 1].isalnum() or text[i - 1] in "_.'"))
                    and not (i + 5 < n and (text[i + 5].isalnum() or text[i + 5] in "_'"))):
                return i, 'at `where`'
        i += 1
    return None, ''


class Source:
    """Read-only access to the Lean source checkout."""

    def __init__(self, root):
        self.root = os.path.realpath(root)
        self.cache = {}
        self.missing = set()

    def lines(self, path):
        if path in self.cache:
            return self.cache[path]
        full = os.path.realpath(os.path.join(self.root, path))
        if not full.startswith(self.root + os.sep) or not os.path.isfile(full):
            self.missing.add(path)
            self.cache[path] = None
            return None
        with open(full, encoding='utf-8', errors='replace') as f:
            self.cache[path] = f.read().split('\n')
        return self.cache[path]

    def excerpt(self, v, max_lines):
        """(text, how) of the statement excerpt of a node, or (None, reason)."""
        if not v['path'] or not v['line']:
            return None, 'no source range in the graph'
        ls = self.lines(v['path'])
        if ls is None:
            return None, f'file {v["path"]} not found under --src'
        a = v['line']
        b = v['end'] if v['end'] and v['end'] >= a else a
        text = '\n'.join(ls[a - 1:b])
        k, rule = cut_point(text)
        if k is not None:
            text = text[:k]
        out = [ln.rstrip() for ln in text.rstrip().split('\n')]
        how = f'lines {a}–{b}, ' + (f'cut {rule}' if k is not None else 'no `:=` found')
        if len(out) > max_lines:
            out = out[:max_lines] + ['…']
            how += f', first {max_lines} lines'
        return '\n'.join(out), how


def fence(text):
    run = max((len(m) for m in re.findall(r'`+', text)), default=0)
    return '`' * max(3, run + 1)


def check_checkout(src, commit):
    """None if --src is a git checkout at the commit; a note if it cannot be confirmed; exit 2 on a mismatch."""
    try:
        r = subprocess.run(['git', '-C', src, 'rev-parse', 'HEAD'], capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.SubprocessError):
        return 'git is not available: could not confirm that --src is at the commit'
    if r.returncode != 0:
        return '--src is not a git checkout: could not confirm that it is at the commit'
    head = r.stdout.strip()
    if not head.lower().startswith(commit.lower()):
        die(f'--src is at commit {head}, not {commit}: the line ranges of the graph belong to {commit}')
    return None


def main():
    ap = argparse.ArgumentParser(
        description='Write per-unit source inventories (results by mass with statement excerpts, definitions,\n'
                    'inputs from other units) or key-statement candidate batches, from the graph and the source.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='examples:\n'
               '  inventory.py --db graph.sqlite --assign declaration-units.tsv --units catalogue.tsv \\\n'
               '      --src lean-src --dominators coarse/dominators.tsv --out-dir map/inventories\n'
               '  inventory.py --candidates --db graph.sqlite --assign declaration-units.tsv --src lean-src \\\n'
               '      --out-dir batches --min-mass 100 --batch-size 25\n'
               'The readers of the Yang-Mills campaign saw 2,424 candidates in 106 groups. --repo-url\n'
               '(e.g. https://github.com/yang-mills-group/OpenAI-YM-20261028) and --commit\n'
               '(e.g. 3456e5e75cf8d4cd558955a5c7638fba2d68f464) are read from the graph when it records them.')
    ap.add_argument('--db', required=True, help='SQLite graph (lean-dependency-graph schema); opened read-only')
    ap.add_argument('--assign', required=True, help='TSV assigning each declaration to one unit')
    ap.add_argument('--src', required=True, help='Lean source checked out at the commit (read only)')
    ap.add_argument('--out-dir', required=True, help='output directory (outside --src)')
    ap.add_argument('--repo-url', help='https://github.com/ORG/REPO of the source (default: meta source_url)')
    ap.add_argument('--commit', help='commit id of the source (default: meta commit); a branch or tag is refused')
    ap.add_argument('--name-col', default='declaration', help='name column of --assign (default declaration)')
    ap.add_argument('--unit-col', default='unit', help='unit column of --assign and --units (default unit)')
    ap.add_argument('--units', help='optional catalogue TSV with columns unit, part, title (order is kept)')
    ap.add_argument('--dominators', help="own_and_scale.py's dominators.tsv (name, mass, idom); default: compute")
    ap.add_argument('--roots-file', help='roots for computing mass (default: the roots table of the graph)')
    ap.add_argument('--key-statements', help='optional key-statements.tsv (number, unit, lean_name, link, '
                    'importance, summary) to list in each inventory')
    ap.add_argument('--result-kinds', default='theorem,lemma,axiom',
                    help='kinds that count as results (default theorem,lemma,axiom, as own_and_scale.py)')
    ap.add_argument('--definition-kinds', default='def,abbrev,opaque,structure,inductive',
                    help='kinds listed as definitions (default def,abbrev,opaque,structure,inductive)')
    ap.add_argument('--scope', choices=('all', 'used'), default='all',
                    help='declarations counted in the size line: all assigned ones (default) or used ones')
    ap.add_argument('--max-results', type=int, default=20, help='results listed per unit (default 20)')
    ap.add_argument('--max-definitions', type=int, default=30, help='definitions listed per unit (default 30)')
    ap.add_argument('--max-inputs', type=int, default=30, help='inputs and outputs listed per unit (default 30)')
    ap.add_argument('--max-files', type=int, default=12, help='source files listed per unit (default 12)')
    ap.add_argument('--excerpt-lines', type=int, default=12, help='longest statement excerpt (default 12 lines)')
    ap.add_argument('--only', action='append', default=[], help='only this unit (repeatable), e.g. for pilots')
    ap.add_argument('--candidates', action='store_true', help='write key-statement candidate batches instead')
    ap.add_argument('--min-mass', type=int, default=100, help='candidates: smallest mass (default 100 lines)')
    ap.add_argument('--batch-size', type=int, default=25, help='candidates: largest batch (default 25)')
    ap.add_argument('--force', action='store_true', help='candidates: replace the batches of an earlier run')
    a = ap.parse_args()

    for p in (a.db, a.assign) + tuple(x for x in (a.units, a.dominators, a.key_statements, a.roots_file) if x):
        if not os.path.isfile(p):
            die(f'no such file: {p}')
    if not os.path.isdir(a.src):
        die(f'no such directory: {a.src}')
    if a.batch_size < 1 or a.excerpt_lines < 1:
        die('--batch-size and --excerpt-lines must be positive')
    src = os.path.realpath(a.src)
    out = os.path.realpath(a.out_dir)
    if out == src or out.startswith(src + os.sep):
        die(f'--out-dir {a.out_dir} is inside --src: the source checkout is read-only')
    con = sqlite3.connect(f'file:{a.db}?mode=ro', uri=True)
    ncols = {r[1] for r in con.execute('PRAGMA table_info(nodes)')}
    ecols = {r[1] for r in con.execute('PRAGMA table_info(edges)')}
    for c in ('name', 'kind', 'path', 'line', 'line_end', 'used'):
        if c not in ncols:
            die(f'nodes has no column {c} (the lean-dependency-graph schema is expected)')
    try:
        meta = dict(con.execute('SELECT key, value FROM meta'))
    except sqlite3.Error:
        meta = {}
    repo = (a.repo_url or meta.get('source_url') or '').rstrip('/')
    commit = (a.commit or meta.get('commit') or '').strip()
    if not repo:
        die('no --repo-url, and the graph records no source_url')
    if repo.endswith('.git'):
        repo = repo[:-4]
    if not re.fullmatch(r'[0-9a-fA-F]{7,40}', commit):
        die(f'refusing an unpinned or missing commit {commit!r}: give --commit with a commit id, not a branch or tag')
    note = check_checkout(src, commit)

    node = {}
    q = ('SELECT name, kind, path, line, line_end, ' + ('lines' if 'lines' in ncols else 'NULL') + ', used, '
         + ('doc' if 'doc' in ncols else 'NULL') + ' FROM nodes')
    for name, kind, path, line, end, ln, used, doc in con.execute(q):
        if ln is None and line and end and end >= line:
            ln = end - line + 1
        old = node.get(name)
        if old is None:
            node[name] = {'kind': kind or '', 'path': path, 'line': line, 'end': end, 'lines': ln or 0,
                          'used': 1 if used else 0, 'doc': doc}
        else:       # repeated rows (a merged database): the largest span, any used flag, the first docstring
            if (ln or 0) > old['lines']:
                old.update(path=path, line=line, end=end, lines=ln or 0)
            old['used'] = max(old['used'], 1 if used else 0)
            old['doc'] = old['doc'] or doc
    used = {n for n, v in node.items() if v['used']}
    if not used:
        die('no declaration has used = 1: run closure.py first')

    arows = read_tsv(a.assign)
    if arows and (a.name_col not in arows[0] or a.unit_col not in arows[0]):
        die(f'{a.assign} needs columns {a.name_col} and {a.unit_col}')
    assign, conflicts = {}, []
    for r in arows:
        nm, u = (r.get(a.name_col) or '').strip(), (r.get(a.unit_col) or '').strip()
        if not nm or not u:
            continue
        if nm in assign and assign[nm] != u:
            conflicts.append(f'{nm}: {assign[nm]} / {u}')
        assign[nm] = u
    if conflicts:
        die(f'{len(conflicts)} names have two units, e.g. {conflicts[0]}')
    catalogue = read_tsv(a.units) if a.units else []
    meta_u = {r[a.unit_col]: r for r in catalogue if r.get(a.unit_col)}
    order = [r[a.unit_col] for r in catalogue if r.get(a.unit_col)]
    order += sorted(set(assign.values()) - set(order), key=natural)
    bad = [u for u in order if not UNIT_RE.match(u)]
    if bad:
        die(f'unit ids must use letters, digits, _ . - (they name files and rollout units): {", ".join(bad[:5])}')
    if a.only:
        missing = sorted(set(a.only) - set(order))
        if missing:
            die(f'--only names units that are not assigned: {", ".join(missing)}')
        order = [u for u in order if u in set(a.only)]
    uix = {u: i for i, u in enumerate(order)}

    source = Source(src)
    probe = [n for n in sorted(used) if node[n]['path']][:50]
    if probe and all(source.lines(node[n]['path']) is None for n in probe):
        die(f'none of the source files of the graph is under --src {a.src} (e.g. {node[probe[0]]["path"]}): '
            f'is it the checkout root, with the path prefix used by build_graph_db.py?')

    roots = read_roots(a.roots_file) if a.roots_file else []
    if not roots:
        try:
            roots = [r[0] for r in con.execute('SELECT name FROM roots')]
        except sqlite3.Error:
            roots = []
    roots = sorted({r for r in roots if r in node})
    if a.dominators:
        mass, idom = {}, {}
        for r in read_tsv(a.dominators):
            try:
                mass[r['name']] = int(r['mass'])
                idom[r['name']] = r.get('idom', '') or ''
            except (KeyError, ValueError):
                die(f'{a.dominators}: needs columns name and mass (dominators.tsv of own_and_scale.py)')
        mass_from = f'read from {os.path.basename(a.dominators)} (own_and_scale.py)'
    else:
        if not roots:
            die('no roots to compute mass (the roots table of the graph, or --roots-file); or give --dominators')
        mass, idom = compute_mass(con, node, roots)
        mass_from = f'computed from the dominator tree of the {len(roots)} roots, as own_and_scale.py does'

    def mass_of(n):
        return mass.get(n, node[n]['lines'])

    def link(n):
        v = node[n]
        url = f'{repo}/blob/{commit}/{v["path"]}'
        if v['line'] and v['end'] and v['end'] > v['line']:
            url += f'#L{v["line"]}-L{v["end"]}'
        elif v['line']:
            url += f'#L{v["line"]}'
        return url

    def md_link(n):
        return f'[`{n}`]({link(n)})' if node[n]['path'] else f'`{n}`'

    result_kinds = {k.strip() for k in a.result_kinds.split(',') if k.strip()}
    def_kinds = {k.strip() for k in a.definition_kinds.split(',') if k.strip()}
    os.makedirs(out, exist_ok=True)
    head_note = (f'Lean source at commit `{commit[:12]}` of {repo}; every link is pinned to it. An excerpt is source '
                 f'text from the recorded lines, cut by a simple rule: it is not the elaborated statement, so open '
                 f'the link before citing it.')

    if a.candidates:
        stale = sorted(f for f in os.listdir(out) if re.fullmatch(r'B\d+\.md', f))
        if stale and not a.force:
            die(f'{a.out_dir} holds batches of an earlier run ({stale[0]}, ...): use a new directory or --force')
        for f in stale:
            os.remove(os.path.join(out, f))
        rootset = set(roots)
        cands = [n for n in used if n in rootset or (node[n]['kind'] in result_kinds and mass_of(n) >= a.min_mass)]
        cands = [n for n in cands if not a.only or assign.get(n) in uix]
        if not cands:
            die(f'no candidates: no root and no result with mass >= {a.min_mass} in the selected units')
        cands.sort(key=lambda n: (uix.get(assign.get(n), len(uix)), node[n]['path'] or '', node[n]['line'] or 0, n))
        groups = collections.OrderedDict()
        for n in cands:
            groups.setdefault(assign.get(n, ''), []).append(n)
        batches = []
        for u, ns in groups.items():
            k = math.ceil(len(ns) / a.batch_size)
            base, extra = divmod(len(ns), k)
            i = 0
            for j in range(k):
                size = base + (1 if j < extra else 0)
                batches.append((u, j + 1, k, ns[i:i + size], i + 1, len(ns)))
                i += size
        width = max(3, len(str(len(batches))))
        units_json = {}
        with open(os.path.join(out, 'candidates.tsv'), 'w', encoding='utf-8') as tsv:
            tsv.write('item\tbatch\tunit\tkind\tlines\tmass\tlink\tdoc\n')
            for t, (u, j, k, ns, first, total) in enumerate(batches):
                bid = f'B{t + 1:0{width}d}'
                ut = meta_u.get(u, {}).get('title', '')
                where = (f'unit {u}' + (f' ({ut})' if ut else '')) if u else 'declarations without a unit'
                title = f'{where}, candidates {first}-{first + len(ns) - 1} of {total}'
                units_json[bid] = {'title': title}
                L = [f'# Key-statement candidates, batch {bid}', '',
                     f'{title[0].upper() + title[1:]} (batch {j} of {k} of this unit). {head_note}', '',
                     'For each candidate: the item to copy into your table (its full Lean name), its kind and size '
                     '(mass: its lines and those of everything reached from the roots only through it), a pinned '
                     'link, its docstring, and an excerpt of its statement.', '']
                for pos, n in enumerate(ns, 1):
                    v = node[n]
                    L += [f'## {pos}. `{n}`', '',
                          f'{v["kind"]} · {num(v["lines"])} lines · mass {num(mass_of(n))}'
                          + (' · root' if n in rootset else '') + (f' · [source]({link(n)})' if v['path'] else ''), '']
                    doc = (v['doc'] or '').strip()
                    if doc:
                        dl = doc.split('\n')
                        dl = dl[:20] + (['…'] if len(dl) > 20 else [])
                        L += ['Docstring:', ''] + ['> ' + x if x.strip() else '>' for x in dl] + ['']
                    else:
                        L += ['No docstring.', '']
                    ex, how = source.excerpt(v, a.excerpt_lines)
                    if ex is None:
                        L += [f'No statement excerpt ({how}).', '']
                    else:
                        fz = fence(ex)
                        L += [f'Statement excerpt ({how}):', '', fz + 'lean', ex, fz, '']
                    tsv.write('\t'.join([n, bid, u, v['kind'], str(v['lines']), str(mass_of(n)),
                                         link(n) if v['path'] else '',
                                         first_line(v['doc']).replace('\t', ' ')]) + '\n')
                with open(os.path.join(out, f'{bid}.md'), 'w', encoding='utf-8') as f:
                    f.write('\n'.join(L).rstrip() + '\n')
        with open(os.path.join(out, 'batches.json'), 'w', encoding='utf-8') as f:
            json.dump(units_json, f, indent=1, ensure_ascii=False)
            f.write('\n')
        if note:
            print(f'note: {note}', file=sys.stderr)
        if source.missing:
            print(f'warning: {len(source.missing)} source files not found under --src, e.g. '
                  f'{sorted(source.missing)[0]}', file=sys.stderr)
        print(f'inventory --candidates: {len(cands)} candidates (roots and results with mass >= {a.min_mass}) in '
              f'{len(batches)} batches from {len(groups)} units -> {a.out_dir}; mass {mass_from}')
        return 0

    # ---------- inventory mode
    members = collections.defaultdict(list)
    for nm, u in assign.items():
        if nm in node and u in uix:
            members[u].append(nm)
    users = collections.Counter()
    inputs = collections.defaultdict(collections.Counter)
    inputs_st = collections.defaultdict(collections.Counter)
    in_pairs = collections.defaultdict(collections.Counter)
    in_decls = collections.defaultdict(lambda: collections.defaultdict(set))
    outputs = collections.defaultdict(collections.Counter)
    out_units = collections.defaultdict(set)
    out_pairs = collections.defaultdict(collections.Counter)
    q = 'SELECT src, dst, ' + ('part' if 'part' in ecols else "'both'") + ' FROM edges'
    for s, d, part in con.execute(q):
        if s == d or s not in used or d not in used:
            continue
        users[d] += 1
        us, ud = assign.get(s), assign.get(d)
        if us == ud:
            continue
        if us in uix:
            inputs[us][d] += 1
            if part in ('statement', 'both'):
                inputs_st[us][d] += 1
            in_pairs[us][ud or NOUNIT] += 1
            in_decls[us][ud or NOUNIT].add(d)
        if ud in uix:
            outputs[ud][d] += 1
            out_units[d].add(us or NOUNIT)
            out_pairs[ud][us or NOUNIT] += 1
    ks = collections.defaultdict(list)
    if a.key_statements:
        for r in read_tsv(a.key_statements):
            ks[(r.get(a.unit_col) or '').strip()].append(r)

    def union(ivs):
        tot, end = 0, None
        for x, y in sorted(ivs):
            if end is None or x > end:
                tot, end = tot + y - x + 1, y
            elif y > end:
                tot, end = tot + y - end, y
        return tot

    rootset = set(roots)
    n_results = 0
    for u in order:
        mem = members.get(u, [])
        scope = [n for n in mem if a.scope == 'all' or n in used]
        spans = collections.defaultdict(list)
        for n in scope:
            v = node[n]
            if v['lines'] > 0 and v['path'] and v['line']:
                spans[v['path']].append((v['line'], v['line'] + v['lines'] - 1))
        per_file = sorted(((union(iv), p) for p, iv in spans.items()), key=lambda t: (-t[0], t[1]))
        total_lines = sum(x for x, _ in per_file)
        ndecl = sum(1 for n in scope if node[n]['lines'] > 0)
        umem = [n for n in mem if n in used]
        kinds = collections.Counter(node[n]['kind'] for n in umem)
        ut = meta_u.get(u, {})
        L = [f'# Source inventory of unit {u}' + (f': {ut["title"]}' if ut.get('title') else ''), '']
        if ut.get('part'):
            L += [f'Part {ut["part"]}.', '']
        L += [f'Generated by `inventory.py` (coarse-graining skill) from the declaration graph and the unit '
              f'assignment. Apart from the size line, it lists only declarations in the closure of the roots '
              f'(`used = 1`). {head_note}', '']
        L += ['## Size', '',
              f'{num(total_lines)} lines (union of the declaration spans per file; '
              f'{"all assigned declarations" if a.scope == "all" else "declarations in the closure"}) in '
              f'{pl(ndecl, "declaration")}; {num(len(umem))} of the unit\'s declarations are in the closure'
              + (' (by kind: ' + ', '.join(f'{k} {num(c)}' for k, c in kinds.most_common()) + ')' if kinds else '')
              + '.', '']
        if per_file:
            L += ['| source file | lines |', '|---|---:|']
            L += [f'| [`{p}`]({repo}/blob/{commit}/{p}) | {num(x)} |' for x, p in per_file[:a.max_files]]
            if len(per_file) > a.max_files:
                L.append(f'| and {len(per_file) - a.max_files} more files | {num(sum(x for x, _ in per_file[a.max_files:]))} |')
            L.append('')
        res = sorted((n for n in umem if node[n]['kind'] in result_kinds), key=lambda n: (-mass_of(n), n))
        L += ['## Results by mass', '',
              f'{pl(len(res), "result")} in the closure. Mass: the lines of a result plus those of every declaration '
              f'it dominates (reached from the roots only through it), {mass_from}. "Under" names its immediate '
              f'dominator: the declaration through which every chain of references from the roots reaches it.', '']
        for i, n in enumerate(res[:a.max_results], 1):
            v = node[n]
            up = idom.get(n, '')
            if up:
                where = f' · under `{up}`' + (f' (unit {assign[up]})' if assign.get(up) not in (None, u) else '')
            else:
                where = ' · a root' if (n in rootset or n in idom) else ''
            L += [f'### R{i}. `{n}`', '',
                  f'{v["kind"]} · {num(v["lines"])} lines · mass {num(mass_of(n))}'
                  + (f' · [source]({link(n)})' if v['path'] else '') + where, '']
            fl = first_line(v['doc'])
            L += [f'Docstring (first line): {fl}' if fl else 'No docstring.', '']
            ex, how = source.excerpt(v, a.excerpt_lines)
            if ex is None:
                L += [f'No statement excerpt ({how}).', '']
            else:
                fz = fence(ex)
                L += [f'Statement excerpt ({how}):', '', fz + 'lean', ex, fz, '']
            n_results += 1
        if len(res) > a.max_results:
            L += [f'And {num(len(res) - a.max_results)} smaller results.', '']
        defs = sorted((n for n in umem if node[n]['kind'] in def_kinds), key=lambda n: (-users[n], n))
        L += ['## Definitions introduced', '',
              f'{pl(len(defs), "definition")} in the closure (kinds {", ".join(sorted(def_kinds))}), most used first '
              f'(users: declarations of the closure that reference it).', '']
        if defs:
            L += ['| definition | kind | users | docstring (first line) |', '|---|---|---:|---|']
            L += [f'| {md_link(n)} | {node[n]["kind"]} | {num(users[n])} | {cell(first_line(node[n]["doc"]))} |'
                  for n in defs[:a.max_definitions]]
            if len(defs) > a.max_definitions:
                L.append(f'| and {num(len(defs) - a.max_definitions)} more | | | |')
            L.append('')
        inp = inputs.get(u, collections.Counter())
        L += ['## Inputs from other units', '',
              f'Declarations of other units that this unit\'s declarations reference: {pl(len(inp), "declaration")}, '
              f'{pl(sum(inp.values()), "reference")} (distinct pairs). These are code references, not a reading '
              f'order.', '']
        if inp:
            L.append('By unit: ' + '; '.join(
                f'{w}: {pl(c, "reference")} to {pl(len(in_decls[u][w]), "declaration")}'
                for w, c in sorted(in_pairs[u].items(), key=lambda t: (-t[1], natural(t[0])))) + '.')
            L += ['', '| declaration | unit | kind | referencing declarations of this unit | in statements | '
                  'docstring (first line) |', '|---|---|---|---:|---:|---|']
            for d, c in sorted(inp.items(), key=lambda t: (-t[1], t[0]))[:a.max_inputs]:
                L.append(f'| {md_link(d)} | {assign.get(d, NOUNIT)} | {node[d]["kind"]} | {num(c)} | '
                         f'{num(inputs_st[u][d])} | {cell(first_line(node[d]["doc"]))} |')
            L.append('')
        outp = outputs.get(u, collections.Counter())
        L += ['## Used by other units', '',
              f'This unit\'s declarations referenced from other units: {pl(len(outp), "declaration")}, '
              f'{pl(sum(outp.values()), "reference")}.', '']
        if outp:
            L.append('By unit: ' + '; '.join(f'{w}: {pl(c, "reference")}' for w, c in
                                            sorted(out_pairs[u].items(), key=lambda t: (-t[1], natural(t[0])))) + '.')
            L += ['', '| declaration | kind | referencing declarations of other units | units |', '|---|---|---:|---|']
            for d, c in sorted(outp.items(), key=lambda t: (-t[1], t[0]))[:a.max_inputs]:
                L.append(f'| {md_link(d)} | {node[d]["kind"]} | {num(c)} | '
                         f'{", ".join(sorted(out_units[d], key=natural))} |')
            L.append('')
        if a.key_statements:
            rows = ks.get(u, [])
            L += ['## Key statements', '', f'{len(rows)} rows of key-statements.tsv for this unit.', '']
            if rows:
                L += ['| number | importance | Lean | summary |', '|---|---|---|---|']
                for r in rows:
                    nm = (r.get('lean_name') or '').strip()
                    lk = (r.get('link') or '').strip()
                    L.append(f'| {cell(r.get("number"))} | {cell(r.get("importance"))} | '
                             + (f'[`{nm}`]({lk})' if lk else f'`{nm}`') + f' | {cell(r.get("summary"))} |')
                L.append('')
        with open(os.path.join(out, f'{u}.md'), 'w', encoding='utf-8') as f:
            f.write('\n'.join(L).rstrip() + '\n')
    if note:
        print(f'note: {note}', file=sys.stderr)
    if source.missing:
        print(f'warning: {len(source.missing)} source files not found under --src, e.g. {sorted(source.missing)[0]}',
              file=sys.stderr)
    unassigned = sum(1 for n in used if n not in assign)
    print(f'inventory: {len(order)} unit inventories -> {a.out_dir}; {n_results} results with excerpts listed; '
          f'{unassigned} used declarations without a unit; mass {mass_from}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
