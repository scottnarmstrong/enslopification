#!/usr/bin/env python3
"""Inventory the routed citations of a LaTeX manuscript: every \\ref-family citation whose label is defined in another
section (or file), with what the citing proof is and what the cited label is.

Reads MAIN.tex and every file it \\input / \\include / \\subfile (recursively, in document order); with --aux, the
printed numbers. Writes, in --out DIR:

  citations.tsv  one row per cross-unit citation (all citations with --all): citing unit, file:line, context
                 (proof / statement / env:NAME / text), the statement whose proof or text cites, the command, the
                 cited label, its kind (lemma, equation, item, ...), where it lives (statement / proof / text: a
                 label inside a proof is a display the citing section uses although no statement says it), its
                 owning statement, unit, file:line, printed number, range id
  ranges.tsv     every range citation (\\ref{a}--\\ref{b}, \\crefrange) with the labels it spans and their kinds
  edges.tsv      the lemma-level citation graph: statement -> statement, from citations inside proofs and statements
  cycles.tsv     the cycles of that graph (candidate loops to clear or confirm), with the units they cross
  pairs.tsv      one row per (citing unit, cited unit): counts, citations inside proofs, ranges, displays from proofs
  labels.tsv     every label: kind, unit, file:line, owner statement, printed number
  unresolved.tsv citations of labels defined nowhere, and labels defined twice
  by-pair/       citations.tsv split by (citing unit, cited unit): one file per checker group

Units: --unit file (default; --unit-map can merge files, e.g. every part2/E-*.tex into one section), or section,
chapter, part (a unit starts at each sectioning command of that level or above and is named by its label).

Heuristics, stated: a proof is attributed to the statement named in its optional argument ([Proof of
Lemma~\\ref{x}]), else to the closest preceding labelled statement in the same file; theorem-like environments are
those declared with \\newtheorem or \\declaretheorem plus --statement-envs; remarks, examples and notation do not give
graph edges (--nonlogical-envs). Comments and verbatim text are ignored. \\import and \\subimport are not followed.

Usage:
  cross_refs.py MAIN.tex --out DIR [--aux MAIN.aux] [--unit file|section|chapter|part] [--unit-map TSV] [--all]
Exit status: 0 ok; 1 a citation of an undefined label or a label defined twice; 2 usage or input error.
"""
from __future__ import annotations

import argparse
import bisect
import collections
import fnmatch
import os
import re
import sys
from pathlib import Path

STATEMENT_DEFAULT = ["theorem", "thm", "lemma", "lem", "proposition", "prop", "corollary", "cor", "claim",
                     "definition", "defn", "dfn", "assumption", "hypothesis", "conjecture", "remark", "rem",
                     "example", "notation", "maintheorem", "principle"]
NONLOGICAL_DEFAULT = ["remark", "rem", "example", "ex", "exmp", "note", "notation", "conjecture", "question",
                      "problem", "exercise", "convention"]
EQUATION_ENVS = {"equation", "align", "gather", "multline", "eqnarray", "flalign", "alignat", "subequations",
                 "dmath", "dgroup"}
LIST_ENVS = {"enumerate", "itemize", "description", "compactenum", "inparaenum"}
LEVELS = {"part": 0, "chapter": 1, "section": 2, "subsection": 3, "subsubsection": 4}
VERBATIM = re.compile(r"\\begin\{(verbatim\*?|Verbatim|lstlisting|minted|comment)\}.*?\\end\{\1\}", re.S)
TOKEN = re.compile(r"""
   \\(?P<be>begin|end)\s*\{(?P<env>[^{}]+)\}
 | \\(?P<inp>input|include|subfile)\s*\{(?P<path>[^{}]+)\}
 | \\label\s*\{(?P<label>[^{}]+)\}
 | \\(?P<sec>part|chapter|section|subsection|subsubsection)\b\*?
 | \\(?P<rng>crefrange|Crefrange|cpagerefrange|Cpagerefrange)\*?\s*\{(?P<r1>[^{}]+)\}\s*\{(?P<r2>[^{}]+)\}
 | \\(?P<ref>ref|eqref|cref|Cref|autoref|Autoref|pageref|nameref|cpageref|Cpageref|labelcref|vref|Vref|vpageref)
     \*?\s*\{(?P<labels>[^{}]+)\}
 | \\hyperref\s*\[(?P<hlabel>[^\]]+)\]
 | \\(?:newtheorem|declaretheorem|spnewtheorem)\*?\s*(?:\[[^\]]*\]\s*)?\{(?P<thm>[^{}]+)\}
""", re.X)
RANGE_GAP = re.compile(r"\A\s*\)?\s*(?:--|–|—|-|\\textendash(?:\{\})?|\\nobreakdash--|to|through)\s*~?\s*\(?\s*\Z")
NEWLABEL = re.compile(r"\\newlabel\{([^{}]+)\}\{\{((?:[^{}]|\{(?:[^{}]|\{[^{}]*\})*\})*)\}")
AUX_INPUT = re.compile(r"\\@input\{([^{}]+)\}")


def strip_comments(text: str) -> str:
    out = []
    for line in text.split("\n"):
        i = 0
        while True:
            j = line.find("%", i)
            if j < 0:
                break
            k, bs = j - 1, 0
            while k >= 0 and line[k] == "\\":
                bs, k = bs + 1, k - 1
            if bs % 2 == 0:
                line = line[:j]
                break
            i = j + 1
        out.append(line)
    return "\n".join(out)


def balanced(text: str, pos: int, open_c: str, close_c: str) -> tuple[str, int] | None:
    """If text[pos:] (after spaces) starts with open_c, return (contents, end offset) of the balanced group."""
    while pos < len(text) and text[pos] in " \t\n":
        pos += 1
    if pos >= len(text) or text[pos] != open_c:
        return None
    depth, i = 0, pos
    while i < len(text):
        c = text[i]
        if c == "\\":
            i += 2
            continue
        if c == open_c:
            depth += 1
        elif c == close_c:
            depth -= 1
            if depth == 0:
                return text[pos + 1:i], i + 1
        i += 1
    return None


def read_aux(path: Path, seen: set | None = None) -> tuple[dict, dict]:
    """Printed numbers and cleveref types from an .aux file and the .aux files it inputs."""
    seen = seen or set()
    numbers, types = {}, {}
    if path in seen or not path.is_file():
        return numbers, types
    seen.add(path)
    text = path.read_text(encoding="utf-8", errors="replace")
    for m in NEWLABEL.finditer(text):
        label, raw = m.group(1), m.group(2)
        if label.endswith("@cref"):
            t = re.match(r"\[([^\]]+)\]", raw)
            if t:
                types[label[:-5]] = t.group(1)
            continue
        num = re.sub(r"\\relax|\\ignorespaces|[{}]", "", raw).strip()
        numbers[label] = re.sub(r"\s+", " ", num)
    for m in AUX_INPUT.finditer(text):
        n2, t2 = read_aux(path.parent / m.group(1), seen)
        numbers.update(n2)
        types.update(t2)
    return numbers, types


class Scanner:
    def __init__(self, main: Path, unit_mode: str, unit_map: list[tuple[str, str]], statement_envs: set[str],
                 nonlogical: set[str], proof_envs: set[str]):
        self.main = main.resolve()
        self.root = self.main.parent
        self.unit_mode = unit_mode
        self.unit_map = unit_map
        self.statement_envs = set(statement_envs)
        self.nonlogical = nonlogical
        self.proof_envs = proof_envs
        self.labels: dict[str, dict] = {}
        self.duplicates: list[tuple[str, str, str]] = []
        self.cites: list[dict] = []
        self.ranges: list[dict] = []
        self.missing_inputs: list[str] = []
        self.order = 0
        self.stack: list[dict] = []
        self.units: list[dict] = [{"name": None, "title": "front matter", "label": None}]
        self.unit_index = 0
        self.pending_section: dict | None = None
        self.last_closed: dict[str, dict] = {}

    # --- files
    def rel(self, path: Path) -> str:
        try:
            return str(path.resolve().relative_to(self.root))
        except ValueError:
            return str(path)

    def resolve_input(self, name: str, base: Path) -> Path | None:
        name = name.strip()
        for cand in (self.root / name, self.root / f"{name}.tex", base.parent / name, base.parent / f"{name}.tex"):
            if cand.is_file():
                return cand
        return None

    def file_unit(self, rel: str) -> str:
        for pat, name in self.unit_map:
            if fnmatch.fnmatch(rel, pat):
                return name
        return rel[:-4] if rel.endswith(".tex") else rel

    def current_unit(self, rel: str) -> str | int:
        return self.file_unit(rel) if self.unit_mode == "file" else self.unit_index

    # --- scanning
    def scan(self) -> None:
        self.prescan(self.main, set())
        self.walk(self.main, depth=0)

    def prescan(self, path: Path, seen: set) -> None:
        """Collect theorem-like environment names from every reachable file before the main pass."""
        if path in seen:
            return
        seen.add(path)
        text = strip_comments(path.read_text(encoding="utf-8", errors="replace"))
        for m in TOKEN.finditer(text):
            if m.group("thm"):
                self.statement_envs.add(m.group("thm").strip())
            elif m.group("inp"):
                child = self.resolve_input(m.group("path"), path)
                if child:
                    self.prescan(child, seen)

    def walk(self, path: Path, depth: int) -> None:
        if depth > 30:
            raise ValueError(f"\\input nesting deeper than 30 at {path}")
        rel = self.rel(path)
        raw = path.read_text(encoding="utf-8", errors="replace")
        text = VERBATIM.sub(lambda m: "\n" * m.group(0).count("\n"), strip_comments(raw))
        newlines = [i for i, c in enumerate(text) if c == "\n"]
        line_of = lambda off: bisect.bisect_right(newlines, off - 1) + 1  # noqa: E731
        skip_spans: list[tuple[int, int, dict]] = []
        prev_single: dict | None = None
        for m in TOKEN.finditer(text):
            off, line = m.start(), line_of(m.start())
            if m.group("inp"):
                child = self.resolve_input(m.group("path"), path)
                if child is None:
                    self.missing_inputs.append(f"{rel}:{line}: {m.group('path')}")
                else:
                    self.walk(child, depth + 1)
                prev_single = None
                continue
            if m.group("sec"):
                self.section(m.group("sec"), text, m.end(), rel, line)
                prev_single = None
                continue
            if m.group("be"):
                self.environment(m.group("be"), m.group("env").strip(), text, m.end(), rel, line, skip_spans)
                prev_single = None
                continue
            if m.group("label"):
                self.define(m.group("label").strip(), rel, line)
                continue
            title_span = next((s for s in skip_spans if s[0] <= off < s[1]), None)
            if m.group("rng") or m.group("ref") or m.group("hlabel"):
                if m.group("rng"):
                    labels, cmd = [m.group("r1").strip(), m.group("r2").strip()], m.group("rng")
                elif m.group("ref"):
                    labels, cmd = [x.strip() for x in m.group("labels").split(",") if x.strip()], m.group("ref")
                else:
                    labels, cmd = [m.group("hlabel").strip()], "hyperref"
                if title_span is not None:
                    frame = title_span[2]
                    frame["proof_of"] = frame.get("proof_of") or labels[0]
                    continue
                recs = [self.cite(lab, cmd, rel, line) for lab in labels]
                if m.group("rng"):
                    self.add_range(recs[0], recs[1], rel, line)
                    prev_single = None
                elif len(recs) == 1:
                    if prev_single is not None and RANGE_GAP.match(text[prev_single["_end"]:m.start()]):
                        self.add_range(prev_single, recs[0], rel, line)
                        prev_single = None
                    else:
                        prev_single = recs[0]
                        recs[0]["_end"] = m.end()
                else:
                    prev_single = None

    def section(self, level: str, text: str, pos: int, rel: str, line: int) -> None:
        if self.unit_mode == "file" or LEVELS[level] > LEVELS[self.unit_mode]:
            self.pending_section = {"label": None, "title": level}      # only for the kind of a following label
            return
        opt = balanced(text, pos, "[", "]")
        title = balanced(text, opt[1] if opt else pos, "{", "}")
        name = re.sub(r"\s+", " ", re.sub(r"\\[A-Za-z]+|[{}$]", "", title[0])).strip()[:40] if title else "?"
        self.units.append({"name": None, "title": name, "label": None, "file": rel, "line": line})
        self.unit_index = len(self.units) - 1
        self.pending_section = self.units[-1]

    def environment(self, be: str, env: str, text: str, pos: int, rel: str, line: int, skip_spans: list) -> None:
        base = env.rstrip("*")
        if be == "begin":
            if base in self.proof_envs:
                kind = "proof"
            elif base in self.statement_envs:
                kind = "statement"
            elif base in EQUATION_ENVS:
                kind = "equation"
            elif base in LIST_ENVS:
                kind = "list"
            else:
                kind = "other"
            frame = {"env": base, "kind": kind, "label": None, "file": rel, "line": line, "proof_of": None,
                     "unit": self.current_unit(rel)}
            if kind == "proof":
                opt = balanced(text, pos, "[", "]")
                if opt:
                    skip_spans.append((pos, opt[1], frame))
                last = self.last_closed.get(rel)
                frame["fallback_of"] = last
            self.stack.append(frame)
            self.pending_section = None
        else:
            for i in range(len(self.stack) - 1, -1, -1):
                if self.stack[i]["env"] == base:
                    frame = self.stack.pop(i)
                    del self.stack[i:]
                    if frame["kind"] == "statement" and frame["env"] not in self.nonlogical:
                        self.last_closed[rel] = frame
                    elif frame["kind"] == "proof":
                        self.last_closed.pop(rel, None)
                    break

    def proof_owner(self, frame: dict) -> str | None:
        if frame.get("proof_of"):
            return frame["proof_of"]
        fb = frame.get("fallback_of")
        return fb["label"] if fb and fb.get("label") else None

    def context(self) -> tuple[str, dict | None]:
        for frame in reversed(self.stack):
            if frame["kind"] == "statement" and frame["env"] not in self.nonlogical:
                return "statement", frame
            if frame["kind"] == "statement":
                return f"env:{frame['env']}", frame
            if frame["kind"] == "proof":
                return "proof", frame
        for frame in reversed(self.stack):
            if frame["kind"] == "other":
                return f"env:{frame['env']}", None
        return "text", None

    def define(self, label: str, rel: str, line: int) -> None:
        self.order += 1
        inner = self.stack[-1] if self.stack else None
        owner_frame, where = None, "text"
        for frame in reversed(self.stack):
            if frame["kind"] in ("statement", "proof"):
                owner_frame, where = frame, ("statement" if frame["kind"] == "statement" else "proof")
                break
        if inner is not None and inner["kind"] == "statement" and inner["label"] is None:
            inner["label"] = label
            kind = inner["env"]
        elif inner is not None and inner["kind"] == "equation":
            kind = "equation"
        elif inner is not None and inner["kind"] == "list":
            kind = "item"
        elif inner is not None and inner["kind"] == "proof":
            kind = "step"
        elif inner is not None and inner["kind"] == "statement":
            kind = "item"
        elif self.pending_section is not None and self.pending_section["label"] is None:
            self.pending_section["label"] = label
            kind = "section"
        elif inner is not None:
            kind = inner["env"]
        else:
            kind = "text"
        self.pending_section = None
        rec = {"label": label, "kind": kind, "file": rel, "line": line, "order": self.order,
               "unit": self.current_unit(rel), "where": where, "owner_frame": owner_frame}
        if label in self.labels:
            first = self.labels[label]
            self.duplicates.append((label, f"{first['file']}:{first['line']}", f"{rel}:{line}"))
        else:
            self.labels[label] = rec

    def cite(self, label: str, cmd: str, rel: str, line: int) -> dict:
        ctx, frame = self.context()
        rec = {"label": label, "command": cmd, "file": rel, "line": line, "context": ctx, "frame": frame,
               "unit": self.current_unit(rel), "range": ""}
        self.cites.append(rec)
        return rec

    def add_range(self, a: dict, b: dict, rel: str, line: int) -> None:
        rid = f"R{len(self.ranges) + 1}"
        a["range"] = b["range"] = rid
        self.ranges.append({"id": rid, "first": a["label"], "last": b["label"], "file": rel, "line": line,
                            "unit": a["unit"], "context": a["context"], "frame": a["frame"]})

    # --- results
    def unit_name(self, u: str | int) -> str:
        if isinstance(u, str):
            return u
        unit = self.units[u]
        if unit["label"]:
            return unit["label"]
        return f"S{u}:{unit['title']}" if u else "front"

    def statement_of_frame(self, frame: dict | None, ctx: str) -> str:
        if frame is None:
            return ""
        if frame["kind"] == "proof":
            return self.proof_owner(frame) or ""
        return frame.get("label") or ""

    def owner_of(self, rec: dict) -> str:
        frame = rec.get("owner_frame")
        if frame is None:
            return ""
        if frame["kind"] == "proof":
            return self.proof_owner(frame) or ""
        return frame.get("label") or ""


def tsv(path: Path, header: list[str], rows: list[list]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.write("\t".join(header) + "\n")
        for r in rows:
            f.write("\t".join(str(x).replace("\t", " ").replace("\n", " ") for x in r) + "\n")


def tarjan(nodes: list[str], adj: dict[str, set[str]]) -> list[list[str]]:
    index, low, on, stack, out = {}, {}, set(), [], []
    counter = 0
    for root in nodes:
        if root in index:
            continue
        work = [(root, iter(sorted(adj.get(root, ()))))]
        index[root] = low[root] = counter
        counter += 1
        stack.append(root)
        on.add(root)
        while work:
            v, it = work[-1]
            advanced = False
            for w in it:
                if w not in index:
                    index[w] = low[w] = counter
                    counter += 1
                    stack.append(w)
                    on.add(w)
                    work.append((w, iter(sorted(adj.get(w, ())))))
                    advanced = True
                    break
                if w in on:
                    low[v] = min(low[v], index[w])
            if advanced:
                continue
            work.pop()
            if work:
                low[work[-1][0]] = min(low[work[-1][0]], low[v])
            if low[v] == index[v]:
                comp = []
                while True:
                    w = stack.pop()
                    on.discard(w)
                    comp.append(w)
                    if w == v:
                        break
                if len(comp) > 1 or v in adj.get(v, ()):
                    out.append(comp)
    return out


def simple_cycles(comp: list[str], adj: dict[str, set[str]], order: dict[str, int], limit: int,
                  max_len: int = 12, budget: int = 200000) -> list[list[str]]:
    """Elementary cycles inside one strongly connected component, each reported once (from its smallest node)."""
    members = sorted(comp, key=lambda x: order.get(x, 0))
    rank = {v: i for i, v in enumerate(members)}
    cycles: list[list[str]] = []
    steps = 0
    for s in members:
        stack = [(s, [s])]
        while stack and len(cycles) < limit and steps < budget:
            v, path = stack.pop()
            steps += 1
            for w in sorted(adj.get(v, ()), key=lambda x: order.get(x, 0), reverse=True):
                if w not in rank or rank[w] < rank[s]:
                    continue
                if w == s:
                    cycles.append(path + [s])
                elif w not in path and len(path) < max_len:
                    stack.append((w, path + [w]))
    return cycles


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="Inventory citations between sections (routed inputs): TSV tables, range citations, the "
                    "lemma-level citation graph and its cycles.",
        epilog="examples:\n"
               "  cross_refs.py manuscript/main.tex --aux manuscript/main.aux --out xref/\n"
               "  cross_refs.py main.tex --out xref/ --unit-map units.tsv     (units.tsv: 'part2/E-*.tex<TAB>14')\n"
               "  cross_refs.py main.tex --out xref/ --unit section",
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("main", help="main .tex file")
    ap.add_argument("--out", required=True, help="output directory")
    ap.add_argument("--aux", help="the .aux file of a compiled build (printed numbers)")
    ap.add_argument("--unit", choices=["file", "section", "chapter", "part"], default="file",
                    help="what counts as one section (default: one input file)")
    ap.add_argument("--unit-map", help="TSV of 'file glob<TAB>unit name' merging files into units (file mode)")
    ap.add_argument("--all", action="store_true", help="list citations inside a unit too")
    ap.add_argument("--statement-envs", default="", help="extra theorem-like environment names, comma-separated")
    ap.add_argument("--nonlogical-envs", default=",".join(NONLOGICAL_DEFAULT),
                    help="theorem-like environments that give no graph edges (default: %(default)s)")
    ap.add_argument("--proof-envs", default="proof", help="proof environments, comma-separated (default: proof)")
    ap.add_argument("--max-cycles", type=int, default=200, help="cap on the cycles listed (default 200)")
    a = ap.parse_args(argv)
    main_tex = Path(a.main)
    if not main_tex.is_file():
        print(f"cross_refs: error: {main_tex} not found", file=sys.stderr)
        return 2
    unit_map = []
    if a.unit_map:
        for ln in Path(a.unit_map).read_text(encoding="utf-8").splitlines():
            if ln.strip() and not ln.startswith("#"):
                parts = ln.split("\t")
                if len(parts) < 2:
                    print(f"cross_refs: error: bad unit-map line {ln!r} (want glob<TAB>name)", file=sys.stderr)
                    return 2
                unit_map.append((parts[0].strip(), parts[1].strip()))
    envs = set(STATEMENT_DEFAULT) | {e.strip() for e in a.statement_envs.split(",") if e.strip()}
    sc = Scanner(main_tex, a.unit, unit_map, envs, {e.strip() for e in a.nonlogical_envs.split(",") if e.strip()},
                 {e.strip() for e in a.proof_envs.split(",") if e.strip()})
    try:
        sc.scan()
    except (OSError, ValueError) as e:
        print(f"cross_refs: error: {e}", file=sys.stderr)
        return 2
    numbers, types = read_aux(Path(a.aux)) if a.aux else ({}, {})
    if a.aux and not numbers:
        print(f"cross_refs: warning: no \\newlabel entries read from {a.aux}", file=sys.stderr)
    out = Path(a.out)
    (out / "by-pair").mkdir(parents=True, exist_ok=True)
    for old in (out / "by-pair").glob("*.tsv"):
        old.unlink()
    L = sc.labels
    un = sc.unit_name

    def kind_of(lab: str) -> str:
        rec = L.get(lab)
        k = rec["kind"] if rec else ""
        return types.get(lab, k) if k in ("", "text") else k

    rows, unresolved, pairs = [], [], collections.defaultdict(lambda: collections.Counter())
    pair_labels = collections.defaultdict(set)
    by_pair = collections.defaultdict(list)
    header = ["id", "citing_unit", "citing_file", "citing_line", "context", "citing_statement", "command",
              "cited_label", "cited_kind", "cited_where", "cited_owner", "cited_unit", "cited_file", "cited_line",
              "printed", "range"]
    n_cross = n_proof = 0
    for c in sc.cites:
        target = L.get(c["label"])
        if target is None:
            unresolved.append(["UNDEFINED", c["label"], f"{c['file']}:{c['line']}", ""])
            continue
        cu, tu = un(c["unit"]), un(target["unit"])
        cross = cu != tu
        if not cross and not a.all:
            continue
        cid = f"C{len(rows) + 1}"
        row = [cid, cu, c["file"], c["line"], c["context"], sc.statement_of_frame(c["frame"], c["context"]),
               c["command"], c["label"], kind_of(c["label"]), target["where"], sc.owner_of(target), tu,
               target["file"], target["line"], numbers.get(c["label"], ""), c["range"]]
        rows.append(row)
        if cross:
            n_cross += 1
            n_proof += c["context"] == "proof"
            key = (cu, tu)
            pairs[key]["citations"] += 1
            pairs[key]["in_proofs"] += c["context"] == "proof"
            pairs[key]["in_statements"] += c["context"] == "statement"
            pairs[key]["elsewhere"] += c["context"] not in ("proof", "statement")
            pairs[key]["ranges"] += bool(c["range"])
            pairs[key]["displays_from_proofs"] += target["where"] == "proof"
            pair_labels[key].add(c["label"])
            by_pair[key].append(row)
    for label, first, second in sc.duplicates:
        unresolved.append(["DUPLICATE", label, first, second])
    tsv(out / "citations.tsv", header, rows)
    safe = lambda s: re.sub(r"[^A-Za-z0-9_.-]+", "_", s).strip("_") or "unit"  # noqa: E731
    for (cu, tu), prs in by_pair.items():
        tsv(out / "by-pair" / f"{safe(cu)}--{safe(tu)}.tsv", header, prs)
    tsv(out / "pairs.tsv", ["citing_unit", "cited_unit", "citations", "in_proofs", "in_statements", "elsewhere",
                            "distinct_cited_labels", "range_citations", "displays_from_proofs"],
        [[cu, tu, c["citations"], c["in_proofs"], c["in_statements"], c["elsewhere"], len(pair_labels[(cu, tu)]),
          c["ranges"], c["displays_from_proofs"]] for (cu, tu), c in sorted(pairs.items())])
    # ranges
    by_order = sorted(L.values(), key=lambda r: r["order"])
    statement_kinds = {r["kind"] for r in L.values() if r["kind"] in sc.statement_envs}
    rrows = []
    for r in sc.ranges:
        A, B = L.get(r["first"]), L.get(r["last"])
        if A is None or B is None:
            rrows.append([r["id"], un(r["unit"]), r["file"], r["line"], r["first"], r["last"], "", "", "?",
                          "an endpoint is undefined", ""])
            continue
        lo, hi = sorted((A["order"], B["order"]))
        family = statement_kinds if A["kind"] in statement_kinds else {A["kind"]}
        span = [x for x in by_order if lo <= x["order"] <= hi and x["kind"] in family]
        kinds = collections.Counter(x["kind"] for x in span)
        note = "reversed" if A["order"] > B["order"] else ""
        rrows.append([r["id"], un(r["unit"]), r["file"], r["line"], r["first"], r["last"],
                      numbers.get(r["first"], ""), numbers.get(r["last"], ""), len(span),
                      ", ".join(f"{k} {v}" for k, v in sorted(kinds.items())) + (f"; {note}" if note else ""),
                      " ".join(x["label"] for x in span)])
    tsv(out / "ranges.tsv", ["range", "citing_unit", "file", "line", "first", "last", "first_printed",
                             "last_printed", "spanned", "spanned_kinds", "spanned_labels"], rrows)
    # lemma-level graph
    logical = lambda lab: lab in L and L[lab]["kind"] in sc.statement_envs and L[lab]["kind"] not in sc.nonlogical  # noqa: E731
    adj: dict[str, set[str]] = collections.defaultdict(set)
    edge_info: dict[tuple[str, str], collections.Counter] = collections.defaultdict(collections.Counter)
    for c in sc.cites:
        if c["context"] not in ("proof", "statement") or c["label"] not in L:
            continue
        src = sc.statement_of_frame(c["frame"], c["context"])
        dst = c["label"] if logical(c["label"]) else sc.owner_of(L[c["label"]])
        if not src or not dst or src == dst or not logical(src) or not logical(dst):
            continue
        adj[src].add(dst)
        edge_info[(src, dst)][c["context"]] += 1
    order = {k: v["order"] for k, v in L.items()}
    tsv(out / "edges.tsv", ["from", "to", "from_unit", "to_unit", "cross_unit", "in_proof", "in_statement"],
        [[s, d, un(L[s]["unit"]), un(L[d]["unit"]), "yes" if un(L[s]["unit"]) != un(L[d]["unit"]) else "no",
          cnt["proof"], cnt["statement"]] for (s, d), cnt in sorted(edge_info.items(), key=lambda kv: (order[kv[0][0]], order[kv[0][1]]))])
    nodes = sorted(set(adj) | {d for ds in adj.values() for d in ds}, key=lambda x: order.get(x, 0))
    comps = tarjan(nodes, adj)
    crow = []
    for comp in comps:
        for cyc in simple_cycles(comp, adj, order, a.max_cycles - len(crow)):
            units = []
            for lab in cyc[:-1]:
                u = un(L[lab]["unit"])
                if u not in units:
                    units.append(u)
            crow.append([f"Y{len(crow) + 1}", len(cyc) - 1, " -> ".join(cyc), ", ".join(units),
                         "yes" if len(units) > 1 else "no",
                         ", ".join("/".join(k for k in ("proof", "statement") if edge_info[(x, y)][k])
                                   for x, y in zip(cyc, cyc[1:]))])
            if len(crow) >= a.max_cycles:
                break
    tsv(out / "cycles.tsv", ["cycle", "length", "cycle_path", "units", "crosses_units", "edge_contexts"], crow)
    tsv(out / "labels.tsv", ["label", "kind", "unit", "file", "line", "where", "owner", "printed"],
        [[r["label"], r["kind"], un(r["unit"]), r["file"], r["line"], r["where"], sc.owner_of(r),
          numbers.get(r["label"], "")] for r in by_order])
    tsv(out / "unresolved.tsv", ["problem", "label", "at", "also_at"], unresolved)
    for msg in sc.missing_inputs:
        print(f"cross_refs: warning: input not found: {msg}", file=sys.stderr)
    n_undef = sum(1 for u in unresolved if u[0] == "UNDEFINED")
    print(f"cross_refs: {n_cross} cross-unit citations ({n_proof} in proofs) over {len(pairs)} unit pairs; "
          f"{len(sc.ranges)} range citation(s); {len(crow)} candidate cycle(s) in {len(comps)} component(s); "
          f"{n_undef} undefined, {len(sc.duplicates)} duplicate label(s); {len(L)} labels; "
          f"aux {'read' if numbers else 'not used'}; tables in {out}")
    return 1 if unresolved else 0


if __name__ == "__main__":
    sys.exit(main())
