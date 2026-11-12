# Unit outlines, allowances and the published pages

How each unit gets its detailed notes and its condensed outline, how both are reviewed and measured, and what the
published unit pages contain. Lessons: [L7](../../lean-to-manuscript/references/lessons-learned.md#l7),
[L22](../../lean-to-manuscript/references/lessons-learned.md#l22),
[L32](../../lean-to-manuscript/references/lessons-learned.md#l32).

## The template

`assets/unit-outline-template.md`: a header (part, Lean folders, size), then seven sections: what the unit proves
(numbered propositions with status and pinned link), what it uses (inputs from other units by id, standard
mathematics, imported constants), strategy, steps (each with a link and *proof read* or *statement only*), where
the difficulty lies, notation, what remains unexplained. Every statement carries its hypotheses and quantifiers;
uncertain statements are marked (probable) or (tentative); only `used = 1` declarations are cited.

**Inputs of every round.** The unit's source inventory, written by `inventory.py` (size and files; results by
mass, each with a pinned link, its docstring and a statement excerpt; definitions introduced; inputs from other
units, most used first; what other units use; key statements); the architecture and interfaces; the statement page
`statement.md`, written in phase 0 of the campaign
([lean-to-manuscript](../../lean-to-manuscript/references/phases.md#0-brief)) in the format of honest-publication's
[statement page template](../../honest-publication/assets/statement-page.template.md); the glossary; the Lean and
the graph, read-only.

Pilot two units first, one on each side of the proof, and adjust the template after them before running the other
units.

## Detailed notes: three rounds

| Round | Who | Does | Resulting status |
|---|---|---|---|
| draft | a fast model | writes the notes from the source inventory, the interfaces, the statement page, the glossary and the Lean | draft |
| compare and rewrite | a strong model | compares every numbered statement with the linked Lean (hypotheses, quantifiers, conclusion, status), reads the main proofs, rewrites | compared |
| edit | a strong model of another family | compares again with the Lean, edits the exposition | edited |

The rollout configuration `assets/rollout.outlines.example.json` expresses this as stages for the driver of
[writing-workflow](../../writing-workflow/SKILL.md): `draft` (writer prompt) → `check` (an independent checker
that prints a report ending in a verdict line) → `edit` (the editor settles every finding against the Lean and
writes a response table) → `confirm` (the checker again, on the edited notes) → `status` (the verdict: `EDITED`
when the confirmation finds no mismatch, `COMPARED` otherwise; a unit that has not reached it is *draft*).
Checkers print their reports and edit nothing: a read-only reviewer asked to write a file fails silently
([L22](../../lean-to-manuscript/references/lessons-learned.md#l22)). Every report starts with the sources it
actually opened, so that a blocked lookup shows at once. The driver requires a reviewer and the writer before it to
come from different model families, so the example drafts with the `writer` profile and checks with the `reviewer`
profile of another family; to draft with a cheaper model, add a profile and keep the checker in the other family.

The second round earns its cost. In the Yang–Mills campaign it found dropped hypotheses and overbroad statements in
the first two units, and a coefficient that the draft described as assumed although the proof computes it.

**Statuses** each mean one thing, and their meaning is published with them
([L32](../../lean-to-manuscript/references/lessons-learned.md#l32)):

- *draft*: written from the Lean; not yet compared with it by another agent;
- *compared*: numbered statements compared with the linked Lean by an agent other than the writer, and the account
  rewritten; subsidiary estimates may remain at statement level (the unit says which);
- *edited*: compared again and edited; local limitations still apply; not an independent human proof review.

The Yang–Mills map called the second status *checked*; this collection says *compared*, because the campaign also
used "checked" for a manuscript section after the project lead's reading, and one word must not name two reviews.
A draft status does not mean the formal result is unproved; it describes the review of the explanation.

## Allowances, measured on landing

The Yang–Mills template asked for three to ten pages per unit. Over the three rounds each reviewer added detail and
nobody measured the total: the outlines grew 4.4 times past the template. The fix keeps two versions and measures:

- The **detailed notes** keep everything the rounds produced, with a proof sketch for every step. They are
  published as they are, on their own pages (595 pages for the 32 Yang–Mills units).
- The **outline** is condensed from the notes within an allowance: one page (about 500 words) per 4,000 Lean lines
  of the unit, at least 3 and at most 10 pages (`outline_budget.py`: the nearest whole page, clamped). A unit of
  7,215 lines gets 3 pages, 1,500 words; one of 49,448 lines gets 10 pages, 5,000 words.
- **Measure when the draft lands**, not when the writer says it is done: word count with link URLs not counted.
  Over the allowance by more than 10%: one retry, with the measured overrun quoted in the prompt. Still over:
  record it and decide by hand; do not loop.
- **Check fidelity:** a reviewer compares the outline with the notes and lists every statement that the notes do
  not support or that is stronger than the notes: a dropped hypothesis, a changed quantifier, a status upgraded
  from assumption to theorem, a changed link. A cap is met by cutting steps and sketches, never by moving
  hypotheses out of statements.

`assets/rollout.compress.example.json` runs `compress` (with `outline_budget.py` as its check, so the driver
retries once with the measured overrun) → `fidelity` → `status-outline`, in a workdir of its own: its STATUS
(FAITHFUL or ISSUES) must never overwrite the notes' status.
`outline_budget.py --units-tsv units.tsv --emit-units-json` prints the per-unit pages and word allowances to paste
into the configuration. The Yang–Mills outlines, the proof in one reading and the architecture made one 164-page PDF.

## Lean maps: the unit page

Generate each unit page from the tables and the outline, so that numbers and links never drift by hand:

- **header**: part, one-sentence description, status with a link to the status meanings, links to the
  previous and next units;
- **the outline** (sections 1 to 7) and a link to the detailed notes;
- **code dependencies**: units referenced (`builds_on`) and referencing (`used_by`) at the threshold, with the
  sentence that these are code references, not a reading order;
- **source inventory**: folders and chains of results with their line counts (`inventory.py` lists the unit's
  files and results); show a group for the unit with the largest share, and for any other unit with at least 15%,
  and say that group totals need not add up;
- **key statements**: number, one-sentence summary, importance label, pinned link;
- **additional source locations**: earlier pinned links that a revised outline no longer cites, kept so that
  links people saved still resolve.

Every link is pinned: `<repo>/blob/<commit>/<path>#L<a>-L<b>` from `lean_links.py`, which refuses branch names.
Run `gh_math.py --check` on every page before publishing: `\#` or `#` inside math, `\operatorname` and a bar in
table math break on GitHub.

## Summary and architecture

- **The proof in one reading** (level 2): the strategy, the key mechanism of each part, what is new, where the
  difficulty lies, written from the outlines by one model and edited by another; revise it when the outlines
  change.
- **The architecture** (level 3): see [ownership-and-units.md](ownership-and-units.md#the-architecture-page).

Each level links down to the next and states its own review status. Put an under-construction marker on any level
that has not finished its reviews.
