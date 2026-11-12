#!/usr/bin/env python3
"""Report pages per section of a compiled LaTeX document against page allowances.

Usage:
  page_report.py --toc main.toc [--allowances allowances.tsv] [--level section]
  page_report.py --aux main.aux --from-labels --allowances allowances.tsv

Pages of a section = start page of the next unit at the same level (or the last page) minus its
own start page. Sections that start mid-page share that page, so each figure is exact to within
one page. The last page comes from --last-page, else from "Output written on ... (N pages" in the
.log next to the .toc/.aux. Roman front-matter numbers are skipped; a document whose arabic
numbering does not start on its first physical page needs --last-page.

Allowances file (TSV, "#" comments allowed):  key <TAB> pages [<TAB> kind [<TAB> note]]
  key   a section number ("12"), a \\label ("sec:uv", looked up in the .aux), or a
        case-insensitive substring of the title
  kind  cap (default): over the allowance fails the check;
        guide: over the allowance is reported and needs a written reason, but does not fail
With --from-labels the keys are \\label names; each unit runs from its label's page to the next
label's page.

Exit status: 0 no cap exceeded, 1 a cap exceeded, 2 usage or input error.
"""
import argparse
import json
import os
import re
import sys


def read_text(path):
    with open(path, encoding="utf-8", errors="replace") as fh:
        return fh.read()


def braced_args(text, pos, n):
    """Read n balanced {...} arguments starting at pos; return (args, end) or (None, pos)."""
    out = []
    i = pos
    for _ in range(n):
        while i < len(text) and text[i] in " \t\n":
            i += 1
        if i >= len(text) or text[i] != "{":
            return None, pos
        depth, j = 0, i
        while j < len(text):
            c = text[j]
            if c == "\\":
                j += 2
                continue
            if c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    break
            j += 1
        out.append(text[i + 1:j])
        i = j + 1
    return out, i


def clean_title(t):
    t = re.sub(r"\\numberline\s*\{([^{}]*)\}", "", t)
    t = re.sub(r"\\[A-Za-z@]+\*?", " ", t)
    return " ".join(t.replace("{", "").replace("}", "").split())


def read_toc(path, level):
    text = read_text(path)
    units = []
    for m in re.finditer(r"\\contentsline\s*", text):
        args, _ = braced_args(text, m.end(), 3)
        if not args or args[0] != level:
            continue
        num = re.search(r"\\numberline\s*\{([^{}]*)\}", args[1])
        page = args[2].strip()
        if not page.isdigit():
            print(f"warning: skipping non-arabic page {page!r} of {clean_title(args[1])!r}", file=sys.stderr)
            continue
        units.append({"key": num.group(1) if num else "", "title": clean_title(args[1]), "start": int(page)})
    return units


def read_labels(path):
    text = read_text(path)
    labels = {}
    for m in re.finditer(r"\\newlabel\{([^{}]*)\}", text):
        args, _ = braced_args(text, m.end(), 1)
        if not args:
            continue
        inner, _ = braced_args(args[0], 0, 2)
        if inner and inner[1].strip().isdigit():
            labels[m.group(1)] = {"number": clean_title(inner[0]), "page": int(inner[1])}
    return labels


def last_page(args, near):
    if args.last_page:
        return args.last_page
    log = os.path.splitext(near)[0] + ".log"
    if os.path.exists(log):
        m = re.findall(r"Output written on .*?\((\d+) pages?", read_text(log))
        if m:
            return int(m[-1])
    raise ValueError(f"no page total: give --last-page or keep {log} next to {near}")


def read_allowances(path):
    rows = []
    for n, line in enumerate(read_text(path).splitlines(), 1):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        cells = line.split("\t")
        if cells[0].strip().lower() == "key":
            continue
        try:
            pages = float(cells[1])
        except (IndexError, ValueError):
            raise ValueError(f"{path}:{n}: expected key<TAB>pages[<TAB>kind[<TAB>note]]")
        kind = (cells[2].strip().lower() if len(cells) > 2 and cells[2].strip() else "cap")
        if kind not in ("cap", "guide"):
            raise ValueError(f"{path}:{n}: kind must be cap or guide, not {kind!r}")
        rows.append({"key": cells[0].strip(), "pages": pages, "kind": kind,
                     "note": cells[3].strip() if len(cells) > 3 else ""})
    return rows


def main():
    ap = argparse.ArgumentParser(
        description="Pages per section of a compiled LaTeX document, from its .toc (or from "
                    "\\label pages in its .aux), compared with page allowances. Exit 1 if a cap is exceeded.",
        epilog="""examples:
  page_report.py --toc main.toc --allowances allowances.tsv
  page_report.py --toc main.toc --level part
  page_report.py --aux main.aux --from-labels --allowances part2-labels.tsv --last-page 241
allowances.tsv rows: "12<TAB>8<TAB>cap" or "sec:uv<TAB>30<TAB>guide<TAB>completeness first".
Make the hardest sections guides (completeness first) and the rest caps.""",
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--toc", help="the document's .toc file")
    ap.add_argument("--aux", help="the document's .aux file (for \\label keys)")
    ap.add_argument("--level", default="section", help="toc level: part, section, subsection (default section)")
    ap.add_argument("--from-labels", action="store_true", help="units start at the pages of the allowance keys (labels)")
    ap.add_argument("--allowances", help="TSV of allowances (see above)")
    ap.add_argument("--last-page", type=int, help="last page of the measured range")
    ap.add_argument("--json", action="store_true", help="print JSON")
    args = ap.parse_args()

    try:
        labels = read_labels(args.aux) if args.aux else {}
        allowances = read_allowances(args.allowances) if args.allowances else []
        if args.from_labels:
            if not (args.aux and allowances):
                raise ValueError("--from-labels needs --aux and --allowances")
            units = []
            for a in allowances:
                if a["key"] not in labels:
                    raise ValueError(f"label {a['key']!r} not found in {args.aux}")
                units.append({"key": a["key"], "title": labels[a["key"]]["number"], "start": labels[a["key"]]["page"]})
            units.sort(key=lambda u: u["start"])
            end = last_page(args, args.aux)
        else:
            if not args.toc:
                raise ValueError("give --toc (or --aux with --from-labels)")
            units = read_toc(args.toc, args.level)
            end = last_page(args, args.toc)
        if not units:
            raise ValueError(f"no {args.level} entries found")
    except (OSError, ValueError) as exc:
        print(f"page_report: input error: {exc}", file=sys.stderr)
        return 2

    for i, u in enumerate(units):
        nxt = units[i + 1]["start"] if i + 1 < len(units) else end + 1
        u["pages"] = max(nxt - u["start"], 0)
        u.update({"allowance": None, "kind": "", "status": "no allowance"})

    unmatched = []
    for a in allowances:
        hit = None
        for u in units:
            if args.from_labels:
                match = u["key"] == a["key"]
            elif a["key"] in labels:
                match = u["key"] == labels[a["key"]]["number"]
            else:
                match = u["key"] == a["key"] or (not a["key"].isdigit() and a["key"].lower() in u["title"].lower())
            if match:
                hit = u
                break
        if hit is None:
            unmatched.append(a["key"])
            continue
        hit.update({"allowance": a["pages"], "kind": a["kind"], "note": a["note"]})
        if hit["pages"] <= a["pages"]:
            hit["status"] = "ok"
        else:
            hit["status"] = "OVER" if a["kind"] == "cap" else "over guide (give the reason)"

    over = [u for u in units if u["status"] == "OVER"]
    guides = [u for u in units if u["status"].startswith("over guide")]
    total = sum(u["pages"] for u in units)
    summary = (f"pages: {len(units)} units, {total} pages measured (last page {end}); "
               f"{len(over)} over cap, {len(guides)} over guide, {len(unmatched)} allowance key(s) unmatched")
    if args.json:
        print(json.dumps({"units": units, "unmatched": unmatched, "summary": summary}, indent=1))
    else:
        print("key\ttitle\tstart\tpages\tallowance\tkind\tstatus")
        for u in units:
            allowance = "" if u["allowance"] is None else f"{u['allowance']:g}"
            print(f"{u['key']}\t{u['title'][:50]}\t{u['start']}\t{u['pages']}\t{allowance}\t{u['kind']}\t{u['status']}")
        for k in unmatched:
            print(f"UNMATCHED allowance key {k!r}")
        print(summary)
    if unmatched:
        return 2
    return 1 if over else 0


if __name__ == "__main__":
    sys.exit(main())
