#!/usr/bin/env python3
"""Summarize adjudications of referee reports written as Markdown verdict tables.

Usage:
  adjudication_summary.py [NAME=]ADJUDICATION.md [...]
                          [--expect N | --expect NAME=N ...] [--part counts|author|writers|all]
                          [--tsv FILE] [--strict]

Every Markdown table with a column whose header contains "verdict" is read. One row is one
adjudicated suggestion (or several, e.g. "20g, 20h" or "5-7"). The other columns are found by
header: the item column ("#", "item", "suggestion", "no", "id"), the reason column ("reason",
"why") and the location column ("where", "location", "file", "edit"); override them with
--col-item, --col-reason, --col-where (exact header text, case-insensitive). Escaped pipes
"\\|" inside cells are kept as text.

Verdicts: ACCEPT, ACCEPT MODIFIED, REJECT, AUTHOR (common variants such as "accepted" are
normalized; anything else is reported as a problem). Text in parentheses is kept as a note, e.g.
"ACCEPT (flag: inside the main theorem)". A split cell such as "ACCEPT MODIFIED (a-c); REJECT (d)"
or "ACCEPT MODIFIED; AUTHOR (deleting Lemma 9.2)" gives one item per part ("8[a-c]", "8[d]"), so
the AUTHOR part reaches the morning list. A non-AUTHOR item whose note mentions the author or
the lead ("ACCEPT MODIFIED (final wording: author)") is reported as a warning.

Output (Markdown, to stdout):
  counts   one row per report and a total row. A report is named NAME if given, else after its file
           (without extension), else, when files share a name (rollout.py writes every one as
           <unit>/adjudicate/adjudication.md), after the first parent directory that differs: the unit;
  author   the AUTHOR items with their reasons, ready for the morning list, each with the
           provisional default "not applied";
  writers  the ACCEPT and ACCEPT MODIFIED items grouped by the first token of each location
           (e.g. "03:218" -> "03", "main.tex:52" -> "main.tex"), for the section writers.
A last line "adjudication_summary: ..." summarizes.

Checks (exit 1 when one fails): a file without any verdict table; a verdict that is not one of
the four; one item given two different verdicts; and, with --expect, any suggestion number
1..N without a verdict. --strict also fails a file whose "Lean facts" heading is missing or
comes after its first verdict table.

Exit status: 0 ok, 1 check failed, 2 usage or input error.
"""
import argparse
import collections
import csv
import os
import re
import sys

VERDICTS = ["ACCEPT", "ACCEPT MODIFIED", "REJECT", "AUTHOR"]
ITEM_HEADERS = {"#", "item", "items", "suggestion", "suggestions", "no", "no.", "nr", "n", "id", "number"}
SEPARATOR = re.compile(r"^\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)*\|?\s*$")
UNESCAPED_PIPE = re.compile(r"(?<!\\)\|")
LEAN_FACTS = re.compile(r"^\s*#{1,6}\s*\**\s*Lean facts", re.IGNORECASE)
ITEM_ID = re.compile(r"^(\d+)\s*(?:\(?([a-z]{1,2})\)?)?$")
RANGE = re.compile(r"^(\d+)\s*[-–—]\s*(\d+)$")


def norm_header(cell):
    return re.sub(r"\s+", " ", cell.replace("*", "").replace("`", "").replace("_", " ")).strip().lower()


def split_row(line):
    s = line.strip()
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|") and not s.endswith("\\|"):
        s = s[:-1]
    return [c.strip().replace("\\|", "|") for c in UNESCAPED_PIPE.split(s)]


def normalize_verdict(text):
    v = re.sub(r"[*_`]", "", text).upper()
    v = re.sub(r"[()\[\]:.,;-]", " ", v)
    v = re.sub(r"\s+", " ", v).strip()
    if v.startswith(("ACCEPT MODIFIED", "ACCEPTED MODIFIED", "ACCEPT WITH MODIFICATION", "ACCEPT AS MODIFIED",
                     "MODIFIED")):
        return "ACCEPT MODIFIED"
    if v.startswith("ACCEPT"):
        return "ACCEPT"
    if v.startswith("REJECT"):
        return "REJECT"
    if v.startswith(("AUTHOR", "PROJECT LEAD", "LEAD")):
        return "AUTHOR"
    return None


def parse_verdicts(cell):
    """Split a verdict cell into [(verdict, qualifier)], e.g. 'ACCEPT MODIFIED (a-c); REJECT (d)'.

    Text in parentheses is a qualifier, never a verdict. Returns [] if no part has a verdict."""
    parts = []
    for seg in cell.split(";"):
        qualifier = "; ".join(q.strip() for q in re.findall(r"\(([^()]*)\)", seg) if q.strip())
        core = re.sub(r"\([^()]*\)", " ", seg)
        verdict = normalize_verdict(core)
        if verdict:
            parts.append((verdict, qualifier))
    return parts


def parse_items(cell):
    """Return a list of (item_id, number or None) from an item cell such as '13a', '20g, 20h', '5-7'."""
    raw = re.sub(r"[*`#]", "", cell).strip()
    raw = re.sub(r"\s*\((?:[^)]*\s[^)]*)\)\s*$", "", raw)  # drop a trailing note like "(both parts)"
    out = []
    pieces = [p.strip() for p in re.split(r"[,;/]|\band\b", raw) if p.strip()]
    last_number = None
    for p in pieces:
        m = RANGE.match(p)
        if m:
            a, b = int(m.group(1)), int(m.group(2))
            if a <= b and b - a < 200:
                out.extend((str(k), k) for k in range(a, b + 1))
                last_number = b
                continue
        m = ITEM_ID.match(p.lower())
        if m:
            n = int(m.group(1))
            out.append((f"{n}{m.group(2) or ''}", n))
            last_number = n
            continue
        if re.fullmatch(r"\(?[a-z]{1,2}\)?", p.lower()) and last_number is not None:
            out.append((f"{last_number}{p.strip('()').lower()}", last_number))  # "20g, h"
            continue
        out.append((p, None))
    return out


def find_col(headers, wanted, contains):
    if wanted:
        for i, h in enumerate(headers):
            if h == wanted.lower():
                return i
        return None
    for i, h in enumerate(headers):
        if any(c in h for c in contains):
            return i
    return None


def parse_file(path, report, args):
    """Return (records, problems, warnings, lean_facts_ok) for one adjudication named report."""
    try:
        with open(path, encoding="utf-8") as fh:
            lines = fh.read().splitlines()
    except OSError as e:
        print(f"adjudication_summary: cannot read {path}: {e}", file=sys.stderr)
        sys.exit(2)
    records, problems, warnings = [], [], []
    lean_facts_line = next((i for i, l in enumerate(lines) if LEAN_FACTS.match(l)), None)
    first_table_line = None
    i = 0
    while i < len(lines) - 1:
        if lines[i].lstrip().startswith("|") and SEPARATOR.match(lines[i + 1]):
            headers = [norm_header(c) for c in split_row(lines[i])]
            v_col = find_col(headers, args.col_verdict, ["verdict"])
            j = i + 2
            body = []
            while j < len(lines) and lines[j].lstrip().startswith("|"):
                body.append((j + 1, split_row(lines[j])))
                j += 1
            if v_col is not None:
                if first_table_line is None:
                    first_table_line = i
                item_col = None
                if args.col_item:
                    item_col = find_col(headers, args.col_item, [])
                else:
                    for k, h in enumerate(headers):
                        if h in ITEM_HEADERS or "suggestion" in h or h.startswith("item"):
                            item_col = k
                            break
                    if item_col is None and v_col != 0:
                        item_col = 0
                r_col = find_col(headers, args.col_reason, ["reason", "why", "justification", "comment"])
                w_col = find_col(headers, args.col_where, ["where", "location", "file", "edit"])
                if item_col is None:
                    problems.append(f"{path}:{i + 1}: verdict table without an item column")
                for lineno, cells in body:
                    def cell(c):
                        return cells[c] if c is not None and c < len(cells) else ""
                    verdicts = parse_verdicts(cell(v_col))
                    if not verdicts:
                        problems.append(f"{path}:{lineno}: unknown verdict {cell(v_col)!r}")
                        continue
                    for item_id, number in parse_items(cell(item_col)):
                        if number is None:
                            warnings.append(f"{path}:{lineno}: item {item_id!r} has no suggestion number")
                        for k, (verdict, qualifier) in enumerate(verdicts):
                            # a split verdict ("ACCEPT MODIFIED (a-c); REJECT (d)") gives one record per part
                            iid = item_id if len(verdicts) == 1 else f"{item_id}[{qualifier or k + 1}]"
                            records.append({"report": report, "item": iid, "number": number, "verdict": verdict,
                                            "note": qualifier if len(verdicts) == 1 else "",
                                            "reason": cell(r_col), "where": cell(w_col), "line": lineno,
                                            "file": path})
            i = j
            continue
        i += 1
    if first_table_line is None:
        problems.append(f"{path}: no verdict table found")
    lean_facts_ok = lean_facts_line is not None and (first_table_line is None or lean_facts_line < first_table_line)
    if not lean_facts_ok:
        msg = f"{path}: no 'Lean facts' heading before the first verdict table"
        (problems if args.strict else warnings).append(msg)
    return records, problems, warnings, lean_facts_ok


def item_sort_key(rec):
    n = rec["number"] if rec["number"] is not None else 10 ** 9
    return (rec["report"], n, rec["item"])


def report_names(entries):
    """[(name or None, path)] -> [(name, path)]. A missing name is the file name without extension; when two
    files share it (rollout.py saves every adjudication as <unit>/<stage>/adjudication.md), the first parent
    directory that tells them apart is used instead (the unit key)."""
    stems = [os.path.splitext(os.path.basename(p))[0] for _, p in entries]
    out = []
    for (name, path), stem in zip(entries, stems):
        if name:
            out.append((name, path))
            continue
        if stems.count(stem) == 1:
            out.append((stem, path))
            continue
        same = [p for (n, p), s in zip(entries, stems) if s == stem and not n]
        parts = [os.path.abspath(p).split(os.sep)[:-1] for p in same]
        mine = os.path.abspath(path).split(os.sep)[:-1]
        chosen = stem
        for depth in range(1, min(len(x) for x in parts) + 1):
            names = [x[-depth] for x in parts]
            if len(set(names)) == len(names):
                chosen = mine[-depth]
                break
        out.append((chosen, path))
    return out


def location_groups(where, regex):
    pieces = [p.strip() for p in re.split(r"[;,]", where) if p.strip() and p.strip() not in {"-", "—", "–"}]
    groups = []
    for p in pieces:
        if re.fullmatch(r"[\d.\-–\s]+", p) or p.startswith(":"):
            continue  # "H:81,86,95" or "E:84, :87": a bare line number continues the previous file
        m = regex.search(p)
        g = m.group(1) if m else None
        if g and g not in groups:
            groups.append(g)
    return groups or ["(no location given)"]


def main():
    ap = argparse.ArgumentParser(
        description="Count and list the verdicts of referee adjudications (Markdown verdict tables): "
                    "counts per verdict and report, AUTHOR items for the morning list, accepted items "
                    "by location for the writers.",
        epilog="Example: adjudication_summary.py adjudication/part1.md adjudication/uv.md "
               "--expect part1=12 --expect uv=15 --part all --tsv verdicts.tsv",
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("files", nargs="+", metavar="[NAME=]FILE",
                    help="adjudication reports (Markdown); NAME defaults to the file name without extension, or to "
                         "the first parent directory that tells same-named files apart")
    ap.add_argument("--expect", action="append", default=[], metavar="[NAME=]N",
                    help="number of suggestions in the referee report; NAME is the adjudication file name "
                         "without extension; without NAME it applies to every file")
    ap.add_argument("--part", choices=["counts", "author", "writers", "all"], default="all",
                    help="which part of the summary to print (default: all)")
    ap.add_argument("--tsv", metavar="FILE", help="also write every parsed item as TSV "
                    "(report, item, number, verdict, note, reason, where, file, line)")
    ap.add_argument("--strict", action="store_true",
                    help="fail when the 'Lean facts' heading is missing or comes after the verdict table")
    ap.add_argument("--group-regex", default=r"([A-Za-z0-9_.\-/]+)",
                    help="regex whose first group names the writer group of a location piece "
                         "(default: the first word-like token)")
    ap.add_argument("--col-item", help="exact header of the item column")
    ap.add_argument("--col-verdict", help="exact header of the verdict column")
    ap.add_argument("--col-reason", help="exact header of the reason column")
    ap.add_argument("--col-where", help="exact header of the location column")
    args = ap.parse_args()

    try:
        group_re = re.compile(args.group_regex)
    except re.error as e:
        ap.error(f"bad --group-regex: {e}")
    expect_all, expect = None, {}
    for e in args.expect:
        name, _, n = e.rpartition("=")
        if not n.isdigit() or int(n) < 1:
            ap.error(f"bad --expect value {e!r}")
        if name:
            expect[name] = int(n)
        else:
            expect_all = int(n)
    entries = []
    for f in args.files:
        m = re.match(r"^([A-Za-z0-9_.-]+)=(.+)$", f)
        name, path = (m.group(1), m.group(2)) if m and not os.path.isfile(f) else (None, f)
        if not os.path.isfile(path):
            print(f"adjudication_summary: no such file: {path}", file=sys.stderr)
            sys.exit(2)
        entries.append((name, path))
    named = report_names(entries)
    if len({n for n, _ in named}) != len(named):
        ap.error("two files get the same report name; give names as NAME=FILE")

    records, problems, warnings, reports = [], [], [], []
    for name, path in named:
        r, p, w, _ = parse_file(path, name, args)
        records += r
        problems += p
        warnings += w
        reports.append(name)
    unknown = set(expect) - set(reports)
    if unknown:
        ap.error("--expect names no given file: " + ", ".join(sorted(unknown)))

    # conflicting verdicts for one item
    seen = {}
    for rec in records:
        key = (rec["report"], rec["item"])
        if key in seen and seen[key]["verdict"] != rec["verdict"]:
            problems.append(f"{rec['file']}:{rec['line']}: item {rec['item']} has two verdicts "
                            f"({seen[key]['verdict']}, {rec['verdict']})")
        seen.setdefault(key, rec)
    unique = list(seen.values())
    for rec in unique:
        if rec["verdict"] != "AUTHOR" and re.search(r"\b(author|lead)\b", rec["note"], re.IGNORECASE):
            warnings.append(f"{rec['file']}:{rec['line']}: item {rec['item']} ({rec['verdict']}) has the note "
                            f"{rec['note']!r}; check whether part of it belongs on the morning list")

    coverage = {}
    for rep in reports:
        n = expect.get(rep, expect_all)
        numbers = {r["number"] for r in unique if r["report"] == rep and r["number"] is not None}
        if n is None:
            coverage[rep] = ""
            continue
        missing = [k for k in range(1, n + 1) if k not in numbers]
        extra = sorted(k for k in numbers if k > n)
        if missing:
            problems.append(f"{rep}: suggestion(s) without a verdict: " + ", ".join(map(str, missing)))
        if extra:
            warnings.append(f"{rep}: verdicts for numbers above the expected {n}: " + ", ".join(map(str, extra)))
        coverage[rep] = f"{n - len(missing)} of {n}"

    counts = collections.OrderedDict((rep, collections.Counter()) for rep in reports)
    for r in unique:
        counts[r["report"]][r["verdict"]] += 1
    total = collections.Counter()
    for c in counts.values():
        total.update(c)

    out = []
    if args.part in ("counts", "all"):
        out.append("## Verdicts per report\n")
        out.append("| report | items | " + " | ".join(VERDICTS) + " | numbers covered |")
        out.append("|---|---:|" + "---:|" * len(VERDICTS) + "---|")
        for rep, c in counts.items():
            out.append(f"| {rep} | {sum(c.values())} | " + " | ".join(str(c[v]) for v in VERDICTS)
                       + f" | {coverage.get(rep, '')} |")
        out.append(f"| **total** | {sum(total.values())} | " + " | ".join(str(total[v]) for v in VERDICTS) + " | |")
        out.append("")
    if args.part in ("author", "all"):
        out.append("## AUTHOR items (for the morning list)\n")
        items = sorted((r for r in unique if r["verdict"] == "AUTHOR"), key=item_sort_key)
        if not items:
            out.append("None.")
        for r in items:
            reason = r["reason"] or "(no reason given)"
            note = f" ({r['note']})" if r["note"] else ""
            out.append(f"- **{r['report']} {r['item']}**{note}: {reason} Provisional default: not applied.")
        out.append("")
    if args.part in ("writers", "all"):
        out.append("## Accepted items by location (for the writers)\n")
        groups = collections.OrderedDict()
        for r in sorted((r for r in unique if r["verdict"] in ("ACCEPT", "ACCEPT MODIFIED")), key=item_sort_key):
            for g in location_groups(r["where"], group_re):
                groups.setdefault(g, []).append(r)
        if not groups:
            out.append("None.")
        for g in sorted(groups):
            out.append(f"### {g}")
            for r in groups[g]:
                note = f"; {r['note']}" if r["note"] else ""
                out.append(f"- {r['report']} {r['item']} ({r['verdict']}{note}): {r['where'] or '(no location given)'}")
            out.append("")
    print("\n".join(out).rstrip() + ("\n" if out else ""))

    if args.tsv:
        try:
            with open(args.tsv, "w", encoding="utf-8", newline="") as fh:
                w = csv.writer(fh, delimiter="\t", lineterminator="\n")
                w.writerow(["report", "item", "number", "verdict", "note", "reason", "where", "file", "line"])
                for r in sorted(unique, key=item_sort_key):
                    w.writerow([r["report"], r["item"], "" if r["number"] is None else r["number"], r["verdict"],
                                r["note"], r["reason"], r["where"], r["file"], r["line"]])
        except OSError as e:
            print(f"adjudication_summary: cannot write {args.tsv}: {e}", file=sys.stderr)
            sys.exit(2)

    for w in warnings:
        print(f"warning: {w}")
    for p in problems:
        print(f"PROBLEM: {p}")
    status = "FAILED" if problems else "ok"
    print(f"adjudication_summary: {len(reports)} report(s), {sum(total.values())} items: "
          + ", ".join(f"{v} {total[v]}" for v in VERDICTS)
          + f"; {len(problems)} problem(s), {len(warnings)} warning(s) -> {status}")
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
