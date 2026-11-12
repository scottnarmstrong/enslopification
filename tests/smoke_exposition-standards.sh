#!/usr/bin/env bash
# Smoke test of the exposition-standards scripts on small synthetic inputs.
# Usage: tests/smoke_exposition-standards.sh   (exit 0 if every check passes)
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
S="$ROOT/skills/exposition-standards/scripts"
A="$ROOT/skills/exposition-standards/assets"
PY="${ENSLOP_PYTHON:-python3}"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
pass=0

fail() { echo "FAIL: $*"; [ -f "$tmp/out" ] && sed 's/^/    /' "$tmp/out" | head -20; exit 1; }
# expect CODE DESCRIPTION -- command...   (stdout and stderr saved in $tmp/out)
expect() {
  local want="$1" what="$2"; shift 3
  set +e; "$@" > "$tmp/out" 2>&1; local rc=$?; set -e
  [ "$rc" -eq "$want" ] || fail "$what: exit $rc, expected $want"
  pass=$((pass + 1)); echo "ok: $what"
}
has() { grep -q -- "$1" "$tmp/out" || fail "output lacks '$1'"; }
hasnot() { if grep -q -- "$1" "$tmp/out"; then fail "output has '$1'"; fi; }

# --- help
for s in check_shape.py check_vocabulary.py page_report.py; do
  expect 0 "$s --help" -- "$PY" -I "$S/$s" --help
done
expect 0 "check_section.sh -h" -- bash "$S/check_section.sh" -h

# --- shape
words() { "$PY" -c "print(' '.join('w%d' % i for i in range($1)))"; }
cat > "$tmp/ok.tex" <<EOF
\\begin{lemma}[Short]\\label{lem:a}
For every \$x\\in B\$ we have \$\\sup_{x\\in B}|u(x)|\\le C\$. % comment words not counted here at all
\\end{lemma}
\\begin{definition}
By Lemmas~\\ref{a}--\\ref{b}, \\ref{c}, \\eqref{d}, \\cref{e,f} and \\ref{g}, set \$E=0\$.
\\end{definition}
EOF
expect 0 "shape: statements under caps (a range counts once; 6 refs allowed in a definition)" -- "$PY" -I "$S/check_shape.py" "$tmp/ok.tex"
has "2 environments, 0 over word cap, 0 over reference cap"
printf '\\begin{theorem*}\n%s\n\\end{theorem*}\n' "$(words 160)" > "$tmp/long.tex"
expect 1 "shape: theorem over the 150-word cap" -- "$PY" -I "$S/check_shape.py" "$tmp/long.tex"
has "OVER CAP"
printf '\\begin{proposition}\nBy \\ref{a}, \\ref{b}, \\ref{c}, \\ref{d} and \\ref{e} it holds.\n\\end{proposition}\n' > "$tmp/refs.tex"
expect 1 "shape: five references in a proposition" -- "$PY" -I "$S/check_shape.py" "$tmp/refs.tex"
has "TOO MANY REFERENCES"
printf '\\begin{maintheorem}\nThe conclusions RG, MT, UB, UV, IV, FC, MC, ST and SC hold.\n\\end{maintheorem}\n' > "$tmp/main.tex"
expect 0 "shape: tags not counted without a tag regex" -- "$PY" -I "$S/check_shape.py" "$tmp/main.tex"
expect 1 "shape: nine tags in a main theorem with the example config" -- "$PY" -I "$S/check_shape.py" --config "$A/shape-config.example.json" "$tmp/main.tex"
has "TOO MANY REFERENCES"
printf '\\begin{maintheorem}\nThe axioms Q0--Q6 hold.\n\\end{maintheorem}\n' > "$tmp/range.tex"
expect 0 "shape: a tag range counts once" -- "$PY" -I "$S/check_shape.py" --config "$A/shape-config.example.json" --list "$tmp/range.tex"
grep -q $'maintheorem\t\t4\t200\t250\t1\t8' "$tmp/out" || fail "range not counted once"
printf '\\begin{thm}\n%s\n\\end{thm}\n' "$(words 120)" > "$tmp/thm.tex"
expect 1 "shape: --env adds an environment" -- "$PY" -I "$S/check_shape.py" --env thm=50/100/4 "$tmp/thm.tex"
expect 0 "shape: --json is valid JSON" -- "$PY" -I "$S/check_shape.py" --json "$tmp/ok.tex"
"$PY" -c 'import json,sys; d=json.load(open(sys.argv[1])); assert len(d["environments"]) == 2' "$tmp/out" || fail "json"
printf '\\input{part}\n%%\\input{commented}\n' > "$tmp/root.tex"; cp "$tmp/long.tex" "$tmp/part.tex"
expect 1 "shape: --root follows \\input, skips commented inputs" -- "$PY" -I "$S/check_shape.py" --root "$tmp/root.tex"
expect 2 "shape: missing input file" -- "$PY" -I "$S/check_shape.py" "$tmp/nosuch.tex"

# --- vocabulary
cat > "$tmp/v.tex" <<'EOF'
% BEGIN-DISCLOSURE
This paper was written by AI agents from the Lean code of the construction.
% END-DISCLOSURE
The bound follows; the Lean proof agrees. % process word outside the region
By Foo.Bar.baz the estimate is crucial.
See Lemma~\ref{lem:gate} and the spectral gap.
EOF
expect 1 "vocabulary: hits outside the region only" -- "$PY" -I "$S/check_vocabulary.py" --lean-namespace Foo "$tmp/v.tex"
has "v.tex:4:process-words:Lean"
has "v.tex:5:lean-names:Foo.Bar.baz"
has "v.tex:5:habitual-phrasing:crucial"
hasnot "v.tex:2:"
hasnot "gate"
hasnot "gap"
printf '%% BEGIN-DISCLOSURE\nWritten from the Lean code.\n' > "$tmp/open.tex"
expect 1 "vocabulary: unterminated exception region" -- "$PY" -I "$S/check_vocabulary.py" "$tmp/open.tex"
has "begin marker without end"
printf 'We prove the theorem by an energy estimate.\n' > "$tmp/clean.tex"
expect 0 "vocabulary: clean file" -- "$PY" -I "$S/check_vocabulary.py" "$tmp/clean.tex"
printf '\\bwidget\\b\n' > "$tmp/retired.txt"; printf 'A widget appears.\n' > "$tmp/w.tex"
expect 1 "vocabulary: project pattern file" -- "$PY" -I "$S/check_vocabulary.py" --patterns retired=$tmp/retired.txt "$tmp/w.tex"
has "retired:widget"
expect 2 "vocabulary: missing file" -- "$PY" -I "$S/check_vocabulary.py" "$tmp/nosuch.tex"
printf 'The spine and the proposal; an owner review, a fresh reader, prose truth, a delivery review, a response table.\n' > "$tmp/proc.tex"
expect 1 "vocabulary: the process words the documentation names are listed" -- "$PY" -I "$S/check_vocabulary.py" "$tmp/proc.tex"
for w in spine proposal "owner review" "fresh reader" "prose truth" "delivery review" "response table"; do has "process-words:$w"; done
printf 'A bridge of the graph and a spectral gap.\n' > "$tmp/art.tex"
expect 1 "vocabulary: a term of art is a hit until the project allows it" -- "$PY" -I "$S/check_vocabulary.py" "$tmp/art.tex"
has "banned-words:bridge"
printf '# allowed by the author on 2026-01-01\n\\bbridges? of the graph\\b\n' > "$tmp/allow-project.txt"
expect 0 "vocabulary: the project's allow file admits the term of art" -- "$PY" -I "$S/check_vocabulary.py" --allow "$tmp/allow-project.txt" "$tmp/art.tex"

# --- page report on synthetic .toc and .log (no LaTeX needed)
cat > "$tmp/doc.toc" <<'EOF'
\contentsline {section}{\numberline {1}Introduction}{1}{section.1}%
\contentsline {section}{\numberline {2}The {\em first} step}{2}{section.2}%
\contentsline {subsection}{\numberline {2.1}Sub}{3}{subsection.2.1}%
\contentsline {section}{\numberline {3}Infinite volume}{5}{section.3}%
EOF
echo 'Output written on doc.pdf (6 pages, 12345 bytes).' > "$tmp/doc.log"
printf 'key\tpages\tkind\n1\t2\tcap\nfirst step\t2\tguide\n3\t3\tcap\n' > "$tmp/allow.tsv"
expect 0 "pages: guide overrun reported, not failed" -- "$PY" -I "$S/page_report.py" --toc "$tmp/doc.toc" --allowances "$tmp/allow.tsv"
has "over guide"
printf '3\t1\tcap\n' > "$tmp/cap.tsv"
expect 1 "pages: cap overrun fails" -- "$PY" -I "$S/page_report.py" --toc "$tmp/doc.toc" --allowances "$tmp/cap.tsv"
has "OVER"
expect 0 "pages: subsection level with --last-page" -- "$PY" -I "$S/page_report.py" --toc "$tmp/doc.toc" --last-page 6 --level subsection
has "Sub"
expect 2 "pages: example allowances parse; keys foreign to this document are unmatched" -- "$PY" -I "$S/page_report.py" --toc "$tmp/doc.toc" --allowances "$A/allowances.example.tsv"
has "UNMATCHED allowance key 'sec:uv-step'"

# --- standalone compile of one section
mkdir -p "$tmp/ms/part"
cat > "$tmp/ms/main.tex" <<'EOF'
\documentclass[11pt]{article}
\usepackage{amsmath,amsthm,amssymb}
\newtheorem{lemma}{Lemma}[section]
\input{macros}
\begin{document}
\input{part/sec}
\end{document}
EOF
echo '\newcommand{\R}{\mathbb{R}}' > "$tmp/ms/macros.tex"
printf '\\section{Setting}\\label{sec:s}\n\\begin{lemma}\\label{lem:x}\nFor $u\\in\\R$, $u^2\\ge0$ by Lemma~\\ref{lem:elsewhere}.\n\\end{lemma}\n' > "$tmp/ms/part/sec.tex"
expect 0 "section: dry run" -- bash "$S/check_section.sh" -n -m "$tmp/ms/main.tex" "$tmp/ms/part/sec.tex"
has "dry run"
printf '\\section{Broken}\\label{sec:b}\nText with \\undefinedmacro here.\n' > "$tmp/ms/part/undef.tex"
printf '\\section{Other}\\label{sec:v}\nThe Lean code says so.\n' > "$tmp/ms/part/vocab.tex"
# without latexmk nothing is compiled: SKIPPED and exit 3, never PASS (a dry run still exits 0)
mkdir -p "$tmp/bin"
for c in bash env dirname basename grep awk sed mktemp rm cat tail head tr cp mkdir python3; do
  p="$(type -P "$c")" && ln -sf "$p" "$tmp/bin/$c"
done
BASH_BIN="$(type -P bash)"
expect 3 "section: no latexmk: SKIPPED, exit 3 (the undefined macro is not seen)" -- \
  env PATH="$tmp/bin" ENSLOP_PYTHON=python3 "$BASH_BIN" "$S/check_section.sh" -m "$tmp/ms/main.tex" "$tmp/ms/part/undef.tex"
has "check_section: SKIPPED (latexmk not found"
hasnot "PASS"
expect 1 "section: no latexmk, a failing text check: FAIL" -- \
  env PATH="$tmp/bin" ENSLOP_PYTHON=python3 "$BASH_BIN" "$S/check_section.sh" -m "$tmp/ms/main.tex" "$tmp/ms/part/vocab.tex"
expect 0 "section: dry run without latexmk" -- \
  env PATH="$tmp/bin" "$BASH_BIN" "$S/check_section.sh" -n -m "$tmp/ms/main.tex" "$tmp/ms/part/undef.tex"
if command -v latexmk >/dev/null 2>&1; then
  expect 1 "section: an undefined macro fails the compile check" -- bash "$S/check_section.sh" -m "$tmp/ms/main.tex" "$tmp/ms/part/undef.tex"
  has "errors: 1"; has "Undefined control sequence"
  printf '\\section{Abort}\\label{sec:a}\nText.\n\\input{no-such-file-anywhere}\n' > "$tmp/ms/part/abort.tex"
  expect 1 "section: LaTeX writes no PDF: FAIL with the first errors, not a silent exit" -- \
    bash "$S/check_section.sh" -m "$tmp/ms/main.tex" "$tmp/ms/part/abort.tex"
  has "LaTeX wrote no PDF"; has "no-such-file-anywhere"; has "check_section: FAIL"
  expect 0 "section: clean section compiles (undefined reference expected)" -- bash "$S/check_section.sh" -m "$tmp/ms/main.tex" "$tmp/ms/part/sec.tex"
  has "errors: 0"; has "undefined references (expected across sections): 1"
  printf '%s\n' 'Averyveryveryveryveryveryverylongwordwithoutanyhyphenationpointsthatoverflowsthelineandmoreandmoreandmore.' >> "$tmp/ms/part/sec.tex"
  expect 1 "section: overfull box fails" -- bash "$S/check_section.sh" -m "$tmp/ms/main.tex" "$tmp/ms/part/sec.tex"
  has "overfull boxes: 1"
  expect 0 "section: -O tolerates overfull boxes" -- bash "$S/check_section.sh" -O -m "$tmp/ms/main.tex" "$tmp/ms/part/sec.tex"
  printf '\\section{Other}\\label{sec:o}\nThe Lean code says so.\n' > "$tmp/ms/part/bad.tex"
  expect 1 "section: vocabulary failure propagates" -- bash "$S/check_section.sh" -m "$tmp/ms/main.tex" "$tmp/ms/part/bad.tex"
  has "process-words:Lean"
  # pages per section of a real compiled document
  printf '%s\n' '\documentclass{article}' '\begin{document}' '\tableofcontents' '\section{One}\label{sec:one}' 'x\newpage' \
    '\section{Two}\label{sec:two}' 'x\newpage x\newpage' '\section{Three}\label{sec:three}' 'x' '\end{document}' > "$tmp/doc2.tex"
  ( cd "$tmp" && latexmk -pdf -interaction=nonstopmode doc2.tex > /dev/null 2>&1 ) || true
  printf 'sec:one\t1\nsec:two\t1\nsec:three\t5\n' > "$tmp/lab.tsv"
  expect 1 "pages: compiled document, label keys, cap exceeded" -- "$PY" -I "$S/page_report.py" --aux "$tmp/doc2.aux" --from-labels --allowances "$tmp/lab.tsv"
  grep -q $'sec:two\t2\t2\t2\t1\tcap\tOVER' "$tmp/out" || fail "label spans"
else
  echo "skip: latexmk not found; compile checks not run"
fi

echo "smoke_exposition-standards: $pass checks passed"
