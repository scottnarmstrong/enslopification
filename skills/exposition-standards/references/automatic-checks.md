# The automatic checks

Four programs, run after every integration, by writers on their own drafts before they finish,
and by the roll-out driver as the `check` command of a writing stage (a non-zero exit sends the
draft back once, with the check's output appended to the prompt; see
[writing-workflow](../../writing-workflow/SKILL.md)). All take paths as arguments; none knows a
project name. Test each on a planted fault before relying on it.

| Check | Script | Fails on |
|---|---|---|
| shape | `check_shape.py` | a statement, definition or main theorem over its word cap or reference cap |
| vocabulary | `check_vocabulary.py` | a banned word, habitual phrase, process word, file path or Lean name; a bad exception region |
| compilation | `check_section.sh` | errors, no PDF, multiply defined labels, overfull boxes (and the two checks above); without latexmk it reports SKIPPED, exit 3 |
| pages | `page_report.py` | a section over a capped allowance |

## Shape

`check_shape.py FILE...` or `check_shape.py --root main.tex` (every active `\input`/`\include`).
It also reads Markdown files whose statements are raw LaTeX environments, such as a statement
spine.

**Counting rule.** The body is the text between `\begin{ENV}` (its optional title not counted) and
`\end{ENV}`. Comments and `\label{…}` are removed; every control word and each of the characters
`{ } $ \ & _ ^` becomes a space; the remaining whitespace-separated tokens are counted. Formulas
therefore count as their tokens: `$\sup_{x\in B}|u(x)|\le C$` counts 4. Keep the rule fixed for a
whole campaign, so that numbers stay comparable.

**References.** Each `\ref`, `\eqref`, `\autoref`, `\nameref` counts once; `\cref` counts once per
label; `\crefrange` once; statement tags count when `--tag-regex` matches them outside command
arguments; two references or two tags joined by a dash form a range and count once. Citations of
the literature are not counted.

**Configuration.** Defaults (this collection's; the word caps and the four-reference cap are the
published caps of the Yang–Mills campaign): statements 100/150 words and 4 references, definitions
120/200 and 6, main theorems 200/250 and 8. Change them with `--env NAME=T/C/R`, `--main-env NAME`,
`--main-caps T/C/R`, or a JSON file (`assets/shape-config.example.json`, which also shows the tag
pattern of the Yang–Mills manuscript). Every main-theorem environment must be listed: a checker
that skipped it let a theorem listing about forty labels through
([L10](../../lean-to-manuscript/references/lessons-learned.md#l10)). `--list` prints every
environment as TSV, for the measured-shape tables of a spine; `--json` for programs.

## Vocabulary

`check_vocabulary.py --root main.tex` scans every active input, comments included. Before
matching it blanks the arguments of label, reference, citation, input, graphics and URL commands
and every remaining control word, so labels, file names in `\input` and macro names do not count.

- **Categories** are the pattern files in `assets/wordlists/`, one regex per line: `banned-words`
  (a copy of the list of `latex-math-writing`; keep it in sync), `habitual-phrasing`,
  `process-words`, `file-paths`, `lean-names`. Add the development's namespaces with
  `--lean-namespace` (for example its top-level namespaces) and project lists with
  `--patterns CATEGORY=FILE`, for instance the retired code words of the terminology table.
- **Allowed phrases** (`allow.txt`) drop a hit that lies inside them, such as "spectral gap" or
  "lens space". Each entry is a decision about a literal technical term; record who took it.
- **Terms of art.** Some listed words are technical terms in some fields: a gap in a spectrum, a
  bridge of a graph, a certificate in complexity theory, the spine of a 3-manifold, a proposal
  distribution. Only the author allows one, as a phrase in the project's allow file
  (`--allow FILE`), with a regex as narrow as the use (`\bbridges? of the graph\b`, never
  `\bbridge\b`). The editor records each decision in that file, as a comment above the entry
  (who, when). In overnight mode the editor may allow a term provisionally, marks it so, and puts
  it on the morning list, where the author confirms or removes it
  ([L35](../../lean-to-manuscript/references/lessons-learned.md#l35)).
- **The exception region** for the source disclosure lies between two marker comments (default
  `BEGIN-DISCLOSURE` and `END-DISCLOSURE`; set others with `--begin-marker`, `--end-marker`).
  Inside it only the categories named by `--except` are allowed (default: process words); Lean
  names and banned words are not. A region that is unterminated, nested or longer than
  `--max-region-lines` fails the check: the exception stays bounded.

Output is `file:line:category:match`. Run it on the whole root before any public commit, and make
passing it a condition of every commit to the public repository.

## Compilation of one section

`check_section.sh -m main.tex SECTION.tex` takes the preamble of `main.tex` (everything before
`\begin{document}`, relative `\input` paths rewritten), wraps the section in it, compiles in a
temporary directory with latexmk, and reports pages, errors, undefined references and citations,
multiply defined labels and overfull boxes; then it runs the two checks above on the section
(`-V` and `-S` pass options to them). Undefined references are expected, since the other sections
are absent, and never fail the check; errors, duplicate labels and overfull boxes do (`-O` reports
overfull boxes without failing), and so does a run in which LaTeX writes no PDF (the first errors
of the log are printed). Without latexmk nothing is compiled: the text checks still run, and the
script ends with `SKIPPED` and exit 3, never `PASS`, because pages, errors, labels and boxes were
not measured; a `check` stage of the driver treats exit 3 as a failure. Exit 2 is a usage error;
a dry run (`-n`) exits 0. Writers run it on their proposals; the editor runs the full build after
integration, where undefined references must be zero.

## Pages per section

`page_report.py --toc main.toc --allowances allowances.tsv` reads the start page of every section
from the compiled table of contents (or the pages of chosen `\label`s from the `.aux` with
`--from-labels`) and the page total from the log, and compares each section with its allowance.
Each allowance is a **cap** (over = not done, the check fails) or a **guide** (over = report the
measured length and the reason) ([L23](../../lean-to-manuscript/references/lessons-learned.md#l23)).
Sections that share a page make each figure exact to within one page.

Measure before and after every pass ([L2](../../lean-to-manuscript/references/lessons-learned.md#l2),
[L7](../../lean-to-manuscript/references/lessons-learned.md#l7)): a page plan made before the pilots
can be far too small for the hardest sections, and only the measurement shows it.

## What passing establishes, and what it does not

Passing these checks establishes that none of the measured mechanical faults is present: no
environment over its caps under the stated counting rule, no listed word or pattern outside the
bounded region, no compile error, duplicate label or overfull box in the standalone build, no
section over a capped allowance.

It establishes nothing about the mathematics: not that a statement is true, faithful to the Lean,
or one idea; not that a definition is concrete; not that an explanatory sentence is true
([L20](../../lean-to-manuscript/references/lessons-learned.md#l20)); not that the terminology is
the literature's (only that retired words are absent); not that the pages look right, which needs
eyes on every page ([L29](../../lean-to-manuscript/references/lessons-learned.md#l29)). A statement
under every cap can still be unreadable. Those questions go to the reviewers of
[writing-workflow](../../writing-workflow/SKILL.md) and to the exposition review
(`assets/prompts/exposition-review.md`, run per section; its manuscript-wide variant for the editorial pass is
`exposition-reviewer.md` of [referee-adjudication](../../referee-adjudication/SKILL.md), with the same six headings).
