# Key statements

Which statements of the closure a reader must know, chosen by graph ranking and by two independent readers. Lesson:
[L8](../../lean-to-manuscript/references/lessons-learned.md#l8).

## Candidates

`inventory.py --candidates` writes them, from the graph, the unit assignment and the source at the pinned commit:

1. **Select** the roots and every result of the closure with mass at least M (default 100 lines; the mass of a
   result counts its lines and those of everything reached from the roots only through it): the results that
   `own_and_scale.py` retains at that scale. A smaller helper is not a candidate; its lines count in the mass of a
   result above it. Keep enough candidates for the readers to discard most: the Yang–Mills readers saw 2,424
   candidate statements in 106 coherent groups.
2. **Batch** them by unit, in source order, at most 25 per batch (`--batch-size`), so that a reader sees a statement
   next to its variants and restatements, which usually sit beside it in the source. Each candidate comes with its
   pinned link, its docstring, its mass and an excerpt of its statement read from the source and cut at the first
   `:=`: an excerpt, not the elaborated statement, so the reader opens the link when it is unclear.
3. **Outputs:** `B001.md`, `B002.md`, … (the batches), `candidates.tsv` (item, batch, unit, kind, lines, mass, link,
   first docstring line) and `batches.json` (the unit entries of the readers' rollout configuration).

## Two independent readers

Two readers, each without the other's labels, label every candidate and write one plain sentence saying what it
states (prompt: `assets/prompts/key-statement-reader.md`):

| Label | Meaning |
|---|---|
| `main` | a conclusion of the development or of a part |
| `key` | a result other units rely on, or the heart of a unit's argument |
| `technical` | needed, but a reader can take it on trust |
| `bookkeeping` | packaging, conversions, restatements |

`assets/rollout.key-statements.example.json` runs one review stage per batch with two jobs, `reader-a` and
`reader-b`, on the same frozen batch. Each reader prints a line "Sources consulted:" and then a tab-separated table
with the header `item`, `label`, `summary`, one row per candidate; the stage requires that header, so a reader that
prints another format is retried once. The rollout driver checks a reviewer's model family only against a
preceding writer, so it does not check that the two readers differ: choose them yourself. Different families
reduce shared blind spots; the same model and prompt twice measure the consistency of one procedure. Say which you
did. The Yang–Mills readers were two runs of one model.

## Agreement: Cohen's κ

`kappa.py` reads the readers' printed tables directly (one report per batch: give a shell glob), checks that every
candidate got a label from each reader and that no other label was used, and reports raw agreement, chance
agreement, κ and the confusion table, optionally after collapsing the labels to a binary split:

```sh
kappa.py --a work/*/read/reader-a.md --b work/*/read/reader-b.md --labels main,key,technical,bookkeeping \
    --collapse main,key --items batches/candidates.tsv
```

The Yang–Mills readers had κ = 0.72 on "main or key" against the other labels. **κ measures agreement between the
readers, not accuracy:** two readers can agree and both be wrong, and κ says nothing about the summary sentences.
Publish it with that sentence attached.

## Selection

Select the union of the graph's numbered results (the top of the ranking in two tiers, sized for a hypothetical
account of a chosen length) and every candidate that either reader labelled main or key. Record the label shown
to readers by a fixed rule, for example: main if either reader said main, else key if either said key, else the
graph tier. The Yang–Mills selection had 989 statements: 59 main results, 605 key results, 5 major and 312
numbered results from graph tiers, 8 without a label. The selection flag and the displayed label are different
fields; keep both.

## Accuracy is measured elsewhere

Measure accuracy only where the answer is known: on an earlier formalization whose human paper exists. Before the
Yang–Mills campaign the same pipeline ran on a Navier–Stokes formalization: the selection matched the human
paper's statements about twice as well as graph ranking alone, and 14 of 15 sampled summary sentences were
accurate. Say that these spot checks were made on that project, and were not repeated on the target, so they give
no accuracy rate for it.

When no earlier formalization with a known paper exists, calibrate on a **hand-checked sample** of the target: a
human reader checks about 15 randomly sampled summary sentences against the linked Lean, and reads the top of the
selection (the main results and the first key results of each part) for omissions and misjudged labels. Report it
as a hand-checked sample of this project, with its size and its result, not as an accuracy rate. A selection that
had neither check is uncalibrated: say so wherever it is published, and never present it as calibrated.

What a selected statement is not: a correctness label, a review status, or a complete statement of hypotheses (the
summary is one sentence). Each row links to the pinned Lean, which is the statement.
