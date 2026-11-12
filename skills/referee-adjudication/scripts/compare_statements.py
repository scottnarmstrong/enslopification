#!/usr/bin/env python3
"""Check that a pass changed no statement and removed no label: compare two versions of a TeX source.

Usage:
  compare_statements.py OLD NEW [--envs auto|ENV,ENV,...] [--labels LABEL,LABEL,...]
                        [--ignore-space] [--strip-comments] [--diff] [--allow-label-changes]

OLD and NEW are each a .tex file or a directory (every *.tex file below it). The text of every
statement environment (between \\begin{ENV} and its \\end{ENV}) is compared byte for byte, matched
by its \\label; unlabelled statements are compared as a multiset of texts. The set of all \\label
keys is compared too.

--envs auto (the default) takes every environment declared by \\newtheorem in either version, plus
maintheorem (the main-theorem environment of the collection's spine templates), theorem, proposition,
lemma, corollary and definition; or give a comma-separated list, which replaces them.
--labels restricts the statement comparison to these labels (e.g. the main theorems) and requires
each of them on both sides; the label-set comparison still covers everything.
--ignore-space collapses runs of white space; --strip-comments removes TeX comments first (the
default is an exact byte comparison, comments included).

Reports CHANGED, REMOVED and ADDED statements, LABEL-REMOVED and LABEL-ADDED keys, then a summary.
Exit status: 0 nothing changed or removed (added statements and labels are allowed), 1 a statement
changed or disappeared or a label disappeared (with --allow-label-changes, label differences are
reported but do not fail), 2 usage or input error.
"""
import argparse
import collections
import difflib
import os
import re
import sys

DEFAULT_ENVS = ["maintheorem", "theorem", "proposition", "lemma", "corollary", "definition"]
COMMENT = re.compile(r"(?<!\\)%.*")
NEWTHEOREM = re.compile(r"\\newtheorem\s*\{([A-Za-z@]+)\}")
LABEL = re.compile(r"\\label\s*\{([^}]*)\}")


def read_sources(path):
    """Return {relative path: text} for a file or every *.tex file below a directory."""
    if os.path.isfile(path):
        files = {os.path.basename(path): path}
    elif os.path.isdir(path):
        files = {}
        for root, dirs, names in os.walk(path):
            dirs.sort()
            for n in sorted(names):
                if n.endswith(".tex"):
                    full = os.path.join(root, n)
                    files[os.path.relpath(full, path)] = full
    else:
        print(f"compare_statements: no such file or directory: {path}", file=sys.stderr)
        sys.exit(2)
    out = {}
    for rel, full in files.items():
        try:
            with open(full, encoding="utf-8") as fh:
                out[rel] = fh.read()
        except (OSError, UnicodeDecodeError) as e:
            print(f"compare_statements: cannot read {full}: {e}", file=sys.stderr)
            sys.exit(2)
    return out


def strip_comments(text):
    return "\n".join(COMMENT.sub("", line) for line in text.split("\n"))


def mask_comments(text):
    """Blank out TeX comments, keeping every offset, so commented-out environments are ignored."""
    return "\n".join(COMMENT.sub(lambda m: " " * len(m.group(0)), line) for line in text.split("\n"))


def statements(text, envs):
    """Yield (env, label or None, body, line) for every environment in envs (bodies taken from the raw text)."""
    pattern = re.compile(r"\\(begin|end)\s*\{(" + "|".join(re.escape(e) for e in envs) + r")\}")
    stack = []
    for m in pattern.finditer(mask_comments(text)):
        kind, env = m.group(1), m.group(2)
        if kind == "begin":
            stack.append((env, m.end(), text.count("\n", 0, m.start()) + 1))
        else:
            for k in range(len(stack) - 1, -1, -1):
                if stack[k][0] == env:
                    _, start, line = stack.pop(k)
                    del stack[k:]
                    body = text[start:m.start()]
                    yield env, first_label(body), body, line
                    break


def first_label(body):
    """The statement's own label: the first \\label before any nested environment, else the first one."""
    head = re.split(r"\\begin\s*\{", body, maxsplit=1)[0]
    m = LABEL.search(strip_comments(head)) or LABEL.search(strip_comments(body))
    return m.group(1).strip() if m else None


def collect(sources, envs, args):
    labelled, unlabelled, labels, dup = {}, collections.Counter(), set(), []
    for rel, text in sources.items():
        labels.update(k.strip() for k in LABEL.findall(strip_comments(text)))
        if args.strip_comments:
            text = strip_comments(text)
        for env, label, body, line in statements(text, envs):
            if args.ignore_space:
                body = re.sub(r"\s+", " ", body).strip()
            if label is None:
                unlabelled[(env, body)] += 1
            elif label in labelled:
                dup.append(label)
            else:
                labelled[label] = (env, body, f"{rel}:{line}")
    return labelled, unlabelled, labels, dup


def main():
    ap = argparse.ArgumentParser(
        description="Compare the statement environments and \\label keys of two versions of a TeX source; "
                    "fail if a statement changed or disappeared or a label disappeared.",
        epilog="Examples:\n"
               "  compare_statements.py approved/ manuscript/                  # whole text, after a typography pass\n"
               "  compare_statements.py approved/main-theorems.tex manuscript/ --labels thm:main,thm:formal\n",
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("old", help="the earlier version (file or directory)")
    ap.add_argument("new", help="the later version (file or directory)")
    ap.add_argument("--envs", default="auto",
                    help="statement environments: 'auto' (\\newtheorem declarations plus "
                         f"{', '.join(DEFAULT_ENVS)}) or a comma-separated list")
    ap.add_argument("--labels", help="compare only these statement labels (comma-separated); each must exist on both sides")
    ap.add_argument("--ignore-space", action="store_true", help="collapse white space before comparing")
    ap.add_argument("--strip-comments", action="store_true", help="remove TeX comments before comparing")
    ap.add_argument("--diff", action="store_true", help="print a unified diff of each changed statement")
    ap.add_argument("--allow-label-changes", action="store_true", help="report label differences without failing")
    args = ap.parse_args()

    old_src, new_src = read_sources(args.old), read_sources(args.new)
    if args.envs == "auto":
        declared = set()
        for text in list(old_src.values()) + list(new_src.values()):
            declared.update(NEWTHEOREM.findall(strip_comments(text)))
        envs = sorted(set(DEFAULT_ENVS) | declared)
    else:
        envs = [e.strip() for e in args.envs.split(",") if e.strip()]
        if not envs:
            ap.error("--envs is empty")

    old_l, old_u, old_labels, old_dup = collect(old_src, envs, args)
    new_l, new_u, new_labels, new_dup = collect(new_src, envs, args)
    failures, notes = [], []
    for side, dup in (("old", old_dup), ("new", new_dup)):
        for d in dup:
            notes.append(f"DUPLICATE-LABEL ({side}) {d}")

    only = None
    if args.labels:
        only = [x.strip() for x in args.labels.split(",") if x.strip()]
        for lab in only:
            if lab not in old_l:
                failures.append(f"MISSING-OLD {lab} (no statement with this label in {args.old})")
            if lab not in new_l:
                failures.append(f"REMOVED {lab} (no statement with this label in {args.new})")

    keys = only if only is not None else sorted(old_l)
    changed = removed = 0
    for lab in keys:
        if lab not in old_l or lab not in new_l:
            if only is None and lab in old_l:
                failures.append(f"REMOVED {lab} ({old_l[lab][0]}, {old_l[lab][2]})")
                removed += 1
            continue
        (oe, ob, oloc), (ne, nb, nloc) = old_l[lab], new_l[lab]
        if ob != nb or oe != ne:
            changed += 1
            failures.append(f"CHANGED {lab} ({oe} at {oloc} -> {ne} at {nloc})")
            if args.diff:
                for d in difflib.unified_diff(ob.split("\n"), nb.split("\n"), f"old {lab}", f"new {lab}", lineterm=""):
                    print(d)
    added = [lab for lab in sorted(new_l) if lab not in old_l] if only is None else []
    for lab in added:
        notes.append(f"ADDED {lab} ({new_l[lab][0]}, {new_l[lab][2]})")

    if only is None:
        lost = old_u - new_u
        for (env, body), n in sorted(lost.items()):
            first = body.strip().split("\n")[0][:70]
            failures.append(f"CHANGED-UNLABELLED {env} x{n}: {first!r}")
            changed += n

    label_issues = []
    for lab in sorted(old_labels - new_labels):
        label_issues.append(f"LABEL-REMOVED {lab}")
    for lab in sorted(new_labels - old_labels):
        notes.append(f"LABEL-ADDED {lab}")
    if args.allow_label_changes:
        notes.extend(label_issues)
    else:
        failures.extend(label_issues)

    for line in failures:
        print(line)
    for line in notes:
        print(line)
    compared = len(keys) + (sum(old_u.values()) if only is None else 0)
    status = "FAILED" if failures else "ok"
    print(f"compare_statements: {compared} statement(s) compared ({', '.join(envs)}); {changed} changed, "
          f"{removed} removed, {len(added)} added; labels {len(old_labels)} -> {len(new_labels)} "
          f"({len(old_labels - new_labels)} removed, {len(new_labels - old_labels)} added) -> {status}")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
