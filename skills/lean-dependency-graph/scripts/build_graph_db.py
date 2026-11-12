#!/usr/bin/env python3
"""Build the declaration graph (SQLite) from the raw TSV chunks written by Extract.lean.

Steps:
  1. Read every declaration, range, docstring and tag; strip `_private.<Module>.0.` prefixes (kept when the
     short name would collide with another declaration).
  2. Classify constants: real declarations; generated auxiliaries (`_proof_3`, `match_1`, `eq_1`, `rec`,
     `casesOn`, `below`, `_simp_1_2`, ...), attributed to the declaration that owns them; metaprogramming
     constants (parsers, macros, unexpanders: their type mentions a meta type), dropped unless --keep-meta.
  3. Liveness: an auxiliary counts only if a real declaration reaches it through references; dead
     auxiliaries contribute no edges. An auxiliary with no owner among the project declarations (for instance
     an equation lemma of a library definition, realized in a project module) is expanded: its users inherit
     its references.
  4. Edges between owners, deduplicated: part = statement (only in the elaborated type of the declaration
     itself), proof (only in its value, or in any of its auxiliaries), or both. Self-references are dropped.

Schema (see references/schema-and-queries.md):
  meta(key, value)
  nodes(name PK, kind, module, path, line, line_end, lines, doc, used, n_aux, sorry, parent)
                                 parent = the inductive type of a constructor, the structure of a field
                                 sorry = 1 if the declaration or one of its auxiliaries uses sorryAx
  edges(src, dst, part, direct)  PK(src, dst); direct = 0 if every reference came through auxiliaries
  aux(name PK, short, owner, status)  name as compiled, short without the private prefix;
                                      status: live | dead | expanded (no project owner) | meta
  roots(name PK)                 filled by closure.py
  ext_edges(src, dst, part)      only with --keep-external: references to constants outside the project

A name declared in two modules (for example a challenge file with a placeholder and the solution that proves
the same name) is an input error: exclude the module that the roots do not import with --exclude-module.

Usage:
  build_graph_db.py raw/ --db graph.sqlite --commit 3456e5e... --tool-version "Lean 4.32.0"
"""
import argparse
import collections
import datetime
import glob
import os
import re
import sqlite3
import sys
import time

# Name components that mark generated auxiliary constants. Kept in the database (meta.aux_component_regex),
# so that compare_usage.py attributes names with the same rule.
AUX_COMPONENTS = (
    # recursors and structural helpers of inductive types
    r'rec|recOn|casesOn|below|brecOn|binductionOn|ibelow|noConfusion|noConfusionType|injEq|inj|ctorIdx|'
    r'ctorElim|ctorElimType|toCtorIdx|_flat_ctor|_sizeOf_inst|sizeOf_spec|_sizeOf_\d+|sizeOf_\d+|rec_\d+|'
    r'below_\d+|brecOn_\d+|_nested_\d+|'
    # abstracted proofs, matchers, equation lemmas, well-founded recursion, compiler and tactic helpers
    r'_proof_\d+(_\d+)*|proof_\d+|_simp_\d+(_\d+)*|_abel_\d+(_\d+)*|_auxLemma_\d+|_aux_\d+|eq_\d+|eq_def|'
    r'eq_unfold|match_\d+(_\d+)*|splitter|_unsafe_rec|_f|_sunfold|_unary|_binary|_mutual|induct|'
    r'mutual_induct|fun_cases|_unfold|else_eq|congr_simp|hcongr_\d+|_cstage\d|_lambda_\d+|_closed_\d+|'
    r'_spec_\d+|_boxed|_rarg|_redArg|_sparseCasesOn_\d+|_private_\d+|_cond_\d+|_ext_\d+')
PRIVATE_RE = r'^_private\.(.+?)\.0\.'
# A declaration whose elaborated type mentions one of these is metaprogramming (syntax, macro, delaborator).
META_TYPES = ('Lean.ParserDescr', 'Lean.TrailingParserDescr', 'Lean.Macro', 'Lean.PrettyPrinter.Unexpander',
              'Lean.PrettyPrinter.Delaborator.Delab', 'Lean.Elab.Term.TermElab', 'Lean.Elab.Command.CommandElab',
              'Lean.Elab.Tactic.Tactic', 'Lean.Parser.Parser', 'Lean.Parser.TrailingParser',
              'Lean.Meta.Simp.Simproc', 'Lean.Meta.Simp.DSimproc')
PART = {1: 'statement', 2: 'proof', 3: 'both'}


def die(msg):
    print(f'build_graph_db.py: {msg}', file=sys.stderr)
    sys.exit(2)


def split_name(n):
    """Split a Lean name at dots outside «...» quotes."""
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


def unescape(s):
    out, i = [], 0
    while i < len(s):
        c = s[i]
        if c == '\\' and i + 1 < len(s):
            out.append({'n': '\n', 't': '\t', 'r': '\r', '\\': '\\'}.get(s[i + 1], s[i + 1]))
            i += 2
        else:
            out.append(c)
            i += 1
    return ''.join(out)


def input_files(paths):
    files = []
    for p in paths:
        if os.path.isdir(p):
            files += sorted(glob.glob(os.path.join(p, 'chunk_*.tsv')))
        elif os.path.isfile(p):
            files.append(p)
        else:
            die(f'no such file or directory: {p}')
    if not files:
        die('no chunk_*.tsv input files found')
    return files


def records(files):
    for f in files:
        with open(f, encoding='utf-8') as fh:
            for line in fh:
                parts = line.rstrip('\n').split('\t')
                if len(parts) == 5:
                    yield parts


def main():
    ap = argparse.ArgumentParser(
        description='Build the SQLite declaration graph from Extract.lean chunks (auxiliaries attributed to owners).',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='example:\n  build_graph_db.py raw/ --db graph.sqlite --commit 3456e5e75cf8d4cd558955a5c7638fba2d68f464 \\\n'
               '      --source-url https://github.com/yang-mills-group/OpenAI-YM-20261028 --tool-version "Lean 4.32.0"')
    ap.add_argument('inputs', nargs='+', help='chunk_*.tsv files, or directories holding them')
    ap.add_argument('--db', required=True, help='output SQLite file')
    ap.add_argument('--force', action='store_true', help='overwrite an existing --db')
    ap.add_argument('--path-prefix', default='', help='prefix of source paths, e.g. "src/" (default: none); '
                    'module A.B.C is read from <prefix>A/B/C.lean')
    ap.add_argument('--commit', default='', help='source commit the build was made from (recorded in meta)')
    ap.add_argument('--source-url', default='', help='source repository URL (recorded in meta)')
    ap.add_argument('--tool-version', default='', help='Lean version used for the build, e.g. "Lean 4.32.0"')
    ap.add_argument('--extra-aux', action='append', default=[],
                    help='extra regex for auxiliary name components (repeatable)')
    ap.add_argument('--keep-meta', action='store_true', help='keep metaprogramming constants as nodes')
    ap.add_argument('--keep-external', action='store_true',
                    help='also store references to constants outside the project (table ext_edges)')
    ap.add_argument('--exclude-module', action='append', default=[],
                    help='ignore every record of modules matching this regex (repeatable), e.g. "^Challenge$"')
    ap.add_argument('--allow-duplicates', action='store_true',
                    help='keep the first of two declarations with the same name instead of failing')
    ap.add_argument('--sorry-const', action='append', default=None,
                    help='constant whose use marks a declaration in nodes.sorry (default: sorryAx)')
    ap.add_argument('--link-ctors', action='store_true',
                    help='add an edge from every inductive type to each of its constructors (part statement)')
    a = ap.parse_args()

    if os.path.exists(a.db) and not a.force:
        die(f'{a.db} exists; use --force to overwrite')
    files = input_files(a.inputs)
    t0 = time.time()
    aux_rx = AUX_COMPONENTS + ''.join('|' + x for x in a.extra_aux)
    aux_re = re.compile(r'^(?:%s)$' % aux_rx)
    priv_re = re.compile(PRIVATE_RE)
    meta_types = set(META_TYPES)
    excl = [re.compile(x) for x in a.exclude_module]
    sorry_consts = set(a.sorry_const or ['sorryAx'])
    excluded_modules = set()

    # ---------- pass 1: declarations, ranges, docs, tags, meta constants, references to auxiliaries
    decl = {}           # raw name -> (module, kind)
    rng, doc, tags, parent = {}, {}, collections.defaultdict(set), {}
    meta = set()
    aux_name_cache = {}
    aux_refs = collections.defaultdict(set)   # referencing raw name -> aux-looking raw names it references
    dup = collections.defaultdict(list)       # raw name -> further modules declaring it
    mod_ok = {}

    def looks_aux(n):
        r = aux_name_cache.get(n)
        if r is None:
            cs = split_name(n)
            r = any(aux_re.match(c) for c in cs[1:]) or '_@' in cs
            aux_name_cache[n] = r
        return r

    for m, c, rec, x, y in records(files):
        ok = mod_ok.get(m)
        if ok is None:
            ok = mod_ok[m] = not any(r.search(m) for r in excl)
            if not ok:
                excluded_modules.add(m)
        if not ok:
            continue
        if rec == 'type' or rec == 'value':
            if rec == 'type' and x in meta_types:
                meta.add(c)
            if looks_aux(x):
                aux_refs[c].add(x)
        elif rec == 'decl':
            if c in decl:
                dup[c].append(m)
            else:
                decl[c] = (m, x)
        elif rec == 'range':
            try:
                rng[c] = (int(x), int(y))
            except ValueError:
                pass
        elif rec == 'doc':
            doc[c] = unescape(x)
        elif rec == 'tag':
            tags[c].add(x)
        elif rec == 'parent':
            parent[c] = x
    if not decl:
        die('no decl records in the input')
    meta = {c for c in meta if c in decl and decl[c][1] != 'theorem'}

    # ---------- names: private prefixes
    public = {n for n in decl if not n.startswith('_private.')}
    short = {}
    for n in decl:
        if n.startswith('_private.'):
            short[n] = priv_re.sub('', n, count=1)
    clash = collections.Counter(short.values())
    norm = {}
    collisions = 0
    for n in decl:
        s = short.get(n, n)
        if n in short and (s in public or clash[s] > 1):
            s = n
            collisions += 1
        norm[n] = s

    def normalize(n):
        r = norm.get(n)
        return r if r is not None else (priv_re.sub('', n, count=1) if n.startswith('_private.') else n)

    # ---------- classification and owners
    def comps_aux(cs):
        last = cs[-1]
        if aux_re.match(last):
            return True
        return last == 'eq' and len(cs) > 2 and bool(aux_re.match(cs[-2]))

    # A constant is real unless its last name component is auxiliary or it carries a macro scope. A constant
    # with a source range was written by a person and stays real whatever its name (e.g. a lemma named `inj`).
    real = set()
    for n in decl:
        if n in meta and not a.keep_meta:
            continue
        cs = split_name(normalize(n))
        if n not in rng and ('_@' in cs or (len(cs) > 1 and comps_aux(cs))):
            continue
        real.add(normalize(n))
    owner_cache = {}

    def owner(n):
        """Owning real declaration (normalized name) of a raw constant name, or None."""
        r = owner_cache.get(n, 0)
        if r != 0:
            return r
        cs = split_name(normalize(n))
        if '_@' in cs and '.'.join(cs) not in real:
            cs = cs[:cs.index('_@')] or cs
        r = None
        while cs:
            cand = '.'.join(cs)
            if cand in real:
                r = cand
                break
            if len(cs) > 1 and comps_aux(cs):
                cs = cs[:-1]
            else:
                break
        owner_cache[n] = r
        return r

    status = {}           # raw aux/meta name -> status
    for n in decl:
        if n in meta and not a.keep_meta:
            status[n] = 'meta'
        elif normalize(n) not in real:
            status[n] = 'aux'
    real_dups = sorted(n for n in dup if n not in status)
    if real_dups and not a.allow_duplicates:
        for n in real_dups[:20]:
            print(f'  {n}: declared in {decl[n][0]} and {", ".join(dup[n])}', file=sys.stderr)
        die(f'{len(real_dups)} declarations are declared in more than one module (listed above); exclude the '
            f'modules that the roots do not import with --exclude-module, or pass --allow-duplicates')
    # liveness: real declarations are live; an auxiliary is live if a live constant references it
    live = {n for n in decl if n not in status}
    stack = list(live)
    while stack:
        x = stack.pop()
        for y in aux_refs.get(x, ()):
            if y in decl and y not in live and status.get(y) == 'aux':
                live.add(y)
                stack.append(y)
    del aux_refs
    for n, st in status.items():
        if st == 'aux':
            if n not in live:
                status[n] = 'dead'
            elif owner(n) is None:
                status[n] = 'expanded'
            else:
                status[n] = 'live'

    # ---------- pass 2: edges
    idx = {}
    names = []

    def ix(n):
        i = idx.get(n)
        if i is None:
            i = idx[n] = len(names)
            names.append(n)
        return i

    for n in sorted(real):
        ix(n)
    nreal = len(names)
    edges = {}            # key src*K + dst -> bits; bit 4 = direct
    K = 1 << 32
    ext = {}
    exp_refs = collections.defaultdict(set)   # expanded aux raw name -> set of (target raw name)
    exp_users = collections.defaultdict(set)  # src index -> expanded aux raw names it references
    n_aux_of = collections.Counter()
    for n, st in status.items():
        if st == 'live':
            n_aux_of[owner(n)] += 1
    nrefs = 0
    sorry_users = set()
    for m, c, rec, x, y in records(files):
        if rec != 'type' and rec != 'value':
            continue
        if not mod_ok[m]:
            continue
        nrefs += 1
        st = status.get(c)
        if st == 'expanded':
            exp_refs[c].add(x)
            continue
        if c not in decl or st in ('dead', 'meta'):
            continue
        o = owner(c)
        if o is None:
            continue
        s = idx[o]
        if x in sorry_consts:
            sorry_users.add(s)
        is_self = st is None
        bit = 1 if (rec == 'type' and is_self) else 2
        if is_self:
            bit |= 4
        tst = status.get(x)
        if x in decl and tst in ('meta', 'dead'):
            continue
        if tst == 'expanded':
            exp_users[s].add(x)
            continue
        d = owner(x) if x in decl else None
        if d is not None:
            if d != o:
                key = s * K + idx[d]
                edges[key] = edges.get(key, 0) | bit
        elif a.keep_external and x not in decl:
            key = (s, x)
            ext[key] = ext.get(key, 0) | (bit & 3)
    # references through expanded auxiliaries (transitively through other expanded ones)
    exp_targets = {}

    def targets_of(u, seen):
        if u in exp_targets:
            return exp_targets[u]
        res = set()
        for t in exp_refs.get(u, ()):
            if status.get(t) == 'expanded':
                if t not in seen:
                    seen.add(t)
                    res |= targets_of(t, seen)
            elif t in decl and status.get(t) in ('meta', 'dead'):
                continue
            else:
                res.add(t)
        exp_targets[u] = res
        return res

    for s, us in exp_users.items():
        o = names[s]
        for u in us:
            for t in targets_of(u, {u}):
                if t in sorry_consts:
                    sorry_users.add(s)
                d = owner(t) if t in decl else None
                if d is not None and d != o:
                    key = s * K + idx[d]
                    edges[key] = edges.get(key, 0) | 2
                elif d is None and a.keep_external and t not in decl:
                    ext[(s, t)] = ext.get((s, t), 0) | 2
    n_linked = 0
    if a.link_ctors:
        for c, ind in parent.items():
            cn, i_n = owner(c), owner(ind)
            if cn and i_n and cn != i_n:
                key = idx[i_n] * K + idx[cn]
                if key not in edges:
                    n_linked += 1
                edges[key] = edges.get(key, 0) | 1

    # ---------- nodes
    structs = set()
    for n, ts in tags.items():
        if 'projection' in ts:
            cs = split_name(normalize(n))
            if len(cs) > 1:
                structs.add('.'.join(cs[:-1]))
    rows = []
    for n_raw, (m, kind) in decl.items():
        if n_raw in status:
            continue
        n = normalize(n_raw)
        ts = tags.get(n_raw, set())
        if 'instance' in ts:
            kind = 'instance'
        elif 'projection' in ts:
            kind = 'field'
        elif kind == 'inductive' and n in structs:
            kind = 'structure'
        line, end = rng.get(n_raw, (None, None))
        lines = (end - line + 1) if (line and end and end >= line) else None
        path = a.path_prefix + m.replace('.', '/') + '.lean'
        par = None
        if kind == 'ctor' and n_raw in parent:
            par = owner(parent[n_raw])
        elif kind == 'field':
            cs = split_name(n)
            par = '.'.join(cs[:-1]) if len(cs) > 1 else None
        rows.append((n, kind, m, path, line, end, lines, doc.get(n_raw), 0, n_aux_of.get(n, 0),
                     1 if idx[n] in sorry_users else 0, par))

    tmp = a.db + '.tmp'
    if os.path.exists(tmp):
        os.remove(tmp)
    con = sqlite3.connect(tmp)
    con.executescript('''
PRAGMA journal_mode=OFF; PRAGMA synchronous=OFF;
CREATE TABLE meta(key TEXT PRIMARY KEY, value TEXT);
CREATE TABLE nodes(name TEXT PRIMARY KEY, kind TEXT, module TEXT, path TEXT, line INTEGER, line_end INTEGER,
                   lines INTEGER, doc TEXT, used INTEGER NOT NULL DEFAULT 0, n_aux INTEGER NOT NULL DEFAULT 0,
                   sorry INTEGER NOT NULL DEFAULT 0, parent TEXT);
CREATE TABLE edges(src TEXT NOT NULL, dst TEXT NOT NULL,
                   part TEXT NOT NULL CHECK (part IN ('statement', 'proof', 'both')),
                   direct INTEGER NOT NULL, PRIMARY KEY (src, dst)) WITHOUT ROWID;
CREATE TABLE aux(name TEXT PRIMARY KEY, short TEXT, owner TEXT, status TEXT NOT NULL);
CREATE TABLE roots(name TEXT PRIMARY KEY);
''')
    con.executemany('INSERT INTO nodes VALUES (?,?,?,?,?,?,?,?,?,?,?,?)', rows)
    con.executemany('INSERT INTO edges VALUES (?,?,?,?)',
                    ((names[k // K], names[k % K], PART[b & 3], 1 if b & 4 else 0) for k, b in edges.items()))
    con.executemany('INSERT INTO aux VALUES (?,?,?,?)',
                    ((n, normalize(n), owner(n) if st in ('live', 'dead') else None, st)
                     for n, st in status.items()))
    if a.keep_external:
        con.execute('CREATE TABLE ext_edges(src TEXT NOT NULL, dst TEXT NOT NULL, part TEXT NOT NULL, '
                    'PRIMARY KEY (src, dst)) WITHOUT ROWID')
        con.executemany('INSERT INTO ext_edges VALUES (?,?,?)',
                        ((names[s], x, PART[b]) for (s, x), b in ext.items()))
    con.executescript('CREATE INDEX edges_dst ON edges(dst); CREATE INDEX nodes_module ON nodes(module); '
                      'CREATE INDEX nodes_used ON nodes(used); CREATE INDEX aux_owner ON aux(owner); '
                      'CREATE INDEX aux_short ON aux(short);')
    sc = collections.Counter(status.values())
    pc = collections.Counter(PART[b & 3] for b in edges.values())
    info = {
        'schema_version': '1',
        'tool': 'build_graph_db.py (lean-dependency-graph skill)',
        'created_utc': datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
        'lean_version': a.tool_version, 'commit': a.commit, 'source_url': a.source_url,
        'path_prefix': a.path_prefix, 'input_files': str(len(files)),
        'aux_component_regex': aux_rx, 'private_prefix_regex': PRIVATE_RE,
        'link_ctors': '1' if a.link_ctors else '0', 'keep_meta': '1' if a.keep_meta else '0',
        'constants_read': str(len(decl)), 'duplicate_constants': str(sum(map(len, dup.values()))),
        'duplicate_declarations_kept_first': str(len(real_dups)), 'reference_records': str(nrefs),
        'excluded_modules': ' '.join(sorted(excluded_modules)), 'nodes_with_sorry': str(len(sorry_users)),
        'nodes': str(len(rows)), 'edges': str(len(edges)),
        'edges_statement': str(pc['statement']), 'edges_proof': str(pc['proof']), 'edges_both': str(pc['both']),
        'aux_live': str(sc['live']), 'aux_dead': str(sc['dead']), 'aux_expanded': str(sc['expanded']),
        'meta_dropped': str(sc['meta']), 'private_name_collisions': str(collisions),
        'ctor_links_added': str(n_linked), 'nodes_with_range': str(sum(1 for r in rows if r[4])),
    }
    con.executemany('INSERT INTO meta VALUES (?,?)', sorted(info.items()))
    con.commit()
    con.close()
    os.replace(tmp, a.db)
    print(f'build_graph_db: {len(decl)} constants read; {len(rows)} nodes ({info["nodes_with_range"]} with source '
          f'ranges), {len(edges)} edges (statement {pc["statement"]}, proof {pc["proof"]}, both {pc["both"]}); '
          f'auxiliaries live {sc["live"]}, dead {sc["dead"]}, expanded {sc["expanded"]}; meta dropped '
          f'{sc["meta"]}; {time.time() - t0:.1f} s -> {a.db}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
