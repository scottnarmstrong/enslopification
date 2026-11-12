#!/usr/bin/env python3
"""Reject manuscript TeX containing banned words, process words, file paths or Lean names.

Usage:
  check_vocabulary.py [options] --root main.tex     (every active \\input/\\include from main.tex)
  check_vocabulary.py [options] FILE [FILE ...]

Every line is scanned, TeX comments included (comments travel with the source). Before
matching, the arguments of reference, label, citation, input and URL commands and all remaining
control words are blanked, so labels, file names in \\input and macro names do not count.

Pattern lists: one Python regex per line in CATEGORY.txt files ("#" starts a comment line; a
line "#!ignorecase" makes the whole file case-insensitive). Every *.txt file of the wordlist
directory is a category, except allow.txt, whose regexes mark allowed phrases: a hit lying
inside an allowed match on the same line is dropped (e.g. "spectral gap"). Default directory:
$ENSLOP_WORDLISTS, else ../assets/wordlists next to this script.

Exception regions: lines strictly between a line containing the begin marker and a line
containing the end marker (both normally TeX comments) are exempt from the categories named
by --except (default: process-words). Marker lines themselves are not scanned. A region
that is unterminated, nested, or longer than --max-region-lines is reported as a failure.

Output: file:line:category:match for each hit, then a one-line summary.
Exit status: 0 no hit, 1 hits or a bad exception region, 2 usage or input error.
"""
import argparse
import glob
import os
import re
import sys

COMMENT = re.compile(r"(?<!\\)%.*")
IGNORED_COMMANDS = ["label", "ref", "eqref", "cref", "Cref", "autoref", "pageref", "nameref", "vref",
                    "labelcref", "crefrange", "Crefrange", "cite", "citep", "citet", "citealp", "citeauthor",
                    "nocite", "input", "include", "includegraphics", "usepackage", "RequirePackage",
                    "documentclass", "bibliography", "bibliographystyle", "url", "href", "hyperref",
                    "begin", "end", "newlabel"]


def active_inputs(root, seen=None, allow_missing=False):
    """Files reachable from root through \\input or \\include outside comments."""
    seen = [] if seen is None else seen
    path = os.path.normpath(root)
    if path in seen:
        return seen
    if not os.path.exists(path):
        if allow_missing:
            print(f"warning: missing input {path}", file=sys.stderr)
            return seen
        raise FileNotFoundError(path)
    seen.append(path)
    base = os.path.dirname(seen[0])
    with open(path, encoding="utf-8", errors="replace") as fh:
        text = "\n".join(COMMENT.sub("", line) for line in fh.read().splitlines())
    for m in re.finditer(r"\\(?:input|include|subfile)\{([^{}]+)\}", text):
        name = m.group(1).strip()
        if not name.endswith(".tex"):
            name += ".tex"
        active_inputs(os.path.join(base, name), seen, allow_missing)
    return seen


def read_patterns(path):
    flags, pats = 0, []
    with open(path, encoding="utf-8") as fh:
        lines = fh.read().splitlines()
    for ln in lines:
        s = ln.strip()
        if s == "#!ignorecase":
            flags = re.IGNORECASE
    for n, ln in enumerate(lines, 1):
        s = ln.strip()
        if not s or s.startswith("#"):
            continue
        try:
            pats.append(re.compile(s, flags))
        except re.error as exc:
            raise ValueError(f"{path}:{n}: bad regex {s!r}: {exc}")
    return pats


def load_lists(args):
    cats, allow = {}, []
    if not args.no_default_lists:
        d = args.wordlists or os.environ.get("ENSLOP_WORDLISTS") or os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "..", "assets", "wordlists")
        if not os.path.isdir(d):
            raise FileNotFoundError(f"wordlist directory {d}")
        for f in sorted(glob.glob(os.path.join(d, "*.txt"))):
            stem = os.path.splitext(os.path.basename(f))[0]
            if stem == "allow":
                allow += read_patterns(f)
            else:
                cats.setdefault(stem, []).extend(read_patterns(f))
    for spec in args.patterns or []:
        cat, _, f = spec.partition("=")
        if not f:
            raise ValueError(f"--patterns expects CATEGORY=FILE, got {spec!r}")
        cats.setdefault(cat, []).extend(read_patterns(f))
    for f in args.allow or []:
        allow += read_patterns(f)
    if args.lean_namespace:
        alt = "|".join(re.escape(ns) for ns in args.lean_namespace)
        cats.setdefault("lean-names", []).append(re.compile(r"\b(?:" + alt + r")\.[A-Za-z_][\w.']*"))
    if not cats:
        raise ValueError("no pattern categories loaded")
    return cats, allow


def blanker(ignored):
    """Return a function that blanks ignored commands with their arguments, then every
    remaining control word, keeping column positions."""
    cmd = re.compile(r"\\(?:" + "|".join(map(re.escape, ignored)) + r")\*?(?:\[[^\]]*\])*(?:\{[^{}]*\}){1,2}")
    word = re.compile(r"\\[A-Za-z@]+")

    def spaces(m):
        return " " * len(m.group(0))
    return lambda line: word.sub(spaces, cmd.sub(spaces, line))


def scan(path, cats, allow, args, blank, out):
    hits, regions, problems = 0, 0, []
    in_region, region_start = False, 0
    with open(path, encoding="utf-8", errors="replace") as fh:
        lines = fh.read().splitlines()
    for n, raw in enumerate(lines, 1):
        if args.begin_marker in raw:
            if in_region:
                problems.append(f"{path}:{n}:exception-region:nested begin marker")
            in_region, region_start = True, n
            regions += 1
            continue
        if args.end_marker in raw:
            if not in_region:
                problems.append(f"{path}:{n}:exception-region:end marker without begin")
            elif n - region_start - 1 > args.max_region_lines:
                problems.append(f"{path}:{region_start}:exception-region:{n - region_start - 1} lines "
                                f"(more than {args.max_region_lines})")
            in_region = False
            continue
        text = blank(raw)
        allowed = [m.span() for a in allow for m in a.finditer(text)]
        found = []
        for cat, pats in cats.items():
            if in_region and cat in args.except_categories:
                continue
            for pat in pats:
                for m in pat.finditer(text):
                    if m.group(0).strip() and not any(a0 <= m.start() and m.end() <= a1 for a0, a1 in allowed):
                        found.append((m.start(), -m.end(), cat, m.group(0).strip()))
        kept = []
        for start, neg_end, cat, word in sorted(found):
            if any(k0 <= start and -neg_end <= k1 for k0, k1 in kept):
                continue  # inside a hit already reported on this line
            kept.append((start, -neg_end))
            out.append(f"{path}:{n}:{cat}:{word}")
            hits += 1
    if in_region:
        problems.append(f"{path}:{region_start}:exception-region:begin marker without end")
    return hits, regions, problems


def main():
    ap = argparse.ArgumentParser(
        description="Scan manuscript TeX (comments included) for banned words, habitual machine "
                    "phrasing, process words, file paths and Lean names. Exit 1 on any hit.",
        epilog="""examples:
  check_vocabulary.py --root main.tex --lean-namespace YM --lean-namespace YangMills
  check_vocabulary.py part2/section.tex --begin-marker BEGIN-VERIFICATION-PARAGRAPH \\
      --end-marker END-VERIFICATION-PARAGRAPH        (the markers of the Yang-Mills manuscript)
  check_vocabulary.py --no-default-lists --patterns process=my-process.txt draft.tex
Shipped lists: banned-words (copied from latex-math-writing), habitual-phrasing, process-words,
file-paths, lean-names, and allow.txt.""",
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("files", nargs="*", help="TeX files to scan")
    ap.add_argument("--root", help="root TeX file: scan every active \\input/\\include from it")
    ap.add_argument("--allow-missing", action="store_true", help="warn instead of failing on a missing input")
    ap.add_argument("--wordlists", help="directory of CATEGORY.txt pattern files (default $ENSLOP_WORDLISTS "
                                        "or the shipped lists)")
    ap.add_argument("--no-default-lists", action="store_true", help="load no directory; use only --patterns")
    ap.add_argument("--patterns", action="append", metavar="CATEGORY=FILE", help="add a pattern file (repeatable)")
    ap.add_argument("--allow", action="append", metavar="FILE", help="add an allow-pattern file (repeatable)")
    ap.add_argument("--lean-namespace", action="append", metavar="NS",
                    help="flag NS.Name as a Lean name (repeatable), e.g. YM")
    ap.add_argument("--begin-marker", default="BEGIN-DISCLOSURE", help="begin marker (default %(default)s)")
    ap.add_argument("--end-marker", default="END-DISCLOSURE", help="end marker (default %(default)s)")
    ap.add_argument("--except", dest="except_categories", action="append", metavar="CATEGORY",
                    help="category exempt inside exception regions (repeatable; default process-words)")
    ap.add_argument("--max-region-lines", type=int, default=25, help="longest exception region (default 25)")
    ap.add_argument("--ignore-command", action="append", metavar="CMD",
                    help="also blank \\CMD{...} before matching (repeatable)")
    args = ap.parse_args()
    if not args.except_categories:
        args.except_categories = ["process-words"]

    try:
        cats, allow = load_lists(args)
        files = list(args.files)
        if args.root:
            files += active_inputs(args.root, allow_missing=args.allow_missing)
        if not files:
            ap.print_usage(sys.stderr)
            print("check_vocabulary: no input files", file=sys.stderr)
            return 2
        blank = blanker(IGNORED_COMMANDS + (args.ignore_command or []))
        out, hits, regions, problems = [], 0, 0, []
        for f in files:
            h, r, p = scan(f, cats, allow, args, blank, out)
            hits, regions, problems = hits + h, regions + r, problems + p
    except (OSError, ValueError) as exc:
        print(f"check_vocabulary: input error: {exc}", file=sys.stderr)
        return 2
    for line in out + problems:
        print(line)
    print(f"vocabulary: {hits} hit(s) in {len(files)} file(s); {regions} exception region(s), "
          f"{len(problems)} region problem(s); categories: {', '.join(sorted(cats))}")
    return 1 if (hits or problems) else 0


if __name__ == "__main__":
    sys.exit(main())
