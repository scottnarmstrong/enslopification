#!/usr/bin/env bash
# Smoke test for skills/referee-adjudication: every script on tiny synthetic inputs, the rollout configs against
# their prompt templates, a dry run with the shared driver if it is installed, and a vocabulary check of the text.
# Usage: tests/smoke_referee-adjudication.sh      (exit 0 = all passed)
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SK="$ROOT/skills/referee-adjudication"
T="$(mktemp -d)"
trap 'rm -rf "$T"' EXIT
PY=(python3 -I)

fail() { echo "FAIL: $*" >&2; exit 1; }
ok() { echo "ok: $*"; }
# expect_rc WANTED DESCRIPTION COMMAND...: run COMMAND, keep its output in $T/out, check its exit status
expect_rc() {
  local want="$1" desc="$2"; shift 2
  local rc=0
  "$@" > "$T/out" 2>&1 || rc=$?
  if [ "$rc" -ne "$want" ]; then cat "$T/out" >&2; fail "$desc: exit $rc, expected $want"; fi
  ok "$desc (exit $rc)"
}
has() { grep -qF -- "$1" "$T/out" || { cat "$T/out" >&2; fail "output lacks: $1"; }; }

# 1. help
expect_rc 0 "adjudication_summary.py --help" "${PY[@]}" "$SK/scripts/adjudication_summary.py" --help
expect_rc 0 "compare_statements.py --help" "${PY[@]}" "$SK/scripts/compare_statements.py" --help
expect_rc 0 "render_pages.sh -h" bash "$SK/scripts/render_pages.sh" -h

# 2. adjudication_summary.py
cat > "$T/part1.md" <<'EOF'
# Adjudication of the Part I report

## Lean facts the verdicts rely on
- `Foo.bar` (Foo.lean:10), used = 1 by query.

## Verdicts
| # | Verdict | Reason | Where to edit |
|---|---|---|---|
| 1 | ACCEPT | Correct as proposed. | 03:12 |
| 2 | ACCEPT MODIFIED | The bound needs \|x\| <= 1, not 2. | 03:40, 05:7 |
| 3a | REJECT | Moving the rows breaks references to them. | — |
| 3b | AUTHOR | Changes the main theorem. | 08:100 |
| 4 | ACCEPT MODIFIED (a-b); AUTHOR (c, deleting Lemma 9.2) | Mixed. | 09:3, :17 |
| 5 | **Accepted** | Typo. | main.tex:52 |
EOF
S="$SK/scripts/adjudication_summary.py"
expect_rc 0 "summary of a complete adjudication" "${PY[@]}" "$S" "$T/part1.md" --expect 5 --tsv "$T/v.tsv"
has "| part1 | 7 | 2 | 2 | 1 | 2 | 5 of 5 |"
has "**part1 3b**"
has "**part1 4[c, deleting Lemma 9.2]**"
has "### 03"
has "### 09"
has "### main.tex"
has "-> ok"
[ "$(wc -l < "$T/v.tsv")" -eq 8 ] || fail "TSV should have a header and 7 items"
ok "TSV written with 7 items"
expect_rc 1 "a suggestion without a verdict" "${PY[@]}" "$S" "$T/part1.md" --expect part1=6
has "suggestion(s) without a verdict: 6"
sed 's/| 1 | ACCEPT |/| 1 | MAYBE |/' "$T/part1.md" > "$T/bad.md"
expect_rc 1 "an unknown verdict" "${PY[@]}" "$S" "$T/bad.md"
has "unknown verdict"
{ cat "$T/part1.md"; echo; echo "| # | Verdict | Reason | Where |"; echo "|---|---|---|---|"; echo "| 1 | REJECT | x | 03:1 |"; } > "$T/twice.md"
expect_rc 1 "one item with two verdicts" "${PY[@]}" "$S" "$T/twice.md"
has "has two verdicts"
grep -v 'Lean facts' "$T/part1.md" > "$T/nofacts.md"
expect_rc 0 "missing Lean facts: a warning by default" "${PY[@]}" "$S" "$T/nofacts.md"
expect_rc 1 "missing Lean facts: a failure with --strict" "${PY[@]}" "$S" "$T/nofacts.md" --strict
expect_rc 2 "a missing file" "${PY[@]}" "$S" "$T/none.md"
# the driver saves every adjudication as <unit>/adjudicate/adjudication.md: the unit names the report
mkdir -p "$T/run/part1/adjudicate" "$T/run/uv/adjudicate"
cp "$T/part1.md" "$T/run/part1/adjudicate/adjudication.md"
cp "$T/part1.md" "$T/run/uv/adjudicate/adjudication.md"
expect_rc 0 "same-named files told apart by unit" "${PY[@]}" "$S" "$T"/run/*/adjudicate/adjudication.md \
  --expect part1=5 --expect uv=5 --part counts
has "| part1 | 7 |"
has "| uv | 7 |"
expect_rc 0 "an explicit report name" "${PY[@]}" "$S" "first=$T/part1.md" --expect first=5 --part counts
has "| first | 7 |"

# 3. compare_statements.py
mkdir -p "$T/old" "$T/new"
cat > "$T/old/a.tex" <<'EOF'
\newtheorem{maintheorem}{Theorem}
\begin{maintheorem}[Main]\label{thm:main}
For every $x>0$ there is $y$ with $x<y$.
\end{maintheorem}
% \begin{lemma} a commented-out environment is ignored
\begin{lemma}\label{lem:a}
If $a>0$ then $a^2>0$.
\end{lemma}
Text before a display \begin{equation}\label{eq:1} 1=1 \end{equation}
EOF
cp "$T/old/a.tex" "$T/new/a.tex"
C="$SK/scripts/compare_statements.py"
expect_rc 0 "identical sources" "${PY[@]}" "$C" "$T/old" "$T/new"
sed -i 's/Text before a display/Reworded prose before a display/' "$T/new/a.tex"
expect_rc 0 "prose outside statements changed" "${PY[@]}" "$C" "$T/old" "$T/new"
sed -i 's/If \$a>0\$/If $a\\ge 0$/' "$T/new/a.tex"
expect_rc 1 "a lemma changed" "${PY[@]}" "$C" "$T/old" "$T/new"
has "CHANGED lem:a"
expect_rc 0 "only the main theorem compared" "${PY[@]}" "$C" "$T/old" "$T/new" --labels thm:main
cp "$T/old/a.tex" "$T/new/a.tex"
sed -i 's/\\label{eq:1}//' "$T/new/a.tex"
expect_rc 1 "a label removed" "${PY[@]}" "$C" "$T/old" "$T/new"
has "LABEL-REMOVED eq:1"
expect_rc 2 "a missing directory" "${PY[@]}" "$C" "$T/old" "$T/nonexistent"
# a natural spine in Markdown declares no environment: maintheorem is compared by default
printf '# Spine\n\n\\begin{maintheorem}\\label{thm:main}\nFor every $x$.\n\\end{maintheorem}\n\\begin{lemma}\\label{lem:s}\nS.\n\\end{lemma}\n' > "$T/spine.md"
printf '\\section{Setting}\n\\begin{maintheorem}\\label{thm:main}\nFor every $x$.\n\\end{maintheorem}\n' > "$T/setting.tex"
expect_rc 0 "maintheorem without \\newtheorem, other spine labels allowed to live elsewhere" "${PY[@]}" "$C" \
  "$T/spine.md" "$T/setting.tex" --labels thm:main --allow-label-changes
has "maintheorem"
sed -i 's/every \$x\$/every $y$/' "$T/setting.tex"
expect_rc 1 "a changed main theorem" "${PY[@]}" "$C" "$T/spine.md" "$T/setting.tex" --labels thm:main --allow-label-changes
has "CHANGED thm:main"

# 4. render_pages.sh on a generated three-page PDF
if command -v pdftoppm >/dev/null 2>&1 && command -v pdfinfo >/dev/null 2>&1; then
  "${PY[@]}" - "$T/tiny.pdf" <<'EOF'
import sys
pages = 3
objs = ["<< /Type /Catalog /Pages 2 0 R >>",
        "<< /Type /Pages /Kids [%s] /Count %d >>" % (" ".join("%d 0 R" % (3 + 2 * i) for i in range(pages)), pages)]
font = 3 + 2 * pages
for i in range(pages):
    content = "BT /F1 24 Tf 72 700 Td (Page %d) Tj ET" % (i + 1)
    objs.append("<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 %d 0 R >> >> "
                "/Contents %d 0 R >>" % (font, 4 + 2 * i))
    objs.append("<< /Length %d >>\nstream\n%s\nendstream" % (len(content), content))
objs.append("<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
out, offsets = b"%PDF-1.4\n", []
for k, o in enumerate(objs, 1):
    offsets.append(len(out))
    out += ("%d 0 obj\n%s\nendobj\n" % (k, o)).encode()
xref = len(out)
out += ("xref\n0 %d\n0000000000 65535 f \n" % (len(objs) + 1)).encode()
out += b"".join(("%010d 00000 n \n" % o).encode() for o in offsets)
out += ("trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (len(objs) + 1, xref)).encode()
open(sys.argv[1], "wb").write(out)
EOF
  R="$SK/scripts/render_pages.sh"
  expect_rc 0 "render pages 2-3" bash "$R" -f 2 -l 3 -r 20 -o "$T/img" "$T/tiny.pdf"
  [ "$(grep -c '\.png$' "$T/out")" -eq 2 ] || fail "render_pages should list 2 images"
  has "2 page image(s), pages 2-3 of 3"
  expect_rc 2 "a page range beyond the PDF" bash "$R" -f 2 -l 9 -o "$T/img" "$T/tiny.pdf"
  expect_rc 2 "no output directory" bash "$R" "$T/tiny.pdf"
else
  echo "skip: render_pages.sh run (pdftoppm or pdfinfo not installed)"
fi

# 5. rollout configs: valid JSON; every placeholder of every template of this skill defined for every unit
expect_rc 0 "rollout configs define every placeholder" "${PY[@]}" - "$SK/assets" <<'PYEOF'
import glob, json, os, re, sys
assets = sys.argv[1]
builtins = {"key", "title", "pages", "stage", "stage_dir", "unit_dir", "workdir", "config_dir", "driver_dir",
            "prev_dir", "prev_stage", "reports_dir", "reports_stage", "packet", "inbox", "name", "review", "item",
            "item_slug", "unit_keys", "common"}
ph = re.compile(r"(?<!\{)\{\{\s*([A-Za-z_][A-Za-z0-9_.-]*)\s*\}\}")
problems = 0
configs = sorted(glob.glob(os.path.join(assets, "rollout.*.example.json")))
assert configs, "no rollout configs"
for cfg in configs:
    c = json.load(open(cfg))
    for field in ("workdir", "agents", "limits", "vars", "units", "stages"):
        assert field in c, f"{cfg}: missing {field}"
    texts = []
    for st in c["stages"]:
        assert st.get("kind") in ("write", "review", "verdict"), f"{cfg}: bad stage kind"
        paths = ([st["prompt"]] if "prompt" in st else []) + list(st.get("reviews", {}).values())
        paths = [x for p in paths for x in (p if isinstance(p, list) else [p])]
        for p in paths:
            assert p.startswith("{{templates}}/"), f"{cfg}: template {p} is not under {{{{templates}}}}"
            full = os.path.join(assets, "prompts", p[len("{{templates}}/"):])
            assert os.path.isfile(full), f"{cfg}: template {full} not found"
            texts.append((os.path.basename(full), open(full).read()))
        for f in ("seed", "packet", "expect", "check"):
            v = st.get(f, [])
            texts += [(f, x) for x in (v if isinstance(v, list) else [v])]
    for key, unit in c["units"].items():
        defined = builtins | set(c["vars"]) | set(unit.get("vars", {}))
        for name, text in texts:
            for v in sorted(set(ph.findall(text)) - defined):
                print(f"{os.path.basename(cfg)}: unit {key}: {{{{{v}}}}} in {name} is not defined")
                problems += 1
print(f"{len(configs)} configs checked, {problems} undefined placeholder(s)")
sys.exit(1 if problems else 0)
PYEOF

# 6. dry run with the shared driver of writing-workflow, every SET-ME value replaced by a scratch path
DRIVER="$ROOT/skills/writing-workflow/scripts/rollout.py"
AGENTS_EXAMPLE="$ROOT/skills/writing-workflow/assets/agents.example.json"
if [ -f "$DRIVER" ] && [ -f "$AGENTS_EXAMPLE" ]; then
  # the example profiles plus the 'referee' profile that rollout.referee.example.json asks for
  "${PY[@]}" - "$AGENTS_EXAMPLE" "$T/agents.json" <<'PYEOF'
import json, sys
a = json.load(open(sys.argv[1]))
a["referee"] = {"extends": "reviewer", "model": "referee-model"}
json.dump(a, open(sys.argv[2], "w"), indent=1)
PYEOF
  for cfg in "$SK"/assets/rollout.*.example.json; do
    name="$(basename "$cfg" .example.json)"
    mapfile -t VARS < <("${PY[@]}" - "$cfg" "$T/scratch" <<'PYEOF'
import json, sys
c = json.load(open(sys.argv[1]))
for k, v in c["vars"].items():
    if "SET-ME" in json.dumps(v):
        print(f"--var={k}={sys.argv[2]}/{k}")
PYEOF
)
    expect_rc 0 "driver dry run of $name" "${PY[@]}" "$DRIVER" "$cfg" --dry-run --workdir "$T/dry-$name" \
      --agents "$T/agents.json" "${VARS[@]}"
    n="$(find "$T/dry-$name/.dry-run" -name 'prompt*.md' | wc -l)"
    [ "$n" -gt 0 ] || fail "dry run of $name rendered no prompt"
    if grep -rlE 'SET-ME|\{\{' "$T/dry-$name/.dry-run" >/dev/null; then fail "unrendered placeholder in $name"; fi
    ok "$name: $n prompt(s) rendered, no placeholder left"
  done
else
  echo "skip: driver dry run (writing-workflow's rollout.py or agents.example.json not present)"
fi

# 6b. the apply config run with the stand-in agent: s14 is NOT YET at c1, so only s14 gets the fix-up f2, the
#     re-confirmation c2 (with the first report in its packet) and the verdict v2
FAKE="$ROOT/tests/fake_agent.py"
if [ -f "$DRIVER" ] && [ -f "$FAKE" ]; then
  P="$T/apply"
  mkdir -p "$P/ms/part1" "$P/ms/part2" "$P/lean" "$P/ref/part1/referee" "$P/ref/uv/referee" \
           "$P/adj/part1/adjudicate" "$P/adj/uv/adjudicate"
  printf '\\section{Setting}\\label{sec:one}\nWe prove a bound.\n' > "$P/ms/part1/01-setting.tex"
  printf '\\section{Step}\\label{sec:B}\nWe prove a bound.\n' > "$P/ms/part2/B-section.tex"
  printf '\\section{Limit}\\label{sec:E}\nWe prove a bound.\n' > "$P/ms/part2/E-one.tex"
  for u in part1 uv; do echo "Suggestions: 1" > "$P/ref/$u/referee/report.md"; cp "$T/part1.md" "$P/adj/$u/adjudicate/adjudication.md"; done
  echo "-- lean" > "$P/lean/Main.lean"
  cat > "$P/agents.json" <<EOF
{"writer": {"argv": ["python3", "-I", "$FAKE"], "model": "fake-w", "family": "fake-a", "stdout": "log", "timeout_s": 120},
 "reviewer": {"argv": ["python3", "-I", "$FAKE"], "model": "fake-r", "family": "fake-b", "stdout": "report", "timeout_s": 120}}
EOF
  AVARS=(--var "manuscript=$P/ms" --var "referees=$P/ref" --var "adjudications=$P/adj" --var "lean=$P/lean"
         --var lean_commit=3456e5e --var "graph_db=$P/graph.sqlite" --var "main_theorems=thm:main")
  # s14's first confirmation says NOT YET in a line that also names INTEGRATE: not a pass
  FAKE_VERDICT='s14/c1/*=NOT YET (do not INTEGRATE before the fixes),*=INTEGRATE' FAKE_STATE="$P/state" \
    expect_rc 0 "apply config run with the stand-in agent" \
    "${PY[@]}" "$DRIVER" "$SK/assets/rollout.apply.example.json" --workdir "$P/wd" --agents "$P/agents.json" "${AVARS[@]}"
  grep -q "Verdict: NOT YET (do not INTEGRATE before the fixes)" "$P/wd/s14/c1/confirm.md" || fail "s14 c1 verdict line"
  [ "$(python3 -I -c 'import json,sys; print(json.load(open(sys.argv[1]))["status"])' "$P/wd/s14/v1/.done")" = "NOT YET" ] \
    || fail "a NOT YET line naming INTEGRATE was read as a pass"
  [ "$(cat "$P/wd/s14/STATUS")" = "INTEGRATE" ] || fail "s14 should be INTEGRATE after the fix-up"
  [ "$(cat "$P/wd/part1/STATUS")" = "INTEGRATE" ] && [ "$(cat "$P/wd/s11/STATUS")" = "INTEGRATE" ] || fail "statuses"
  [ -s "$P/wd/s14/f2/response-f2.tsv" ] && [ -s "$P/wd/s14/c2/packet/first-confirmation.md" ] || fail "fix-up outputs"
  [ ! -e "$P/wd/part1/f2" ] && [ ! -e "$P/wd/s11/c2" ] || fail "the fix-up ran for a unit that was INTEGRATE"
  grep -q "s14/f2/prompt.md" <(find "$P/wd" -name prompt.md) || fail "no f2 prompt"
  grep -q "c1/confirm.md says NOT YET" "$P/wd/s14/f2/prompt.md" || fail "the f2 prompt does not point to confirm.md"
  grep -q "This is the re-check after a fix-up" "$P/wd/s14/c2/prompt-confirm.md" || fail "c2 lacks the re-check addendum"
  ok "f1-c1-v1 for every unit; f2-c2-v2 only for the NOT YET unit; STATUS INTEGRATE after the re-check"
else
  echo "skip: stand-in run of the apply config (rollout.py or fake_agent.py not present)"
fi

# 6c. every reviewer prompt asks for the sources consulted; the typography report format parses for check_coverage.py
for f in adjudicator.md confirmation-reviewer.md referee.md comparison.md exposition-reviewer.md typography-reviewer.md; do
  grep -q "Sources consulted" "$SK/assets/prompts/$f" || fail "$f does not ask for the sources consulted"
done
ok "every reviewer prompt asks for the sources consulted"
COV="$ROOT/skills/writing-workflow/scripts/check_coverage.py"
if [ -f "$COV" ]; then
  printf 'Sources consulted: the images of pages 1-10 at 60 dpi.\n\n| Page | Quote | Defect | Suggested fix |\n|---|---|---|---|\n| 6 | "Then" | one-word line | rewrite |\n\nNeeds the editor: none.\n\nClean pages: 1-5, 7-10\n' > "$T/typo.md"
  expect_rc 0 "a typography report in the prompt's format covers its range" "${PY[@]}" "$COV" --pages 1-10 "$T/typo.md"
  expect_rc 1 "a page missing from the report is reported" "${PY[@]}" "$COV" --pages 1-11 "$T/typo.md"
  has "NOT COVERED"
else
  echo "skip: check_coverage.py of writing-workflow not present"
fi

# 7. vocabulary and privacy of the skill's text
BANNED='crucial|leverage|delve|robust|seamless|comprehensive|pivotal|intricate|nuanced|holistic|landscape|navigate|tapestry|underscore|unlock|showcase|harness|foster|paradigm|game-changer|cutting-edge|state-of-the-art|worth noting|in summary'
if grep -rniE "$BANNED" "$SK" --include='*.md' --include='*.json' --include='*.yaml'; then
  fail "banned or private words in the skill's text"
fi
ok "no banned or private words in the skill's text"

echo "smoke_referee-adjudication: all checks passed"
