#!/usr/bin/env bash
# Smoke test of the statement-spine scripts and assets on small synthetic inputs.
# Usage: tests/smoke_statement-spine.sh   (exit 0 if every check passes)
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SK="$ROOT/skills/statement-spine"
S="$SK/scripts"
SHAPE="$ROOT/skills/exposition-standards/scripts/check_shape.py"
PY="${ENSLOP_PYTHON:-python3}"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
pass=0

fail() { echo "FAIL: $*"; [ -f "$tmp/out" ] && sed 's/^/    /' "$tmp/out" | head -20; exit 1; }
expect() {
  local want="$1" what="$2"; shift 3
  set +e; "$@" > "$tmp/out" 2>&1; local rc=$?; set -e
  [ "$rc" -eq "$want" ] || fail "$what: exit $rc, expected $want"
  pass=$((pass + 1)); echo "ok: $what"
}
has() { grep -q -- "$1" "$tmp/out" || fail "output lacks '$1'"; }

# --- help
expect 0 "clause_map_check.py --help" -- "$PY" -I "$S/clause_map_check.py" --help
expect 0 "typeset_spine.sh -h" -- bash "$S/typeset_spine.sh" -h

# --- a frozen spine with clause tags, and a natural spine with a clause map
cat > "$tmp/SPINE.md" <<'EOF'
# Frozen contracts
Theorem 1. Let s > d/2+1 [clause:T1.h1] and u0 in H^s [clause:T1.h2]. Then there is a solution
[clause:T1.c1], unique in C([0,T];H^s) [clause:T1.c2], with |u(t)| <= C [clause:T1.c3].
EOF
cat > "$tmp/NATURAL.md" <<'EOF'
# Natural spine

## Main theorem {#sec:main}

\begin{maintheorem}\label{thm:main}
For every $s>d/2+1$ and every $u_0\in H^s$ there is a unique solution $u\in C([0,T];H^s)$.
\end{maintheorem}

### II.A Energy estimates

\begin{lemma}\label{lem:energy}
For every $t\in[0,T]$, $|u(t)|\le C$, where $C$ depends only on $s$, $d$ and $|u_0|$.
\end{lemma}

## Clause map

| clause | destination | scope retained | note |
|---|---|---|---|
| T1.h1 | thm:main | every $s>d/2+1$; constants depend on $|s|$ and $d$ only | |
| T1.h2 | thm:main, lem:energy (data) | every $u_0\in H^s$ | split: data in both |
| T1.h2 | sec:main | repeated in the setup | |
| T1.c1 | thm:main | existence of one solution; fixed by `Pkg.Main.exists` | |
| T1.c2 | thm:main | uniqueness only in $C([0,T];H^s)$ | |
| T1.c3 | II.A | uniform in $t$ | |

| Key | Used declaration | What it fixes |
|---|---|---|
| U-src | `Pkg.Main.exists` | existence form |
EOF
printf 'Pkg.Main.exists\n' > "$tmp/used.txt"
expect 0 "clause map: clean map passes (math with | in cells, headings and \\label as destinations)" -- \
  "$PY" -I "$S/clause_map_check.py" --map "$tmp/NATURAL.md" --spine "$tmp/SPINE.md" --labels-from "$tmp/NATURAL.md" --used-names "$tmp/used.txt"
has "5 frozen clauses, 6 rows in 1 table(s) (1 other table(s) ignored); 0 unmapped"

# plant one problem of each kind
sed -e 's/^| T1.c3 | II.A |/| T1.c9 \/ T1.c1 | lem:nosuch |/' -e 's/`Pkg.Main.exists` | existence form/`Pkg.Other.unused` | existence form/' \
  "$tmp/NATURAL.md" > "$tmp/BAD.md"
expect 1 "clause map: planted faults are reported" -- \
  "$PY" -I "$S/clause_map_check.py" --map "$tmp/BAD.md" --spine "$tmp/SPINE.md" --labels-from "$tmp/BAD.md" --used-names "$tmp/used.txt"
has $'unmapped\tT1.c3'
has $'missing-destination\tlem:nosuch'
has $'unknown-clause\tT1.c9'
has $'duplicate-no-note\tT1.c1'
has $'not-used\tPkg.Other.unused'

# TSV map, clause ids from a list, extra labels from a file, an allowed destination pattern
printf 'T1.h1\nT1.h2\nT1.c1\nT1.c2\nT1.c3\n' > "$tmp/ids.txt"
printf 'clause\tdestination\tscope retained\tnote\nT1.h1\tthm:main\tall s\t\nT1.h2\tthm:main\tdata\t\nT1.c1\tthm:main\texists\t\nT1.c2\tprop:uniq\tclass\t\nT1.c3\tprose:after-main\tuniform\t\n' > "$tmp/map.tsv"
printf 'prop:uniq\n' > "$tmp/labels.txt"
expect 0 "clause map: TSV, --clauses, --labels, --allow-dest" -- \
  "$PY" -I "$S/clause_map_check.py" --map "$tmp/map.tsv" --clauses "$tmp/ids.txt" --labels-from "$tmp/NATURAL.md" --labels "$tmp/labels.txt" --allow-dest '^prose:'
expect 1 "clause map: same map without --allow-dest fails" -- \
  "$PY" -I "$S/clause_map_check.py" --map "$tmp/map.tsv" --clauses "$tmp/ids.txt" --labels-from "$tmp/NATURAL.md" --labels "$tmp/labels.txt"
has $'missing-destination\tprose:after-main'

# --rows-only: a map without a row fails and says where the map must be; placeholder rows do not count
head -1 "$SK/assets/clause-map-header.tsv" > "$tmp/empty.tsv"
expect 1 "clause map --rows-only: header only" -- "$PY" -I "$S/clause_map_check.py" --rows-only --map "$tmp/empty.tsv"
has "NO ROWS"; has "section 6"; has "CLAUSE-MAP.tsv"
expect 1 "clause map --rows-only: the template's placeholder row is not a row" -- \
  "$PY" -I "$S/clause_map_check.py" --rows-only --map "$SK/assets/SPINE-NATURAL-template.md"
expect 0 "clause map --rows-only: the natural spine's section 6" -- \
  "$PY" -I "$S/clause_map_check.py" --rows-only --map "$tmp/NATURAL.md"
has "6 row(s) with a clause id in 1 table(s)"
expect 2 "clause map --rows-only: a missing file" -- "$PY" -I "$S/clause_map_check.py" --rows-only --map "$tmp/none.tsv"

# the shipped clause-map header parses, with its example rows
printf 'T1.h2\nT1.c3\n' > "$tmp/ids2.txt"; printf 'thm:main\nlem:energy\nprop:uniqueness\n' > "$tmp/labels2.txt"
printf 'Pkg.Main.unique\n' > "$tmp/used2.txt"
expect 0 "clause map: assets/clause-map-header.tsv parses" -- \
  "$PY" -I "$S/clause_map_check.py" --map "$SK/assets/clause-map-header.tsv" --clauses "$tmp/ids2.txt" --labels "$tmp/labels2.txt" --used-names "$tmp/used2.txt"
expect 2 "clause map: no ids is an input error" -- \
  "$PY" -I "$S/clause_map_check.py" --map "$tmp/NATURAL.md" --clauses /dev/null --labels-from "$tmp/NATURAL.md"

# --- the natural spine's raw LaTeX environments are measured by the shape checker
expect 0 "shape check counts environments in a Markdown spine" -- "$PY" -I "$SHAPE" --list "$tmp/NATURAL.md"
has "2 environments, 0 over word cap"

# --- prompt templates: placeholders well formed and documented in spine-procedure.md
"$PY" -I - "$SK" <<'PY' > "$tmp/out" 2>&1 || fail "prompt placeholders"
import pathlib, re, sys
sk = pathlib.Path(sys.argv[1])
doc = (sk / "references" / "spine-procedure.md").read_text()
for t in sorted((sk / "assets" / "prompts").glob("*.md")):
    text = t.read_text()
    found = set(re.findall(r"\{\{([a-z_]+)\}\}", text))
    stray = re.sub(r"\{\{[a-z_]+\}\}", "", text)
    assert "{{" not in stray and "}}" not in stray, f"stray braces in {t.name}"
    row = re.search(r"\| `" + re.escape(t.name) + r"` \| (.*) \|", doc)
    assert row, f"{t.name} missing from the placeholder table"
    documented = set(re.findall(r"`([a-z_]+)`", row.group(1)))
    assert found == documented, f"{t.name}: used {sorted(found - documented)} undocumented {sorted(documented - found)}"
    print(t.name, len(found), "placeholders")
PY
pass=$((pass + 1)); echo "ok: prompt placeholders well formed and documented"

# --- the natural-spine template: its clause-map table is recognized
printf '<ID>\n' > "$tmp/tids.txt"; printf '<label>\n' > "$tmp/tlabels.txt"
expect 0 "clause map: the table of assets/SPINE-NATURAL-template.md parses" -- \
  "$PY" -I "$S/clause_map_check.py" --map "$SK/assets/SPINE-NATURAL-template.md" --clauses "$tmp/tids.txt" --labels "$tmp/tlabels.txt"
has "1 rows in 1 table(s)"

# --- typesetting
expect 0 "typeset: dry run" -- bash "$S/typeset_spine.sh" -n "$tmp/NATURAL.md"
has "dry run"
# without pandoc and latexmk nothing is measured: SKIPPED and exit 3, never a pass (a dry run still exits 0)
mkdir -p "$tmp/bin"
for c in bash env dirname basename grep awk sed mktemp rm cat tail head tr cp mkdir; do
  p="$(type -P "$c")" && ln -sf "$p" "$tmp/bin/$c"
done
BASH_BIN="$(type -P bash)"
expect 3 "typeset: no pandoc or latexmk, with -m: SKIPPED" -- env PATH="$tmp/bin" "$BASH_BIN" "$S/typeset_spine.sh" -m 40 "$tmp/NATURAL.md"
has "SKIPPED (pandoc and latexmk not found)"
expect 3 "typeset: no pandoc or latexmk, without -m: SKIPPED" -- env PATH="$tmp/bin" "$BASH_BIN" "$S/typeset_spine.sh" "$tmp/NATURAL.md"
expect 0 "typeset: dry run without the tools" -- env PATH="$tmp/bin" "$BASH_BIN" "$S/typeset_spine.sh" -n "$tmp/NATURAL.md"
if command -v pandoc >/dev/null 2>&1 && command -v latexmk >/dev/null 2>&1; then
  expect 0 "typeset: natural spine compiles" -- bash "$S/typeset_spine.sh" -o "$tmp/build" "$tmp/NATURAL.md"
  has "errors: 0"; has "typeset_spine: 1 pages"
  [ -f "$tmp/build/spine.pdf" ] || fail "no PDF kept"
  expect 1 "typeset: over the -m allowance fails" -- bash "$S/typeset_spine.sh" -m 0 "$tmp/NATURAL.md"
  expect 0 "typeset: the SPINE template itself compiles" -- bash "$S/typeset_spine.sh" "$SK/assets/SPINE-template.md"
  has "errors: 0"
  expect 0 "typeset: the SPINE-NATURAL template compiles" -- bash "$S/typeset_spine.sh" "$SK/assets/SPINE-NATURAL-template.md"
  has "errors: 0"
  printf '# Spine\n\n## A\n\nText.\n\n\\input{no-such-file-anywhere}\n' > "$tmp/ABORT.md"
  expect 1 "typeset: LaTeX writes no PDF: exit 1 with the first errors" -- bash "$S/typeset_spine.sh" "$tmp/ABORT.md"
  has "LaTeX wrote no PDF"; has "no-such-file-anywhere"
  printf '%s\n' '\documentclass{article}' '\usepackage{amsmath,amsthm}' '\newtheorem{lemma}{Lemma}' \
    '\newtheorem{maintheorem}{Theorem}' '\begin{document}' 'unused body' '\end{document}' > "$tmp/main.tex"
  expect 0 "typeset: with a manuscript main.tex as preamble" -- bash "$S/typeset_spine.sh" -p "$tmp/main.tex" "$tmp/NATURAL.md"
  has "errors: 0"
else
  echo "skip: pandoc or latexmk not found; typesetting not run"
fi

echo "smoke_statement-spine: $pass checks passed"
