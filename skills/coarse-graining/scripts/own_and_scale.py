#!/usr/bin/env python3
"""Ownership and scales on the declaration graph: dominator tree, line mass, and a ladder of retained results.

Input: an SQLite graph with the lean-dependency-graph schema (nodes: name, kind, line, line_end [, lines], used;
edges: src, dst [, part]); `src` uses `dst`. Roots: arguments, --roots-file, or the database's `roots` table.

Method:
  1. Restrict to the used declarations (used = 1) reachable from the roots, under a virtual root.
  2. Dominator tree (computed iteratively over a reverse postorder): d dominates v if every chain of uses from
     the roots to v passes through d. mass(v) = lines(v) + lines of everything v dominates.
  3. At scale M a node is retained if it is a root, or a proof node (kind in --proof-kinds) with mass >= M.
     Retained sets nest: a larger M keeps a subset.
  4. Every other node is labelled from its users, users first (cycles are processed as one block): private to
     K if all its users lie in K's region (K or nodes private to K), else shared: toolbox if it is a proof
     node or used only by toolbox nodes, concept otherwise (definitions and types used from several regions).
     A private node is a helper reached only through K and is folded into K.
  5. Induced edges between regions (retained node plus its private helpers): count of declaration edges, of
     those in statements, and a transitive-reduction flag when the region graph is acyclic.

Outputs in --out-dir:
  dominators.tsv        name, kind, lines, idom, mass, proof
  ladder.tsv            per scale: retained, private, toolbox and concept counts and lines, region edges
  M<M>-nodes.tsv        name, label (retained|private|toolbox|concept), owner (the region, if any)
  M<M>-retained.tsv     retained results with mass, folded lines (own + private helpers), library uses, location
  M<M>-edges.tsv        src, dst, n, n_statement, reduced

Usage:
  own_and_scale.py --db graph.sqlite --out-dir coarse --scales 100,200,400,800,1600,3200
"""
import argparse
import collections
import os
import sqlite3
import sys
import time

TOOLBOX, CONCEPT, UNSET = -2, -3, -1


def die(msg):
    print(f'own_and_scale.py: {msg}', file=sys.stderr)
    sys.exit(2)


def read_roots(path):
    out = []
    with open(path, encoding='utf-8') as f:
        for line in f:
            line = line.split('#', 1)[0].strip()
            if line:
                out.append(line.split()[0])
    return out


def dominators(n, succ, pred, roots):
    """idom over nodes 0..n-1 reachable from a virtual root n linked to the roots. Returns (idom, rpo)."""
    VR = n
    # iterative DFS for postorder
    po = [-1] * (n + 1)
    order = []
    visited = bytearray(n + 1)
    stack = [(VR, iter(roots))]
    visited[VR] = 1
    while stack:
        v, it = stack[-1]
        for w in it:
            if not visited[w]:
                visited[w] = 1
                stack.append((w, iter(succ[w])))
                break
        else:
            stack.pop()
            po[v] = len(order)
            order.append(v)
    rpo = order[::-1]
    idom = [-1] * (n + 1)
    idom[VR] = VR
    rootset = set(roots)
    changed = True
    while changed:
        changed = False
        for v in rpo:
            if v == VR:
                continue
            new = VR if v in rootset else -1
            for p in pred[v]:
                if idom[p] == -1:
                    continue
                if new == -1:
                    new = p
                    continue
                a, b = p, new
                while a != b:
                    while po[a] < po[b]:
                        a = idom[a]
                    while po[b] < po[a]:
                        b = idom[b]
                new = a
            if idom[v] != new:
                idom[v] = new
                changed = True
    return idom, rpo


def sccs(n, succ, nodes):
    """Strongly connected components of the given nodes (iterative low-link search), dependencies first."""
    index = [-1] * n
    low = [0] * n
    onstack = bytearray(n)
    st, comps, counter = [], [], 0
    for s in nodes:
        if index[s] != -1:
            continue
        work = [(s, 0)]
        while work:
            v, i = work.pop()
            if i == 0:
                index[v] = low[v] = counter
                counter += 1
                st.append(v)
                onstack[v] = 1
            recurse = False
            sv = succ[v]
            while i < len(sv):
                w = sv[i]
                i += 1
                if index[w] == -1:
                    work.append((v, i))
                    work.append((w, 0))
                    recurse = True
                    break
                if onstack[w]:
                    low[v] = min(low[v], index[w])
            if recurse:
                continue
            if low[v] == index[v]:
                comp = []
                while True:
                    w = st.pop()
                    onstack[w] = 0
                    comp.append(w)
                    if w == v:
                        break
                comps.append(comp)
            if work:
                u = work[-1][0]
                low[u] = min(low[u], low[v])
    return comps


def main():
    ap = argparse.ArgumentParser(
        description='Dominator-tree ownership, line mass and a ladder of retained results on a declaration graph.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='example:\n  own_and_scale.py --db graph.sqlite --out-dir coarse --scales 100,200,400,800,1600,3200\n'
               'This script does not first fold fields, constructors, instances and short wrapper theorems into the\n'
               'declarations they serve; a pipeline that folds them gets different counts at every scale. Say\n'
               'which convention a published ladder uses.')
    ap.add_argument('roots', nargs='*', help='root names (default: --roots-file, else the roots table)')
    ap.add_argument('--db', required=True, help='SQLite graph (lean-dependency-graph schema); opened read-only')
    ap.add_argument('--roots-file', help='file with one root per line (# starts a comment)')
    ap.add_argument('--scales', default='100,200,400,800,1600,3200', help='comma-separated scales M, in lines')
    ap.add_argument('--proof-kinds', default='theorem,lemma,axiom',
                    help='kinds that count as proof nodes (default theorem,lemma,axiom)')
    ap.add_argument('--parts', default='statement,proof,both', help='edge parts to use (default: all)')
    ap.add_argument('--ignore-used', action='store_true',
                    help='use everything reachable from the roots, ignoring nodes.used')
    ap.add_argument('--joints', action='store_true',
                    help='promote a shared proof node that depends, through proof nodes, on a retained node')
    ap.add_argument('--reduce-max', type=int, default=20000,
                    help='compute the transitive-reduction flag only up to this many retained nodes')
    ap.add_argument('--out-dir', required=True, help='directory for the TSV outputs')
    a = ap.parse_args()

    t0 = time.time()
    try:
        scales = sorted({int(x) for x in a.scales.split(',') if x.strip()})
    except ValueError:
        die(f'bad --scales: {a.scales}')
    if not os.path.isfile(a.db):
        die(f'no such database: {a.db}')
    con = sqlite3.connect(f'file:{a.db}?mode=ro', uri=True)
    ncols = {r[1] for r in con.execute('PRAGMA table_info(nodes)')}
    ecols = {r[1] for r in con.execute('PRAGMA table_info(edges)')}
    for c in ('name', 'kind', 'line', 'line_end', 'used'):
        if c not in ncols:
            die(f'nodes has no column {c}')
    lines_expr = 'lines' if 'lines' in ncols else 'CASE WHEN line > 0 AND line_end >= line THEN line_end - line + 1 END'
    info = {}
    for name, kind, ln, used, mod, path, line in con.execute(
            f'SELECT name, kind, {lines_expr}, used, '
            + ('module' if 'module' in ncols else "''") + ', ' + ('path' if 'path' in ncols else "''")
            + ', line FROM nodes'):
        old = info.get(name)
        if old is None:
            info[name] = [kind, ln or 0, used or 0, mod, path, line]
        else:   # repeated rows for one name: keep the largest span, any used flag
            old[1] = max(old[1], ln or 0)
            old[2] = max(old[2], used or 0)
    roots = list(a.roots)
    if a.roots_file:
        roots += read_roots(a.roots_file)
    if not roots:
        try:
            roots = [r[0] for r in con.execute('SELECT name FROM roots')]
        except sqlite3.Error:
            roots = []
    roots = sorted(set(roots))
    if not roots:
        die('no roots (arguments, --roots-file, or a roots table)')
    missing = [r for r in roots if r not in info]
    if missing:
        die(f'roots not in the graph: {", ".join(missing[:10])}')
    has_used = any(v[2] for v in info.values())
    keep = set(info) if (a.ignore_used or not has_used) else {n for n, v in info.items() if v[2]}
    keep |= set(roots)
    names = sorted(keep)
    idx = {n: i for i, n in enumerate(names)}
    n = len(names)
    kind = [info[x][0] for x in names]
    lines = [info[x][1] for x in names]
    proof_kinds = {k.strip() for k in a.proof_kinds.split(',')}
    isproof = bytearray(1 if k in proof_kinds else 0 for k in kind)
    parts = [p.strip() for p in a.parts.split(',') if p.strip()]
    succ = [[] for _ in range(n + 1)]
    pred = [[] for _ in range(n + 1)]
    stmt_edges = set()
    q = 'SELECT src, dst' + (', part FROM edges' if 'part' in ecols else ", 'both' FROM edges")
    seen_pairs = set()
    for s, d, part in con.execute(q):
        if part not in parts and 'part' in ecols:
            continue
        i, j = idx.get(s), idx.get(d)
        if i is None or j is None or i == j:
            continue
        key = i * (n + 1) + j
        if key in seen_pairs:
            continue
        seen_pairs.add(key)
        succ[i].append(j)
        pred[j].append(i)
        if part in ('statement', 'both'):
            stmt_edges.add(key)
    del seen_pairs
    rix = [idx[r] for r in roots]
    VR = n
    succ[VR] = rix
    for r in rix:
        pred[r].append(VR)
    t1 = time.time()
    idom, rpo = dominators(n, succ, pred, rix)
    reached = [v for v in rpo if v != VR]
    if len(reached) < n:
        print(f'note: {n - len(reached)} of {n} selected declarations are not reachable from these roots; '
              f'they are left out', file=sys.stderr)
    mass = list(lines) + [0]
    for v in reversed(rpo):
        if v != VR:
            mass[idom[v]] += mass[v]
    t2 = time.time()
    comps = sccs(n, succ, reached)          # dependencies first
    comps.reverse()                          # users first
    os.makedirs(a.out_dir, exist_ok=True)
    with open(os.path.join(a.out_dir, 'dominators.tsv'), 'w', encoding='utf-8') as f:
        f.write('name\tkind\tlines\tidom\tmass\tproof\n')
        for v in reached:
            d = idom[v]
            f.write(f'{names[v]}\t{kind[v]}\t{lines[v]}\t{names[d] if d != VR else ""}\t{mass[v]}\t{isproof[v]}\n')

    rootset = set(rix)
    ladder = []
    for M in scales:
        kept = bytearray(n)
        for v in reached:
            if v in rootset or (isproof[v] and mass[v] >= M):
                kept[v] = 1
        anc = bytearray(n)
        if a.joints:
            stack = [v for v in reached if kept[v]]
            for v in stack:
                anc[v] = 1
            while stack:
                v = stack.pop()
                for u in pred[v]:
                    if u != VR and not anc[u] and isproof[u]:
                        anc[u] = 1
                        stack.append(u)
        label = [UNSET] * n
        joints = 0
        for comp in comps:
            cset = set(comp) if len(comp) > 1 else None
            ks = [v for v in comp if kept[v]]
            if ks:
                k0 = max(ks, key=lambda v: mass[v])
                for v in comp:
                    label[v] = v if kept[v] else k0
                continue
            regs = set()
            for v in comp:
                for u in pred[v]:
                    if u == VR or (cset and u in cset) or label[u] == UNSET:   # UNSET: user not reached
                        continue
                    regs.add(label[u])
                if len(regs) > 1:
                    break
            if len(regs) == 1:
                r = next(iter(regs))
                if r >= 0:
                    for v in comp:
                        label[v] = r
                    continue
            if a.joints:
                js = [v for v in comp if isproof[v] and anc[v]]
                if js:
                    j0 = max(js, key=lambda v: mass[v])
                    kept[j0] = 1
                    joints += 1
                    for v in comp:
                        label[v] = j0
                    continue
            only_tb = len(regs) == 1 and next(iter(regs)) == TOOLBOX
            for v in comp:
                label[v] = TOOLBOX if (isproof[v] or only_tb) else CONCEPT
        # regions, folded lines, edges
        region = [label[v] if label[v] >= 0 else -1 for v in range(n)]
        folded = collections.Counter()
        npriv = collections.Counter()
        cnt = collections.Counter()
        for v in reached:
            if label[v] >= 0:
                folded[label[v]] += lines[v]
                if label[v] != v:
                    npriv[label[v]] += 1
            cnt[label[v] if label[v] < 0 else ('kept' if label[v] == v else 'private')] += 1
        tl = sum(lines[v] for v in reached if label[v] == TOOLBOX)
        cl = sum(lines[v] for v in reached if label[v] == CONCEPT)
        E = collections.Counter()
        ES = collections.Counter()
        libuse = collections.Counter()
        tb_into = 0
        for u in reached:
            ru = region[u]
            for w in succ[u]:
                rw = region[w]
                if ru >= 0 and rw >= 0:
                    if ru != rw:
                        E[(ru, rw)] += 1
                        if u * (n + 1) + w in stmt_edges:
                            ES[(ru, rw)] += 1
                elif ru >= 0:
                    libuse[ru] += 1
                elif rw >= 0 and label[u] == TOOLBOX:
                    tb_into += 1
        keptv = [v for v in reached if kept[v]]
        reduced = set()
        acyclic = None
        if len(keptv) <= a.reduce_max:
            out_k = collections.defaultdict(list)
            indeg = collections.Counter()
            for (x, y) in E:
                out_k[x].append(y)
                indeg[y] += 1
            order = [v for v in keptv if indeg[v] == 0]
            i = 0
            while i < len(order):
                x = order[i]
                i += 1
                for y in out_k[x]:
                    indeg[y] -= 1
                    if indeg[y] == 0:
                        order.append(y)
            acyclic = len(order) == len(keptv)
            if acyclic:
                pos = {v: k for k, v in enumerate(order)}
                reach = {}
                for x in reversed(order):
                    r = 0
                    covered = 0
                    for y in sorted(out_k[x], key=lambda y: pos[y]):
                        if not (covered >> pos[y]) & 1:
                            reduced.add((x, y))
                        covered |= reach[y] | (1 << pos[y])
                        r |= reach[y] | (1 << pos[y])
                    reach[x] = r
        pre = os.path.join(a.out_dir, f'M{M}')
        with open(pre + '-nodes.tsv', 'w', encoding='utf-8') as f:
            f.write('name\tlabel\towner\n')
            for v in reached:
                lb = label[v]
                if lb >= 0:
                    f.write(f'{names[v]}\t{"retained" if lb == v else "private"}\t{names[lb]}\n')
                else:
                    f.write(f'{names[v]}\t{"toolbox" if lb == TOOLBOX else "concept"}\t\n')
        with open(pre + '-retained.tsv', 'w', encoding='utf-8') as f:
            f.write('name\tkind\tlines\tmass\tfolded_lines\tprivate_nodes\tlibrary_uses\tmodule\tpath\tline\n')
            for v in sorted(keptv, key=lambda v: -mass[v]):
                _, _, _, mod, path, line = info[names[v]]
                f.write(f'{names[v]}\t{kind[v]}\t{lines[v]}\t{mass[v]}\t{folded[v]}\t{npriv[v]}\t{libuse[v]}\t'
                        f'{mod or ""}\t{path or ""}\t{line or ""}\n')
        with open(pre + '-edges.tsv', 'w', encoding='utf-8') as f:
            f.write('src\tdst\tn\tn_statement\treduced\n')
            for (x, y), c in sorted(E.items(), key=lambda kv: (-kv[1], names[kv[0][0]], names[kv[0][1]])):
                red = '' if acyclic is None or not acyclic else ('1' if (x, y) in reduced else '0')
                f.write(f'{names[x]}\t{names[y]}\t{c}\t{ES[(x, y)]}\t{red}\n')
        ladder.append((M, len(keptv), cnt['private'], cnt[TOOLBOX], tl, cnt[CONCEPT], cl, len(E),
                       len(reduced) if acyclic else '', tb_into, joints))
    with open(os.path.join(a.out_dir, 'ladder.tsv'), 'w', encoding='utf-8') as f:
        hdr = ('M', 'retained', 'private', 'toolbox', 'toolbox_lines', 'concept', 'concept_lines', 'region_edges',
               'reduced_edges', 'toolbox_edges_into_retained', 'joints')
        f.write('\t'.join(hdr) + '\n')
        for row in ladder:
            f.write('\t'.join(map(str, row)) + '\n')
    total = sum(lines[v] for v in reached)
    print(f'{len(reached)} declarations reached from {len(roots)} roots ({total} lines); '
          f'{len(stmt_edges)} statement edges of {sum(len(succ[v]) for v in range(n))}; '
          f'dominators in {t2 - t1:.1f} s')
    print('M\tretained\tprivate\ttoolbox\tconcept\tregion edges\treduced')
    for row in ladder:
        print(f'{row[0]}\t{row[1]}\t{row[2]}\t{row[3]}\t{row[5]}\t{row[7]}\t{row[8]}')
    print(f'own_and_scale: {len(scales)} scales written to {a.out_dir} in {time.time() - t0:.1f} s')
    return 0


if __name__ == '__main__':
    sys.exit(main())
