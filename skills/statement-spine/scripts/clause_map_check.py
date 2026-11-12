#!/usr/bin/env python3
"""Check a clause map: every frozen clause has a destination, and every destination exists.

Usage:
  clause_map_check.py --map CLAUSE-MAP.md --spine SPINE.md --labels-from SPINE-NATURAL.md part1/*.tex
  clause_map_check.py --map clause-map.tsv --clauses clause-ids.txt --labels-from main.tex
  clause_map_check.py --rows-only --map CLAUSE-MAP.tsv

The clause map is one or more tables, in Markdown (rows "| a | b | c |") or TSV with a header
row. A table counts as a clause map when its header has a clause-id column (header matching
--id-col, default "clause") and a destination column (--dest-col, default "destination"); a scope
column (--scope-col, default "scope") and a note column (--note-col, default "note") are optional.
Other tables in the file are ignored.
  clause-id cell     one or more frozen clause ids separated by "," ";" or " / " and nothing else
                     (backticks and bold markers are stripped); describe the clause in the scope
                     column, not here
  destination cell   one or more destinations separated by "," or ";"; each starts with a label
                     (backticks, \\ref{...} and \\cref{...} wrappers are stripped); any text after the
                     label is a comment, e.g. "lem:energy (hypothesis on s)"; "a--b" checks both ends

Frozen clause ids come from --clauses (one id per line, "#" comments) or from tags in the frozen
spine (--spine), found by --clause-regex (default: tags written "[clause:ID]").
Existing destinations come from the files given to --labels-from (\\label{...}, pandoc heading
ids {#...}, HTML ids id="...", the first token and the full text of every Markdown heading), from
--labels (one per line), and from --allow-dest regexes (e.g. "^prose:").

Problems reported (one per line: KIND, item, where):
  unmapped            a frozen clause with no row, or only rows with an empty destination
  missing-destination a destination that is not an existing label
  duplicate-no-note   a clause in more than one row, none of which has a note
  unknown-clause      a clause id in the map that is not a frozen clause id
  not-used            with --used-names: a backticked dotted Lean name anywhere in the map files
                      (other than a clause id or a label) that is not in the list of declarations
                      used by the main theorem
--rows-only checks only that the map has at least one row whose clause cell holds an id (a template
placeholder such as <ID> does not count), and says where the map must be when it has none; it needs
neither --clauses nor --spine. Rollout configs run it before every review that reads the map.
Exit status: 0 no problem, 1 problems (with --rows-only: no row), 2 usage or input error.
"""
import argparse
import json
import re
import sys

ID_SPLIT = re.compile(r"\s*(?:,|;|\s/\s)\s*")
DEST_SPLIT = re.compile(r"\s*[,;]\s*")
RANGE = re.compile(r"\s*(?:--|\u2013)\s*")
PLACEHOLDER = re.compile(r"<[^<>]*>")
WHERE = ("The clause map must be in one of two places: a TSV file with the header of statement-spine's "
         "assets/clause-map-header.tsv (spine/CLAUSE-MAP.tsv of the working tree), or the table of section 6 "
         "(\"Clause map\") of the natural spine SPINE-NATURAL.md, with the columns clause and destination. Fill "
         "one of them with a row per clause id of SPINE.md, and point --map (in a rollout config, the variable "
         "clause_map) at the file that holds the rows.")
WRAP = re.compile(r"\\(?:c?ref|Cref|eqref|autoref)\{([^{}]*)\}")


def read_text(path):
    with open(path, encoding="utf-8", errors="replace") as fh:
        return fh.read()


def split_row(line):
    """Split a Markdown table row on |, ignoring | inside $...$, `...` and after a backslash."""
    s = line.strip()
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|") and not s.endswith("\\|"):
        s = s[:-1]
    cells, cur, math, code, i = [], [], False, False, 0
    while i < len(s):
        c = s[i]
        if c == "\\" and i + 1 < len(s):
            cur.append(s[i:i + 2])
            i += 2
            continue
        if c == "`" and not math:
            code = not code
        elif c == "$" and not code:
            math = not math
        elif c == "|" and not math and not code:
            cells.append("".join(cur).strip())
            cur = []
            i += 1
            continue
        cur.append(c)
        i += 1
    cells.append("".join(cur).strip())
    return cells


def find_cols(header, args):
    def col(rx):
        if not rx:
            return None
        for k, h in enumerate(header):
            if re.search(rx, h, re.I):
                return k
        return None
    return {"id": col(args.id_col), "dest": col(args.dest_col), "scope": col(args.scope_col), "note": col(args.note_col)}


def read_tables(path, args):
    """Return (rows, tables_used, tables_ignored); each row: dict with ids, dests, scope, note, where."""
    lines = read_text(path).splitlines()
    fmt = args.format or ("tsv" if path.endswith((".tsv", ".tab")) else "md")
    blocks = []
    if fmt == "tsv":
        body = [(n, ln) for n, ln in enumerate(lines, 1) if ln.strip() and not ln.lstrip().startswith("#")]
        if body:
            blocks.append([(n, ln.split("\t")) for n, ln in body])
    else:
        cur = []
        for n, ln in enumerate(lines, 1):
            if ln.lstrip().startswith("|"):
                cur.append((n, split_row(ln)))
            elif cur:
                blocks.append(cur)
                cur = []
        if cur:
            blocks.append(cur)
    rows, used, ignored = [], 0, 0
    for block in blocks:
        header = block[0][1]
        cols = find_cols(header, args)
        if cols["id"] is None or cols["dest"] is None:
            ignored += 1
            continue
        used += 1
        for n, cells in block[1:]:
            if all(re.fullmatch(r":?-{2,}:?", c.strip()) for c in cells if c.strip()):
                continue  # separator row
            if [c.strip() for c in cells] == [h.strip() for h in header]:
                continue  # repeated header

            def cell(k):
                return cells[k].strip() if k is not None and k < len(cells) else ""
            ids = [x.strip("`*[] ") for x in ID_SPLIT.split(cell(cols["id"])) if x.strip("`*[] ")]
            rows.append({"ids": ids, "dest": cell(cols["dest"]), "scope": cell(cols["scope"]),
                         "note": cell(cols["note"]), "where": f"{path}:{n}"})
    return rows, used, ignored


def destinations(text):
    out = []
    for item in DEST_SPLIT.split(WRAP.sub(r"\1", text)):
        item = item.strip().strip("`*")
        if not item:
            continue
        first = item.split()[0].strip("`*()[]")
        out.extend(p.strip("`*()[].") for p in RANGE.split(first) if p.strip("`*()[]."))
    return out


def known_labels(files, label_files):
    labels = set()
    for f in files:
        text = read_text(f)
        labels.update(re.findall(r"\\label\{([^{}]+)\}", text))
        labels.update(re.findall(r"\{#([^\s{}]+)[^{}]*\}", text))
        labels.update(re.findall(r"""\bid=["']([^"']+)["']""", text))
        for m in re.finditer(r"^#{1,6}\s+(.+?)\s*(?:\{#[^}]*\})?\s*#*\s*$", text, re.M):
            heading = m.group(1).strip()
            labels.add(heading)
            labels.add(heading.split()[0].rstrip(".:"))
    for f in label_files:
        for ln in read_text(f).splitlines():
            if ln.strip() and not ln.lstrip().startswith("#"):
                labels.add(ln.split()[0])
    return labels


def frozen_ids(args):
    ids = []
    if args.clauses:
        for ln in read_text(args.clauses).splitlines():
            if ln.strip() and not ln.lstrip().startswith("#"):
                ids.append(ln.split()[0])
    if args.spine:
        rx = re.compile(args.clause_regex)
        text = read_text(args.spine)
        for m in rx.finditer(text):
            ids.append(m.group(1) if rx.groups else m.group(0))
    seen, out = set(), []
    for i in ids:
        if i not in seen:
            seen.add(i)
            out.append(i)
    return out


def rows_only(args):
    """--rows-only: exit 1 unless the map files hold at least one row with a real clause id."""
    rows, used, ignored = [], 0, 0
    try:
        for m in args.map:
            r, u, i = read_tables(m, args)
            rows += r
            used += u
            ignored += i
    except OSError as exc:
        print(f"clause_map_check: input error: {exc}", file=sys.stderr)
        return 2
    data = [r for r in rows if any(not PLACEHOLDER.fullmatch(i) for i in r["ids"])]
    files = ", ".join(args.map)
    if not data:
        print(f"NO ROWS\t{files}: no clause-map row with a clause id. {WHERE}")
    print(f"clause map: {len(data)} row(s) with a clause id in {used} table(s) of {files} "
          f"({ignored} other table(s) ignored) -> {'ok' if data else 'NO ROWS'}")
    return 0 if data else 1


def main():
    ap = argparse.ArgumentParser(
        description="Check that every frozen clause is mapped to an existing destination, that no "
                    "clause is mapped twice without a note, and (optionally) that every Lean name "
                    "cited in the map is used by the main theorem. Exit 1 on any problem.",
        epilog="""examples:
  clause_map_check.py --map SPINE-NATURAL.md --spine SPINE.md --labels-from SPINE-NATURAL.md
  clause_map_check.py --map clause-map.tsv --clauses ids.txt --labels-from main.tex part1/*.tex \\
      --used-names used.txt
  clause_map_check.py --rows-only --map spine/CLAUSE-MAP.tsv     (a rollout build step)
  (used.txt from the dependency database, e.g.
   sqlite3 graph.sqlite "select name from nodes where used=1" > used.txt)
See the module docstring for the table format.""",
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--map", action="append", required=True, help="clause map file (Markdown or TSV; repeatable)")
    ap.add_argument("--format", choices=["md", "tsv"], help="force the map format (default: by extension)")
    ap.add_argument("--clauses", help="file of frozen clause ids, one per line")
    ap.add_argument("--spine", help="frozen spine whose tags give the clause ids")
    ap.add_argument("--clause-regex", default=r"\[clause:\s*([^\]\s]+)\s*\]",
                    help="regex finding clause ids in --spine; group 1 is the id (default: [clause:ID])")
    ap.add_argument("--labels-from", nargs="+", default=[], metavar="FILE",
                    help="TeX or Markdown files whose labels and headings are valid destinations")
    ap.add_argument("--labels", action="append", default=[], metavar="FILE", help="file of extra labels, one per line")
    ap.add_argument("--allow-dest", action="append", default=[], metavar="REGEX",
                    help="destinations matching REGEX are accepted without a label (repeatable)")
    ap.add_argument("--used-names", help="file of declarations used by the main theorem (one per line)")
    ap.add_argument("--lean-name-regex", default=r"`([A-Za-z_][\w']*(?:\.[A-Za-z_][\w']*)+)`",
                    help="regex for Lean names checked against --used-names (group 1 is the name)")
    ap.add_argument("--id-col", default="clause", help="regex for the clause-id column header")
    ap.add_argument("--dest-col", default="destination", help="regex for the destination column header")
    ap.add_argument("--scope-col", default="scope", help="regex for the scope column header")
    ap.add_argument("--note-col", default="note", help="regex for the note column header")
    ap.add_argument("--json", action="store_true", help="print JSON")
    ap.add_argument("--rows-only", action="store_true",
                    help="only check that the map has a row with a clause id (placeholders such as <ID> do not "
                         "count); exit 1 if it has none")
    args = ap.parse_args()
    if args.rows_only:
        return rows_only(args)
    if not (args.clauses or args.spine):
        ap.error("give --clauses or --spine (or --rows-only)")

    try:
        frozen = frozen_ids(args)
        labels = known_labels(args.labels_from, args.labels)
        allow = [re.compile(r) for r in args.allow_dest]
        rows, used_tables, ignored_tables = [], 0, 0
        for m in args.map:
            r, u, i = read_tables(m, args)
            rows += r
            used_tables += u
            ignored_tables += i
        used_names = None
        if args.used_names:
            used_names = {ln.strip() for ln in read_text(args.used_names).splitlines() if ln.strip()}
        name_rx = re.compile(args.lean_name_regex)
    except (OSError, re.error) as exc:
        print(f"clause_map_check: input error: {exc}", file=sys.stderr)
        return 2
    if not frozen:
        print("clause_map_check: input error: no frozen clause ids found", file=sys.stderr)
        return 2
    if not rows:
        print("clause_map_check: input error: no clause-map rows found (check the column headers)", file=sys.stderr)
        return 2

    problems = []
    frozen_set = set(frozen)
    by_id = {}
    for row in rows:
        for cid in row["ids"]:
            by_id.setdefault(cid, []).append(row)
            if cid not in frozen_set:
                problems.append(("unknown-clause", cid, row["where"]))
        for d in destinations(row["dest"]):
            if d not in labels and not any(a.search(d) for a in allow):
                problems.append(("missing-destination", d, row["where"]))
    for cid in frozen:
        mapped = [r for r in by_id.get(cid, []) if destinations(r["dest"])]
        if not mapped:
            problems.append(("unmapped", cid, by_id[cid][0]["where"] if cid in by_id else "-"))
        elif len(by_id[cid]) > 1 and not any(r["note"] for r in by_id[cid]):
            problems.append(("duplicate-no-note", cid, ", ".join(r["where"] for r in by_id[cid])))
    if used_names is not None:
        for m in args.map:
            for n, ln in enumerate(read_text(m).splitlines(), 1):
                for mm in name_rx.finditer(ln):
                    name = mm.group(1) if name_rx.groups else mm.group(0)
                    if name not in used_names and name not in frozen_set and name not in labels:
                        problems.append(("not-used", name, f"{m}:{n}"))

    kinds = ["unmapped", "missing-destination", "duplicate-no-note", "unknown-clause", "not-used"]
    counts = {k: sum(1 for p in problems if p[0] == k) for k in kinds}
    summary = (f"clause map: {len(frozen)} frozen clauses, {len(rows)} rows in {used_tables} table(s) "
               f"({ignored_tables} other table(s) ignored); "
               + ", ".join(f"{counts[k]} {k}" for k in kinds if k != "not-used" or used_names is not None))
    if args.json:
        print(json.dumps({"problems": [dict(zip(("kind", "item", "where"), p)) for p in problems],
                          "counts": counts, "summary": summary}, indent=1))
    else:
        for p in problems:
            print("\t".join(p))
        print(summary)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
