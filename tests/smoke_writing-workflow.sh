#!/usr/bin/env bash
# Smoke test of the writing-workflow skill: the shared agent layer (agent_cli.py, rollout.py, make_packet.py,
# verify_packet.py, check_allowance.py, check_coverage.py) and the example configs, driven by tests/fake_agent.py.
# Usage: tests/smoke_writing-workflow.sh [-h]
set -euo pipefail
if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then sed -n '2,4p' "$0"; exit 0; fi

HERE="$(cd "$(dirname "$0")" && pwd)"
SK="$HERE/../skills/writing-workflow"
SC="$SK/scripts"
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
hasnt() { if grep -q -- "$2" "$1"; then die "'$2' unexpectedly found in $1"; fi; }
calls() { grep -c -- "^$1 " "$T/calls.log" || true; }

# ------------------------------------------------------------------ --help of every script
for s in agent_cli.py rollout.py make_packet.py verify_packet.py check_allowance.py check_coverage.py; do
  $PY "$SC/$s" --help > /dev/null || die "$s --help"
done
$PY "$FAKE" --help > /dev/null
pass "--help of every script"

# ------------------------------------------------------------------ rendering
cat > "$T/render.py" <<EOF
import importlib.util, sys
sys.dont_write_bytecode = True
spec = importlib.util.spec_from_file_location("agent_cli", "$SC/agent_cli.py")
m = importlib.util.module_from_spec(spec); sys.modules["agent_cli"] = m; spec.loader.exec_module(m)
out = m.render(r"Bound \$\frac{a}{b}\$ in {{x}}; {{{{literal}} and \mathbf{v}.", {"x": "X"})
assert out == r"Bound \$\frac{a}{b}\$ in X; {{literal}} and \mathbf{v}.", out
assert m.render_list(["--add-dir", "{{d}}", "-C", "{{c}}"], {"d": ["/a", "/b"], "c": "/c"}) == ["--add-dir", "/a", "/b", "-C", "/c"]
assert m.render("{{l}}", {"l": ["thm:A", "thm:B"]}) == "thm:A, thm:B"
try:
    m.render("{{nope}}", {}); raise SystemExit("unknown placeholder accepted")
except m.TemplateError:
    pass
print("render ok")
EOF
$PY "$T/render.py" > /dev/null
pass "placeholders: LaTeX braces untouched, {{{{ escape, list splicing, unknown name is an error"

# ------------------------------------------------------------------ agent_cli single jobs
mkdir -p "$T/a/prot"
cat > "$T/a/agents.json" <<EOF
{"rev": {"argv": ["python3", "-I", "$FAKE", "--mode", "report"], "family": "r", "stdout": "report", "min_chars": 2000, "timeout_s": 60},
 "wri": {"argv": ["python3", "-I", "$FAKE", "--mode", "write"], "family": "w", "stdout": "log", "timeout_s": 60}}
EOF
echo 'Review {{what}}.' > "$T/a/p.md"
cd "$T/a"
export FAKE_LOG="$T/calls.log" FAKE_STATE="$T/state"
expect_rc 0 $PY "$SC/agent_cli.py" --agents agents.json --profile rev --prompt p.md --var what=X --out out/r.md --require '(?m)^\**Verdict'
has out/r.md "Verdict: PASS"
expect_rc 2 $PY "$SC/agent_cli.py" --agents agents.json --profile rev --prompt p.md --out out/r2.md
has "$T/last.out" "unknown placeholder"
FAKE_QUOTA='*' expect_rc 1 $PY "$SC/agent_cli.py" --agents agents.json --profile rev --prompt p.md --var what=X --out out/q.md
has "$T/last.out" "status=quota attempts=1"
FAKE_SHORT='*' expect_rc 1 $PY "$SC/agent_cli.py" --agents agents.json --profile rev --prompt p.md --var what=X --out out/s.md
has "$T/last.out" "status=failed attempts=2"
[[ -f out/s.md.rejected && ! -f out/s.md ]] || die "short report not rejected"
echo base > prot/a.txt
FAKE_WRITE_OUTSIDE="*=$T/a/prot/a.txt" expect_rc 1 $PY "$SC/agent_cli.py" --agents agents.json --profile wri --prompt p.md --var what=X --cwd w --protect prot
has "$T/last.out" "status=protect attempts=1"
has w/agent.protect.txt "CHANGED"
expect_rc 0 $PY "$SC/agent_cli.py" --agents agents.json --profile rev --prompt p.md --var what=X --out out/d.md --dry-run
has "$T/last.out" "fake_agent.py --mode report"
[[ ! -f out/d.md ]] || die "dry run ran the agent"
pass "agent_cli: report saved, unknown placeholder, quota stops without retry, short report retried then rejected, protect violation, dry run"

echo "first line" > src.txt
FAKE_READONLY=1 expect_rc 0 $PY "$SC/agent_cli.py" --agents agents.json --profile rev --preflight --read src.txt --run "echo hello" --cwd w
has "$T/last.out" "preflight: profile rev: PASS"
expect_rc 1 $PY "$SC/agent_cli.py" --agents agents.json --profile rev --preflight --read src.txt --cwd w
has "$T/last.out" "FAIL  write"
pass "agent_cli --preflight: read and run checked; a reviewer that can write fails"

# ------------------------------------------------------------------ make_packet / verify_packet / check_allowance
mkdir -p "$T/p/src/sub" "$T/p/repo"
echo one > "$T/p/src/a.tex"; echo two > "$T/p/src/sub/b.md"; echo log > "$T/p/src/agent.log"; echo spine > "$T/p/spine.md"
git -C "$T/p/repo" init -q && echo r > "$T/p/repo/f" && git -C "$T/p/repo" add f \
  && git -C "$T/p/repo" -c user.name=test -c user.email=test@example.invalid commit -qm init
cd "$T/p"
expect_rc 0 $PY "$SC/make_packet.py" pk proposal=src SPINE.md=spine.md --repo repo --exclude agent.log
python3 - "$T/p/pk/manifest.json" <<'EOF'
import json, sys
m = json.load(open(sys.argv[1]))
assert sorted(m["files"]) == ["SPINE.md", "proposal/a.tex", "proposal/sub/b.md"], m["files"]
assert all(len(h) == 64 for h in m["files"].values())
assert list(m["repos"].values())[0]["head"] and m["created_utc"].endswith("Z")
EOF
expect_rc 2 $PY "$SC/make_packet.py" pk src
expect_rc 0 $PY "$SC/verify_packet.py" pk --sources --repos
echo changed >> src/a.tex
expect_rc 1 $PY "$SC/verify_packet.py" pk --sources
has "$T/last.out" "SOURCE-CHANGED  proposal/a.tex"
expect_rc 0 $PY "$SC/verify_packet.py" pk
rm pk/SPINE.md
expect_rc 1 $PY "$SC/verify_packet.py" pk
has "$T/last.out" "MISSING         SPINE.md"
pass "make_packet: DEST= names, excludes, hashes, git HEAD; verify_packet: CHANGED source, MISSING copy"

python3 - <<EOF
import importlib.util, sys
sys.dont_write_bytecode = True
spec = importlib.util.spec_from_file_location("fake", "$FAKE"); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
from pathlib import Path
m.minimal_pdf(Path("$T/p/doc.pdf"), 12)
EOF
expect_rc 1 $PY "$SC/check_allowance.py" --pdf doc.pdf --pages 8
has "$T/last.out" "OVER THE ALLOWANCE"
expect_rc 0 $PY "$SC/check_allowance.py" --pdf doc.pdf --pages 8 --report-only
rm doc.log
expect_rc 0 $PY "$SC/check_allowance.py" --pdf doc.pdf --pages 12
printf 'one two three four\n' > words.md
expect_rc 1 $PY "$SC/check_allowance.py" --words 3 words.md
pass "check_allowance: pages from the LaTeX log or the PDF, report-only, words"

# ------------------------------------------------------------------ check_coverage
mkdir -p "$T/c/r1" && cd "$T/c"
cat > sec.tex <<'EOF'
\section{Beta}\label{sec:B}
\begin{lemma}[Bound]\label{lem:B1}
B1. % \label{lem:commented}
\begin{equation}\label{eq:B1-inner} x \le y \end{equation}
\end{lemma}
\begin{definition}\label{def:B2} B2. \end{definition}
\begin{lemma}\label{lem:B10} B10. \end{lemma}
\begin{verbatim}
\begin{lemma}\label{lem:verbatim}\end{lemma}
\end{verbatim}
EOF
printf 'Sources consulted: the packet.\nlem:B1 is correct. def:B2 too.\nVerdict: CORRECT\n' > r1/math.md
printf 'A prompt naming lem:B10 does not count.\n' > r1/prompt-math.md
printf 'It cites lem:B1.2 and lem:B10x only.\n' > r1/fresh.md
expect_rc 1 $PY "$SC/check_coverage.py" --tex sec.tex r1
has "$T/last.out" "NOT MENTIONED	lem:B10	sec.tex:7 (lemma)"
has "$T/last.out" "3 label(s); 2 mentioned in 2 report(s), 1 never mentioned"
hasnt "$T/last.out" "eq:B1-inner"
expect_rc 0 $PY "$SC/check_coverage.py" --tex sec.tex --report-only r1
expect_rc 1 $PY "$SC/check_coverage.py" --tex sec.tex --env lemma,equation r1
has "$T/last.out" "NOT MENTIONED	eq:B1-inner"
printf '\\begin{maintheorem}\\label{thm:M}\nM.\n\\end{maintheorem}\n' > main-thm.tex
expect_rc 1 $PY "$SC/check_coverage.py" --tex main-thm.tex r1
has "$T/last.out" "NOT MENTIONED	thm:M	main-thm.tex:1 (maintheorem)"
printf '| id | kind | section |\n|---|---|---|\n| `thm:IV` | theorem | 15 |\n| prop:FC | proposition | 15 |\n| lem:C1 | lemma | 12 |\n' > REG.md
printf 'thm:IV passes.\n' > owner.md
expect_rc 1 $PY "$SC/check_coverage.py" --register REG.md --where section=15 owner.md
has "$T/last.out" "NOT MENTIONED	prop:FC	REG.md:4"
hasnt "$T/last.out" "lem:C1"
printf '# commit: abc\nid\tcited_label\nC1\tlem:E1; lem:E2\nC2\tlem:E2\n' > pair.tsv
printf 'lem:E1 MATCH, lem:E2 MISMATCH.\n' > routed.md
expect_rc 0 $PY "$SC/check_coverage.py" --register pair.tsv --column cited_label routed.md
expect_rc 2 $PY "$SC/check_coverage.py" --register pair.tsv --column nope routed.md
expect_rc 2 $PY "$SC/check_coverage.py" --tex sec.tex --env nothing routed.md
expect_rc 1 $PY "$SC/check_coverage.py" --labels Y1,Y2 routed.md
cat > typo.md <<'EOF'
Sources consulted: the images of pages 1-14.

| Page | Quote | Defect | Suggested fix |
|---|---|---|---|
| 6 | "a \| b" | one-word line | rewrite |
| 1 vs 8 | abstract | two wordings | harmonize |
| pp. 12–13 | split formula | break | \mbox |

**Clean pages (none):** 2–5, 7, 9–11.
EOF
expect_rc 1 $PY "$SC/check_coverage.py" --pages 1-14 typo.md
has "$T/last.out" "NOT COVERED	pages 14"
expect_rc 0 $PY "$SC/check_coverage.py" --pages 1–13 typo.md
printf '| Page | Quote | Defect | Fix |\n|---|---|---|---|\n| 21 | x | y | z |\n\nThese page ranges are clean: 15–19 and 22.\n' > typo2.md
expect_rc 1 $PY "$SC/check_coverage.py" --pages 14-23 typo2.md
has "$T/last.out" "NOT COVERED	pages 14, 20, 23"
expect_rc 2 $PY "$SC/check_coverage.py" --pages 14 typo2.md
pass "check_coverage: labels from TeX environments (maintheorem by default), a register (--where, --column), a list; whole-token mentions; prompt files skipped; pages from defects tables and clean-pages lines"

# ------------------------------------------------------------------ rollout: synthetic project
P="$T/proj"
mkdir -p "$P/ms/part1" "$P/ms/part2" "$P/work/spine" "$P/lean"
printf '\\section{Infinite volume}\\label{sec:F}\n' > "$P/ms/part2/F-section.tex"
printf '\\section{Coupling reset}\\label{sec:C}\n' > "$P/ms/part2/C-section.tex"
for f in 01-introduction 02-setting 03-principal; do printf '\\section{%s}\n' "$f" > "$P/ms/part1/$f.tex"; done
printf '%s\n' '\documentclass{article}' '\usepackage{amsthm}' '\newtheorem{maintheorem}{Theorem}' \
  '\newtheorem{theorem}{Theorem}[section]' '\newtheorem{proposition}[theorem]{Proposition}' \
  '\newtheorem{definition}[theorem]{Definition}' '\begin{document}' '\end{document}' > "$P/ms/main.tex"
# The natural spine, shaped like statement-spine's assets/SPINE-NATURAL-template.md: Markdown sections, raw LaTeX
# environments with the main theorems in maintheorem, and the clause map as the table of section 6.
cat > "$P/work/spine/SPINE-NATURAL.md" <<'EOF'
# Natural spine of Part I: a test

Status: approved by the author on 2026-11-01

## 1. Plan of Part I

| Section | Content | Statements | Proved in |
|---|---|---|---|
| 2 | the measure | thm:A, thm:B | 15 |

## 2. Definitions

\begin{definition}[Admissible choice]\label{def:adm}
A choice is admissible if it satisfies the bound.
\end{definition}

- Purpose: names the choices of the main theorems. Interpretation: none.
- Correspondence: `Pkg.Admissible`, DIRECT.

## 3. Main theorems

\begin{maintheorem}\label{thm:A}
There is a measure with the stated properties.
\end{maintheorem}

- Correspondence: `Pkg.main`, DIRECT.

\begin{maintheorem}\label{thm:B}
For every admissible choice, the bound holds.
\end{maintheorem}

## 4. Principal statements

\begin{proposition}[IV]\label{thm:IV}
The infinite-volume limit exists.
\end{proposition}

## 6. Clause map

| clause | destination | scope retained | note |
|---|---|---|---|
| T1.h1 | thm:A | every admissible choice | |
EOF
{ printf '\\section{Setting}\n'; sed -n '/begin{maintheorem}/,/end{maintheorem}/p' "$P/work/spine/SPINE-NATURAL.md"; } > "$P/good-setting.tex"
sed 's/stated properties/stated property/' "$P/good-setting.tex" > "$P/changed-setting.tex"
echo "contracts [clause:T1.h1]" > "$P/work/spine/SPINE.md"
printf 'clause\tdestination\nT1.h1\tthm:A\n' > "$P/work/spine/CLAUSE-MAP.tsv"
for f in STYLE DETAIL-STANDARD NOTATION REGISTER; do echo "# $f" > "$P/work/$f.md"; done
echo "-- lean" > "$P/lean/Main.lean"
cat > "$P/agents.json" <<EOF
{"writer": {"argv": ["python3", "-I", "$FAKE"], "model": "fake-w", "effort": "high", "family": "fake-a", "stdout": "log", "timeout_s": 120},
 "writer-high": {"extends": "writer", "effort": "low"},
 "reviewer": {"argv": ["python3", "-I", "$FAKE"], "model": "fake-r", "effort": "high", "family": "fake-b", "stdout": "report", "min_chars": 2000, "timeout_s": 120}}
EOF
VARS=(--var "manuscript=$P/ms" --var "lean=$P/lean" --var lean_commit=3456e5e --var "graph_db=$P/work/graph.sqlite"
      --var "work=$P/work" --var "disclosure=$P/work/DISCLOSURE.md")
ES="$SK/../exposition-standards/scripts"
REAL_TEX=1
if [[ ! -f "$ES/check_shape.py" || ! -f "$ES/check_vocabulary.py" || ! -f "$ES/check_section.sh" ]] || ! command -v latexmk > /dev/null; then
  mkdir -p "$P/stubs"; for s in check_shape.py check_vocabulary.py; do printf 'print("stub")\n' > "$P/stubs/$s"; done
  printf 'echo "check_section: stub"\n' > "$P/stubs/check_section.sh"
  VARS+=(--var "standards=$P/stubs"); REAL_TEX=0; echo "# exposition-standards checks or latexmk not found: using stubs"
fi
CYCLE="$SK/assets/rollout.section-cycle.example.json"
FIXUP="$SK/assets/rollout.fixup.example.json"
cd "$P"
RO() { $PY "$SC/rollout.py" "$@" --agents "$P/agents.json" "${VARS[@]}"; }

expect_rc 2 $PY "$SC/rollout.py" "$CYCLE" --workdir wd0 --agents "$P/agents.json" --dry-run
has "$T/last.out" "is not set"
expect_rc 0 RO "$CYCLE" --workdir wd0 --dry-run
has "$T/last.out" "5 unit(s), 7 stage(s), 70 prompt(s) rendered"
has "$T/last.out" "compare_statements.py .*SPINE-NATURAL.md 02-setting.tex --labels thm:A,thm:B"
has "$T/last.out" "build: cd .*/F/w3 && bash .*check_section.sh"
has "$T/last.out" "check: bash .*check_section.sh -O -m .*/main.tex -k . F-section.tex"
has "$T/last.out" "build: python3 -I .*/clause_map_check.py --rows-only --map .*/CLAUSE-MAP.tsv"
has "$T/last.out" "build: python3 -I .*/check_allowance.py --pdf .*/F/w3/standalone.pdf --pages 8"
if grep -rl '{{' wd0/.dry-run > /dev/null; then die "unrendered placeholder in a dry-run prompt"; fi
D=wd0/.dry-run
has $D/F/w1/prompt.md "C — Path actions and the coupling reset"
has $D/F/w1/prompt.md "approved natural spine .*SPINE-NATURAL.md"
has $D/F/r1/prompt-owner-thm_IV.md "SPINE-NATURAL.md: a main theorem must be byte for"
has $D/F/r1/prompt-math.md "CLAUSE-MAP.tsv"
has $D/setting/w1/prompt.md "of the opening part (a proposal"
has $D/setting/w1/prompt.md "only those needed to state the main theorems"
has $D/intro/w1/prompt.md "% BEGIN-DISCLOSURE"
has $D/intro/w1/prompt.md "DISCLOSURE.md"
expect_rc 0 RO "$FIXUP" --workdir wd0 --dry-run
expect_rc 2 RO "$CYCLE" --workdir wd0 --stages w9 --dry-run
sed 's/"fake-b"/"fake-a"/' "$P/agents.json" > "$P/same-family.json"
expect_rc 2 $PY "$SC/rollout.py" "$CYCLE" --workdir wd0 --agents "$P/same-family.json" "${VARS[@]}" --dry-run
has "$T/last.out" "same model family"
sed 's/, "family": "fake-b"//' "$P/agents.json" > "$P/no-family.json"
expect_rc 2 $PY "$SC/rollout.py" "$CYCLE" --workdir wd0 --agents "$P/no-family.json" "${VARS[@]}" --dry-run
has "$T/last.out" "reviewer profile 'reviewer' has no 'family'"
pass "rollout --dry-run: SET-ME refused; 70 prompts for the opening, pilot and introduction units; natural spine, contracts and unit keys in the prompts; same-family or family-less reviewer refused"

# allow_same_family: the run goes ahead with a warning in progress.log; a build runs before the packet is frozen.
printf 'Task for {{key}}.\n' > "$P/task.md"
cat > "$P/small.json" <<EOF
{"workdir": "wd-small", "agents": "$P/same-family.json", "units": {"U": {"title": "a unit"}},
 "stages": [{"name": "w", "kind": "write", "profile": "writer", "prompt": "$P/task.md", "expect": ["out.md"]},
            {"name": "r", "kind": "review", "profile": "reviewer", "allow_same_family": true,
             "build": ["echo built from {{prev_dir}}"], "reviews": {"rev": "$P/task.md"}}]}
EOF
expect_rc 0 $PY "$SC/rollout.py" "$P/small.json"
has "$P/wd-small/progress.log" "WARNING stage r (allow_same_family): review rev: the reviewer profile 'reviewer' is of the same model family"
has "$P/wd-small/U/r/packet/build.txt" "built from $P/wd-small/U/w"
has "$P/wd-small/U/r/packet/manifest.json" "before freezing, the driver ran: echo built"
sed -e 's/"allow_same_family": true,//' -e "s#$P/same-family.json#$P/agents.json#" -e 's/wd-small/wd-fail/' \
    -e 's/"build": \["echo built from {{prev_dir}}"\]/"build": ["echo first", "exit 7"]/' "$P/small.json" > "$P/small-fail.json"
expect_rc 1 $PY "$SC/rollout.py" "$P/small-fail.json"
has "$P/wd-fail/progress.log" "BUILD FAILED before freezing"
has "$P/wd-fail/U/r/build.txt" "\[exit 7\]"
[[ ! -e "$P/wd-fail/U/r/rev.md" && ! -e "$P/wd-fail/U/r/packet" ]] || die "a review ran after a failed build"
pass "allow_same_family warns in progress.log; build output frozen into the packet; a failing build stops the stage before any review"

# Full cycle: a writer failure (retried), a check overrun (retried with the check output), an inbox request,
# one NOT YET delivery.
mkdir -p wd/F && printf '## Request from Section 12\nState the uniform bound for every admissible input.\n' > wd/F/INBOX.md
rm -f "$T/calls.log"
FAKE_FAIL_ONCE='F/w1/*' FAKE_OVERRUN_ONCE='F/w2/*' FAKE_VERDICT='F/d/*=NOT YET (do not DELIVER before the fixes)' \
  expect_rc 0 RO "$CYCLE" --workdir wd --only F,C
[[ "$(calls 'F w1 write')" == 2 && "$(calls 'F w2 write')" == 2 && "$(calls 'C w1 write')" == 1 ]] || die "call counts"
has wd/F/w2/check-1.txt "OVER THE ALLOWANCE"
has wd/F/w2/prompt-retry.md "The check failed"
has wd/F/w2/.done "passed after one retry"
has wd/F/w1/prompt.md "State the uniform bound"
hasnt wd/F/w2/prompt.md "State the uniform bound"
has wd/F/inbox-archive.md "State the uniform bound"
[[ ! -s wd/F/INBOX.md ]] || die "inbox not emptied"
for j in math fresh prose owner-thm_IV owner-prop_FC; do [[ -s wd/F/r1/$j.md && -s wd/F/r2/$j.md ]] || die "missing review $j"; done
[[ -s wd/C/r1/owner-thm_RG.md && ! -e wd/C/r1/owner-thm_IV.md ]] || die "owner reviews per principal statement"
expect_rc 0 $PY "$SC/verify_packet.py" wd/F/r1/packet
[[ -f wd/F/d/packet/reviews-1/math.md && ! -e wd/F/d/packet/proposal/agent.log && ! -e wd/F/r1/packet/proposal/prompt.md ]] \
  || die "packet contents"
has wd/F/d/delivery.md "Verdict: NOT YET (do not DELIVER before the fixes)"
[[ "$(cat wd/F/STATUS)" == "NOT YET" && "$(cat wd/C/STATUS)" == "DELIVER" ]] || die "verdicts"
has wd/F/d/packet/build.txt "check_section"
has wd/F/d/packet/build.txt "check_coverage"
has wd/F/d/packet/build.txt "clause map: 1 row(s)"
has wd/F/d/packet/build.txt "check_allowance: standalone.pdf: 5 pages"
has wd/C/w1/check-1.txt "check_section"
for f in SPINE-NATURAL.md SPINE.md CLAUSE-MAP.tsv; do [[ -s wd/F/r1/packet/$f ]] || die "packet lacks $f"; done
pass "section cycle w1-r1-w2-r2-w3-d-verdict: retry after failure, check retry, inbox delivered once, owner jobs per statement, packets with both spine files, build (clause map, compile, pages, coverage) before delivery, a NOT YET line naming DELIVER is not a pass"

expect_rc 0 RO "$FIXUP" --workdir wd
has "$T/last.out" "C w4 skip (STATUS DELIVER"
[[ "$(cat wd/F/STATUS)" == "DELIVER" && -s wd/F/w4/response-w4.tsv && ! -d wd/C/w4 ]] || die "fix-up"
expect_rc 0 RO "$CYCLE" --workdir wd --only F,C
[[ "$(cat wd/F/STATUS)" == "DELIVER" ]] || die "rerunning the cycle changed a fixed-up STATUS"
expect_rc 0 RO "$CYCLE" --workdir wd --status
has "$T/last.out" "DELIVER"
pass "fix-up w4-d2-verdict2 only for NOT YET; rerun leaves STATUS alone; --status"

# Resume after the driver is killed while five reviewers run: the reviewers finish and are adopted, not rerun.
rm -f "$T/calls.log"
( export FAKE_SLEEP='F/r1/*=4'
  exec python3 -I -B "$SC/rollout.py" "$CYCLE" --workdir wd2 --only F --stages w1,r1 --agents "$P/agents.json" "${VARS[@]}" \
    > "$T/killed.out" 2>&1 ) &
pid=$!          # the driver itself (exec), so that kill -9 kills the driver and not a wrapper shell
for _ in $(seq 1 100); do
  [[ "$(ls wd2/F/r1/*.agent.running 2>/dev/null | wc -l)" -ge 5 ]] && break; sleep 0.1
done
[[ "$(ls wd2/F/r1/*.agent.running 2>/dev/null | wc -l)" -ge 5 ]] || die "reviewers did not start"
kill -9 "$pid"; wait "$pid" 2>/dev/null || true
expect_rc 0 RO "$CYCLE" --workdir wd2 --only F --stages w1,r1
has "$T/last.out" "adopting running job"
[[ "$(calls 'F r1')" == 5 && "$(calls 'F w1 write')" == 1 ]] || die "jobs were rerun after the restart"
for j in math fresh prose owner-thm_IV owner-prop_FC; do [[ -s wd2/F/r1/$j.md ]] || die "adopted report $j missing"; done
pass "resume after a killed driver: running reviewers adopted, nothing run twice"

# Quota: the run stops without retrying; after the reset, a rerun resumes where it stopped.
rm -f "$T/calls.log"
FAKE_QUOTA='C/r1/math' expect_rc 1 RO "$CYCLE" --workdir wd3 --only C
has wd3/progress.log "QUOTA"
[[ "$(calls 'C r1 math')" == 1 && ! -e wd3/C/r1/.done && ! -e wd3/C/w2 ]] || die "quota did not stop the unit"
expect_rc 0 RO "$CYCLE" --workdir wd3 --only C
[[ "$(calls 'C w1 write')" == 1 && "$(calls 'C r1 math')" == 2 && "$(cat wd3/C/STATUS)" == "DELIVER" ]] || die "resume after quota"
pass "quota message: no retry, unit stopped; rerun resumes from the stopped job"

# Protect violation: a writer that writes into the protected manuscript fails loudly and is not retried.
rm -f "$T/calls.log"
FAKE_WRITE_OUTSIDE="F/w1/*=$P/ms/main.tex" expect_rc 1 RO "$CYCLE" --workdir wd4 --only F
has wd4/progress.log "PROTECT VIOLATION"
has wd4/F/w1/agent.protect.txt "main.tex"
[[ "$(calls 'F w1 write')" == 1 && ! -e wd4/F/w1/.done ]] || die "protect violation retried or accepted"
pass "protect violation: job failed, not retried, run stopped"

# A check that still fails after its retry leaves the stage not done.
FAKE_PAGES=30 expect_rc 1 RO "$CYCLE" --workdir wd5 --only F --stages w1
has wd5/progress.log "CHECK FAILED after the retry"
[[ ! -e wd5/F/w1/.done ]] || die "stage over its allowance marked done"
pass "over the allowance after the retry = not done"

# The opening part: the main theorems must be byte for byte those of the natural spine (unit check); the
# introduction must deliver abstract.tex.
if [[ -f "$SK/../referee-adjudication/scripts/compare_statements.py" ]]; then
  FAKE_TEX="setting/w1/*=$P/good-setting.tex" expect_rc 0 RO "$CYCLE" --workdir wd6 --only setting --stages w1
  has wd6/setting/w1/check-1.txt "0 changed, 0 removed"
  has wd6/setting/w1/check-1.txt "maintheorem"
  expect_rc 1 RO "$CYCLE" --workdir wd7 --only setting --stages w1
  has wd7/setting/w1/check-2.txt "compare_statements"
  has wd7/progress.log "CHECK FAILED after the retry"
  FAKE_TEX="setting/w1/*=$P/changed-setting.tex" expect_rc 1 RO "$CYCLE" --workdir wd12 --only setting --stages w1
  has wd12/setting/w1/check-2.txt "CHANGED thm:A"
  pass "opening unit, natural spine shaped like the template (maintheorem): main theorems copied byte for byte pass; a changed or missing one is not done"
else
  echo "# referee-adjudication's compare_statements.py not found: opening-unit run skipped"
fi
expect_rc 1 RO "$CYCLE" --workdir wd8 --only intro --stages w1
has wd8/intro/w1/check-2.txt "test -s abstract.tex"
[[ ! -e wd8/intro/w1/.done ]] || die "introduction without an abstract marked done"
pass "introduction unit: a proposal without abstract.tex is not done"

# A LaTeX error in a proposal fails the write stage's compile check, and the writer gets its one retry.
if [[ "$REAL_TEX" == 1 ]]; then
  FAKE_BAD_TEX_ONCE='F/w1/*' expect_rc 0 RO "$CYCLE" --workdir wd9 --only F --stages w1
  has wd9/F/w1/check-1.txt "check_section: FAIL"
  has wd9/F/w1/prompt-retry.md "Undefined control sequence"
  has wd9/F/w1/.done "passed after one retry"
  pass "a compile error in a proposal: check failed, one retry quoting the LaTeX error, then done"
else
  echo "# latexmk not found: compile-error retry not run"
fi

# A clause map without a row stops every review stage before any review, saying where the map must be; the map
# kept as section 6 of the natural spine passes.
head -1 "$P/work/spine/CLAUSE-MAP.tsv" > "$P/work/spine/EMPTY-MAP.tsv"
expect_rc 1 RO "$CYCLE" --workdir wd10 --only C --stages w1,r1 --var "clause_map=$P/work/spine/EMPTY-MAP.tsv"
has wd10/progress.log "BUILD FAILED before freezing"
has wd10/C/r1/build.txt "NO ROWS"
has wd10/C/r1/build.txt "section 6"
[[ ! -e wd10/C/r1/packet && ! -e wd10/C/r1/math.md ]] || die "a review ran with an empty clause map"
expect_rc 0 RO "$CYCLE" --workdir wd11 --only C --stages w1,r1 --var "clause_map=$P/work/spine/SPINE-NATURAL.md"
has wd11/C/r1/packet/build.txt "clause map: 1 row(s)"
pass "clause map: a header-only CLAUSE-MAP.tsv stops r1 before any review; the map as section 6 of the natural spine passes"

# Every verdict pattern of the collection's example configs is anchored to the word after "Verdict".
$PY - "$SK/.." > "$T/patterns.out" 2>&1 <<'PYEOF' || { cat "$T/patterns.out" >&2; die "verdict patterns"; }
import glob, json, re, sys
n = 0
for cfg in sorted(glob.glob(sys.argv[1] + "/*/assets/rollout.*.example.json")):
    for st in json.load(open(cfg))["stages"]:
        if st.get("kind") != "verdict":
            continue
        m = re.fullmatch(r"\(\?i\)verdict\\W\+(.+)\\b", st["pattern"])
        assert m, f"{cfg}: stage {st['name']}: pattern {st['pattern']!r} is not (?i)verdict\\W+<words>\\b"
        word = m.group(1).upper()
        assert re.search(st["pattern"], f"**Verdict: {word}**"), (cfg, st["name"])
        for bad in (f"Verdict: NOT YET (do not {word} before the fixes)", f"Verdict: {word}X", f"Verdict: NOT {word}"):
            assert not re.search(st["pattern"], bad), (cfg, st["name"], bad)
        n += 1
assert n >= 7, n
print(f"{n} verdict patterns anchored")
PYEOF
has "$T/patterns.out" "verdict patterns anchored"
pass "verdict patterns of every example config: the pass word right after 'Verdict', never inside a NOT YET line"

echo "smoke_writing-workflow: $n checks passed"
