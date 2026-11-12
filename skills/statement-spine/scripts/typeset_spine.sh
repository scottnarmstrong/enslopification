#!/usr/bin/env bash
# Typeset a statement spine (Markdown with LaTeX math and raw LaTeX environments) alone and
# report its pages, in total and per block. Part of the statement-spine skill.
set -euo pipefail

usage() {
  cat <<'EOF'
usage: typeset_spine.sh [-p PREAMBLE] [-o OUTDIR] [-e pdf|lualatex|xelatex] [-l LEVEL]
                        [-m MAXPAGES] [-n] SPINE.md

Converts SPINE.md with pandoc (Markdown math becomes LaTeX math; raw \begin{...}...\end{...}
environments pass through unchanged), wraps it in PREAMBLE, compiles with latexmk in a fresh
temporary directory, and prints the total pages and the pages of each block (heading at
LEVEL). The measured size is the spine alone, before introduction and connecting prose.

  -p PREAMBLE  preamble file; if it contains \begin{document} (e.g. the manuscript's main.tex)
               only the text before it is used. Default: $ENSLOP_SPINE_PREAMBLE, else
               ../assets/spine-preamble.tex next to this script
  -o OUTDIR    keep the PDF, the generated body.tex and the log in OUTDIR
  -e ENGINE    pdf (default), lualatex or xelatex
  -l LEVEL     section or subsection: the heading level reported per block (default: section
               if the spine has at least two "#" headings, else subsection, i.e. "##")
  -m MAXPAGES  exit 1 if the total exceeds MAXPAGES (use it as an allowance check)
  -n           dry run: print the commands, run nothing, exit 0
  -h           this help
Exit 0 when measured (and within -m); 1 if the total exceeds -m or LaTeX wrote no PDF (the first
errors of the log are printed); 2 on usage errors; 3 when the measurement could not run: pandoc
or latexmk not found, or -m given and no page count found. Exit 3 prints SKIPPED and the
commands it would have run; nothing was measured, so it never counts as a pass.
Example: typeset_spine.sh -p manuscript/main.tex -o build/spine -m 40 spine/SPINE-NATURAL.md
EOF
}

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
preamble="${ENSLOP_SPINE_PREAMBLE:-$here/../assets/spine-preamble.tex}"
outdir=""; engine=pdf; level=""; maxpages=""; dry=0
while getopts ":p:o:e:l:m:nh" opt; do
  case "$opt" in
    p) preamble="$OPTARG" ;;
    o) outdir="$OPTARG" ;;
    e) engine="$OPTARG" ;;
    l) level="$OPTARG" ;;
    m) maxpages="$OPTARG" ;;
    n) dry=1 ;;
    h) usage; exit 0 ;;
    *) usage >&2; exit 2 ;;
  esac
done
shift $((OPTIND - 1))
[ $# -eq 1 ] || { usage >&2; exit 2; }
spine="$1"
[ -f "$spine" ] || { echo "typeset_spine: no such file: $spine" >&2; exit 2; }
[ -f "$preamble" ] || { echo "typeset_spine: no such preamble: $preamble" >&2; exit 2; }
case "$engine" in pdf|lualatex|xelatex) ;; *) echo "typeset_spine: engine must be pdf, lualatex or xelatex" >&2; exit 2 ;; esac
case "$level" in ""|section|subsection) ;; *) echo "typeset_spine: level must be section or subsection" >&2; exit 2 ;; esac
[ -z "$maxpages" ] || [[ "$maxpages" =~ ^[0-9]+$ ]] || { echo "typeset_spine: -m needs an integer" >&2; exit 2; }
if [ -z "$level" ]; then
  if [ "$(grep -c '^# ' "$spine" || true)" -ge 2 ]; then level=section; else level=subsection; fi
fi
latex_flag="-pdf"; [ "$engine" = pdf ] || latex_flag="-$engine"
pre_dir="$(cd "$(dirname "$preamble")" && pwd)"

missing=""
command -v pandoc >/dev/null 2>&1 || missing="pandoc"
command -v latexmk >/dev/null 2>&1 || missing="${missing:+$missing and }latexmk"
if [ "$dry" -eq 1 ] || [ -n "$missing" ]; then
  echo "pandoc -f markdown -t latex --wrap=preserve $spine -o body.tex"
  echo "{ preamble of $preamble; packages pandoc needs; \\setcounter{secnumdepth}{0}; \\begin{document}; \\input{body}; \\end{document} } > spine.tex"
  echo "TEXINPUTS=$pre_dir: latexmk $latex_flag -interaction=nonstopmode spine.tex"
  if [ "$dry" -eq 1 ]; then echo "typeset_spine: dry run: nothing measured"; exit 0; fi
  echo "typeset_spine: SKIPPED ($missing not found): nothing measured"
  exit 3
fi

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
pandoc -f markdown -t latex --wrap=preserve "$spine" -o "$tmp/body.tex" || { echo "typeset_spine: pandoc failed on $spine"; exit 1; }
{
  awk '/\\begin\{document\}/ { sub(/\\begin\{document\}.*/, ""); print; exit } { print }' "$preamble"
  # what pandoc's LaTeX output needs, in case the preamble lacks it (a repeated \usepackage is ignored)
  printf '%s\n' '\usepackage{longtable,booktabs,array,calc}' \
    '\providecommand{\tightlist}{\setlength{\itemsep}{0pt}\setlength{\parskip}{0pt}}' \
    '\providecommand{\href}[2]{#2}' '\providecommand{\url}[1]{\texttt{#1}}' \
    '\setcounter{secnumdepth}{0}' '\begin{document}' '\input{body}' '\end{document}'
} > "$tmp/spine.tex"
( cd "$tmp" && TEXINPUTS="$pre_dir:${TEXINPUTS:-}" latexmk "$latex_flag" -interaction=nonstopmode spine.tex > build.log 2>&1 ) || true
log="$tmp/spine.log"
keep_outputs() {
  if [ -n "$outdir" ]; then
    mkdir -p "$outdir"
    cp "$tmp/body.tex" "$outdir/"
    if [ -f "$log" ]; then cp "$log" "$outdir/"; fi
    if [ -f "$tmp/spine.pdf" ]; then cp "$tmp/spine.pdf" "$outdir/"; fi
  fi
  return 0
}
[ -f "$log" ] || { echo "typeset_spine: no log produced; build output:"; tail -20 "$tmp/build.log"; keep_outputs; exit 1; }
# every pipeline below is guarded: a log without the line searched for must not end the script silently
errors="$(grep -c '^!' "$log" || true)"
if [ ! -f "$tmp/spine.pdf" ]; then
  echo "typeset_spine: LaTeX wrote no PDF ($errors error(s)); first errors of the log:"
  grep -m 4 -A2 '^!' "$log" || tail -8 "$log"
  keep_outputs
  exit 1
fi
pages=""
if command -v pdfinfo >/dev/null 2>&1; then
  pages="$(pdfinfo "$tmp/spine.pdf" 2>/dev/null | awk '/^Pages:/ {print $2}' || true)"
fi
[ -n "$pages" ] || pages="$(grep -o 'Output written on [^ ]* ([0-9]* page' "$log" | grep -o '([0-9]*' | tr -d '(' | tail -1 || true)"

echo "block (${level})	start	pages"
python3 -I - "$tmp/spine.aux" "$level" "${pages:-0}" <<'PY'
import os, re, sys
aux, level, last = sys.argv[1], sys.argv[2], int(sys.argv[3] or 0)
text = open(aux, encoding="utf-8", errors="replace").read() if os.path.exists(aux) else ""
rows = []
for m in re.finditer(r"\\contentsline\s*\{" + level + r"\}\{(.*?)\}\{(\d+)\}\{[^{}]*\}", text):
    title = re.sub(r"\\[A-Za-z@]+\s*", " ", m.group(1)).replace("{", "").replace("}", "")
    rows.append((" ".join(title.split()), int(m.group(2))))
for i, (title, start) in enumerate(rows):
    nxt = rows[i + 1][1] if i + 1 < len(rows) else last + 1
    span = max(nxt - start, 0)
    print(f"{title[:60]}\t{start}\t{span if span else '<1'}")
if not rows:
    print(f"(no {level} headings found)")
PY
echo "errors: $errors"
[ "$errors" -eq 0 ] || { grep -m 3 -A2 '^!' "$log" || true; echo "(pages are approximate while errors remain)"; }
keep_outputs
echo "typeset_spine: ${pages:-unknown} pages ($spine)"
if [ -n "$maxpages" ]; then
  if [ -z "$pages" ]; then
    echo "typeset_spine: SKIPPED (no page count found): the allowance of $maxpages pages was not checked"
    exit 3
  elif [ "$pages" -gt "$maxpages" ]; then
    echo "typeset_spine: over the allowance of $maxpages pages"
    exit 1
  fi
fi
exit 0
