---
name: statement-spine
description: Fix every statement of a manuscript's opening part (definitions, main theorems, principal statements, deduction, later lemmas) in natural form before any prose is written, show with a clause map that together they carry exactly what a completed Lean development proves, freeze them with the author's approval, and control later changes with a drift log. Load after the Lean dependency closure and the unit outlines exist and before any section is drafted, or when a frozen statement or a later lemma must change.
---

# Statement spine

The spine is one document that fixes every statement of the opening part before any prose: the
definitions the main theorem needs, the main theorems, the principal statements, the deduction of
the main theorems from them with the order of choices, the list of later lemmas that prove them,
and its measured typeset size. Every section is written against it. **The paper claims nothing
the Lean does not prove; weaker or more natural forms are allowed, stronger never.** Statements
take a natural form, not the Lean's shape, and **a clause map shows that the natural statements
together carry every clause of the frozen contracts**.

## When to use

- After [lean-dependency-graph](../lean-dependency-graph/SKILL.md) has computed the closure of the
  main theorem (`used = 1`) and [coarse-graining](../coarse-graining/SKILL.md) has produced unit
  outlines; before [writing-workflow](../writing-workflow/SKILL.md) drafts any section.
- When a frozen statement must change, or a later lemma is split, added or reworded.

Not for: auditing one Lean declaration against a source (`lean-statement-audit`); the style caps
and the scripts that measure them ([exposition-standards](../exposition-standards/SKILL.md), whose
`check_shape.py` this skill uses); the general drift protocol and statement packets
(`math-paper-campaign`, reference `shared-controls.md`); publishing the correspondence table
([honest-publication](../honest-publication/SKILL.md)).

## Procedure

1. **Fix the authorities.** Pin the commit; name the roots of the main theorem and the dependency
   database; mark outlines and summaries as maps, never evidence; name the reader, the detail
   standard and the exemplar. *Deliverable:* a spine section in the campaign brief.
2. **Two independent drafts** ([L16](../lean-to-manuscript/references/lessons-learned.md#l16)).
   Two drafters, preferably from different model families, each propose the principal statements
   with an envelope per statement, the deduction and the definitions needed
   (`assets/prompts/spine-drafter.md`). A principal statement is a real interface: a large block of
   the proof establishes it, and the deduction or another principal statement consumes it.
   *Deliverable:* two draft files.
3. **Reconcile** ([L5](../lean-to-manuscript/references/lessons-learned.md#l5)). Check every cited
   name against the closure and replace each unused one by the used declaration that proves the
   same content; map one draft to the other; choose statement by statement; list the decisions for
   the author with a recommendation each (`assets/prompts/reconcile.md`). *Deliverable:*
   `RECONCILE.md` and the author's rulings, recorded in the brief.
4. **Write and review the frozen contracts.** The merged statements in full, every clause tagged
   `[clause:ID]`, with conventions, definitions, main theorems, deduction, and constants with
   their order of choice (`assets/SPINE-template.md`). A fresh reviewer checks strength in both
   directions and existence against universality
   ([L11](../lean-to-manuscript/references/lessons-learned.md#l11),
   [L12](../lean-to-manuscript/references/lessons-learned.md#l12)). *Deliverable:* `SPINE.md`, its
   review, and the responses.
5. **Restate in natural form** ([L9](../lean-to-manuscript/references/lessons-learned.md#l9),
   [L10](../lean-to-manuscript/references/lessons-learned.md#l10),
   [L13](../lean-to-manuscript/references/lessons-learned.md#l13),
   [L14](../lean-to-manuscript/references/lessons-learned.md#l14),
   [L15](../lean-to-manuscript/references/lessons-learned.md#l15)). One result per statement,
   quantifiers first, conclusion displayed, objects set up before, side conditions to later
   lemmas, no packaging statements; main theorems state, they do not list; the literal formal
   statement goes to an appendix (`assets/prompts/natural-form.md`,
   `assets/SPINE-NATURAL-template.md`). *Deliverable:* `SPINE-NATURAL.md`, every statement a raw
   LaTeX environment, `check_shape.py` reporting no cap exceeded.
6. **Map every clause.** Every clause of every frozen contract goes to a statement, a later lemma,
   a definition or a labelled setup passage; the union equals what the Lean proves; scope-sensitive
   clauses cite named `used = 1` declarations; doubtful clauses are listed under "Clauses requiring
   care", never changed silently. Run `clause_map_check.py`, then an independent review
   (`assets/prompts/clause-map-review.md`). *Deliverable:* the clause map, a clean check, and an
   approving review with its fixes.
7. **Measure** ([L7](../lean-to-manuscript/references/lessons-learned.md#l7),
   [L23](../lean-to-manuscript/references/lessons-learned.md#l23)). Typeset the spine alone with the
   manuscript's preamble and compare the pages per block with the allowance of the opening part.
   *Deliverable:* pages per block and words per environment; if over, the block to tighten.
8. **Freeze.** The author approves; record the date and the SHA-256 of the approved file. The
   natural spine becomes the authority for statements; the frozen contracts remain the record it
   must cover. *Deliverable:* the approval entry in the brief.
9. **Control change.** A change to a frozen statement follows the drift protocol of
   `math-paper-campaign` (collection *math-paper-skills*, which this skill requires), plus: the old
   text, the new text, the reason and the Lean evidence go to the author, and nothing changes
   before approval; owner reviews check strength in both directions. Later lemmas are editable
   targets: split, add or reword them with a log entry and an updated clause map. Never move a
   hypothesis out of a statement to meet a cap. *Deliverable:* `DRIFT-LOG.md`
   (`assets/drift-log-template.md`).

Every statement and definition carries a correspondence note: its Lean declarations (`used = 1`
only) and the relation DIRECT, WEAKENING, COMPOSITION, CITED or NONE, as defined once for the
whole collection in
[honest-publication](../honest-publication/references/correspondence-and-statement.md#relations).

## References

- [Drafting, reconciling and measuring](references/spine-procedure.md): contents, the envelope,
  the two drafts, the reconciliation, the review of the contracts, measuring, the placeholders of
  the prompt templates.
- [Natural form](references/natural-form.md): the rules with an example, main theorems, the formal
  statement in an appendix, opening definitions.
- [The clause map](references/clause-map.md): clause ids, the table, scope-sensitive clauses,
  correspondence notes and their relations, the check and the review.
- [Freezing and drift](references/freezing-and-drift.md): approval, Lean-specific drift rules, the
  drift log, owner reviews, later lemmas as targets.

## Scripts

- `scripts/clause_map_check.py`: checks that every frozen clause id has a row with a destination,
  that every destination is an existing label or heading, that no clause is mapped twice without a
  note, that no row names an unknown clause, and optionally that every cited Lean name is in the
  closure; `--rows-only` only checks that the map has a row, and says where the map must be (the
  section-cycle configs run it before every review). Assumes ids tagged in the frozen spine (or a
  list) and labels in the given files. Does not read the destinations' text.
- `scripts/typeset_spine.sh`: converts the Markdown spine with pandoc, compiles it with latexmk and
  the manuscript's preamble, prints total pages and pages per block, and fails over a given
  maximum. Assumes pandoc and latexmk: without them it measures nothing, prints SKIPPED and
  exits 3; if LaTeX writes no PDF it exits 1 with the first errors; `-n` is a dry run (exit 0).
  Does not check content.

Assets: `SPINE-template.md` (the drafts, the reconciled merge and the frozen contracts,
`SPINE.md`); `SPINE-NATURAL-template.md` (the natural spine, `SPINE-NATURAL.md`, the authority
for statements once approved, with the clause map); `clause-map-header.tsv`,
`drift-log-template.md`, `spine-preamble.tex`, and prompt templates in `assets/prompts/` for the
shared agent layer.

## What this establishes and what it does not

- A clean `clause_map_check.py` establishes that every frozen clause is assigned to a destination
  that exists and, only when run with `--used-names`, that every backticked dotted Lean name in
  the map files is in the closure of the main theorem (a name written otherwise is not seen). It
  does not establish that the destination says what the clause says, nor that the clause is true.
- The clause-map review and the owner reviews are comparisons of statements with Lean
  declarations by AI agents. They are not proof checks, and agreement between two drafts or two
  reviewers is not correctness.
- `used = 1` establishes that a declaration is reached from the main theorem, not that it proves
  the clause cited to it.
- The measured pages describe the typeset spine, nothing about its mathematics.
- Freezing records the author's decision; it verifies nothing.

## Related skills

- [exposition-standards](../exposition-standards/SKILL.md): caps, counting rule, vocabulary.
- [writing-workflow](../writing-workflow/SKILL.md): sections written against the spine; owner reviews.
- [cross-section-consistency](../cross-section-consistency/SKILL.md): users of a changed later lemma.
- [honest-publication](../honest-publication/SKILL.md): the correspondence table and the appendix.
- `math-paper-campaign` (collection *math-paper-skills*, required): drift protocol and packets
  (`shared-controls.md`); claims and the correspondence table (`from-formalization.md`).
- `latex-math-writing`: how to craft a statement ("Craft statements" in `artisan-writing.md`).
- `lean-statement-audit`: one Lean declaration against its mathematical source.
