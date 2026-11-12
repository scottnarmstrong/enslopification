#!/usr/bin/env bash
# Smoke test of the coarse-graining skill.
#   - --help of every script;
#   - own_and_scale.py and unit_tables.py on a synthetic graph (lean-dependency-graph schema) with hand-computed
#     dominators, masses, ladder, labels (private, toolbox, concept), span unions and unit references;
#   - inventory.py on the same graph with a synthetic source: unit inventories (results by mass, statement excerpts
#     cut at the first := outside brackets and strings or before a pattern match, definitions, inputs from other
#     units, pinned links; the same mass as own_and_scale.py) and key-statement candidate batches; refusals;
#   - lean_links.py (pinned link, branch refused, missing name), gh_math.py (--check, fix), kappa.py (known value,
#     readers' printed reports over several batches, label and coverage checks), outline_budget.py (within, over,
#     headings, JSON for rollout configs);
#   - if the writing-workflow driver is present: rollout.py --dry-run of the three rollout configurations, and a
#     stand-in run of the outline and compression configs (each run keeps its own <unit>/STATUS).
# Usage: tests/smoke_coarse-graining.sh        (exit 0 = all passed)
set -euo pipefail
ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
SK="$ROOT/skills/coarse-graining/scripts"
AS="$ROOT/skills/coarse-graining/assets"
T=$(mktemp -d)
trap 'rm -rf "$T"' EXIT
fail() { echo "FAIL: $*" >&2; exit 1; }
ok() { echo "ok: $*"; }
PY="python3 -I -B"

for s in own_and_scale.py inventory.py unit_tables.py lean_links.py gh_math.py kappa.py outline_budget.py; do
  $PY "$SK/$s" --help > "$T/help.txt" || fail "$s --help"
  grep -q "example" "$T/help.txt" || fail "$s --help has no example"
done
ok "help texts"

# Synthetic graph: R uses A and B; A uses a1 and s; B uses b1, s and d1; a1 uses d1; s uses d2; u (unused) uses a1.
# Expected masses: a1 30, A 80, b1 20, B 80, s 45, d1 5, d2 5, R 220 (R dominates d1 and s).
$PY - "$T/g.sqlite" <<'EOF'
import sqlite3, sys
c = sqlite3.connect(sys.argv[1])
c.executescript('''CREATE TABLE meta(key TEXT PRIMARY KEY, value TEXT);
CREATE TABLE nodes(name TEXT PRIMARY KEY, kind TEXT, module TEXT, path TEXT, line INTEGER, line_end INTEGER,
  lines INTEGER, doc TEXT, used INTEGER, n_aux INTEGER, sorry INTEGER, parent TEXT);
CREATE TABLE edges(src TEXT, dst TEXT, part TEXT, direct INTEGER, PRIMARY KEY (src, dst));
CREATE TABLE roots(name TEXT PRIMARY KEY);''')
N = [('R', 'theorem', 'X.lean', 1, 10), ('A', 'theorem', 'X.lean', 11, 60), ('a1', 'theorem', 'X.lean', 20, 49),
     ('B', 'theorem', 'Y.lean', 1, 60), ('b1', 'theorem', 'Y.lean', 61, 80), ('s', 'theorem', 'Z.lean', 1, 40),
     ('d1', 'def', 'Z.lean', 41, 45), ('d2', 'def', 'Z.lean', 46, 50), ('u', 'theorem', 'W.lean', 1, 7)]
for n, k, p, a, b in N:
    c.execute('INSERT INTO nodes VALUES (?,?,?,?,?,?,?,?,?,0,0,NULL)',
              (n, k, p[:-5], p, a, b, b - a + 1, None, 0 if n == 'u' else 1))
E = [('R', 'A', 'statement'), ('R', 'B', 'proof'), ('A', 'a1', 'proof'), ('A', 's', 'proof'), ('B', 'b1', 'proof'),
     ('B', 's', 'proof'), ('B', 'd1', 'both'), ('a1', 'd1', 'proof'), ('s', 'd2', 'proof'), ('u', 'a1', 'proof')]
c.executemany('INSERT INTO edges VALUES (?,?,?,1)', E)
c.execute("INSERT INTO roots VALUES ('R')")
c.commit()
EOF

$PY "$SK/own_and_scale.py" --db "$T/g.sqlite" --scales 40,50,100 --out-dir "$T/c" > "$T/os.txt" || fail "own_and_scale.py"
col() { awk -F'\t' -v n="$2" -v k="$3" 'NR>1 && $1==n {print $k}' "$1"; }
[ "$(col "$T/c/dominators.tsv" R 5)" = 220 ] || fail "mass of R"
[ "$(col "$T/c/dominators.tsv" A 5)" = 80 ] || fail "mass of A"
[ "$(col "$T/c/dominators.tsv" s 4)" = R ] || fail "idom of s"
[ "$(col "$T/c/dominators.tsv" d2 4)" = s ] || fail "idom of d2"
[ "$(awk -F'\t' 'NR>1{printf "%s:%s ", $1, $2}' "$T/c/ladder.tsv")" = "40:4 50:3 100:1 " ] || fail "ladder"
lab() { awk -F'\t' -v n="$2" 'NR>1 && $1==n {print $2 "/" $3}' "$T/c/M$1-nodes.tsv"; }
[ "$(lab 50 a1)" = "private/A" ] || fail "a1 private to A at M=50"
[ "$(lab 50 s)" = "toolbox/" ] || fail "s toolbox at M=50"
[ "$(lab 50 d1)" = "concept/" ] || fail "d1 concept at M=50"
[ "$(lab 50 d2)" = "toolbox/" ] || fail "d2 used only by toolbox at M=50"
[ "$(lab 40 d2)" = "private/s" ] || fail "d2 private to s at M=40"
[ "$(lab 100 d1)" = "private/R" ] || fail "d1 private to R at M=100"
[ "$(awk -F'\t' 'NR>1{print $1 "->" $2 ":" $5}' "$T/c/M40-edges.tsv" | sort | tr '\n' ' ')" = \
  "A->s:1 B->s:1 R->A:1 R->B:1 " ] || fail "region edges at M=40"
[ "$(col "$T/c/M50-retained.tsv" A 5)" = 80 ] || fail "folded lines of A at M=50"
$PY "$SK/own_and_scale.py" --db "$T/g.sqlite" --scales 50 --out-dir "$T/c2" --ignore-used > /dev/null \
  || fail "own_and_scale.py --ignore-used"
[ "$(lab_c2=$(awk -F'\t' '$1=="a1"{print $2 "/" $3}' "$T/c2/M50-nodes.tsv"); echo "$lab_c2")" = "private/A" ] \
  || fail "an unreached user (u) must not make a1 shared"
$PY "$SK/own_and_scale.py" --db "$T/g.sqlite" --scales 50 --out-dir "$T/c3" --joints > /dev/null || fail "--joints"
ok "own_and_scale.py: dominators, mass, ladder, labels, region edges, unreached users"

# unit tables: d1 left without a unit; a1's span lies inside A's span (union, not sum)
printf 'declaration\tunit\nR\tU3\nA\tU1\na1\tU1\ns\tU1\nd2\tU1\nB\tU2\nb1\tU2\n' > "$T/assign.tsv"
printf 'unit\tpart\ttitle\nU1\tI\tFirst\nU2\tI\tSecond\nU3\tII\tAssembly\n' > "$T/cat.tsv"
$PY "$SK/unit_tables.py" --db "$T/g.sqlite" --assign "$T/assign.tsv" --units "$T/cat.tsv" --threshold 1 \
    --out-dir "$T/u" > "$T/ut.txt" || fail "unit_tables.py"
row() { awk -F'\t' -v u="$1" -v k="$2" '$1==u {print $k}' "$T/u/units.tsv"; }
[ "$(row U1 4)" = 95 ] || fail "U1 lines: union of spans should be 95, got $(row U1 4)"
[ "$(row U2 4)" = 80 ] || fail "U2 lines"
[ "$(row U3 9)" = "U1;U2" ] || fail "U3 builds_on"
[ "$(row U1 10)" = "U2;U3" ] || fail "U1 used_by"
grep -q '^d1	' "$T/u/unassigned.tsv" || fail "d1 should be reported without a unit"
grep -q 'used names without a unit: 1' "$T/ut.txt" || fail "scope line"
ok "unit_tables.py: span unions, builds_on/used_by, unassigned, scopes"

# inventories and key-statement candidates: a synthetic source for the graph above
SHA=0123456789abcdef0123456789abcdef01234567
mkdir -p "$T/src"
$PY - "$T/src" <<'PYEOF'
import os, sys
def mk(name, n, put):
    L = [f'-- line {i}' for i in range(1, n + 1)]
    for k, v in put.items():
        for j, t in enumerate(v.split('\n')):
            L[k - 1 + j] = t
    open(os.path.join(sys.argv[1], name), 'w').write('\n'.join(L) + '\n')
mk('X.lean', 60, {1: 'theorem R (x : Nat)\n    (h : x = x) :\n    x + 0 = x := by\n  simp',
                  11: 'theorem A {α : Type} [Inhabited α] (f : α → Nat := fun _ => 0) :\n    f default = f default := rfl',
                  20: 'theorem a1 : ∀ n : Nat, n = n\n  | 0 => rfl\n  | n+1 => rfl'})
mk('Y.lean', 80, {1: 'theorem B (s : String := "a := b") : True := trivial', 61: 'theorem b1 : 1 = 1 := rfl'})
mk('Z.lean', 50, {1: 'theorem s : 2 = 2 := by\n  rfl', 41: 'def d1 : Nat := 5', 46: 'def d2 : Nat := 7'})
mk('W.lean', 7, {1: 'theorem u : True := trivial'})
PYEOF
INV="$PY $SK/inventory.py --db $T/g.sqlite --assign $T/assign.tsv --units $T/cat.tsv --src $T/src --repo-url https://github.com/o/r --commit $SHA"
$INV --out-dir "$T/inv" > "$T/inv.txt" 2> /dev/null || fail "inventory.py"
[ "$(ls "$T/inv" | tr '\n' ' ')" = "U1.md U2.md U3.md " ] || fail "one inventory per unit"
grep -q '^95 lines (union of the declaration spans' "$T/inv/U1.md" || fail "U1 size (union of spans)"
[ "$(grep '^### R' "$T/inv/U1.md" | tr '\n' ' ')" = '### R1. `A` ### R2. `s` ### R3. `a1` ' ] || fail "results by mass"
grep -qF "mass 80 · [source](https://github.com/o/r/blob/$SHA/X.lean#L11-L60) · under \`R\` (unit U3)" "$T/inv/U1.md" \
  || fail "pinned link, mass and dominator of A"
grep -qF '    f default = f default' "$T/inv/U1.md" || fail "excerpt of A"
if grep -qF 'f default = f default :=' "$T/inv/U1.md"; then fail "excerpt of A not cut at :="; fi
grep -qF '(lines 20–49, cut before the first pattern-matching line)' "$T/inv/U1.md" || fail "pattern-matching cut"
grep -qF 'theorem B (s : String := "a := b") : True' "$T/inv/U2.md" || fail ":= inside a string or brackets cut"
grep -q '^| \[`d1`\](.*) | (no unit) | def | 1 | 0 |' "$T/inv/U1.md" || fail "inputs of U1 from other units"
grep -q 'By unit: U2: 1 reference; U3: 1 reference.' "$T/inv/U1.md" || fail "used by other units"
$INV --dominators "$T/c/dominators.tsv" --out-dir "$T/inv2" > /dev/null 2>&1 || fail "inventory.py --dominators"
diff <(grep -v 'results\? in the closure' "$T/inv/U1.md") <(grep -v 'results\? in the closure' "$T/inv2/U1.md") \
  > /dev/null || fail "computed mass differs from own_and_scale.py's dominators.tsv"
$INV --candidates --min-mass 40 --batch-size 2 --out-dir "$T/bat" > "$T/bat.txt" 2> /dev/null || fail "inventory.py --candidates"
grep -q '4 candidates (roots and results with mass >= 40) in 3 batches' "$T/bat.txt" || fail "candidate count"
[ "$(cut -f1,2 "$T/bat/candidates.tsv" | tail -n +2 | tr '\t\n' ': ')" = "A:B001 s:B001 B:B002 R:B003 " ] \
  || fail "candidates by unit in source order"
$PY -c 'import json,sys; d=json.load(open(sys.argv[1])); assert list(d)==["B001","B002","B003"] and "U1" in d["B001"]["title"], d' \
  "$T/bat/batches.json" || fail "batches.json"
grep -qF 'theorem s : 2 = 2' "$T/bat/B001.md" || fail "excerpt in a batch"
set +e
$INV --candidates --out-dir "$T/bat" > /dev/null 2>&1; rc=$?
$INV --out-dir "$T/src/inv" > /dev/null 2>&1; rc2=$?
$PY "$SK/inventory.py" --db "$T/g.sqlite" --assign "$T/assign.tsv" --src "$T/src" --repo-url https://github.com/o/r \
    --commit main --out-dir "$T/inv3" > /dev/null 2>&1; rc3=$?
set -e
[ $rc -eq 2 ] || fail "batches of an earlier run must not be mixed (exit 2, got $rc)"
[ $rc2 -eq 2 ] || fail "an --out-dir inside --src must be refused (got $rc2)"
[ $rc3 -eq 2 ] || fail "a branch name must be refused (got $rc3)"
ok "inventory.py: inventories (size, results by mass, excerpts, inputs, used by), candidate batches, refusals"

# pinned links
[ "$($PY "$SK/lean_links.py" --db "$T/g.sqlite" --repo-url https://github.com/o/r --commit $SHA A 2> /dev/null)" = \
  "A	https://github.com/o/r/blob/$SHA/X.lean#L11-L60	theorem" ] || fail "pinned link"
set +e
$PY "$SK/lean_links.py" --db "$T/g.sqlite" --repo-url https://github.com/o/r --commit main A > /dev/null 2>&1; rc=$?
$PY "$SK/lean_links.py" --db "$T/g.sqlite" --repo-url https://github.com/o/r --commit $SHA Nope > /dev/null 2>&1; rc2=$?
set -e
[ $rc -eq 2 ] || fail "a branch name must be refused (exit 2)"
[ $rc2 -eq 1 ] || fail "a missing name must exit 1"
ok "lean_links.py"

# GitHub math
printf 'Count $\\#A$ and $#B$; $\\operatorname{tr} X$.\n\n| a | $|x|$ |\n|---|---|\n\nCode `$#x$`.\n' > "$T/m.md"
set +e; $PY "$SK/gh_math.py" --check "$T/m.md" > /dev/null; rc=$?; set -e
[ $rc -eq 1 ] || fail "gh_math --check should exit 1"
$PY "$SK/gh_math.py" "$T/m.md" > /dev/null || fail "gh_math fix"
grep -qF 'Count $\sharp A$ and $\sharp B$; $\mathrm{tr} X$.' "$T/m.md" || fail "gh_math rewrite"
grep -qF '$\vert x\vert $' "$T/m.md" || fail "gh_math table bars"
grep -qF 'Code `$#x$`.' "$T/m.md" || fail "gh_math touched code"
$PY "$SK/gh_math.py" --check "$T/m.md" > /dev/null || fail "gh_math --check after fixing"
ok "gh_math.py"

# kappa: 7 items, collapsed main|key vs rest: po = 6/7, pe = 24/49, kappa = 0.720
printf 'item\tfirst\tsecond\ns1\tmain\tmain\ns2\tkey\tkey\ns3\tkey\ttechnical\ns4\ttechnical\ttechnical\ns5\tbookkeeping\ttechnical\ns6\tbookkeeping\tbookkeeping\ns7\tmain\tkey\ns8\ttechnical\t\n' > "$T/k.tsv"
$PY "$SK/kappa.py" --file "$T/k.tsv" --item-col item --a-col first --b-col second --collapse main,key > "$T/k.txt" \
  || fail "kappa.py"
grep -q 'kappa: 0.720 on 7 items' "$T/k.txt" || fail "kappa value"
grep -q 'by one only (left out): 1' "$T/k.txt" || fail "kappa left-out count"
# the same labels as the readers print them: sources first, then the table, one report per batch
mkdir -p "$T/kw/B1/read" "$T/kw/B2/read"
printf 'Sources consulted: batch.md\n\nitem\tlabel\tsummary\ns1\tmain\tA.\ns2\tkey\tB.\ns3\tkey\tC.\ns4\ttechnical\tD.\n' > "$T/kw/B1/read/reader-a.md"
printf 'Sources consulted: batch.md\nitem\tlabel\tsummary\ns5\tbookkeeping\tE.\ns6\tbookkeeping\tF.\ns7\tmain\tG.\n\nEnd.\n' > "$T/kw/B2/read/reader-a.md"
printf 'Sources consulted: batch.md\n\nitem\tlabel\tsummary\ns1\tmain\tA.\ns2\tkey\tB.\ns3\ttechnical\tC.\ns4\ttechnical\tD.\n' > "$T/kw/B1/read/reader-b.md"
printf 'Sources consulted: batch.md\n\nitem\tlabel\tsummary\ns5\ttechnical\tE.\ns6\tbookkeeping\tF.\ns7\tkey\tG.\n' > "$T/kw/B2/read/reader-b.md"
printf 'item\tbatch\n' > "$T/kc.tsv"; for i in 1 2 3 4 5 6 7; do printf 's%s\tB\n' $i >> "$T/kc.tsv"; done
$PY "$SK/kappa.py" --a "$T"/kw/*/read/reader-a.md --b "$T"/kw/*/read/reader-b.md --labels main,key,technical,bookkeeping \
    --collapse main,key --items "$T/kc.tsv" > "$T/k2.txt" || fail "kappa.py on readers' reports"
grep -q 'kappa: 0.720 on 7 items' "$T/k2.txt" || fail "kappa value from reports"
printf 's8\tB\n' >> "$T/kc.tsv"
set +e; $PY "$SK/kappa.py" --a "$T"/kw/*/read/reader-a.md --b "$T"/kw/*/read/reader-b.md --labels main,key \
    --items "$T/kc.tsv" > "$T/k3.txt"; rc=$?; set -e
[ $rc -eq 1 ] || fail "unknown labels and unlabelled candidates must exit 1"
grep -q "labels outside --labels: 'technical'" "$T/k3.txt" || fail "label check"
grep -q 'not labelled by the first reader: 1, by the second: 1' "$T/k3.txt" || fail "coverage check"
ok "kappa.py: TSV, readers' reports, label and coverage checks"

# outline budget: 7,215 lines -> 3 pages, 1,500 words
{ printf '# U. Title\n\n## 1. What this unit proves\n'; for i in $(seq 1400); do printf 'word '; done
  printf '[text](https://example.org/not/counted)\n'; } > "$T/short.md"
{ printf '# U. Title\n'; for i in $(seq 2000); do printf 'w '; done; printf '\n'; } > "$T/long.md"
$PY "$SK/outline_budget.py" "$T/short.md" --lines 7215 --require-heading '^## 1\.' > "$T/b1.txt" || fail "within allowance"
grep -q '1410 words; allowance 1500 (3 pages for 7215 Lean lines); OK' "$T/b1.txt" || fail "word count"
set +e; $PY "$SK/outline_budget.py" "$T/long.md" --lines 7215 > "$T/b2.txt"; rc=$?; set -e
[ $rc -eq 1 ] || fail "an overrun must exit 1"
grep -q 'OVER by 34%' "$T/b2.txt" || fail "overrun message"
set +e; $PY "$SK/outline_budget.py" "$T/long.md" --no-budget --require-heading '^## 1\.' > /dev/null; rc=$?; set -e
[ $rc -eq 1 ] || fail "a missing heading must exit 1"
printf 'unit\ttitle\tlines\nIII.9\tReset\t7215\nIII.10\tStep\t49448\n' > "$T/units.tsv"
$PY "$SK/outline_budget.py" --units-tsv "$T/units.tsv" --emit-units-json > "$T/u.json" || fail "--emit-units-json"
$PY -c 'import json,sys; d=json.load(open(sys.argv[1])); assert d["III.10"]["pages"]==10 and d["III.10"]["vars"]["words_max"]=="5000", d' \
  "$T/u.json" || fail "allowance JSON"
ok "outline_budget.py"

# rollout configurations, if the driver of writing-workflow is present
DRIVER="$ROOT/skills/writing-workflow/scripts/rollout.py"
if [ -f "$DRIVER" ]; then
  for cfg in rollout.outlines.example.json rollout.compress.example.json rollout.key-statements.example.json; do
    $PY "$DRIVER" "$AS/$cfg" --dry-run --workdir "$T/rw" --var "project=a test" --var "lean_root=$T" \
        --var "map=$T" --var "batches=$T/bat" --var "outlines_workdir=$T/ow" > "$T/dry.txt" 2>&1 \
      || { cat "$T/dry.txt" >&2; fail "rollout.py --dry-run $cfg"; }
    grep -q 'nothing run' "$T/dry.txt" || fail "dry run of $cfg"
  done
  grep -q 'jobs=reader-a,reader-b' "$T/dry.txt" || fail "two readers per batch"
  ok "rollout.py --dry-run of the three configurations"
  # A real run with the stand-in agent: the outline run's STATUS (EDITED) is the published status of the notes;
  # the compression run, in its own workdir, writes FAITHFUL there and leaves the outline run's STATUS alone.
  FAKE="$ROOT/tests/fake_agent.py"
  if [ -f "$FAKE" ]; then
    cat > "$T/agents.json" <<EOF
{"writer": {"argv": ["python3", "-I", "$FAKE"], "family": "fake-a", "stdout": "log", "timeout_s": 60},
 "writer-high": {"extends": "writer"},
 "reviewer": {"argv": ["python3", "-I", "$FAKE"], "family": "fake-b", "stdout": "report", "min_chars": 2000, "timeout_s": 60}}
EOF
    OV=(--agents "$T/agents.json" --var "project=a test" --var "lean_root=$T" --var "map=$T" --var "sections=")
    $PY "$DRIVER" "$AS/rollout.outlines.example.json" --workdir "$T/ow" --only IV.1 "${OV[@]}" > "$T/run1.txt" 2>&1 \
      || { cat "$T/run1.txt" >&2; fail "outline run with the stand-in agent"; }
    [ "$(cat "$T/ow/IV.1/STATUS")" = EDITED ] || fail "outline run: STATUS should be EDITED"
    FAKE_VERDICT='*/fidelity/*=FAITHFUL' $PY "$DRIVER" "$AS/rollout.compress.example.json" --workdir "$T/cw" --only IV.1 \
      "${OV[@]}" --var "outlines_workdir=$T/ow" > "$T/run2.txt" 2>&1 || { cat "$T/run2.txt" >&2; fail "compression run"; }
    [ "$(cat "$T/cw/IV.1/STATUS")" = FAITHFUL ] || fail "compression run: STATUS should be FAITHFUL in its own workdir"
    [ "$(cat "$T/ow/IV.1/STATUS")" = EDITED ] || fail "the compression run changed the published status of the notes"
    [ -s "$T/cw/IV.1/compress/notes.md" ] && [ -s "$T/cw/IV.1/fidelity/packet/notes.md" ] || fail "notes not seeded"
    ok "outline run (STATUS EDITED) and compression run in its own workdir (STATUS FAITHFUL there; EDITED kept)"
  fi
else
  echo "skip: rollout configurations (no $DRIVER)"
fi
echo "smoke_coarse-graining: all checks passed"
