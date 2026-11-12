#!/usr/bin/env python3
"""Measure words and references in theorem-like environments against targets and caps.

Usage:
  check_shape.py [options] FILE [FILE ...]
  check_shape.py [options] --root main.tex      (every active input reachable from main.tex)

Works on .tex files and on Markdown files whose statements are raw LaTeX environments
(a statement spine). Exit status: 0 no cap exceeded, 1 a cap exceeded, 2 usage or input error.

Counting rule (keep it fixed for a whole campaign, so that numbers stay comparable):
  1. The body is the text between \\begin{ENV} and the matching \\end{ENV}. The optional
     [title] right after \\begin{ENV} is not counted. Starred variants count as ENV.
  2. TeX comments (an unescaped % to the end of the line) and every \\label{...} are removed.
  3. Every control word (\\frac, \\alpha, \\mathbb, ...) is replaced by a space, and so is each
     of the characters { } $ \\ & _ ^ .
  4. The remaining whitespace-separated tokens are counted. Formulas count as their tokens:
     "$\\sup_{x\\in B}|u(x)|\\le C$" counts 4 tokens (x, B, |u(x)|, C).

References: \\ref, \\eqref, \\autoref, \\nameref, \\pageref, \\vref, \\cpageref count once each;
\\cref, \\Cref, \\labelcref count once per label of their comma list; \\crefrange and \\Crefrange
count once. Matches of --tag-regex (statement tags such as "Q3") count too, outside the
arguments of reference, label and citation commands. Two references, or two tags, joined only
by "--", "-" or an en dash form a range and count once. Citations (\\cite) are not counted.
"""
import argparse
import json
import os
import re
import sys

DEFAULT_ENVS = {
    "theorem": (100, 150, 4),
    "proposition": (100, 150, 4),
    "lemma": (100, 150, 4),
    "corollary": (100, 150, 4),
    "definition": (120, 200, 6),
}
DEFAULT_MAIN_ENVS = ["maintheorem"]
DEFAULT_MAIN = (200, 250, 8)

REF_CMD = re.compile(
    r"\\(ref|eqref|autoref|nameref|pageref|vref|cpageref|cref|Cref|labelcref|crefrange|Crefrange)"
    r"\*?\{([^{}]*)\}(\{[^{}]*\})?")
STRIP_ARGS = re.compile(
    r"\\(?:ref|eqref|autoref|nameref|pageref|vref|cpageref|cref|Cref|labelcref|crefrange|Crefrange"
    r"|label|cite[a-zA-Z]*|nocite|begin|end|hyperref)\*?(?:\[[^\]]*\])*(?:\{[^{}]*\})+")
RANGE_JOIN = re.compile(r"^\s*(?:--|-|\u2013)\s*$")
COMMENT = re.compile(r"(?<!\\)%.*")
LABEL = re.compile(r"\\label\{[^{}]*\}")
WORD_STRIP = re.compile(r"\\[a-zA-Z]+|[{}$\\&_^]")


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
    for m in re.finditer(r"\\(?:input|include)\{([^{}]+)\}", text):
        name = m.group(1).strip()
        if not name.endswith(".tex"):
            name += ".tex"
        active_inputs(os.path.join(base, name), seen, allow_missing)
    return seen


def parse_triple(spec, what):
    parts = spec.split("/")
    if len(parts) != 3 or not all(p.strip().isdigit() for p in parts):
        raise ValueError(f"{what}: expected TARGET/CAP/REFCAP, got {spec!r}")
    return tuple(int(p) for p in parts)


def load_config(args):
    envs = dict(DEFAULT_ENVS)
    main_envs = list(DEFAULT_MAIN_ENVS)
    main = DEFAULT_MAIN
    tag_regex = None
    cfg_path = args.config or os.environ.get("ENSLOP_SHAPE_CONFIG")
    if cfg_path:
        with open(cfg_path, encoding="utf-8") as fh:
            cfg = json.load(fh)
        if "environments" in cfg:
            envs = {k: (v["target"], v["cap"], v["refcap"]) for k, v in cfg["environments"].items()}
        if "main_environments" in cfg:
            main_envs = list(cfg["main_environments"])
        if "main" in cfg:
            m = cfg["main"]
            main = (m["target"], m["cap"], m["refcap"])
        tag_regex = cfg.get("tag_regex") or None
    for spec in args.env or []:
        name, _, triple = spec.partition("=")
        envs[name.strip()] = parse_triple(triple, "--env")
    for name in args.main_env or []:
        if name not in main_envs:
            main_envs.append(name)
    if args.main_caps:
        main = parse_triple(args.main_caps, "--main-caps")
    if args.tag_regex is not None:
        tag_regex = args.tag_regex or None
    limits = {name: envs[name] for name in envs}
    for name in main_envs:
        limits[name] = main
    return limits, set(main_envs), (re.compile(tag_regex) if tag_regex else None)


def skip_title(text, pos):
    """Return (title, position after the optional [title]) starting at pos."""
    i = pos
    while i < len(text) and text[i] in " \t":
        i += 1
    if i >= len(text) or text[i] != "[":
        return "", pos
    depth, j = 0, i + 1
    while j < len(text):
        c = text[j]
        if c == "\\":
            j += 2
            continue
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
        elif c == "]" and depth == 0:
            return text[i + 1:j], j + 1
        j += 1
    return "", pos


def count_words(body):
    body = "\n".join(COMMENT.sub("", line) for line in body.splitlines())
    body = LABEL.sub(" ", body)
    return len(WORD_STRIP.sub(" ", body).split())


def merge_ranges(spans, text):
    """spans: sorted list of (start, end, weight); joined pairs count once."""
    total = sum(w for _, _, w in spans)
    for (s1, e1, _), (s2, e2, _) in zip(spans, spans[1:]):
        if RANGE_JOIN.match(text[e1:s2]):
            total -= 1
    return total


def count_refs(body, tag_re):
    body = "\n".join(COMMENT.sub("", line) for line in body.splitlines())
    body = LABEL.sub(" ", body)
    spans = []
    for m in REF_CMD.finditer(body):
        cmd, arg = m.group(1), m.group(2)
        if cmd in ("cref", "Cref", "labelcref"):
            weight = len([a for a in arg.split(",") if a.strip()])
        else:
            weight = 1
        spans.append((m.start(), m.end(), weight))
    n = merge_ranges(spans, body)
    if tag_re is not None:
        plain = STRIP_ARGS.sub(lambda m: " " * len(m.group(0)), body)
        tags = [(m.start(), m.end(), 1) for m in tag_re.finditer(plain)]
        n += merge_ranges(tags, plain)
    return n


def measure(path, limits, main_envs, tag_re):
    with open(path, encoding="utf-8", errors="replace") as fh:
        text = fh.read()
    names = sorted(limits, key=len, reverse=True)
    begin = re.compile(r"\\begin\{(" + "|".join(re.escape(n) for n in names) + r")(\*?)\}")
    out, problems = [], []
    for m in begin.finditer(text):
        env, star = m.group(1), m.group(2)
        title, start = skip_title(text, m.end())
        end_tag = "\\end{" + env + star + "}"
        end = text.find(end_tag, start)
        line = text.count("\n", 0, m.start()) + 1
        if end < 0:
            problems.append(f"UNTERMINATED  {path}:{line} {env}: no {end_tag}")
            continue
        body = text[start:end]
        target, cap, refcap = limits[env]
        rec = {
            "file": path, "line": line, "env": env, "title": " ".join(title.split())[:60],
            "main": env in main_envs, "words": count_words(body), "target": target, "cap": cap,
            "refs": count_refs(body, tag_re), "refcap": refcap,
        }
        status = []
        if rec["words"] > cap:
            status.append("over-cap")
        elif rec["words"] > target:
            status.append("over-target")
        if rec["refs"] > refcap:
            status.append("too-many-refs")
        rec["status"] = ",".join(status) or "ok"
        out.append(rec)
    return out, problems


def main():
    ap = argparse.ArgumentParser(
        description="Count words and references in statement, definition and main-theorem "
                    "environments of TeX (or Markdown with raw LaTeX environments) and compare "
                    "them with targets and caps. Exit 1 if any cap is exceeded.",
        epilog="""defaults: theorem/proposition/lemma/corollary target 100, cap 150, at most 4
references; definition 120/200/6; main theorems (environment maintheorem) 200/250/8. These are
this collection's defaults (the word caps and the four-reference cap are the published caps of the
Yang-Mills campaign, 2026); change them with --config or --env.

example (the Yang-Mills tags; ranges such as Q0--Q6 count once):
  check_shape.py --root main.tex \\
    --tag-regex '\\b(?:RG|MT|UB|UV|IV|FC|MC|ST|SC|PH|RC|TR|NF|OP|CT|Q[0-6]|B[1-6]|E[1-7]|W[0-3])\\b'
  check_shape.py --env thm=100/150/4 --main-env mainthm --json part2/*.tex
The counting rule is stated in the docstring at the top of this file.""",
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("files", nargs="*", help="TeX or Markdown files to measure")
    ap.add_argument("--root", help="root TeX file: measure every active \\input/\\include from it")
    ap.add_argument("--allow-missing", action="store_true", help="warn instead of failing on a missing input")
    ap.add_argument("--config", help="JSON config (environments, main_environments, main, tag_regex); "
                                     "default from $ENSLOP_SHAPE_CONFIG")
    ap.add_argument("--env", action="append", metavar="NAME=TARGET/CAP/REFCAP",
                    help="add or replace a statement environment's limits (repeatable)")
    ap.add_argument("--main-env", action="append", metavar="NAME", help="add a main-theorem environment (repeatable)")
    ap.add_argument("--main-caps", metavar="TARGET/CAP/REFCAP", help="limits for main theorems (default 200/250/8)")
    ap.add_argument("--tag-regex", help="regex for statement tags counted as references ('' disables)")
    ap.add_argument("--json", action="store_true", help="print one JSON document instead of text lines")
    ap.add_argument("--list", action="store_true", help="also list every environment (TSV), not only problems")
    args = ap.parse_args()

    try:
        limits, main_envs, tag_re = load_config(args)
        files = list(args.files)
        if args.root:
            files += active_inputs(args.root, allow_missing=args.allow_missing)
        if not files:
            ap.print_usage(sys.stderr)
            print("check_shape: no input files", file=sys.stderr)
            return 2
        records, problems = [], []
        for f in files:
            r, p = measure(f, limits, main_envs, tag_re)
            records += r
            problems += p
    except (OSError, ValueError, KeyError, re.error, json.JSONDecodeError) as exc:
        print(f"check_shape: input error: {exc}", file=sys.stderr)
        return 2

    over_cap = [r for r in records if "over-cap" in r["status"]]
    over_ref = [r for r in records if "too-many-refs" in r["status"]]
    over_target = [r for r in records if "over-target" in r["status"]]
    summary = (f"shape: {len(records)} environments, {len(over_cap)} over word cap, "
               f"{len(over_ref)} over reference cap, {len(over_target)} over target")
    if args.json:
        print(json.dumps({"environments": records, "problems": problems, "summary": summary}, indent=1))
    else:
        if args.list:
            print("file\tline\tenv\ttitle\twords\ttarget\tcap\trefs\trefcap\tstatus")
            for r in records:
                print("\t".join(str(r[k]) for k in
                                ("file", "line", "env", "title", "words", "target", "cap", "refs", "refcap", "status")))
        for p in problems:
            print(p)
        for r in records:
            where = f"{r['file']}:{r['line']} {r['env']} [{r['title']}]"
            if "over-cap" in r["status"]:
                print(f"OVER CAP  {where}: {r['words']} words (cap {r['cap']})")
            elif "over-target" in r["status"]:
                print(f"over target  {where}: {r['words']} words (target {r['target']})")
            if "too-many-refs" in r["status"]:
                print(f"TOO MANY REFERENCES  {where}: {r['refs']} (cap {r['refcap']}): a statement must state, not list")
        print(summary)
    if problems:
        return 2
    return 1 if (over_cap or over_ref) else 0


if __name__ == "__main__":
    sys.exit(main())
