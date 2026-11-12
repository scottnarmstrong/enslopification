#!/usr/bin/env bash
# render_pages.sh: render a range of PDF pages as PNG images for a typographic inspection.
# Usage: render_pages.sh [-f FIRST] [-l LAST] [-r DPI] [-p PREFIX] -o OUTDIR PDF   (-h for help)
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: render_pages.sh [-f FIRST] [-l LAST] [-r DPI] [-p PREFIX] -o OUTDIR PDF

Render pages FIRST..LAST of PDF as PNG images at DPI into OUTDIR (created if needed), then print
the image paths, one per line, and a one-line summary. It renders; it inspects nothing.

  -f FIRST   first page (default 1)
  -l LAST    last page (default: the last page of PDF)
  -r DPI     resolution (default: $ENSLOP_RENDER_DPI, else 60). 60 dpi shows layout defects
             (blank areas, broken displays, stranded lines); about 130 dpi zooms on a suspect page.
  -p PREFIX  image file prefix (default p); images are PREFIX-NNN.png
  -o OUTDIR  output directory (required)
  -h         print this help

Requires pdftoppm and pdfinfo (poppler-utils).
Exit status: 0 ok, 2 usage or input error.

Example (three reviewers on a 180-page PDF):
  render_pages.sh -f 1   -l 60  -o review/typo/img-1-60    build/main.pdf
  render_pages.sh -f 61  -l 120 -o review/typo/img-61-120  build/main.pdf
  render_pages.sh -f 121        -o review/typo/img-121-180 build/main.pdf
  render_pages.sh -f 14 -l 14 -r 130 -p hi -o review/typo/img-1-60 build/main.pdf   # zoom on page 14
EOF
}

first=1
last=""
dpi="${ENSLOP_RENDER_DPI:-60}"
prefix="p"
outdir=""
while getopts ":f:l:r:p:o:h" opt; do
  case "$opt" in
    f) first="$OPTARG" ;;
    l) last="$OPTARG" ;;
    r) dpi="$OPTARG" ;;
    p) prefix="$OPTARG" ;;
    o) outdir="$OPTARG" ;;
    h) usage; exit 0 ;;
    :) echo "render_pages: option -$OPTARG needs a value" >&2; usage >&2; exit 2 ;;
    *) echo "render_pages: unknown option -$OPTARG" >&2; usage >&2; exit 2 ;;
  esac
done
shift $((OPTIND - 1))

if [ "$#" -ne 1 ] || [ -z "$outdir" ]; then
  echo "render_pages: need one PDF and -o OUTDIR" >&2
  usage >&2
  exit 2
fi
pdf="$1"

for tool in pdftoppm pdfinfo; do
  if ! command -v "$tool" >/dev/null 2>&1; then
    echo "render_pages: $tool not found (install poppler-utils)" >&2
    exit 2
  fi
done
if [ ! -f "$pdf" ]; then
  echo "render_pages: no such file: $pdf" >&2
  exit 2
fi

is_int() { [[ "$1" =~ ^[0-9]+$ ]]; }
pages="$(pdfinfo "$pdf" 2>/dev/null | awk '/^Pages:/ {print $2}')"
if ! is_int "${pages:-}"; then
  echo "render_pages: cannot read the page count of $pdf" >&2
  exit 2
fi
[ -n "$last" ] || last="$pages"
for v in "$first" "$last" "$dpi"; do
  if ! is_int "$v"; then
    echo "render_pages: not a positive integer: $v" >&2
    exit 2
  fi
done
if [ "$first" -lt 1 ] || [ "$first" -gt "$last" ] || [ "$last" -gt "$pages" ] || [ "$dpi" -lt 1 ]; then
  echo "render_pages: bad range $first-$last for a PDF of $pages pages (or bad resolution $dpi)" >&2
  exit 2
fi

mkdir -p "$outdir"
pdftoppm -png -r "$dpi" -f "$first" -l "$last" "$pdf" "$outdir/$prefix"

# pdftoppm pads page numbers with zeros; find each page's image whatever the padding.
count=0
missing=0
for ((p = first; p <= last; p++)); do
  found=""
  for w in 1 2 3 4 5 6; do
    name="$(printf '%s/%s-%0*d.png' "$outdir" "$prefix" "$w" "$p")"
    if [ -f "$name" ]; then found="$name"; break; fi
  done
  if [ -n "$found" ]; then
    echo "$found"
    count=$((count + 1))
  else
    echo "render_pages: no image for page $p" >&2
    missing=$((missing + 1))
  fi
done
echo "render_pages: $count page image(s), pages $first-$last of $pages, at $dpi dpi, in $outdir"
if [ "$missing" -gt 0 ]; then
  exit 2
fi
