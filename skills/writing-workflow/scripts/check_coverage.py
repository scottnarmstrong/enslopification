#!/usr/bin/env python3
"""Check that review reports cover what they were asked to cover: every label, or every page of a range.

Labels mode. The labels come from a register (a Markdown table or a TSV file: --register, with --column and
--where), from the \\label commands inside chosen environments of TeX files (--tex, --env), or from a list
(--labels, --labels-file). Every label that no report mentions is listed. A label that no report names is a
coverage gap: no reviewer reported on it by name. A label that a report names is NOT thereby reviewed: the check
reads the reports' text, not the work behind them. A mention is a whole-token match of the label (lem:B1 does not
match lem:B10), case-sensitive, so ask reviewers to name statements by their labels.

Pages mode (--pages A-B). Every page of the range must appear in some report's defects table (a Markdown table
whose first column is "Page") or on its "Clean pages:" line (also accepted: "... pages are clean: ..."). Ranges
such as "2-5, 7-13 and 15" (hyphens or dashes) are expanded; a cell such as "1 vs 6" counts both pages. A page in
neither place was not reported as inspected; a page listed was only reported as inspected.

REPORT arguments are files, or directories whose *.md files are read, except the driver's prompt files
(prompt*.md). Register cells may hold several labels separated by commas, semicolons or spaces.

Usage:
  check_coverage.py [--register FILE]... [--column NAME] [--where COL=VALUE]... [--tex FILE]... [--env ENV]...
                    [--labels L1,L2] [--labels-file FILE] [--report-only] REPORT...
  check_coverage.py --pages A-B [--report-only] REPORT...
Exit status: 0 everything covered, or --report-only; 1 a label or page is not covered; 2 usage or input error
(no report file, unreadable file, no table with the column, no labels found; with --report-only, no labels is a
warning and exits 0).
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

DEFAULT_ENVS = ["maintheorem", "theorem", "proposition", "lemma", "corollary", "definition"]
COMMENT = re.compile(r"(?<!\\)%.*")
VERBATIM = re.compile(r"\\begin\{(verbatim\*?|Verbatim|lstlisting|minted|comment)\}.*?\\end\{\1\}", re.S)
TEX_TOKEN = re.compile(r"\\(begin|end)\s*\{([^{}]+)\}|\\label\s*\{([^{}]+)\}")
SEPARATOR = re.compile(r"^\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)*\|?\s*$")
CLEAN_LINE = [re.compile(r"(?i)\bclean\s+pages?\b[^:\n]*:\s*(.*)$"),
              re.compile(r"(?i)\bpages?(?:\s+ranges?)?\s+(?:are|is)\s+clean\b[^:\n]*:\s*(.*)$")]
DASHES = re.compile("[\u2010-\u2015\u2212]")
RANGE = re.compile(r"(\d+)\s*(?:-+|to)\s*(\d+)|(\d+)")
MAX_SPAN = 100000


class InputError(ValueError):
    pass


# ----------------------------------------------------------------------------------------------- reading

def read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError as e:
        raise InputError(f"cannot read {path}: {e}") from None


def report_files(items: list[str]) -> list[Path]:
    out: list[Path] = []
    for item in items:
        p = Path(item)
        if p.is_dir():
            found = sorted(f for f in p.glob("*.md") if f.is_file() and not f.name.startswith("prompt"))
            if not found:
                raise InputError(f"no report (*.md other than prompt*.md) in directory {p}")
            out.extend(found)
        elif p.is_file():
            out.append(p)
        else:
            raise InputError(f"no such report file or directory: {p}")
    return out


def split_cells(line: str) -> list[str]:
    s = line.strip()
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|") and not s.endswith("\\|"):
        s = s[:-1]
    return [c.strip() for c in re.split(r"(?<!\\)\|", s)]


def clean_cell(cell: str) -> str:
    return cell.strip().strip("`*_ ").strip()


def markdown_tables(lines: list[str]) -> list[tuple[list[str], list[tuple[int, list[str]]]]]:
    """Every Markdown table: (header cells, [(line number, cells)])."""
    tables, i = [], 0
    while i < len(lines) - 1:
        if lines[i].lstrip().startswith("|") and SEPARATOR.match(lines[i + 1]):
            header = [clean_cell(c) for c in split_cells(lines[i])]
            rows, j = [], i + 2
            while j < len(lines) and lines[j].lstrip().startswith("|"):
                rows.append((j + 1, split_cells(lines[j])))
                j += 1
            tables.append((header, rows))
            i = j
        else:
            i += 1
    return tables


def tsv_table(lines: list[str]) -> list[tuple[list[str], list[tuple[int, list[str]]]]]:
    body = [(n, ln) for n, ln in enumerate(lines, 1) if ln.strip() and not ln.lstrip().startswith("#")]
    if not body:
        return []
    header = [clean_cell(c) for c in body[0][1].split("\t")]
    return [(header, [(n, ln.split("\t")) for n, ln in body[1:]])]


def split_labels(value: str) -> list[str]:
    return [x for x in (clean_cell(t) for t in re.split(r"[;,\s]+", value)) if x and x not in ("-", "\u2014")]


def register_labels(path: Path, column: str | None, where: list[tuple[str, str]]) -> list[tuple[str, str]]:
    lines = read(path).splitlines()
    tables = markdown_tables(lines) if any(ln.lstrip().startswith("|") for ln in lines) else tsv_table(lines)
    wanted = [column.lower()] if column else ["id", "label"]
    for header, rows in tables:
        low = [h.lower() for h in header]
        col = next((low.index(w) for w in wanted if w in low), None)
        if col is None and column is None and header:
            col = 0
        if col is None:
            continue
        missing = [k for k, _ in where if k.lower() not in low]
        if missing:
            raise InputError(f"{path}: no column {missing[0]!r} for --where (columns: {', '.join(header)})")
        conditions = [(low.index(k.lower()), v) for k, v in where]
        out = []
        for n, cells in rows:
            keep = all(i < len(cells) and clean_cell(cells[i]) == v for i, v in conditions)
            if keep and col < len(cells):
                out.extend((lab, f"{path.name}:{n}") for lab in split_labels(cells[col]))
        return out
    raise InputError(f"{path}: no table with a column {column or 'id or label'}")


def tex_labels(path: Path, envs: set[str]) -> list[tuple[str, str]]:
    """Labels whose innermost enclosing environment is one of envs (a label in an equation or a list inside a
    lemma belongs to the equation or the item, as in LaTeX)."""
    text = VERBATIM.sub(lambda m: "\n" * m.group(0).count("\n"), read(path))
    out, stack = [], []
    for n, line in enumerate(text.splitlines(), 1):
        for m in TEX_TOKEN.finditer(COMMENT.sub("", line)):
            if m.group(1) == "begin":
                stack.append(m.group(2).strip())
            elif m.group(1) == "end":
                name = m.group(2).strip()
                if name in stack:
                    while stack and stack.pop() != name:
                        pass
            else:
                env = stack[-1] if stack else ""
                if env.rstrip("*") in envs:
                    out.append((m.group(3).strip(), f"{path.name}:{n} ({env})"))
    return out


def page_set(text: str) -> set[int]:
    pages: set[int] = set()
    for m in RANGE.finditer(DASHES.sub("-", text)):
        if m.group(3):
            pages.add(int(m.group(3)))
            continue
        a, b = int(m.group(1)), int(m.group(2))
        if b < a or b - a > MAX_SPAN:
            raise InputError(f"bad page range {m.group(0)!r} in {text.strip()[:60]!r}")
        pages.update(range(a, b + 1))
    return pages


def ranges(pages: set[int] | list[int]) -> str:
    out, ps = [], sorted(pages)
    i = 0
    while i < len(ps):
        j = i
        while j + 1 < len(ps) and ps[j + 1] == ps[j] + 1:
            j += 1
        out.append(str(ps[i]) if i == j else f"{ps[i]}-{ps[j]}")
        i = j + 1
    return ", ".join(out)


def report_pages(text: str) -> tuple[set[int], set[int], bool, bool]:
    """Pages of the defects table, pages of the clean-pages line, whether each was found."""
    lines = text.splitlines()
    defects, clean, has_table, has_clean = set(), set(), False, False
    for header, rows in markdown_tables(lines):
        if header and header[0].lower() in ("page", "pages"):
            has_table = True
            for _, cells in rows:
                defects |= page_set(cells[0]) if cells else set()
    for i, line in enumerate(lines):
        if line.lstrip().startswith("|"):
            continue
        plain = line.replace("*", "").replace("`", "")
        m = next((r.search(plain) for r in CLEAN_LINE if r.search(plain)), None)
        if not m:
            continue
        has_clean = True
        rest = m.group(1).strip()
        if not rest:
            rest = next((x for x in lines[i + 1:] if x.strip()), "")
        clean |= page_set(rest)
    return defects, clean, has_table, has_clean


# ----------------------------------------------------------------------------------------------- modes

def mentioned(label: str, texts: list[str]) -> bool:
    pat = re.compile(r"(?<![A-Za-z0-9:._-])" + re.escape(label) + r"(?![A-Za-z0-9:_-])(?!\.[A-Za-z0-9])")
    return any(pat.search(t) for t in texts)


def labels_mode(a: argparse.Namespace, reports: list[Path]) -> int:
    envs = {e.strip().rstrip("*") for item in (a.env or DEFAULT_ENVS) for e in item.split(",") if e.strip()}
    where = []
    for w in a.where:
        if "=" not in w:
            raise InputError(f"--where expects COLUMN=VALUE, got {w!r}")
        k, v = w.split("=", 1)
        where.append((k.strip(), v.strip()))
    found: list[tuple[str, str]] = []
    for r in a.register:
        found += register_labels(Path(r), a.column, where)
    for t in a.tex:
        found += tex_labels(Path(t), envs)
    for item in a.labels:
        found += [(lab, "--labels") for lab in split_labels(item)]
    if a.labels_file:
        lines = [ln for ln in read(Path(a.labels_file)).splitlines() if not ln.lstrip().startswith("#")]
        found += [(lab, Path(a.labels_file).name) for ln in lines for lab in split_labels(ln)]
    origin: dict[str, str] = {}
    for lab, where_from in found:
        origin.setdefault(lab, where_from)
    if not origin:
        print("check_coverage: no labels found in the given sources (check --env, --column, --where)")
        return 0 if a.report_only else 2
    texts = [read(p) for p in reports]
    gaps = [lab for lab in origin if not mentioned(lab, texts)]
    for lab in gaps:
        print(f"NOT MENTIONED\t{lab}\t{origin[lab]}")
    print(f"check_coverage: {len(origin)} label(s); {len(origin) - len(gaps)} mentioned in {len(reports)} "
          f"report(s), {len(gaps)} never mentioned. A label no report names was not reviewed by name; a label "
          f"that is named is not thereby reviewed.")
    return 1 if gaps and not a.report_only else 0


def pages_mode(a: argparse.Namespace, reports: list[Path]) -> int:
    if not re.fullmatch(r"\s*\d+\s*(?:-+|to)\s*\d+\s*", DASHES.sub("-", a.pages)):
        raise InputError(f"--pages expects a range A-B, got {a.pages!r}")
    want = page_set(a.pages)
    covered: set[int] = set()
    for p in reports:
        defects, clean, has_table, has_clean = report_pages(read(p))
        notes = [] if has_table else ["no defects table"]
        notes += [] if has_clean else ["no 'Clean pages:' line"]
        print(f"REPORT\t{p.name}\t{len(defects)} page(s) in the defects table, {len(clean)} listed as clean"
              + (f"; {', '.join(notes)}" if notes else ""))
        outside = (defects | clean) - want
        if outside:
            print(f"OUTSIDE\t{p.name}\tpage(s) {ranges(outside)} lie outside {min(want)}-{max(want)}")
        covered |= defects | clean
    gaps = want - covered
    if gaps:
        print(f"NOT COVERED\tpages {ranges(gaps)}")
    print(f"check_coverage: pages {min(want)}-{max(want)}; {len(want & covered)} covered by {len(reports)} "
          f"report(s) (defects table or clean-pages line), {len(gaps)} not covered. A page listed was reported as "
          f"inspected, which is not evidence that it was looked at.")
    return 1 if gaps and not a.report_only else 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="List the labels that no review report mentions, or the pages of a range that no "
                    "typography report lists. A gap means not reviewed by name; a mention is not proof of review.",
        epilog="examples:\n"
               "  check_coverage.py --tex proposal/F-section.tex rollout/F/r1 rollout/F/r2\n"
               "  check_coverage.py --register REGISTER.md --where section=15 rollout/F/r1\n"
               "  check_coverage.py --register xref/by-pair/16--15.tsv --column cited_label check/G1/routed.md\n"
               "  check_coverage.py --pages 1-50 rollout/p001/inspect/typography.md",
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("reports", nargs="+", metavar="REPORT", help="report file, or directory of *.md reports")
    ap.add_argument("--register", action="append", default=[], metavar="FILE",
                    help="Markdown table or TSV whose column holds labels (repeat)")
    ap.add_argument("--column", help="register column with the labels (default: id or label, else the first)")
    ap.add_argument("--where", action="append", default=[], metavar="COL=VALUE",
                    help="keep only register rows whose column equals the value (repeat: all must hold)")
    ap.add_argument("--tex", action="append", default=[], metavar="FILE", help="TeX file whose labels to take (repeat)")
    ap.add_argument("--env", action="append", metavar="ENV[,ENV]",
                    help=f"environments whose labels count (default: {', '.join(DEFAULT_ENVS)})")
    ap.add_argument("--labels", action="append", default=[], metavar="L1,L2", help="labels given directly")
    ap.add_argument("--labels-file", metavar="FILE", help="labels, one or more per line ('#' starts a comment)")
    ap.add_argument("--pages", metavar="A-B", help="pages mode: the range every page of which must be covered")
    ap.add_argument("--report-only", action="store_true", help="list the gaps, never fail on them")
    a = ap.parse_args(argv)
    has_labels = a.register or a.tex or a.labels or a.labels_file
    if a.pages and has_labels:
        ap.error("--pages cannot be combined with label sources")
    if not a.pages and not has_labels:
        ap.error("give label sources (--register, --tex, --labels, --labels-file) or --pages")
    try:
        reports = report_files(a.reports)
        return pages_mode(a, reports) if a.pages else labels_mode(a, reports)
    except InputError as e:
        print(f"check_coverage: error: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
