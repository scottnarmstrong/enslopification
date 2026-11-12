#!/usr/bin/env python3
"""Check a published correspondence table (numbered statements <-> Lean declarations) mechanically.

Usage:
  check_correspondence.py TABLE.tsv --db GRAPH.sqlite [--tex PATH ...] [--commit SHA]
                          [--lean-repo DIR] [--check-graph-locations] [options]

TABLE.tsv: UTF-8, tab-separated, one header row. Lines starting with "#" above the header are
metadata "# key: value"; the table must record its pin as "# commit: <hash>" (or pass --pin-file).
Columns (found by header, case-insensitive; override with --col-*):
  label     the \\label of the statement, definition or display in the TeX
  kind      free text (definition, lemma, identity, ...)
  names     Lean declarations, separated by --sep (default ";"); a name may carry a tag in
            parentheses, e.g. "Foo.bar (Mathlib)": tags listed in --external-tags are external
            declarations, counted but not looked up; an entry wholly in parentheses is a note
  relation  one of --relations (default DIRECT,WEAKENING,COMPOSITION,CITED,NONE)
  where     file:line or file:start-end entries at the pinned commit, separated by --sep
Other columns (e.g. notes, with the bibliography key of a standard result) are ignored. Several
rows may share a label (one row per part of a statement). The relation words are defined in
references/correspondence-and-statement.md of the honest-publication skill.

A names cell "-" or an em dash means no declaration. A where entry may be a GitHub link
(.../blob/<commit>/<path>#L10-L20) or a module name with a line (YM.Gauge.Colors:52, read as
YM/Gauge/Colors.lean). Rows whose relation is in --text-relations (default NONE) point into the
TeX and are not looked up in the Lean repository.

Checks (each failure is printed with a tag; any failure gives exit 1):
  NOT-IN-GRAPH / UNUSED  every Lean name exists in the graph table and has used = 1 there (it is in
                         the closure of the main theorem as computed by the graph builder)
  BAD-RELATION           the relation is in the allowed set (put notes in another column)
  NO-LABEL / NO-NAMES    every row has a label; rows whose relation is in --needs-names (default
                         every relation but NONE) list at least one declaration
  NO-PIN / PIN-MISMATCH  a commit is recorded, equals --commit when given (prefix match), and every
                         link in a where cell is pinned at that commit
  LABEL-NOT-IN-TEX       with --tex: every table label is a \\label of the TeX
  NOT-IN-TABLE           with --tex: every label of a numbered statement environment is in the table
                         (--envs auto = environments declared by \\newtheorem; --displays adds
                         labelled equation, align, gather, multline, flalign, eqnarray)
  BAD-LOCATION           with --lean-repo: the commit exists there, each cited file exists at the
                         commit and each cited line is within it (uses git)
  STALE-LOCATION         with --check-graph-locations: each name's path and line in the graph lie in
                         one of the row's where entries (re-pin when either side changes)

Graph database: SQLite, table --table (default nodes) with columns --name-col (name), --used-col
(used), and for --check-graph-locations --path-col (path) and --line-col (line). A name may occur in
several rows; it counts as used if any row has used = 1.

Output: one line per failure, then a summary such as
  "3 rows, 3 name references (2 distinct project names, 1 external); all 2 in the closure; ...".
Exit status: 0 all checks pass, 1 a check failed, 2 usage or input error.
"""
import argparse
import os
import re
import shutil
import sqlite3
import subprocess
import sys
from pathlib import Path

DEFAULT_RELATIONS = "DIRECT,WEAKENING,COMPOSITION,CITED,NONE"
DEFAULT_ENVS = ["theorem", "proposition", "lemma", "corollary", "definition"]
DISPLAY_ENVS = ["equation", "align", "gather", "multline", "flalign", "eqnarray", "alignat"]
COL_ALIASES = {
    "label": ["label", "manuscript label", "tex label"],
    "kind": ["kind", "type"],
    "names": ["lean declarations used=1", "lean declarations", "lean declaration", "lean names", "lean",
              "declarations", "names"],
    "relation": ["relation"],
    "where": ["file:line", "lean file:line", "lean module:line", "module:line", "where", "location", "locations",
              "file_line", "lines"],
}
PLACEHOLDERS = {"-", "\u2013", "\u2014", "n/a", "none", "\u2205"}
COMMENT = re.compile(r"(?<!\\)%.*")
IDENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def die(msg):
    print(f"check_correspondence: {msg}", file=sys.stderr)
    sys.exit(2)


def read_table(path, args):
    try:
        with open(path, encoding="utf-8") as fh:
            lines = fh.read().split("\n")
    except (OSError, UnicodeDecodeError) as e:
        die(f"cannot read {path}: {e}")
    meta, i = {}, 0
    while i < len(lines) and (not lines[i].strip() or lines[i].lstrip().startswith("#")):
        m = re.match(r"^\s*#\s*([A-Za-z][\w .-]*?)\s*[:=]\s*(.+?)\s*$", lines[i])
        if m:
            meta[m.group(1).strip().lower()] = m.group(2)
        i += 1
    if i >= len(lines):
        die(f"{path}: no header row")
    header = [h.strip() for h in lines[i].split("\t")]
    lower = [h.lower() for h in header]
    cols = {}
    for key, aliases in COL_ALIASES.items():
        wanted = getattr(args, f"col_{key}")
        if wanted:
            if wanted.lower() not in lower:
                die(f"{path}: no column {wanted!r} (header: {header})")
            cols[key] = lower.index(wanted.lower())
        else:
            cols[key] = next((lower.index(a) for a in aliases if a in lower), None)
    for key in ("label", "names", "relation"):
        if cols[key] is None:
            die(f"{path}: cannot find the {key} column (header: {header}); use --col-{key}")
    rows = []
    for n in range(i + 1, len(lines)):
        line = lines[n]
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        cells = [c.strip() for c in line.split("\t")]
        rows.append((n + 1, cells))
    return meta, cols, rows


def split_names(cell, sep, external_tags):
    names, external, notes = [], [], []
    for raw in cell.split(sep):
        e = raw.strip().strip("`").strip()
        if not e or e.lower() in PLACEHOLDERS:
            continue
        if e.startswith("(") and e.endswith(")"):
            notes.append(e)
            continue
        m = re.match(r"^(\S+)\s*\(([^()]*)\)\s*$", e)
        if m:
            name, tag = m.group(1).strip("`"), m.group(2).strip()
            if tag.lower() in external_tags:
                external.append(name)
                continue
            e = name
        names.append(e)
    return names, external, notes


def parse_where(cell, sep):
    """Return [(path, first line, last line, commit in a link or None)]; (entry, None, None, None) if unparsable."""
    out = []
    for raw in cell.split(sep):
        e = raw.strip().strip("`<>")
        if not e:
            continue
        link_commit = None
        u = re.match(r"^https?://\S*?/blob/([0-9a-fA-F]{7,40})/(.+)$", e)
        if u:
            link_commit, e = u.group(1).lower(), u.group(2)
        m = re.match(r"^(.+?)#L(\d+)(?:-L(\d+))?$", e) or re.match(r"^(.+?):(\d+)(?:\s*[-\u2013]\s*L?(\d+))?$", e)
        if not m:
            out.append((e, None, None, link_commit))
            continue
        a = int(m.group(2))
        b = int(m.group(3)) if m.group(3) else a
        path = m.group(1)[2:] if m.group(1).startswith("./") else m.group(1)
        if re.fullmatch(r"[A-Z][\w']*(\.[A-Z][\w']*)*", path):
            path = path.replace(".", "/") + ".lean"  # a module name such as YM.Gauge.Colors
        out.append((path, a, b, link_commit))
    return out


def tex_labels(paths, envs_opt, displays):
    """Return (all labels, {label: (env, file:line)} for numbered statements, envs used)."""
    files = []
    for p in paths:
        if os.path.isdir(p):
            for root, dirs, names in os.walk(p):
                dirs.sort()
                files += [os.path.join(root, n) for n in sorted(names) if n.endswith(".tex")]
        elif os.path.isfile(p):
            files.append(p)
        else:
            die(f"no such TeX file or directory: {p}")
    texts = {}
    for f in files:
        try:
            with open(f, encoding="utf-8") as fh:
                texts[f] = "\n".join(COMMENT.sub("", l) for l in fh.read().split("\n"))
        except (OSError, UnicodeDecodeError) as e:
            die(f"cannot read {f}: {e}")
    if envs_opt == "auto":
        declared = set()
        for t in texts.values():
            declared.update(re.findall(r"\\newtheorem\s*\{([A-Za-z@]+)\}", t))
        envs = set(declared) if declared else set(DEFAULT_ENVS)
    else:
        envs = {e.strip() for e in envs_opt.split(",") if e.strip()}
    if displays:
        envs |= set(DISPLAY_ENVS)
    token = re.compile(r"\\(begin|end)\s*\{([A-Za-z@*]+)\}|\\label\s*\{([^}]*)\}")
    all_labels, statement_labels = set(), {}
    for f, t in texts.items():
        stack = []
        for m in token.finditer(t):
            if m.group(1) == "begin":
                stack.append(m.group(2))
            elif m.group(1) == "end":
                if m.group(2) in stack:
                    k = len(stack) - 1 - stack[::-1].index(m.group(2))
                    del stack[k:]
            else:
                lab = m.group(3).strip()
                all_labels.add(lab)
                if stack and stack[-1] in envs and lab not in statement_labels:
                    statement_labels[lab] = (stack[-1], f"{f}:{t.count(chr(10), 0, m.start()) + 1}")
    return all_labels, statement_labels, sorted(envs), len(files)


def lookup_used(db, table, name_col, used_col, used_value, names):
    for ident in (table, name_col, used_col):
        if not IDENT.match(ident):
            die(f"bad SQL identifier {ident!r}")
    try:
        con = sqlite3.connect(Path(db).resolve().as_uri() + "?mode=ro", uri=True)
    except sqlite3.Error as e:
        die(f"cannot open {db}: {e}")
    found = {}
    names = sorted(names)
    try:
        for k in range(0, len(names), 500):
            chunk = names[k:k + 500]
            q = (f'SELECT "{name_col}", MAX(CASE WHEN CAST("{used_col}" AS TEXT) = ? THEN 1 ELSE 0 END) '
                 f'FROM "{table}" WHERE "{name_col}" IN ({",".join("?" * len(chunk))}) GROUP BY "{name_col}"')
            for name, used in con.execute(q, [str(used_value)] + chunk):
                found[name] = bool(used)
    except sqlite3.Error as e:
        die(f"query on {db} failed ({e}); check --table, --name-col, --used-col")
    return con, found


def git_lines(repo, commit, path, cache):
    key = path
    if key not in cache:
        r = subprocess.run(["git", "-C", repo, "show", f"{commit}:{path}"], capture_output=True)
        cache[key] = None if r.returncode != 0 else r.stdout.count(b"\n") + (0 if r.stdout.endswith(b"\n") else 1)
    return cache[key]


def main():
    ap = argparse.ArgumentParser(
        description="Check a correspondence table (statement labels <-> Lean declarations) against a compiled "
                    "dependency graph (SQLite), the TeX labels and the pinned Lean commit.",
        epilog="Example (with the Yang-Mills pin):\n"
               "  check_correspondence.py correspondence.tsv --db graph.sqlite --tex manuscript/ \\\n"
               "      --commit 3456e5e --lean-repo ../OpenAI-YM-20261028",
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("tsv", metavar="TABLE.tsv", help="correspondence table (TSV)")
    ap.add_argument("--db", default=os.environ.get("ENSLOP_GRAPH_DB"),
                    help="SQLite dependency graph (default: $ENSLOP_GRAPH_DB)")
    ap.add_argument("--table", dest="graph_table", default="nodes", help="graph table (default nodes)")
    ap.add_argument("--name-col", default="name", help="declaration-name column (default name)")
    ap.add_argument("--used-col", default="used", help="closure flag column (default used)")
    ap.add_argument("--used-value", default="1", help="value of the closure flag for used declarations (default 1)")
    ap.add_argument("--path-col", default="path", help="source path column, for --check-graph-locations")
    ap.add_argument("--line-col", default="line", help="source line column, for --check-graph-locations")
    ap.add_argument("--tex", action="append", metavar="PATH", help="TeX file or directory to scan for \\label (repeatable)")
    ap.add_argument("--envs", default="auto", help="numbered statement environments: 'auto' (\\newtheorem) or a list")
    ap.add_argument("--displays", action="store_true", help="also require labelled displays in the table")
    ap.add_argument("--exclude-label", metavar="REGEX", help="TeX labels matching REGEX need no row")
    ap.add_argument("--relations", default=DEFAULT_RELATIONS, help=f"allowed relations (default {DEFAULT_RELATIONS})")
    ap.add_argument("--needs-names", default="DIRECT,WEAKENING,COMPOSITION,CITED",
                    help="relations whose rows must name a declaration (default DIRECT,WEAKENING,COMPOSITION,CITED)")
    ap.add_argument("--text-relations", default="NONE",
                    help="relations whose where entries point into the TeX, not the Lean (default NONE); "
                         "they are skipped by --lean-repo")
    ap.add_argument("--external-tags", default="Mathlib,core,Lean,Std,Batteries",
                    help="name tags marking declarations outside the project graph (default Mathlib,core,Lean,Std,Batteries)")
    ap.add_argument("--sep", default=";", help="separator inside the names and where cells (default ';')")
    ap.add_argument("--commit", help="expected pinned commit (prefix match against the table's '# commit:')")
    ap.add_argument("--pin-file", help="file whose first hexadecimal token is the pin, if the table has no '# commit:' line")
    ap.add_argument("--lean-repo", help="git checkout of the Lean source: check cited files and lines at the pin")
    ap.add_argument("--check-graph-locations", action="store_true",
                    help="require each name's graph path and line to lie in one of the row's where entries")
    ap.add_argument("--max-print", type=int, default=200, help="print at most this many failures (default 200)")
    for key in COL_ALIASES:
        ap.add_argument(f"--col-{key}", help=f"exact header of the {key} column")
    args = ap.parse_args()

    if not args.db:
        ap.error("--db is required (or set ENSLOP_GRAPH_DB)")
    if not os.path.isfile(args.db):
        die(f"no such database: {args.db}")
    if not os.path.isfile(args.tsv):
        die(f"no such table: {args.tsv}")
    relations = {r.strip().upper() for r in args.relations.split(",") if r.strip()}
    needs_names = {r.strip().upper() for r in args.needs_names.split(",") if r.strip()}
    text_relations = {r.strip().upper() for r in args.text_relations.split(",") if r.strip()}
    external_tags = {t.strip().lower() for t in args.external_tags.split(",") if t.strip()}
    try:
        exclude = re.compile(args.exclude_label) if args.exclude_label else None
    except re.error as e:
        ap.error(f"bad --exclude-label: {e}")
    if args.lean_repo and not shutil.which("git"):
        die("--lean-repo needs git on the PATH")
    if args.lean_repo and not os.path.isdir(args.lean_repo):
        die(f"no such directory: {args.lean_repo}")

    meta, cols, rows = read_table(args.tsv, args)
    failures = []

    def fail(msg):
        failures.append(msg)

    # pin
    pin = meta.get("commit") or meta.get("pin") or meta.get("pinned commit")
    if not pin and args.pin_file:
        try:
            with open(args.pin_file, encoding="utf-8") as fh:
                m = re.search(r"\b[0-9a-fA-F]{7,40}\b", fh.read())
            pin = m.group(0) if m else None
        except OSError as e:
            die(f"cannot read {args.pin_file}: {e}")
    if not pin or not re.fullmatch(r"[0-9a-fA-F]{7,40}", pin.strip()):
        fail("NO-PIN the table records no pinned commit (add '# commit: <full hash>' above the header)")
        pin = None
    else:
        pin = pin.strip().lower()
        if args.commit and not (pin.startswith(args.commit.lower()) or args.commit.lower().startswith(pin)):
            fail(f"PIN-MISMATCH the table is pinned at {pin}, expected {args.commit}")

    # rows
    def cell(cells, key):
        c = cols.get(key)
        return cells[c] if c is not None and c < len(cells) else ""

    all_names, all_external, table_labels, row_names = set(), set(), {}, []
    references = 0
    for lineno, cells in rows:
        label = cell(cells, "label")
        relation = cell(cells, "relation").upper()
        names, external, _ = split_names(cell(cells, "names"), args.sep, external_tags)
        where = parse_where(cell(cells, "where"), args.sep) if cols.get("where") is not None else []
        if not label:
            fail(f"NO-LABEL line {lineno}")
        table_labels.setdefault(label, lineno)
        if relation not in relations:
            fail(f"BAD-RELATION {relation or '(empty)'!r} for {label} (line {lineno})")
        if relation in needs_names and not names and not external:
            fail(f"NO-NAMES {label} (line {lineno}) has relation {relation} but names no declaration")
        all_names.update(names)
        all_external.update(external)
        references += len(names) + len(external)
        row_names.append((lineno, label, names, where if relation not in text_relations else []))

    con, found = lookup_used(args.db, args.graph_table, args.name_col, args.used_col, args.used_value, all_names)
    missing = sorted(n for n in all_names if n not in found)
    unused = sorted(n for n in all_names if n in found and not found[n])
    first_use = {}
    for lineno, label, names, _ in row_names:
        for n in names:
            first_use.setdefault(n, (label, lineno))
    for n in missing:
        fail(f"NOT-IN-GRAPH {n} ({first_use[n][0]}, line {first_use[n][1]})")
    for n in unused:
        fail(f"UNUSED {n} ({first_use[n][0]}, line {first_use[n][1]}): not in the closure (used != {args.used_value})")

    # graph locations
    if args.check_graph_locations:
        for ident in (args.path_col, args.line_col):
            if not IDENT.match(ident):
                die(f"bad SQL identifier {ident!r}")
        locs = {}
        try:
            names = sorted(all_names)
            for k in range(0, len(names), 500):
                chunk = names[k:k + 500]
                q = (f'SELECT "{args.name_col}", "{args.path_col}", "{args.line_col}" FROM "{args.graph_table}" '
                     f'WHERE "{args.name_col}" IN ({",".join("?" * len(chunk))})')
                for name, path, line in con.execute(q, chunk):
                    locs.setdefault(name, []).append((path, line))
        except sqlite3.Error as e:
            die(f"location query failed ({e}); check --path-col and --line-col")
        for lineno, label, names, where in row_names:
            for n in names:
                ok_any = False
                for path, line in locs.get(n, []):
                    try:
                        line = int(line)
                    except (TypeError, ValueError):
                        continue
                    if any(p == path and a is not None and a <= line <= b for p, a, b, _ in where):
                        ok_any = True
                if locs.get(n) and not ok_any:
                    gp, gl = locs[n][0]
                    fail(f"STALE-LOCATION {n} ({label}, line {lineno}): the graph has {gp}:{gl}, "
                         f"not in the row's where entries")
    con.close()

    # links pinned to another commit
    if pin:
        for lineno, label, _, where in row_names:
            for path, a, b, link_commit in where:
                if link_commit and not (link_commit.startswith(pin) or pin.startswith(link_commit)):
                    fail(f"PIN-MISMATCH link to {path} ({label}, line {lineno}) is pinned at {link_commit[:12]}, "
                         f"the table at {pin[:12]}")

    # Lean repository at the pin
    if args.lean_repo:
        if not pin:
            fail("BAD-LOCATION cannot check files and lines without a pinned commit")
        else:
            r = subprocess.run(["git", "-C", args.lean_repo, "cat-file", "-e", f"{pin}^{{commit}}"], capture_output=True)
            if r.returncode != 0:
                fail(f"BAD-LOCATION commit {pin} is not in {args.lean_repo}")
            else:
                cache = {}
                for lineno, label, _, where in row_names:
                    for path, a, b, _ in where:
                        if a is None:
                            fail(f"BAD-LOCATION {path!r} ({label}, line {lineno}) is not file:line")
                            continue
                        n = git_lines(args.lean_repo, pin, path, cache)
                        if n is None:
                            fail(f"BAD-LOCATION {path} ({label}, line {lineno}) does not exist at {pin[:12]}")
                        elif a < 1 or b > n or a > b:
                            fail(f"BAD-LOCATION {path}:{a}-{b} ({label}, line {lineno}) outside the file ({n} lines)")

    # TeX labels
    covered = None
    if args.tex:
        all_labels, statement_labels, envs, nfiles = tex_labels(args.tex, args.envs, args.displays)
        for label, lineno in sorted(table_labels.items(), key=lambda x: x[1]):
            if label and label not in all_labels:
                fail(f"LABEL-NOT-IN-TEX {label} (line {lineno})")
        needed = {k: v for k, v in statement_labels.items() if not (exclude and exclude.search(k))}
        for label, (env, where) in sorted(needed.items(), key=lambda x: x[1][1]):
            if label not in table_labels:
                fail(f"NOT-IN-TABLE {label} ({env}, {where})")
        covered = (len([k for k in needed if k in table_labels]), len(needed), envs, nfiles)

    for f in failures[:args.max_print]:
        print(f)
    if len(failures) > args.max_print:
        print(f"... and {len(failures) - args.max_print} more")
    bad_names = len(missing) + len(unused)
    parts = [f"{len(rows)} rows, {references} name references ({len(all_names)} distinct project names, "
             f"{len(all_external)} external)"]
    parts.append(f"all {len(all_names)} in the closure" if not bad_names else
                 f"{len(missing)} not in the graph, {len(unused)} not in the closure")
    if covered:
        parts.append(f"{covered[0]} of {covered[1]} statement labels covered ({', '.join(covered[2])}; {covered[3]} TeX files)")
    else:
        parts.append("TeX not checked")
    parts.append(f"pin {pin[:12]}" if pin else "no pin")
    print("check_correspondence: " + "; ".join(parts) + f"; {len(failures)} failure(s) -> " + ("FAILED" if failures else "ok"))
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
