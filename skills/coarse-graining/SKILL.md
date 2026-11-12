---
name: coarse-graining
description: Divide the closure of a Lean development's main theorem into parts and units with an owner for every declaration, select key statements with two independent readers, and write unit outlines (detailed notes, then condensed outlines within measured word allowances) with pinned Lean links, plus summary and architecture pages, a glossary of the code's nicknames and a provenance analysis. Use after the dependency graph exists, when a large formal proof must be mapped and explained before a manuscript is planned, or when such a map must be reviewed, re-cut or republished.
---

# Coarse-graining a formal proof

Reduce the closure of a main theorem, tens of thousands of declarations, to a few parts and a few dozen units that
a mathematician can read, and give each unit an outline whose every statement links to the exact Lean lines. The
map is the skeleton of everything written later.

**Cut along the mathematics, place every declaration with the graph, and measure every length.** Folders and names
record the history of the code ([L6](../lean-to-manuscript/references/lessons-learned.md#l6)); outlines that
nobody measured grew 4.4 times past their template ([L7](../lean-to-manuscript/references/lessons-learned.md#l7)).

## When to use

- After [lean-dependency-graph](../lean-dependency-graph/SKILL.md) has built the graph and marked `used = 1`.
- Before [statement-spine](../statement-spine/SKILL.md) fixes the paper's statements and
  [writing-workflow](../writing-workflow/SKILL.md) writes sections: units become sections, outlines become the
  writers' inputs.
- When a published map must be re-cut after the graph changes, or its tables republished.

Not for: extracting the graph (lean-dependency-graph); natural-form statements and the clause map
(statement-spine); prose style (`latex-math-writing`); auditing one declaration against a source
(`lean-statement-audit`).

## Procedure

0. **Calibrate on a known case.** Run every automatic step first on an earlier formalization whose human paper is
   known, and measure. Before Yang–Mills, the pipeline ran on a Navier–Stokes formalization: statement selection
   matched the human paper about twice as well as graph ranking alone, and 14 of 15 sampled summary sentences were
   accurate. **If no such formalization exists, calibrate on a hand-checked sample:** a human reader checks about
   15 sampled summary sentences and the top of the selection, and the report calls it a hand-checked sample of this
   project. Never present an uncalibrated selection as calibrated. *Deliverable:* the measured comparison or the
   hand-checked sample, and the list of changes it caused.
1. **Ownership and scales.** `own_and_scale.py` computes the dominator tree from the roots, each result's mass
   (its lines plus everything it dominates), and a ladder of retained results at scales M = 100 … 3,200 lines;
   every other declaration is private to one result or shared. The script does not first fold fields, instances
   and short wrappers into the declarations they serve; a pipeline that does gets different counts, so state the
   convention with any published ladder. *Deliverable:* `dominators.tsv`, `ladder.tsv`, retained lists and edges.
2. **Shared machinery.** Group the toolbox (material used from several regions) by source folder and by
   similarity of use. *Deliverable:* named toolbox groups with lines and users.
3. **Parts, units, interfaces.** Cut along the mathematics, in dependency order where it allows; reuse any
   decomposition the authors made explicit; never trust a folder name without its graph. Write what each part
   hands to the next. Yang–Mills: 8 parts, 32 units. *Deliverable:* a unit catalogue,
   `declaration-units.tsv` (one unit per declaration), an interfaces page.
4. **Data tables.** `unit_tables.py` writes `units.tsv` (lines, declarations, `builds_on`/`used_by` at a pair
   threshold, default 25) and lists used declarations without a unit; state the counting scopes
   ([L4](../lean-to-manuscript/references/lessons-learned.md#l4)). *Deliverable:* tables and a data dictionary.
5. **Key statements.** `inventory.py --candidates` writes the candidates (the roots and the results retained at
   M = 100) in batches of about 25, each with its docstring and statement excerpt. Two independent readers label
   each (main, key, technical, bookkeeping) with a one-sentence summary (`assets/rollout.key-statements.example.json`,
   `assets/prompts/key-statement-reader.md`); `kappa.py` reads their tables and reports Cohen's κ as agreement, not
   accuracy ([L8](../lean-to-manuscript/references/lessons-learned.md#l8)). Yang–Mills: 2,424 candidates,
   κ = 0.72, 989 selected. *Deliverable:* `key-statements.tsv`, the κ report.
6. **Glossary.** Translate the code's nicknames, each entry with a confidence label (certain, probable,
   tentative) whose meaning is published. *Deliverable:* the glossary page.
7. **Unit outlines: detailed notes.** `inventory.py` writes each unit's source inventory (size, results by mass
   with statement excerpts, definitions, inputs from other units); the writers also read the statement page made
   in phase 0 ([lean-to-manuscript](../lean-to-manuscript/SKILL.md)). Pilot two units first; then writer →
   independent checker → editor for every unit (`assets/rollout.outlines.example.json`), each statement compared
   with its linked declaration; publish each unit's status (draft, compared, edited) with its defined meaning
   ([L32](../lean-to-manuscript/references/lessons-learned.md#l32)). *Deliverable:* inventories, notes, check
   reports, response tables, status files.
8. **Condensed outlines within an allowance.** One page (about 500 words) per 4,000 Lean lines, at least 3 and at
   most 10 pages, measured on landing by `outline_budget.py`, one retry quoting the overrun, then a fidelity check
   against the notes (`assets/rollout.compress.example.json`). *Deliverable:* outlines within allowance, measured
   counts, fidelity verdicts.
9. **Pages.** Unit pages with the Lean map (source inventory, key statements, code dependencies, pinned links from
   `lean_links.py`), "the proof in one reading", the architecture page, the provenance analysis;
   `gh_math.py --check` on every page. *Deliverable:* the published levels of detail, every link pinned to the commit.

## References

- [ownership-and-units.md](references/ownership-and-units.md): dominators, mass, scales, toolbox, cutting units,
  interfaces and the architecture page.
- [key-statements.md](references/key-statements.md): candidates, two readers, κ, calibration on a known paper.
- [unit-outlines.md](references/unit-outlines.md): template, review rounds and statuses, allowances, compression,
  fidelity, Lean maps, summary pages.
- [glossary-and-provenance.md](references/glossary-and-provenance.md): nickname glossaries; where the ideas come from.
- [data-tables.md](references/data-tables.md): the published tables and their counting scopes.

## Scripts and assets

| Script | What it does | Assumes | Does not |
|---|---|---|---|
| `own_and_scale.py` | Dominator tree, mass, ladder of retained results, private/toolbox/concept labels, region edges | graph with `used`; roots | choose units |
| `inventory.py` | Per-unit source inventories: size, results by mass with pinned links, docstrings and statement excerpts, definitions, inputs from other units; `--candidates`: key-statement batches | graph with `used`; a declaration → unit TSV; the source at the commit (only read) | give the elaborated statement (an excerpt is cut source text) or judge importance |
| `unit_tables.py` | `units.tsv`, unit pairs, unassigned used declarations, counting scopes | a declaration → unit TSV | say what a unit means mathematically |
| `lean_links.py` | Pinned links `blob/<commit>/<path>#La-Lb`; refuses branch names | paths and lines in the graph | check that a link supports a sentence |
| `gh_math.py` | Makes Markdown math render on GitHub; `--check` reports only | `$…$` math | check the mathematics |
| `kappa.py` | Cohen's κ, raw agreement, confusion table, optional binary split; reads the readers' printed tables; checks labels and coverage | two readers' labels | measure accuracy |
| `outline_budget.py` | Words against the allowance from Lean lines; exit 1 if over; usable as a rollout `check` | Markdown outlines | judge content |

Assets: `unit-outline-template.md`; prompt templates in `assets/prompts/` (outline writer, checker, editor,
compression, fidelity; key-statement reader); rollout configurations for the driver of
[writing-workflow](../writing-workflow/SKILL.md): outlines, compression, key-statement readers.

## What this establishes and what it does not

- **Computed by the scripts:** a deterministic placement of every used declaration (retained, private to one
  result, toolbox or concept) given the graph and the roots; unit tables whose numbers count exactly what their
  scopes say; how often two readers agreed (κ).
- **Asked of agents and reported by them:** a checker was asked to compare every numbered statement of a unit's
  notes with its linked declaration, and a fidelity reviewer to list every statement of the condensed outline that
  the notes do not support or that is stronger than they are. Their reports, ending in a verdict line, are the only
  record of that work.
- **Verified by the driver:** each report exists, has its minimum length and its verdict line, and was written on
  a frozen, hashed packet; the notes and outlines have the required headings and no math that `gh_math.py --check`
  flags; each condensed outline is within its word allowance as `outline_budget.py` counts it (with the example
  config's 10% tolerance). A status (EDITED, COMPARED, FAITHFUL, ISSUES) is a regex on a verdict line.
- **Verified by nothing here:** that a checker read what it reports; that the units are the right mathematical
  decomposition (an editorial choice); that a code reference between units is a mathematical prerequisite or a
  reading order; that a "compared" or "edited" outline is correct (the prose is not machine-checked); that κ
  measures accuracy; that a glossary label certifies correctness; that a provenance analysis shows borrowing or
  priority (it names the closest antecedents among the sources read).

## Related skills

[lean-dependency-graph](../lean-dependency-graph/SKILL.md) (the graph),
[lean-to-manuscript](../lean-to-manuscript/SKILL.md) (the campaign),
[statement-spine](../statement-spine/SKILL.md) and [writing-workflow](../writing-workflow/SKILL.md) (next steps;
the rollout driver), [honest-publication](../honest-publication/SKILL.md) (status tables, wording of what was
checked); `visual-paper` and `math-figures` (companion sites and figures), `math-paper-campaign` (its
`from-formalization.md` reference).
