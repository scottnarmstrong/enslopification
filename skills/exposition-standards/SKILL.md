---
name: exposition-standards
description: Set and enforce the binding style rules of a manuscript written from a Lean development (word and reference caps per statement, definitions by formula, dependency sentences, terminology from the literature, no Lean names or process words, global numbering, a detail standard and an exemplar), with scripts that check statement shape, vocabulary, standalone compilation and pages per section after every integration. Load when writing a manuscript's style file or detail standard, briefing writers or reviewers, or checking a drafted or integrated section.
---

# Exposition standards

This skill gives the rules that make a manuscript written from a formal development readable,
each with its number and the failure it answers, and the programs that measure them. **Every rule that can be measured
is enforced by a script after every integration; every rule that cannot gets a dedicated
reviewer** ([L1](../lean-to-manuscript/references/lessons-learned.md#l1)). General prose,
statements and typesetting belong to `latex-math-writing`; this skill adds what a Lean source
makes necessary.

## When to use

- At the start of a campaign: choose the exemplar, write the style file and the detail standard,
  configure the checks.
- In every writing and review task: brief writers with the style file; run the checks on every
  draft and after every integration.
- Before the editorial pass: build the terminology table.

Not for: prose, notation and display craft (`latex-math-writing`); statement contracts, natural
form and the clause map ([statement-spine](../statement-spine/SKILL.md)); the review cycle and the
roll-out driver ([writing-workflow](../writing-workflow/SKILL.md)); figures (`math-figures`); the
typographic pass over rendered pages ([referee-adjudication](../referee-adjudication/SKILL.md)).

## The rules

| Rule | Number | Enforced by | Lesson |
|---|---|---|---|
| words per statement | target 100, cap 150 | `check_shape.py` | [L9](../lean-to-manuscript/references/lessons-learned.md#l9) |
| words per definition | target 120, cap 200 | `check_shape.py` | [L9](../lean-to-manuscript/references/lessons-learned.md#l9), [L14](../lean-to-manuscript/references/lessons-learned.md#l14) |
| main theorems | at most 250 counted tokens, formulas included, and 8 references | `check_shape.py` | [L10](../lean-to-manuscript/references/lessons-learned.md#l10) |
| references or tags per statement | at most 4 (definitions 6); a range counts once | `check_shape.py` | [L10](../lean-to-manuscript/references/lessons-learned.md#l10) |
| Lean names, file paths, process words | none, comments included; one bounded disclosure region | `check_vocabulary.py` | [L28](../lean-to-manuscript/references/lessons-learned.md#l28) |
| banned words, habitual phrasing | none | `check_vocabulary.py` | `latex-math-writing` |
| compilation | no errors, duplicate labels or overfull boxes | `check_section.sh` | mechanical need |
| pages | allowance per section, cap or guide | `page_report.py` | [L7](../lean-to-manuscript/references/lessons-learned.md#l7), [L23](../lean-to-manuscript/references/lessons-learned.md#l23) |
| numbering | global, by cross-reference; counters never redefined | review, compile | [L17](../lean-to-manuscript/references/lessons-learned.md#l17) |
| hypotheses | never moved out of a statement to meet a cap | review | [L13](../lean-to-manuscript/references/lessons-learned.md#l13) |

Not measurable, so enforced by the exposition review: one idea per statement; definitions by
formula with one sentence of purpose, never a translation of a Lean structure; dependency
sentences ("By Lemma X, which bounds …, …") instead of reference lists; one interpreting sentence
after a dense estimate; "Idea of the proof. Step 1 … k"; about one lemma per page, a proof over
three pages split at a genuine intermediate statement; standard results cited exactly; terminology
from the literature ([L28](../lean-to-manuscript/references/lessons-learned.md#l28)); one idea per
figure.

## Procedure

1. **Choose the exemplar** before anything is written. *Deliverable:* `EXEMPLAR.md`, at most about
   120 lines: patterns to copy with line references, features not to copy. Copy patterns, never
   statements ([detail and exemplar](references/detail-and-exemplar.md)).
2. **Write the style file** from `assets/STYLE-template.md`, with the numbers above and an empty
   section for the author's calibration. *Deliverable:* `STYLE.md`
   ([style rules](references/style-rules.md)).
3. **Write the detail standard** from `assets/DETAIL-STANDARD-template.md`: the named reader; one
   line or a citation, written out, never; representative cases. *Deliverable:*
   `DETAIL-STANDARD.md`.
4. **Configure and test the checks.** Set the environment lists and tag pattern of
   `check_shape.py`, the Lean namespaces and disclosure markers of `check_vocabulary.py`, the
   allowances of `page_report.py`; plant one fault of each kind in a scratch file and see each
   check fail. A listed word that is a term of art in the field (a spectral gap, a bridge of a
   graph) is allowed only by the author, in the project's allow file. *Deliverable:* the
   configuration files and the test output.
5. **Calibrate.** Turn every comment of the author on a pilot into a rule in the calibration
   section of `STYLE.md` the same day, with what enforces it
   ([L24](../lean-to-manuscript/references/lessons-learned.md#l24)). *Deliverable:* the updated
   style file.
6. **Check after every integration**, and make writers run the same checks before they finish;
   wire them as `check` commands of the roll-out stages. *Deliverable:* clean output, or a guide
   section's measured overrun with its reason ([automatic checks](references/automatic-checks.md)).
7. **Review what is not measured** with a dedicated reviewer (`assets/prompts/exposition-review.md`).
   *Deliverable:* findings with exact rewrites, each decided in a response table.
8. **Build the terminology table** before the editorial pass, keeping every term a human reader
   uses, and add the retired words to the vocabulary check
   ([L26](../lean-to-manuscript/references/lessons-learned.md#l26),
   [L28](../lean-to-manuscript/references/lessons-learned.md#l28),
   [terminology](references/terminology.md)). *Deliverable:* `TERMINOLOGY.tsv` and a pattern file.

## Scripts

- `scripts/check_shape.py`: words and references per theorem-like environment against targets
  and caps (TeX, or Markdown with raw LaTeX environments); `--json`, `--list`. Assumes standard
  `\begin`/`\end` environments. Does not judge whether a statement is one idea.
- `scripts/check_vocabulary.py`: banned words, habitual phrasing, process words, file paths and
  Lean names in every active input, comments included, with a bounded exception region. Assumes
  the shipped pattern files or yours. Does not judge terminology beyond its lists.
- `scripts/check_section.sh`: compiles one section with the manuscript's preamble in a temporary
  directory; reports pages, errors, undefined and duplicate labels, overfull boxes; runs the two
  checks above. Assumes latexmk: without it the text checks still run, but the result is SKIPPED
  (exit 3), never PASS; a LaTeX run that writes no PDF fails with the first errors of the log.
  Does not inspect the pages.
- `scripts/page_report.py`: pages per section from the `.toc` (or `\label` pages from the `.aux`)
  against caps and guides. Assumes a compiled document with arabic page numbers. Exact to within
  one page per section.

Assets: `STYLE-template.md`, `DETAIL-STANDARD-template.md`, `terminology-header.tsv`,
`shape-config.example.json`, `allowances.example.tsv`, `wordlists/` (the banned-word list copied
from `latex-math-writing`, with attribution), and `prompts/exposition-review.md`.

## What this establishes and what it does not

- Passing the checks establishes that no measured mechanical fault is present: no environment
  over its caps under the stated counting rule, no listed word or pattern outside the bounded
  region, a clean standalone compile, no section over a capped allowance.
- It establishes nothing about the mathematics, nor that a statement is faithful, true or one
  idea, nor that an explanatory sentence is true, nor that the pages look right. A statement under
  every cap can still be unreadable.
- The vocabulary check finds only what its lists name; an empty report does not mean the
  terminology is the literature's.
- The exposition review is one AI reader's judgement, not a referee's report.

## Related skills

- `latex-math-writing` (collection *math-paper-skills*, which this skill requires): writing rules,
  statements, proofs, the banned-word list, house style.
- [statement-spine](../statement-spine/SKILL.md): the statements these rules shape.
- [writing-workflow](../writing-workflow/SKILL.md): where the checks run, and the reviews.
- [referee-adjudication](../referee-adjudication/SKILL.md): editorial plans, typographic pass.
- `math-figures`: figures that express one idea.
- `math-paper-campaign`: the detail standard and the detail critic (`from-formalization.md`).
