#!/usr/bin/env bash
# Smoke test of the lean-dependency-graph skill.
#   - --help of every script; package_build.sh -h, --dry-run and refusal of a branch name; extract.py --dry-run;
#   - a synthetic set of Extract.lean records through build_graph_db.py, closure.py and compare_usage.py, with the
#     expected counts (auxiliary attribution, dead and expanded auxiliaries, metaprogramming, private names,
#     statement/proof parts, duplicates, sorry flag, classes of differences, header detection);
#   - the statement closure: theorem -> Def -> Inner (Inner only in Def's body) keeps Inner, which
#     `--parts statement,both` misses; a structure brings its constructor and the types of its fields;
#   - refusals: an output directory inside the checkout (extract.py, package_build.sh), a partial --parts write;
#   - only if ENSLOP_LEAN is set (e.g. ENSLOP_LEAN="lean +leanprover/lean4:v4.32.0"): compile a tiny module with that
#     Lean, run the real extraction on it, and recompute its closure with ClosureCheck.lean (one Lean process at a
#     time).
# Usage: tests/smoke_lean-dependency-graph.sh        (exit 0 = all passed)
set -euo pipefail
ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
SK="$ROOT/skills/lean-dependency-graph/scripts"
T=$(mktemp -d)
trap 'rm -rf "$T"' EXIT
fail() { echo "FAIL: $*" >&2; exit 1; }
ok() { echo "ok: $*"; }
PY="python3 -I -B"

# 1. help texts
for s in extract.py build_graph_db.py closure.py compare_usage.py; do
  $PY "$SK/$s" --help > "$T/help.txt" || fail "$s --help"
  grep -q "example" "$T/help.txt" || fail "$s --help has no example"
done
bash "$SK/package_build.sh" -h > /dev/null || fail "package_build.sh -h"
ok "help texts"

# 2. synthetic Extract.lean output (module, constant, record, a, b)
mkdir -p "$T/raw"
tab() { printf '%s\t%s\t%s\t%s\t%s\n' "$@"; }
{
  tab M.A Foo.thm decl theorem ""; tab M.A Foo.thm range 10 20; tab M.A Foo.thm type Foo.Def ""
  tab M.A Foo.thm value Foo.thm._proof_1 ""
  tab M.A Foo.thm._proof_1 decl theorem ""; tab M.A Foo.thm._proof_1 type Foo.lemma ""
  tab M.A Foo.Def decl def ""; tab M.A Foo.Def range 3 5; tab M.A Foo.Def type Nat ""
  tab M.A Foo.Def value Foo.Struct ""
  tab M.A Foo.Def.eq_1 decl theorem ""; tab M.A Foo.Def.eq_1 type Foo.Unused ""
  tab M.A Foo.lemma decl theorem ""; tab M.A Foo.lemma range 6 8; tab M.A Foo.lemma type Foo.Def ""
  tab M.A Foo.lemma doc 'A lemma\nwith two lines.' ""
  tab M.A Foo.Unused decl def ""; tab M.A Foo.Unused range 22 23
  tab M.A Foo.Struct decl inductive ""; tab M.A Foo.Struct range 1 2
  tab M.A Foo.Struct.mk decl ctor ""; tab M.A Foo.Struct.mk parent Foo.Struct ""; tab M.A Foo.Struct.mk type Foo.Struct ""
  tab M.A Foo.Struct.x decl def ""; tab M.A Foo.Struct.x tag projection ""; tab M.A Foo.Struct.x range 2 2
  tab M.A Foo.Struct.x type Foo.Struct ""
  tab M.A Foo.Struct.rec decl rec ""; tab M.A Foo.Struct.rec type Foo.Struct.mk ""
} > "$T/raw/chunk_00000.tsv"
{
  tab M.B _private.M.B.0.Foo.helper decl theorem ""; tab M.B _private.M.B.0.Foo.helper range 30 31
  tab M.B _private.M.B.0.Foo.helper type Foo.Def ""
  tab M.B Foo.main decl theorem ""; tab M.B Foo.main range 40 50
  tab M.B Foo.main value _private.M.B.0.Foo.helper ""; tab M.B Foo.main value Foo.thm ""
  tab M.B Foo.main value instFooThing ""; tab M.B Foo.main value Lib.thing.eq_1 ""
  tab M.B Foo.main value Foo.main.match_1 ""; tab M.B Foo.main type Nat ""
  tab M.B Foo.main.match_1 decl def ""; tab M.B Foo.main.match_1 value Foo.viaAux ""
  tab M.B instFooThing decl def ""; tab M.B instFooThing tag instance ""; tab M.B instFooThing range 52 53
  tab M.B Lib.thing.eq_1 decl theorem ""; tab M.B Lib.thing.eq_1 type Foo.lemma2 ""
  tab M.B Foo.lemma2 decl theorem ""; tab M.B Foo.lemma2 range 60 61
  tab M.B Foo.viaAux decl def ""; tab M.B Foo.viaAux range 70 72
  tab M.B Foo.notation decl def ""; tab M.B Foo.notation type Lean.ParserDescr ""
  tab M.B Foo.sorryThing decl theorem ""; tab M.B Foo.sorryThing range 80 81; tab M.B Foo.sorryThing value sorryAx ""
} > "$T/raw/chunk_00001.tsv"
$PY "$SK/build_graph_db.py" "$T/raw" --db "$T/g.sqlite" --commit 0123456789abcdef0123456789abcdef01234567 \
    --tool-version test > "$T/build.txt" || fail "build_graph_db.py"
q() { $PY -c 'import sqlite3,sys; c=sqlite3.connect(sys.argv[1]); print("|".join(str(x) for r in c.execute(sys.argv[2]) for x in r))' "$T/g.sqlite" "$1"; }
[ "$(q 'select count(*) from nodes')" = 13 ] || fail "13 nodes expected, got $(q 'select count(*) from nodes')"
[ "$(q "select kind from nodes where name='Foo.Struct'")" = structure ] || fail "structure kind"
[ "$(q "select kind from nodes where name='instFooThing'")" = instance ] || fail "instance kind"
[ "$(q "select kind from nodes where name='Foo.Struct.x'")" = field ] || fail "field kind"
[ "$(q "select count(*) from nodes where name='Foo.helper'")" = 1 ] || fail "private prefix not stripped"
[ "$(q "select owner||','||status from aux where name='Foo.thm._proof_1'")" = "Foo.thm,live" ] || fail "proof aux owner"
[ "$(q "select status from aux where name='Foo.Def.eq_1'")" = dead ] || fail "dead aux"
[ "$(q "select status from aux where name='Lib.thing.eq_1'")" = expanded ] || fail "expanded aux"
[ "$(q "select status from aux where name='Foo.notation'")" = meta ] || fail "meta constant"
[ "$(q "select count(*) from edges where src='Foo.Def' and dst='Foo.Unused'")" = 0 ] || fail "dead aux made an edge"
[ "$(q "select part||','||direct from edges where src='Foo.thm' and dst='Foo.lemma'")" = "proof,0" ] || fail "aux edge part"
[ "$(q "select part from edges where src='Foo.thm' and dst='Foo.Def'")" = statement ] || fail "statement edge"
[ "$(q "select count(*) from edges where src='Foo.main' and dst='Foo.lemma2'")" = 1 ] || fail "expanded aux edge"
[ "$(q "select doc from nodes where name='Foo.lemma'")" = "A lemma
with two lines." ] || fail "docstring unescaped"
[ "$(q "select lines from nodes where name='Foo.thm'")" = 11 ] || fail "lines from range"
[ "$(q "select sorry from nodes where name='Foo.sorryThing'")" = 1 ] || fail "sorry flag"
ok "build_graph_db.py: nodes, kinds, owners, liveness, expansion, parts, docs, sorry ($(q 'select count(*) from edges') edges)"

# duplicates stop the build; --exclude-module resolves them
mkdir -p "$T/raw2"; cp "$T/raw"/chunk_*.tsv "$T/raw2/"
tab M.C Foo.main decl theorem "" > "$T/raw2/chunk_00002.tsv"
if $PY "$SK/build_graph_db.py" "$T/raw2" --db "$T/dup.sqlite" 2> "$T/dup.txt"; then fail "duplicate not refused"; fi
grep -q "declared in more than one module" "$T/dup.txt" || fail "duplicate message"
$PY "$SK/build_graph_db.py" "$T/raw2" --db "$T/dup.sqlite" --exclude-module '^M\.C$' > /dev/null || fail "--exclude-module"
ok "duplicate declarations refused, resolved by --exclude-module"

# 3. closure
printf 'Foo.main  # the root\n' > "$T/roots.txt"
$PY "$SK/closure.py" --db "$T/g.sqlite" --roots-file "$T/roots.txt" --export "$T/used.txt" > "$T/closure.txt" \
  || fail "closure.py"
[ "$(wc -l < "$T/used.txt")" -eq 9 ] || fail "closure of 9 expected, got $(wc -l < "$T/used.txt")"
grep -q '^Foo.viaAux$' "$T/used.txt" || fail "Foo.viaAux should be used"
if grep -q '^Foo.Unused$' "$T/used.txt"; then fail "Foo.Unused should not be used"; fi
[ "$($PY "$SK/closure.py" --db "$T/g.sqlite" --why Foo.Struct)" = "Foo.main -> Foo.helper -> Foo.Def -> Foo.Struct" ] \
  || fail "--why chain"
set +e
$PY "$SK/closure.py" --db "$T/g.sqlite" Foo.sorryThing --dry-run > /dev/null 2>&1; rc=$?
$PY "$SK/closure.py" --db "$T/g.sqlite" No.Such.Root --dry-run > /dev/null 2>&1; rc2=$?
set -e
[ $rc -eq 1 ] || fail "a used sorry should exit 1 (got $rc)"
[ $rc2 -eq 2 ] || fail "a missing root should exit 2 (got $rc2)"
ok "closure.py: 9 declarations, --why chain, sorry check, missing root"

# 4. comparison with a synthetic usage record
{
  printf 'module\tdeclaration\tstatus\n'
  for n in Foo.main Foo.thm._proof_1 _private.M.B.0.Foo.helper Foo.Def.eq_1 Foo.lemma Foo.Struct Foo.Struct.mk \
           instFooThing Foo.lemma2 Mathlib.thing; do printf 'M\t%s\tused\n' "$n"; done
  printf 'M\tFoo.Unused\toutside\n'
} > "$T/usage.tsv"
$PY "$SK/compare_usage.py" --db "$T/g.sqlite" --record "$T/usage.tsv" --column declaration \
    --filter status=used,headline --out-dir "$T/cmp" > "$T/cmp.txt" || fail "compare_usage.py"
grep -q 'compare_usage: closure 9, record 9, intersection 8, difference 2' "$T/cmp.txt" || fail "comparison counts"
grep -q 'constructor whose inductive type is in the closure: 1' "$T/cmp.txt" || fail "constructor class"
grep -q 'reached only through auxiliary constants: 1' "$T/cmp.txt" || fail "auxiliary class"
grep -q 'not attributed (not in the graph): 1' "$T/cmp.txt" || fail "unattributed name"
set +e; $PY "$SK/compare_usage.py" --db "$T/g.sqlite" --record "$T/usage.tsv" --column declaration \
    --filter status=used --max-diff 1 > /dev/null; rc=$?; set -e
[ $rc -eq 1 ] || fail "--max-diff should exit 1"
# a one-name-per-line record: the first line is data unless it is a header word (a note says which)
printf 'Foo.main\nFoo.thm\n' > "$T/names1.txt"; printf 'name\nFoo.main\nFoo.thm\n' > "$T/names2.txt"
$PY "$SK/compare_usage.py" --db "$T/g.sqlite" --record "$T/names1.txt" > "$T/h1.txt" 2> "$T/h1.err" || fail "names1"
grep -q 'record: 2 rows kept' "$T/h1.txt" || fail "first name read as a header"
grep -q "read as data" "$T/h1.err" || fail "no note on the header decision"
$PY "$SK/compare_usage.py" --db "$T/g.sqlite" --record "$T/names2.txt" > "$T/h2.txt" 2> "$T/h2.err" || fail "names2"
grep -q 'record: 2 rows kept' "$T/h2.txt" || fail "header word read as a name"
grep -q "read as a header" "$T/h2.err" || fail "no note on the detected header"
$PY "$SK/compare_usage.py" --db "$T/g.sqlite" --record "$T/names2.txt" --no-header 2> /dev/null \
  | grep -q 'record: 3 rows kept' || fail "--no-header"
ok "compare_usage.py: attribution, classes, --max-diff, header detection"

# 3b. statement closure (S.thm states S.Def; S.Def's body uses S.Inner; S.thm's proof uses
# S.lemma, whose statement uses S.Aux; S.thm also states S.Str, whose constructor takes an S.Field)
mkdir -p "$T/raw3"
{
  tab S S.thm decl theorem ""; tab S S.thm range 1 3; tab S S.thm type S.Def ""; tab S S.thm type S.Str ""
  tab S S.thm value S.lemma ""
  tab S S.Def decl def ""; tab S S.Def range 5 6; tab S S.Def type Nat ""; tab S S.Def value S.Inner ""
  tab S S.Inner decl def ""; tab S S.Inner range 8 9
  tab S S.lemma decl theorem ""; tab S S.lemma range 11 12; tab S S.lemma type S.Aux ""
  tab S S.Aux decl def ""; tab S S.Aux range 14 14
  tab S S.Str decl inductive ""; tab S S.Str range 16 18
  tab S S.Str.mk decl ctor ""; tab S S.Str.mk parent S.Str ""; tab S S.Str.mk type S.Str ""
  tab S S.Str.mk type S.Field ""
  tab S S.Str.x decl def ""; tab S S.Str.x tag projection ""; tab S S.Str.x range 17 17; tab S S.Str.x type S.Str ""
  tab S S.Field decl def ""; tab S S.Field range 20 20
} > "$T/raw3/chunk_00000.tsv"
$PY "$SK/build_graph_db.py" "$T/raw3" --db "$T/s.sqlite" > /dev/null || fail "build of the statement-closure graph"
$PY "$SK/closure.py" --db "$T/s.sqlite" S.thm --parts statement,both --dry-run --export "$T/p.txt" > /dev/null \
  || fail "closure --parts statement,both --dry-run"
[ "$(tr '\n' ' ' < "$T/p.txt")" = "S.Def S.Str S.thm " ] || fail "--parts statement,both: $(tr '\n' ' ' < "$T/p.txt")"
$PY "$SK/closure.py" --db "$T/s.sqlite" S.thm --statement-closure --export "$T/st.txt" > /dev/null \
  || fail "closure --statement-closure"
[ "$(tr '\n' ' ' < "$T/st.txt")" = "S.Def S.Field S.Inner S.Str S.Str.mk S.thm " ] \
  || fail "statement closure: $(tr '\n' ' ' < "$T/st.txt")"
[ "$($PY "$SK/closure.py" --db "$T/s.sqlite" S.thm --statement-closure --why S.Inner)" = "S.thm -> S.Def -> S.Inner" ] \
  || fail "--statement-closure --why"
[ "$($PY -c 'import sqlite3,sys; print(sqlite3.connect(sys.argv[1]).execute("select count(*) from nodes where used=1").fetchone()[0])' "$T/s.sqlite")" = 0 ] \
  || fail "--statement-closure wrote used = 1"
set +e
$PY "$SK/closure.py" --db "$T/s.sqlite" S.thm --parts statement,both > /dev/null 2>&1; rc=$?
set -e
[ $rc -eq 2 ] || fail "a partial --parts must not write used = 1 (exit 2, got $rc)"
ok "closure.py --statement-closure: keeps S.Inner (missed by --parts statement,both), constructors, field types"

# 5. extract.py and package_build.sh without running Lean or Lake
mkdir -p "$T/lib/A" && : > "$T/lib/A/B.olean" && : > "$T/lib/C.olean"
$PY "$SK/extract.py" --lib-dir "$T/lib" --out-dir "$T/out" --chunk-size 1 --dry-run > "$T/plan.txt" || fail "extract --dry-run"
grep -q 'plan: 2 modules' "$T/plan.txt" || fail "extract plan"
[ ! -e "$T/out" ] || fail "extract --dry-run wrote files"
mkdir -p "$T/src/.lake/build/lib"
bash "$SK/package_build.sh" --source "$T/src" --commit 0123456 --out "$T/rel" --targets "A B" \
    --repo-url https://example.invalid/r --dry-run > "$T/pk.txt" || fail "package_build --dry-run"
grep -q 'lake build --no-build A B' "$T/pk.txt" || fail "package plan"
[ ! -e "$T/rel" ] || fail "package --dry-run wrote files"
set +e; bash "$SK/package_build.sh" --source "$T/src" --commit main --out "$T/rel" --targets A 2> /dev/null; rc=$?; set -e
[ $rc -eq 2 ] || fail "a branch name should be refused with exit 2"
set +e
bash "$SK/package_build.sh" --source "$T/src" --commit 0123456 --out "$T/src/release" --targets A \
    --repo-url https://example.invalid/r --dry-run > /dev/null 2>&1; rc=$?
mkdir -p "$T/src/.lake/build/lib/lean/A" && : > "$T/src/.lake/build/lib/lean/A/B.olean"
$PY "$SK/extract.py" --lib-dir "$T/src/.lake/build/lib/lean" --out-dir "$T/src/raw" --dry-run > /dev/null 2>&1; rc2=$?
set -e
[ $rc -eq 2 ] || fail "package_build.sh must refuse --out inside the checkout (got $rc)"
[ $rc2 -eq 2 ] || fail "extract.py must refuse --out-dir inside the checkout (got $rc2)"
ok "extract.py and package_build.sh dry runs; output inside the checkout refused"

# 6. optional: real extraction of a tiny module with the given Lean
if [ -n "${ENSLOP_LEAN:-}" ]; then
  mkdir -p "$T/lean/Tiny" "$T/leanout/Tiny"
  cat > "$T/lean/Tiny/Basic.lean" <<'EOF'
/-- Twice a number. -/
def Tiny.double (n : Nat) : Nat := n + n

theorem Tiny.double_eq (n : Nat) : Tiny.double n = n + n := rfl

structure Tiny.Pt where
  x : Nat
  y : Nat

instance : Inhabited Tiny.Pt := ⟨⟨0, 0⟩⟩

theorem Tiny.main : Tiny.double 2 = 4 := by rw [Tiny.double_eq]
EOF
  (cd "$T/lean" && $ENSLOP_LEAN Tiny/Basic.lean -o "$T/leanout/Tiny/Basic.olean") || fail "compiling the tiny module"
  $PY "$SK/extract.py" --lib-dir "$T/leanout" --out-dir "$T/xraw" --lean-cmd "$ENSLOP_LEAN --run" > "$T/x.txt" \
    || fail "extract.py with $ENSLOP_LEAN"
  $PY "$SK/build_graph_db.py" "$T/xraw" --db "$T/x.sqlite" > /dev/null || fail "build from real extraction"
  $PY "$SK/closure.py" --db "$T/x.sqlite" Tiny.main > /dev/null || fail "closure of Tiny.main"
  x() { $PY -c 'import sqlite3,sys; c=sqlite3.connect(sys.argv[1]); print("|".join(str(v) for r in c.execute(sys.argv[2]) for v in r))' "$T/x.sqlite" "$1"; }
  [ "$(x "select line||'-'||line_end from nodes where name='Tiny.double_eq'")" = "4-4" ] || fail "range of Tiny.double_eq"
  [ "$(x "select doc from nodes where name='Tiny.double'")" = "Twice a number. " ] || fail "docstring of Tiny.double"
  [ "$(x "select count(*) from nodes where kind='instance'")" -ge 1 ] || fail "instance tag"
  [ "$(x "select group_concat(name) from (select name from nodes where used=1 order by name)")" = \
    "Tiny.double,Tiny.double_eq,Tiny.main" ] || fail "closure of Tiny.main: $(x "select group_concat(name) from nodes where used=1")"
  ok "real extraction with $ENSLOP_LEAN: ranges, docstrings, instance tag, closure"
  LEAN_PATH="$T/leanout" $ENSLOP_LEAN --run "$SK/ClosureCheck.lean" "$T/cc.txt" --import Tiny.Basic Tiny.main \
    2> "$T/cc.log" || { cat "$T/cc.log" >&2; fail "ClosureCheck.lean with $ENSLOP_LEAN"; }
  [ "$(tr '\n' ' ' < "$T/cc.txt")" = "Tiny.double Tiny.double_eq Tiny.main " ] || fail "ClosureCheck output"
  $PY "$SK/compare_usage.py" --db "$T/x.sqlite" --record "$T/cc.txt" --no-header > "$T/cc-cmp.txt" \
    || fail "compare_usage.py on the ClosureCheck output"
  grep -q 'intersection 3, difference 0' "$T/cc-cmp.txt" || fail "ClosureCheck and the graph differ"
  ok "ClosureCheck.lean with $ENSLOP_LEAN: the same closure as the graph"
else
  echo "skip: real extraction (set ENSLOP_LEAN, e.g. \"lean +leanprover/lean4:v4.32.0\", to run it)"
fi
echo "smoke_lean-dependency-graph: all checks passed"
