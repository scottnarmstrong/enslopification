#!/usr/bin/env bash
# Compile one section of a manuscript standalone with the manuscript's own preamble, then run
# the vocabulary and shape checks on it. Part of the exposition-standards skill.
set -euo pipefail

usage() {
  cat <<'EOF'
usage: check_section.sh [-m MAIN.tex] [-e pdf|lualatex|xelatex] [-k KEEPDIR] [-O] [-n]
                        [-S "shape args"] [-V "vocabulary args"] SECTION.tex

Takes the preamble of MAIN.tex (everything before \begin{document}; relative \input paths in
it are rewritten to absolute ones, and MAIN's directory is put on TEXINPUTS), wraps SECTION.tex
in it, compiles in a fresh temporary directory with latexmk, and reports:
  pages; errors; undefined references and citations (expected: other sections are absent);
  multiply defined labels; overfull boxes; then check_vocabulary.py and check_shape.py on
  SECTION.tex.
Exit 0 if clean; 1 on compile errors, no PDF written, duplicate labels, overfull boxes (unless
-O), vocabulary hits or shape violations; 2 on usage errors; 3 if the compilation could not run
(latexmk not found): the last line then says SKIPPED, never PASS, because pages, errors, labels
and boxes were not measured. Undefined references never fail the check.

  -m MAIN.tex   manuscript root whose preamble is used (default: $ENSLOP_MAIN_TEX)
  -e ENGINE     pdf (default), lualatex or xelatex
  -k KEEPDIR    copy the PDF and log of the standalone build into KEEPDIR
  -O            report overfull boxes without failing
  -n            dry run: print the wrapper and the commands, run nothing
  -S ARGS       extra arguments for check_shape.py, e.g. -S "--tag-regex '\bQ[0-6]\b'"
  -V ARGS       extra arguments for check_vocabulary.py, e.g. -V "--lean-namespace YM"
  -h            this help
Without latexmk the two text checks still run; a failing one gives exit 1, else exit 3 (SKIPPED).
A dry run (-n) runs nothing and exits 0.
Environment: ENSLOP_MAIN_TEX, ENSLOP_PYTHON (default python3).
Example: check_section.sh -m manuscript/main.tex -V "--lean-namespace YM" manuscript/part2/section.tex
EOF
}

main_tex="${ENSLOP_MAIN_TEX:-}"; engine=pdf; keep=""; allow_overfull=0; dry=0; shape_args=""; vocab_args=""
while getopts ":m:e:k:OnS:V:h" opt; do
  case "$opt" in
    m) main_tex="$OPTARG" ;;
    e) engine="$OPTARG" ;;
    k) keep="$OPTARG" ;;
    O) allow_overfull=1 ;;
    n) dry=1 ;;
    S) shape_args="$OPTARG" ;;
    V) vocab_args="$OPTARG" ;;
    h) usage; exit 0 ;;
    *) usage >&2; exit 2 ;;
  esac
done
shift $((OPTIND - 1))
[ $# -eq 1 ] || { usage >&2; exit 2; }
section="$1"
[ -n "$main_tex" ] || { echo "check_section: give -m MAIN.tex or set ENSLOP_MAIN_TEX" >&2; exit 2; }
[ -f "$main_tex" ] || { echo "check_section: no such file: $main_tex" >&2; exit 2; }
[ -f "$section" ] || { echo "check_section: no such file: $section" >&2; exit 2; }
grep -q '\\begin{document}' "$main_tex" || { echo "check_section: no \\begin{document} in $main_tex" >&2; exit 2; }
case "$engine" in pdf|lualatex|xelatex) ;; *) echo "check_section: engine must be pdf, lualatex or xelatex" >&2; exit 2 ;; esac

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
py="${ENSLOP_PYTHON:-python3}"
main_dir="$(cd "$(dirname "$main_tex")" && pwd)"
sec_abs="$(cd "$(dirname "$section")" && pwd)/$(basename "$section")"
sec_dir="$(dirname "$sec_abs")"

make_wrapper() {
  # preamble up to \begin{document}; relative \input{...} rewritten to MAIN's directory
  awk '/\\begin\{document\}/ { sub(/\\begin\{document\}.*/, ""); print; exit } { print }' "$main_tex" |
    sed -E "s|\\\\input\{([^}/~][^}]*)\}|\\\\input{${main_dir}/\1}|g"
  printf '\\begin{document}\n\\input{%s}\n\\end{document}\n' "$sec_abs"
}

eval "shape_extra=($shape_args)"
eval "vocab_extra=($vocab_args)"
latex_flag="-pdf"; [ "$engine" = pdf ] || latex_flag="-$engine"

if [ "$dry" -eq 1 ]; then
  echo "# wrapper (standalone.tex):"; make_wrapper
  echo "# TEXINPUTS=$main_dir:$sec_dir: latexmk $latex_flag -interaction=nonstopmode standalone.tex"
  echo "# $py -I $here/check_vocabulary.py ${vocab_extra[*]-} $section"
  echo "# $py -I $here/check_shape.py ${shape_extra[*]-} $section"
  echo "check_section: dry run, nothing compiled or checked"
  exit 0
fi

fail=0; skipped=""
if command -v latexmk >/dev/null 2>&1; then
  tmp="$(mktemp -d)"
  trap 'rm -rf "$tmp"' EXIT
  make_wrapper > "$tmp/standalone.tex"
  ( cd "$tmp" && TEXINPUTS="$main_dir:$sec_dir:${TEXINPUTS:-}" BIBINPUTS="$main_dir:${BIBINPUTS:-}" \
      latexmk "$latex_flag" -interaction=nonstopmode standalone.tex > build.log 2>&1 ) || true
  log="$tmp/standalone.log"
  [ -f "$log" ] || { echo "check_section: latexmk produced no log; see the build output:"; tail -20 "$tmp/build.log"; exit 1; }
  # every pipeline below is guarded: a log without the line searched for must not end the script silently
  pages=""
  if [ -f "$tmp/standalone.pdf" ] && command -v pdfinfo >/dev/null 2>&1; then
    pages="$(pdfinfo "$tmp/standalone.pdf" 2>/dev/null | awk '/^Pages:/ {print $2}' || true)"
  fi
  [ -n "$pages" ] || pages="$(grep -o 'Output written on [^ ]* ([0-9]* page' "$log" | grep -o '([0-9]*' | tr -d '(' | tail -1 || true)"
  errors="$(grep -c '^!' "$log" || true)"
  undef_refs="$(grep -c 'Reference .* undefined' "$log" || true)"
  undef_cites="$(grep -c 'Citation .* undefined' "$log" || true)"
  dup="$(grep -c 'multiply defined' "$log" || true)"
  overfull="$(grep -c '^Overfull \\[hv]box' "$log" || true)"
  if [ -f "$tmp/standalone.pdf" ]; then
    echo "pages: ${pages:-unknown}"
  else
    echo "pages: none (LaTeX wrote no PDF)"; fail=1
  fi
  echo "errors: $errors"; [ "$errors" -eq 0 ] || grep -m 4 -A2 '^!' "$log" || true
  if [ ! -f "$tmp/standalone.pdf" ] && [ "$errors" -eq 0 ]; then echo "end of the log:"; tail -8 "$log"; fi
  echo "undefined references (expected across sections): $undef_refs; undefined citations: $undef_cites"
  echo "multiply defined labels: $dup"; [ "$dup" -eq 0 ] || grep -m 5 'multiply defined' "$log" || true
  echo "overfull boxes: $overfull"; [ "$overfull" -eq 0 ] || grep -m 8 '^Overfull \\[hv]box' "$log" || true
  if [ -n "$keep" ]; then mkdir -p "$keep"; cp "$log" "$keep/"; if [ -f "$tmp/standalone.pdf" ]; then cp "$tmp/standalone.pdf" "$keep/"; fi; fi
  [ "$errors" -eq 0 ] || fail=1
  [ "$dup" -eq 0 ] || fail=1
  [ "$overfull" -eq 0 ] || [ "$allow_overfull" -eq 1 ] || fail=1
else
  skipped="latexmk not found: pages, errors, labels and boxes not measured"
  echo "compile: SKIPPED ($skipped)"
fi

echo "--- vocabulary"
"$py" -I "$here/check_vocabulary.py" ${vocab_extra[@]+"${vocab_extra[@]}"} "$section" | tail -15 || fail=1
echo "--- shape"
"$py" -I "$here/check_shape.py" ${shape_extra[@]+"${shape_extra[@]}"} "$section" | tail -15 || fail=1
if [ "$fail" -ne 0 ]; then
  echo "check_section: FAIL $section"; exit 1
elif [ -n "$skipped" ]; then
  echo "check_section: SKIPPED ($skipped; the text checks passed) $section"; exit 3
fi
echo "check_section: PASS $section"
exit 0
