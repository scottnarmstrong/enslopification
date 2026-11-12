# Drafting, reconciling and measuring the spine

How to produce the spine up to the frozen contracts, with examples from the Yang–Mills campaign
(2026), which turned OpenAI's Lean proof of the construction of four-dimensional quantum
Yang–Mills theory into a manuscript. Natural form and the clause map have their own references.

## What the spine contains

One document, written before any prose, fixing:

- **the definitions the main theorem needs**, and nothing more: machinery is defined later,
  where it is used ([L14](../../lean-to-manuscript/references/lessons-learned.md#l14));
- **the main theorems**: the natural theorem a reader wants, and the literal formal statement
  for the appendix ([L15](../../lean-to-manuscript/references/lessons-learned.md#l15));
- **the principal statements**: the real interfaces of the proof. Each is established by a large
  block of the later part and consumed by the deduction or by another principal statement. A
  statement that nothing consumes is not principal; neither is a component extracted from a
  larger result, an immediate specialisation, an identity local to one proof, or a convenience
  of the formal proof;
- **the deduction of the main theorems** from the principal statements, as numbered steps in
  the order in which objects and constants are chosen, with a table checking every clause of
  the main theorems against the steps, and a table of constants (constant, chosen after,
  depends on, fixed by);
- **the later lemmas** that prove the principal statements and carry their side conditions,
  each in one line with its home and its Lean declarations;
- **its measured size**, typeset alone.

Use `assets/SPINE-template.md` for the drafts and the frozen contracts, and
`assets/SPINE-NATURAL-template.md` for the natural spine. In the Yang–Mills campaign the opening
part has fifteen principal statements after the natural restatement, from the one-step
renormalization bound to the contact extensions of the operator product expansion.

## The envelope of a principal statement

| Field | Content |
|---|---|
| role | what it is for; which deduction steps and statements use it |
| statement | hypotheses, quantifiers in order, conclusion displayed, uniformities, constants with their dependence; existence or universality as the Lean decides |
| correspondence | the `used = 1` declarations with file:line at the pinned commit; DIRECT, WEAKENING, COMPOSITION, CITED or NONE ([clause map](clause-map.md#correspondence-notes)) |
| consumers and dependencies | who uses it; what it uses; standard results cited exactly |
| home and allowance | the later section that proves it; its pages |
| idea of the proof | five to ten lines, "Step 1 … Step k"; it becomes the text after the statement |
| least certain point | where the sources are incomplete or the Lean is hard to read |

The least certain point is not optional. It tells the reviewers where to look first and keeps
the drafter from writing over what it did not understand.

## Two independent drafts

One drafter's spine is one opinion ([L16](../../lean-to-manuscript/references/lessons-learned.md#l16)).
Give the same task (`assets/prompts/spine-drafter.md`) to two drafters, preferably from different
model families, neither seeing the other's output. Give them the exact theorem, the maps
(outlines, summary, glossary; never evidence), the detail standard and the dependency database,
and the rule that only `used = 1` declarations may be cited.

The drafts will differ in granularity, and that is useful: one drafter may split a long
construction into a one-step statement, a statement about the whole trajectory, uniform bounds and
a limit, while the other folds them into a single family statement. Which interface the later
part needs is a decision for the author, not for either drafter.

## The reconciliation

Run it as a read-only job that prints its result (`assets/prompts/reconcile.md`). It contains:

1. **A used-check of every cited name**, looked up exactly and then by suffix. Expect three kinds
   of misses: declarations on unused alternative routes
   ([L5](../../lean-to-manuscript/references/lessons-learned.md#l5)); structure fields that the
   main route never reads although it builds the structure (cite the producer that the main route
   consumes instead); and names that do not exist. A miss can mean that the claim is wrong, not
   just its citation: a criterion that only an unused route imposes may be, on the used route, a
   later conclusion or no condition at all.
2. **A map from one draft to the other**, statement by statement: same, split, merged, missing,
   different.
3. **The choice, statement by statement**, with the Lean evidence and the reader in mind.
4. **The merged spine** with full envelopes, the deduction and the recommended main theorems.
5. **Decisions for the author**, numbered, each with options, evidence and a recommendation.
   Typical questions: the granularity of the principal statements where the drafts differ; where
   the inputs of later statements live; the order of the quantifiers over sequences and constants;
   the scope of each law (every case, or a selected one); one statement or several for a result
   and its extensions; the scope of the detailed main theorem; whether to prove standard facts or
   cite them.

The author rules on each decision before the contracts are written; a ruling may be revised after
the review below.

## Review of the frozen contracts

Write the merged statements in full as the frozen contracts, every clause tagged `[clause:ID]`,
and have them reviewed by a fresh reader with the Lean and the database. Ask for strength in both
directions, the reading of every quantifier, and every citation.

The typical blocker is a phrase such as "for admissible constants", which a reader takes as "for
every choice above the thresholds" while the Lean proves that one run of the construction works:
restate such statements in existence form, with the order in which constants are chosen
([L12](../../lean-to-manuscript/references/lessons-learned.md#l12)). Typical fixes remove what the
Lean does not state: an explicit rate, or a claim about how an object is built. Apply the fixes,
have the changed statements re-read once, then restate in natural form.

## Measure the spine before writing prose

Typeset the spine alone with the manuscript's preamble (`scripts/typeset_spine.sh -p main.tex`),
add the expected introduction and connecting prose, and compare the pages with the allowance of
the opening part ([L7](../../lean-to-manuscript/references/lessons-learned.md#l7)). The pages per
block show where the opening part spends its length and so name the place to cut, often the
definitions: a spine whose definitions crowd out the main theorem gives a paper that reaches its
main theorem late ([L14](../../lean-to-manuscript/references/lessons-learned.md#l14)).

Measure again after the natural restatement, and derive the allowances of the later sections from
the measured spine and the pilots, not from a guess made before them
([L23](../../lean-to-manuscript/references/lessons-learned.md#l23)).

## Placeholders of the prompt templates

The templates in `assets/prompts/` use double-brace placeholders for the shared agent layer
(`agent_cli.py` and `rollout.py` in [writing-workflow](../../writing-workflow/SKILL.md)); set them
as `vars`.

| Template | Placeholders |
|---|---|
| `spine-drafter.md` | `project`, `lean_repo`, `commit`, `output`, `manuscript_plan`, `reader`, `detail_standard`, `style`, `db`, `statement_file`, `maps`, `roots`, `max_lines` |
| `reconcile.md` | `project`, `db`, `lean_repo`, `commit`, `draft_a`, `draft_b`, `drafter_task`, `detail_standard`, `statement_file`, `reader` |
| `natural-form.md` | `frozen_spine`, `output`, `measured_shape`, `style`, `detail_standard`, `exemplar`, `stmt_target`, `stmt_cap`, `def_target`, `def_cap`, `main_cap`, `main_refcap`, `shape_cmd`, `check_cmd` |
| `clause-map-review.md` | `natural_spine`, `frozen_spine`, `db`, `lean_repo`, `commit`, `check_output` |

Run the drafters as writers (their deliverable is a file) and the reconciliation and the
clause-map review as reviewers (they print their report, which the driver saves; read-only
reviewers cannot write files, [L22](../../lean-to-manuscript/references/lessons-learned.md#l22)).
