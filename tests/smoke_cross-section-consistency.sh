#!/usr/bin/env bash
# Smoke test of the cross-section-consistency skill: cross_refs.py on a synthetic three-section TeX project (a cycle, a
# range citation, a display cited from inside a proof), route_requests.py with and without --config, and its rollout
# configs run with the writing-workflow driver and tests/fake_agent.py (no model is called).
# Usage: tests/smoke_cross-section-consistency.sh [-h]
set -euo pipefail
if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then sed -n '2,5p' "$0"; exit 0; fi

HERE="$(cd "$(dirname "$0")" && pwd)"
SK="$HERE/../skills/cross-section-consistency"
XS="$SK/scripts"
RO="$HERE/../skills/writing-workflow/scripts/rollout.py"
FAKE="$HERE/fake_agent.py"
T="$(mktemp -d)"
trap 'rm -rf "$T"' EXIT
PY="python3 -I -B"
n=0
pass() { n=$((n + 1)); echo "ok $n - $1"; }
die() { echo "FAIL: $1" >&2; exit 1; }
expect_rc() { local want="$1"; shift; local rc=0; "$@" > "$T/last.out" 2>&1 || rc=$?
  [[ "$rc" == "$want" ]] || { cat "$T/last.out" >&2; die "expected exit $want, got $rc: $*"; }; }
has() { grep -q -- "$2" "$1" || { echo "--- $1" >&2; tail -20 "$1" >&2; die "'$2' not found in $1"; }; }

$PY "$XS/cross_refs.py" --help > /dev/null
$PY "$XS/route_requests.py" --help > /dev/null
pass "--help"

# ------------------------------------------------------------------ synthetic manuscript
M="$T/ms"; mkdir -p "$M/parts"
cat > "$M/main.tex" <<'EOF'
\documentclass{article}
\newtheorem{lemma}{Lemma}[section]
\newtheorem{definition}[lemma]{Definition}
\newtheorem{remark}[lemma]{Remark}
\begin{document}
\input{parts/secA}
\input{parts/secB}
\include{parts/secC}
\end{document}
EOF
cat > "$M/parts/secA.tex" <<'EOF'
\section{Alpha}\label{sec:A}
\begin{lemma}\label{lem:A1}
Statement A1, for the objects of Definition~\ref{def:B2}.
\end{lemma}
\begin{proof}
By Lemma~\ref{lem:B1} and the bound \eqref{eq:B1-inner}.
\end{proof}
\begin{remark}
Lemma~\ref{lem:C1} below uses this.
\end{remark}
% a commented citation \ref{lem:C1} is ignored
EOF
cat > "$M/parts/secB.tex" <<'EOF'
\section{Beta}\label{sec:B}
\begin{lemma}\label{lem:B1}
B1.
\end{lemma}
\begin{proof}
Uses Lemma~\ref{lem:C1}.
\begin{equation}\label{eq:B1-inner} x \le y \end{equation}
\end{proof}
\begin{definition}\label{def:B2}
B2.
\end{definition}
\begin{lemma}\label{lem:B3}
B3.
\end{lemma}
EOF
cat > "$M/parts/secC.tex" <<'EOF'
\section{Gamma}\label{sec:C}
\begin{lemma}\label{lem:C1}
C1.
\end{lemma}
\begin{proof}[Proof of Lemma~\ref{lem:C1}]
By Lemma~\ref{lem:A1} and Lemmas~\ref{lem:B1}--\ref{lem:B3}.
\end{proof}
\begin{verbatim}
\ref{lem:A1} inside verbatim is ignored
\end{verbatim}
EOF
cat > "$M/main.aux" <<'EOF'
\relax
\newlabel{sec:A}{{1}{1}}
\newlabel{lem:A1}{{1.1}{1}}
\newlabel{sec:B}{{2}{1}}
\newlabel{lem:B1}{{2.1}{1}}
\newlabel{eq:B1-inner}{{2.1}{1}}
\newlabel{def:B2}{{2.2}{1}}
\newlabel{lem:B3}{{2.3}{2}}
\@input{parts/secC.aux}
EOF
printf '\\newlabel{sec:C}{{3}{2}}\n\\newlabel{lem:C1}{{3.1}{2}}\n' > "$M/parts/secC.aux"
printf 'parts/secA.tex\tA\nparts/secB.tex\tB\nparts/secC.tex\tC\n' > "$T/units.tsv"
cd "$T"
expect_rc 0 $PY "$XS/cross_refs.py" ms/main.tex --aux ms/main.aux --unit-map units.tsv --out xref
has "$T/last.out" "8 cross-unit citations (6 in proofs) over 5 unit pairs; 1 range citation(s); 2 candidate cycle"
python3 - "$T/xref" <<'EOF'
import csv, sys
from pathlib import Path
d = Path(sys.argv[1])
rows = lambda f: list(csv.DictReader(open(d / f), delimiter="\t"))
cit = rows("citations.tsv")
assert len(cit) == 8, len(cit)
eq = [r for r in cit if r["cited_label"] == "eq:B1-inner"]
assert eq and eq[0]["cited_where"] == "proof" and eq[0]["cited_owner"] == "lem:B1", eq
assert {(r["citing_unit"], r["context"]) for r in cit if r["cited_label"] == "lem:C1"} == {("A", "env:remark"), ("B", "proof")}
assert [r["printed"] for r in cit if r["cited_label"] == "lem:C1"] == ["3.1", "3.1"]
assert not any(r["citing_file"] == "parts/secC.tex" and r["citing_line"] == "5" for r in cit), "proof title counted"
assert sum(r["cited_label"] == "lem:A1" for r in cit) == 1, "comment or verbatim citation counted"
assert {r["citing_statement"] for r in cit if r["citing_unit"] == "C"} == {"lem:C1"}
rng = rows("ranges.tsv")
assert len(rng) == 1 and rng[0]["spanned"] == "3" and rng[0]["spanned_kinds"] == "definition 1, lemma 2", rng
assert rng[0]["first_printed"] == "2.1" and rng[0]["last_printed"] == "2.3"
cyc = [r["cycle_path"] for r in rows("cycles.tsv")]
assert "lem:A1 -> lem:B1 -> lem:C1 -> lem:A1" in cyc and "lem:B1 -> lem:C1 -> lem:B1" in cyc, cyc
edges = {(r["from"], r["to"]) for r in rows("edges.tsv")}
assert ("lem:A1", "lem:C1") not in edges, "a remark gave a graph edge"
pairs = {(r["citing_unit"], r["cited_unit"]): r for r in rows("pairs.tsv")}
assert pairs[("A", "B")]["displays_from_proofs"] == "1" and pairs[("C", "B")]["range_citations"] == "2"
assert (d / "by-pair" / "A--B.tsv").is_file() and len(list((d / "by-pair").glob("*.tsv"))) == 5
EOF
pass "cross_refs: 8 routed citations, a display cited from inside a proof, the range spanning 3 labels, cycles, printed numbers"

cat > "$T/one.tex" <<'EOF'
\documentclass{article}
\newtheorem{theorem}{Theorem}
\begin{document}
\section{Setting}\label{sec:set}
\begin{theorem}\label{thm:main}
Main, from Theorem~\ref{thm:key}.
\end{theorem}
\section{Proofs}\label{sec:proof}
\begin{theorem}\label{thm:key}
Key.
\end{theorem}
\begin{proof}
Uses \ref{thm:main} and \ref{thm:missing}.
\end{proof}
\begin{theorem}\label{thm:key}
Twice.
\end{theorem}
\end{document}
EOF
expect_rc 1 $PY "$XS/cross_refs.py" one.tex --unit section --out xs
has xs/unresolved.tsv "UNDEFINED	thm:missing"
has xs/unresolved.tsv "DUPLICATE	thm:key"
has xs/cycles.tsv "thm:main -> thm:key -> thm:main"
has xs/citations.tsv "sec:set	one.tex	6	statement	thm:main"
pass "cross_refs --unit section: units named by their labels; undefined and duplicate labels exit 1"

# ------------------------------------------------------------------ requests routed through the inbox
mkdir -p wd/A/w1 wd/B wd/C
sed -e 's/^- To: .*/- To: B/' -e 's/^- Statement: .*/- Statement: For every admissible input the uniform bound holds./' \
    -e '/^  it may continue/d' "$SK/assets/REQUESTS.template.md" > wd/A/w1/REQUESTS.md
expect_rc 0 $PY "$XS/route_requests.py" wd --stage w1
has "$T/last.out" "A -> B	new"
expect_rc 0 $PY "$XS/route_requests.py" wd --stage w1 --deliver
has wd/B/INBOX.md "uniform bound holds"
expect_rc 0 $PY "$XS/route_requests.py" wd --stage w1 --deliver
has "$T/last.out" "delivered earlier"
[[ "$(grep -c '^## Request' wd/B/INBOX.md)" == 1 ]] || die "request delivered twice"
mkdir -p wd/D/w1 && printf '## R1\n- To: Z\n- Statement: something\n\n## R2\n- To: B\n' > wd/D/w1/REQUESTS.md
expect_rc 1 $PY "$XS/route_requests.py" wd --stage w1
has "$T/last.out" "UNKNOWN UNIT 'Z'"
has "$T/last.out" "INCOMPLETE"
rm -r wd/D
pass "route_requests: list, deliver once, unknown unit and incomplete requests exit 1"

# --config: the unit keys come from the rollout config (its extends chain resolved), so a unit that has not run yet,
# and has no directory, receives the request; without --config it is unknown, with a message saying why.
mkdir -p wd/D/w1 && printf '## R1\n- To: N\n- Statement: The bound for every admissible input.\n' > wd/D/w1/REQUESTS.md
printf '{"units": {"A": {}, "B": {}, "C": {}, "D": {}}, "stages": []}\n' > units-base.json
printf '{"extends": "units-base.json", "units": {"N": {"title": "a section not yet run"}}}\n' > units.json
expect_rc 1 $PY "$XS/route_requests.py" wd --stage w1
has "$T/last.out" "UNKNOWN UNIT 'N' (no directory in WORKDIR)"
has "$T/last.out" "no --config"
expect_rc 0 $PY "$XS/route_requests.py" wd --config units.json --stage w1 --deliver --select D/w1/R1
has "$T/last.out" "D -> N	DELIVERED"
has wd/N/INBOX.md "The bound for every admissible input"
expect_rc 1 $PY "$XS/route_requests.py" wd --config units-base.json --stage w1
has "$T/last.out" "UNKNOWN UNIT 'N' (not a unit of units-base.json)"
expect_rc 2 $PY "$XS/route_requests.py" wd --config no-such.json
rm -r wd/D wd/N
pass "route_requests --config: a configured unit without a directory receives its request; unknown otherwise"

# ------------------------------------------------------------------ the configs, with the writing-workflow driver
mkdir -p lean work/spine && echo "-- lean" > lean/Main.lean && echo contracts > work/spine/SPINE.md
echo "natural spine" > work/spine/SPINE-NATURAL.md
for f in STYLE DETAIL-STANDARD NOTATION; do echo "# $f" > "work/$f.md"; done
echo "# merged mismatch table" > report.md
cat > agents.json <<EOF
{"writer": {"argv": ["python3", "-I", "$FAKE"], "family": "fake-a", "stdout": "log", "timeout_s": 60},
 "writer-high": {"extends": "writer"},
 "reviewer": {"argv": ["python3", "-I", "$FAKE"], "family": "fake-b", "stdout": "report", "min_chars": 2000, "timeout_s": 60}}
EOF
UNITS='{"G1": {"title": "B cited by A and C", "vars": {"rows": ["A--B.tsv", "C--B.tsv"], "cycles": ["Y1", "Y2"]}},
        "G2": {"title": "the other pairs", "vars": {"rows": ["A--C.tsv", "B--C.tsv", "C--A.tsv"], "cycles": "none"}}}'
echo "{\"extends\": \"$SK/assets/rollout.routed-check.example.json\", \"units\": $UNITS}" > check.json
echo "{\"extends\": \"$SK/assets/rollout.routed-recheck.example.json\", \"units\": $UNITS}" > recheck.json
cat > repair.json <<EOF
{"extends": "$SK/assets/rollout.repair.example.json",
 "units": {"A": {"title": "Alpha", "vars": {"number": "1", "files": "parts/secA.tex"}},
           "B": {"title": "Beta", "vars": {"number": "2", "files": "parts/secB.tex"}}}}
EOF
V=(--agents "$T/agents.json" --var "manuscript=$M" --var "xref=$T/xref" --var "lean=$T/lean" --var "graph_db=$T/g.sqlite"
   --var "report=$T/report.md" --var lean_commit=abc --var "work=$T/work")
if [[ ! -f "$SK/../exposition-standards/scripts/check_shape.py" ]]; then
  mkdir -p stubs; for s in check_shape.py check_vocabulary.py; do printf 'print("stub")\n' > "stubs/$s"; done
  V+=(--var "standards=$T/stubs")
fi
for c in "$SK/assets/rollout.routed-check.example.json" "$SK/assets/rollout.routed-recheck.example.json" "$SK/assets/rollout.repair.example.json"; do
  expect_rc 0 $PY "$RO" "$c" --workdir dry "${V[@]}" --dry-run
done
if grep -rl '{{' dry/.dry-run > /dev/null; then die "unrendered placeholder in a dry-run prompt"; fi
has dry/.dry-run/E/w5/prompt.md "approved natural spine $T/work/spine/SPINE-NATURAL.md"
has dry/.dry-run/E/w5/prompt.md "^D — Activities and the inductive step"
pass "dry runs of the routed-check, re-check and repair configs: every prompt rendered, natural spine and unit keys named"

FAKE_VERDICT='*/check/*=MISMATCHES 3' expect_rc 0 $PY "$RO" check.json --workdir wd --only G1,G2 "${V[@]}"
has wd/G1/check/routed.md "Verdict: MISMATCHES 3"
has wd/G1/check/prompt-routed.md "A--B.tsv, C--B.tsv"
[[ -f wd/G1/check/packet/xref/by-pair/A--B.tsv && -f wd/G1/check/packet/manuscript/main.tex ]] || die "check packet"
expect_rc 1 $PY "$RO" check.json --workdir wd2 --only G1 "${V[@]}"
has wd2/G1/check/routed.md.rejected "Verdict: PASS"
CC="$HERE/../skills/writing-workflow/scripts/check_coverage.py"
if [[ -f "$CC" ]]; then
  expect_rc 1 $PY "$CC" --register xref/by-pair/A--B.tsv --register xref/by-pair/C--B.tsv --column cited_label wd/G1/check/routed.md
  has "$T/last.out" "NOT MENTIONED	lem:B1"
  # cycles: a group's report against its own cycle ids; every report at once against all of xref/cycles.tsv
  expect_rc 1 $PY "$CC" --labels Y1,Y2 wd/G1/check/routed.md
  has "$T/last.out" "2 label(s); 0 mentioned in 1 report(s)"
  expect_rc 1 $PY "$CC" --register xref/cycles.tsv --column cycle wd/G1/check/routed.md wd/G2/check/routed.md
  has "$T/last.out" "2 label(s); 0 mentioned in 2 report(s)"
fi
pass "routed-check: one checker per group on a frozen packet; a report without the verdict vocabulary is rejected; cited labels the report never names are listed"

expect_rc 0 $PY "$RO" repair.json --workdir wd --only A,B "${V[@]}"
has wd/B/w5/prompt.md "uniform bound holds"
[[ -s wd/A/w5/response-w5.tsv && -s wd/B/w5/secB.tex && ! -s wd/B/INBOX.md ]] || die "repair round"
has wd/B/inbox-archive.md "uniform bound holds"
FAKE_VERDICT='*/recheck1/*=ALL RESOLVED' expect_rc 0 $PY "$RO" recheck.json --workdir wd --only G1,G2 "${V[@]}"
has wd/G1/recheck1/prompt-routed.md "wd/G1/check/routed.md"
[[ "$(cat wd/G1/STATUS)" == RESOLVED && "$(cat wd/G2/STATUS)" == RESOLVED ]] || die "convergence status"
pass "repair round w5 with the delivered request, then the targeted re-check: both groups RESOLVED"

echo "smoke_cross-section-consistency: $n checks passed"
