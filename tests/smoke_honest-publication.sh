#!/usr/bin/env bash
# Smoke test for skills/honest-publication: check_correspondence.py on a tiny synthetic graph, table, TeX source and
# Lean repository; the assets exist; a vocabulary check of the skill's text.
# Usage: tests/smoke_honest-publication.sh      (exit 0 = all passed)
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SK="$ROOT/skills/honest-publication"
C="$SK/scripts/check_correspondence.py"
T="$(mktemp -d)"
trap 'rm -rf "$T"' EXIT
PY=(python3 -I)

fail() { echo "FAIL: $*" >&2; exit 1; }
ok() { echo "ok: $*"; }
expect_rc() {
  local want="$1" desc="$2"; shift 2
  local rc=0
  "$@" > "$T/out" 2>&1 || rc=$?
  if [ "$rc" -ne "$want" ]; then cat "$T/out" >&2; fail "$desc: exit $rc, expected $want"; fi
  ok "$desc (exit $rc)"
}
has() { grep -qF -- "$1" "$T/out" || { cat "$T/out" >&2; fail "output lacks: $1"; }; }

expect_rc 0 "check_correspondence.py --help" "${PY[@]}" "$C" --help

# --- a tiny Lean repository with two files, committed (in the temporary directory only)
mkdir -p "$T/lean"
for i in $(seq 1 30); do echo "-- line $i"; done > "$T/lean/A.lean"
for i in $(seq 1 10); do echo "-- line $i"; done > "$T/lean/B.lean"
git -C "$T/lean" -c init.defaultBranch=main init -q
git -C "$T/lean" add A.lean B.lean
git -C "$T/lean" -c user.name=smoke -c user.email=smoke@example.invalid -c commit.gpgsign=false \
  -c core.hooksPath=/dev/null commit -q -m "synthetic source"
PIN="$(git -C "$T/lean" rev-parse HEAD)"

# --- a graph: nodes(name, used, path, line); Dup.decl has two rows, one used
"${PY[@]}" - "$T/graph.sqlite" <<'PYEOF'
import sqlite3, sys
con = sqlite3.connect(sys.argv[1])
con.execute("CREATE TABLE nodes(name TEXT, used INT, path TEXT, line INT)")
con.executemany("INSERT INTO nodes VALUES (?,?,?,?)", [
    ("Good.decl", 1, "A.lean", 10), ("Unused.decl", 0, "A.lean", 20),
    ("Dup.decl", 0, "B.lean", 5), ("Dup.decl", 1, "B.lean", 5)])
con.commit()
PYEOF

# --- TeX: two numbered environments, an unnumbered one, a display, a commented-out label
mkdir -p "$T/tex"
cat > "$T/tex/main.tex" <<'TEXEOF'
\newtheorem{theorem}{Theorem}
\newtheorem{lemma}[theorem]{Lemma}
\newtheorem*{remark*}{Remark}
\begin{theorem}[Main]\label{thm:main} For every $x$ there is $y>x$. \end{theorem}
\begin{lemma}\label{lem:a} A bound. \end{lemma}
\begin{lemma}\label{lem:b} Another bound. \end{lemma}
\begin{remark*}\label{rem:u} Unnumbered. \end{remark*}
% \begin{lemma}\label{lem:ghost} commented out \end{lemma}
\begin{equation}\label{eq:one} 1 = 1 \end{equation}
TEXEOF

tab() { local IFS=$'\t'; echo "$*"; }
HEADER="$(tab label kind 'Lean declarations used=1' relation 'file:line')"

# --- a good table
{ echo "# commit: $PIN"
  echo "$HEADER"
  tab thm:main theorem Good.decl DIRECT A.lean:10
  tab lem:a lemma 'Dup.decl; Real.exp_le_exp (Mathlib)' WEAKENING B.lean:5
  tab lem:b lemma '—' NONE main.tex:6
} > "$T/good.tsv"
expect_rc 0 "a good table" "${PY[@]}" "$C" "$T/good.tsv" --db "$T/graph.sqlite" --tex "$T/tex" --commit "${PIN:0:7}"
has "3 rows, 3 name references (2 distinct project names, 1 external); all 2 in the closure"
has "3 of 3 statement labels covered"
expect_rc 0 "files and lines at the pin" "${PY[@]}" "$C" "$T/good.tsv" --db "$T/graph.sqlite" --lean-repo "$T/lean"
expect_rc 0 "graph locations agree" "${PY[@]}" "$C" "$T/good.tsv" --db "$T/graph.sqlite" --check-graph-locations
expect_rc 1 "another expected pin" "${PY[@]}" "$C" "$T/good.tsv" --db "$T/graph.sqlite" --commit 0123456
has "PIN-MISMATCH"
expect_rc 1 "displays required too" "${PY[@]}" "$C" "$T/good.tsv" --db "$T/graph.sqlite" --tex "$T/tex" --displays
has "NOT-IN-TABLE eq:one"
expect_rc 0 "a display exempted by pattern" "${PY[@]}" "$C" "$T/good.tsv" --db "$T/graph.sqlite" --tex "$T/tex" \
  --displays --exclude-label '^eq:'

# --- a bad table: no pin, an unused name, a missing name, a bad relation, a label not in the TeX, lem:b missing
{ echo "$HEADER"
  tab thm:main theorem Unused.decl DIRECT A.lean:20
  tab lem:a lemma Missing.decl COMPOSITION A.lean:1
  tab lem:zzz lemma Good.decl GUESS A.lean:10
} > "$T/bad.tsv"
expect_rc 1 "a bad table" "${PY[@]}" "$C" "$T/bad.tsv" --db "$T/graph.sqlite" --tex "$T/tex"
for tag in "NO-PIN" "UNUSED Unused.decl" "NOT-IN-GRAPH Missing.decl" "BAD-RELATION 'GUESS'" \
           "LABEL-NOT-IN-TEX lem:zzz" "NOT-IN-TABLE lem:b"; do has "$tag"; done
ok "every failure of the bad table reported"

# --- stale locations: a line outside a file, a moved declaration, a link pinned elsewhere
{ echo "# commit: $PIN"
  echo "$HEADER"
  tab thm:main theorem Good.decl DIRECT A.lean:11
  tab lem:a lemma Dup.decl DIRECT B.lean:99
  tab lem:b lemma Good.decl CITED "https://example.org/x/y/blob/0123456789abcdef0123456789abcdef01234567/A.lean#L10"
} > "$T/stale.tsv"
expect_rc 1 "stale locations" "${PY[@]}" "$C" "$T/stale.tsv" --db "$T/graph.sqlite" --lean-repo "$T/lean" \
  --check-graph-locations
has "STALE-LOCATION Good.decl"
has "BAD-LOCATION B.lean:99-99"
has "PIN-MISMATCH link to A.lean"

# --- usage and input errors
expect_rc 2 "a missing database" "${PY[@]}" "$C" "$T/good.tsv" --db "$T/none.sqlite"
expect_rc 2 "no --db" env -u ENSLOP_GRAPH_DB "${PY[@]}" "$C" "$T/good.tsv"
expect_rc 2 "a wrong graph table name" "${PY[@]}" "$C" "$T/good.tsv" --db "$T/graph.sqlite" --table decls
printf 'label\tkind\n' > "$T/nocols.tsv"
expect_rc 2 "a table without the needed columns" "${PY[@]}" "$C" "$T/nocols.tsv" --db "$T/graph.sqlite"

# --- relations as defined in correspondence-and-statement.md: CITED points to a declaration; a notes column is ignored
{ echo "# commit: $PIN"
  tab label kind 'Lean declarations used=1' relation 'file:line' notes
  tab thm:main theorem Good.decl DIRECT A.lean:10 ''
  tab lem:a lemma Dup.decl CITED B.lean:5 'standard result, bibliography key Key2020'
  tab lem:b lemma '—' CITED main.tex:6 'a pointer without a declaration'
} > "$T/cited.tsv"
expect_rc 1 "a CITED row without a declaration" "${PY[@]}" "$C" "$T/cited.tsv" --db "$T/graph.sqlite" --tex "$T/tex"
has "NO-NAMES"
expect_rc 0 "the same row allowed by an explicit --needs-names" "${PY[@]}" "$C" "$T/cited.tsv" --db "$T/graph.sqlite" \
  --tex "$T/tex" --needs-names DIRECT,WEAKENING,COMPOSITION
grep -q 'id="relations"' "$SK/references/correspondence-and-statement.md" || fail "the relations table has no anchor"
for r in DIRECT WEAKENING COMPOSITION CITED NONE; do
  grep -q "^| \`$r\` |" "$SK/references/correspondence-and-statement.md" || fail "relation $r is not defined"
done
ok "the five relations are defined once, in correspondence-and-statement.md"

# --- assets present
for f in disclosure-wordings.md status-table.template.md faq-evidence-table.template.md statement-page.template.md \
         changelog-entry.template.md prepublication-checklist.md correspondence.template.tsv public-readme.template.md; do
  [ -s "$SK/assets/$f" ] || fail "missing asset $f"
done
ok "all assets present"
# the correspondence template has the right columns and is refused until its pin is filled in
expect_rc 1 "the unfilled correspondence template" "${PY[@]}" "$C" "$SK/assets/correspondence.template.tsv" \
  --db "$T/graph.sqlite"
has "NO-PIN"

# --- vocabulary and privacy of the skill's text
BANNED='crucial|leverage|delve|robust|seamless|comprehensive|pivotal|intricate|nuanced|holistic|landscape|navigate|tapestry|underscore|unlock|showcase|harness|foster|paradigm|game-changer|cutting-edge|state-of-the-art|worth noting|in summary'
if grep -rniE "$BANNED" "$SK" --include='*.md' --include='*.yaml' --include='*.tsv'; then
  fail "banned or private words in the skill's text"
fi
ok "no banned or private words in the skill's text"

echo "smoke_honest-publication: all checks passed"
