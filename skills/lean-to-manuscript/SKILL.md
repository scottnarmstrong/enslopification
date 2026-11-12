---
name: lean-to-manuscript
description: Run the whole campaign that turns a completed Lean development into a natural-language mathematical manuscript — map its compiled dependency graph, coarse-grain and outline it, freeze a statement spine with the author, write it with writers, one editor and independent reviewers checking against the Lean, reconcile sections, run referee rounds, and publish with exact claims about what was checked. Use when starting, planning, resuming or supervising such a campaign, setting its budgets, deciding what to put to the author, or running it overnight.
---

# From a Lean development to a manuscript

A completed formal proof settles the correctness of its formal theorem. It does not give a reader a proof they can
follow. This campaign produces that text: a manuscript a mathematician can read and check by hand, which claims
nothing the Lean does not prove and says exactly what was checked, by whom and how. **The Lean is the only
authority; outlines, summaries and the graph are maps for finding things in it.** Two failures dominate every
campaign of this kind: text that takes the shape of the code ([L9](references/lessons-learned.md#l9),
[L10](references/lessons-learned.md#l10)), and text that grows because nobody measures it
([L1](references/lessons-learned.md#l1), [L7](references/lessons-learned.md#l7)). The process below is built
against both.

Use this skill to plan and run the campaign. Each phase is carried out with a narrower skill of this collection.
Do not use it to formalize a paper in Lean (use `lean-orchestrator`), to audit one declaration against a source
(`lean-statement-audit`), or to polish a manuscript whose mathematics is already checked (`math-paper-campaign`,
route B). For the prose of each section use `latex-math-writing`.

## Roles

| role | who | does | never |
|---|---|---|---|
| **author** (project lead) | a person | sets goals, approves the brief, the spine and every change to a frozen statement, reads pilots and finished parts, rules on scope, length and authorship | — |
| **editor** | the orchestrating agent | writes tasks, integrates proposals (the only one who edits the manuscript), runs checks, keeps the records, decides findings, writes the morning list | writes sections itself instead of editing; applies unadjudicated review text |
| **writers** | agents of one model family | write proposals for one section or unit at a time in their own directory, with notes and a correspondence table | edit the manuscript or another section |
| **reviewers** | agents of another family, fresh context | read a frozen snapshot and report | edit anything |
| **human readers** | colleagues | read and comment; they outrank agent reviewers ([L26](references/lessons-learned.md#l26)) | — |

The rule that matters is that **the writer and the reviewer of a packet come from different model families**; the
scripts take any agent command line ([driver](../writing-workflow/SKILL.md)).

## The campaign

Carry the campaign through these phases. Each ends with a deliverable; ★ marks an author decision. Details,
inputs and budgets: [phases](references/phases.md).

0. **Brief.** Inspect the development, its verification record and any usage record; propose the decisions of
   [author decisions](references/author-decisions.md) (principal results, authority, reader, detail standard,
   citation policy, Lean names, workers, visibility, authorship, pilots, page totals) and the size of the
   campaign ([sizing](references/phases.md#sizing-the-campaign)). ★ The author approves. Deliverables: `BRIEF.md`
   (decisions only; progress lives elsewhere) and a first statement page: the formal statement verbatim, in words,
   and in ordinary mathematics compared definition by definition with the Lean, with explicit nonclaims.
1. **Map the Lean.** Compiled dependency graph, the closure of the headline results (`used = 1`), comparison with
   the authors' record ([`lean-dependency-graph`](../lean-dependency-graph/SKILL.md)). Deliverable: a SQLite
   graph and a report of what it does and does not check.
2. **Coarse-grain and outline.** Parts and units owning every declaration, key statements, unit outlines with
   measured length, summary, architecture, glossary, provenance ([`coarse-graining`](../coarse-graining/SKILL.md)).
   ★ The author approves the architecture. Deliverable: the map, at several levels of detail.
3. **Freeze the spine.** Two independent drafts, a reconciliation, natural-form statements, a clause map showing
   that nothing was lost ([`statement-spine`](../statement-spine/SKILL.md)). ★ The author approves; from then on
   every change to a frozen statement is drift and goes to the author.
4. **Fix the standards.** Exemplar paper, style file, detail standard, terminology, automatic checks
   ([`exposition-standards`](../exposition-standards/SKILL.md)). Deliverable: `STYLE.md`, `DETAIL-STANDARD.md`,
   the checks running clean on an empty skeleton.
5. **Write the opening part** (definitions, main theorems, principal statements with proof ideas, the deduction)
   through the full review cycle ([`writing-workflow`](../writing-workflow/SKILL.md)).
6. **Pilots.** Two proof sections, on different sides of the proof, through the full cycle. ★ The author reads
   them and calibrates; the comments become binding style the same day
   ([L24](references/lessons-learned.md#l24)).
7. **Roll out** the other sections in parallel at the pilots' level, each through the full cycle
   ([`writing-workflow`](../writing-workflow/SKILL.md)).
8. **Reconcile sections** with routed-inputs checks until a targeted re-check confirms every item
   ([`cross-section-consistency`](../cross-section-consistency/SKILL.md)).
9. **Introduction and abstract**, only once the theorem surface has stopped moving, with the disclosure
   ([`honest-publication`](../honest-publication/SKILL.md)).
10. **Referees, adjudication, typography** ([`referee-adjudication`](../referee-adjudication/SKILL.md)).
11. **Human reading and editorial pass**: an editorial plan merging human and agent reviews, with page budgets.
    ★ The author rules on its decisions ([`referee-adjudication`](../referee-adjudication/SKILL.md)).
12. **Publish and keep publishing honestly**: status table, correspondence table, process page, changelog,
    markers ([`honest-publication`](../honest-publication/SKILL.md)); before calling it finished, the final audit
    and completion test of `math-paper-campaign`.

Phases 1–2 can run without waiting for the author; writing (phase 5 onwards) waits for the approved spine. Do not
stop after a plan or a review when the next step is ready; stop only for an author decision, a mathematical
question the Lean does not settle, missing sources, or authority you have not been given.

## Budgets: measure, never estimate

- **Pages.** A total, a share per part, an allowance per section derived from the measured frozen statements and the
  pilots. Measure after every round; **over the allowance means not done**. A projected overrun goes to the author
  with measured options before work continues ([L23](references/lessons-learned.md#l23)); for the hardest sections
  the author may make completeness binding and the page figure a guide.
- **Shape.** Words per statement and definition, references per statement, forbidden vocabulary: checked by
  scripts after every integration ([L1](references/lessons-learned.md#l1)).
- **Passes.** A pass is done when its measured target is met and its response table is complete, not when an agent
  stops ([L2](references/lessons-learned.md#l2)).
- **Machine.** One heavy Lean job at a time, throttled; a fixed number of writer and reviewer slots
  ([L34](references/lessons-learned.md#l34)).

## Records

Keep the working files in a private repository and the reader-facing text in a public one if the author chooses to
write in public; `scripts/init_campaign.py` creates the working tree. Minimum records: `BRIEF.md` (decisions),
`STYLE.md` and `DETAIL-STANDARD.md` (binding), the spine and its drift log, the statement register (one row per
numbered statement with separate mathematical, exposition and rendering statuses), the correspondence table, the
response table of every review round, prompts (superseded ones archived, never reused), and `MORNING.md`.

## Overnight mode

When the author is away, keep working through reversible steps, take provisional defaults for decisions that are
the author's, and write the morning list as you go ([L35](references/lessons-learned.md#l35);
[template and rules](references/author-decisions.md#overnight-mode-and-the-morning-list)). Never change a frozen
statement, publish a new kind of claim, or delete a proved result overnight.

## Scripts

- `scripts/init_campaign.py DIR` — creates the working tree of [phases](references/phases.md#the-working-repository)
  from the templates of all the skills; `--dry-run` lists it. It writes only templates; it decides nothing.
- The drivers that run writers and reviewers are in [`writing-workflow`](../writing-workflow/SKILL.md)
  (`agent_cli.py`, `rollout.py`, `make_packet.py`); the checks are in
  [`exposition-standards`](../exposition-standards/SKILL.md).

## What this establishes and what it does not

Run as described, the campaign produces a record: for every numbered statement, a report by a reviewer of another
model family than its writer, asked to compare it clause by clause with the Lean declarations it rests on; for every
section, a prose-truth report on its explanatory sentences; a decision for every finding; the measured shape and
length. Scripts verify what they can count: each report exists, is long enough and ends with a verdict; every label
and page appears in some report (`check_coverage.py`); the shape, vocabulary and compile checks pass. Whether a
reviewer did what it reports is not mechanically verified; the editor spot-checks it.

The correctness of the *theorem* rests on the Lean kernel check of the formal development. The faithfulness of the
*manuscript* to the Lean rests on agent reviews, independent of the writers but not of each other's training. Nothing
here replaces a human referee's reading, or checks that the formal statement expresses the intended mathematics
(`lean-statement-audit`). Say this, in these terms, wherever the work is published.

## References

- [phases](references/phases.md): inputs, deliverables, checks and budgets of each phase; the working repository.
- [author decisions](references/author-decisions.md): what the author decides, when to stop and ask, overnight
  mode and the morning list.
- [worked example](references/worked-example.md): the Yang–Mills campaign, phase by phase, with times and sizes.
- [lessons learned](references/lessons-learned.md): every failure and its fix, cited by ID across the collection.

## Related skills

This collection: `lean-dependency-graph`, `coarse-graining`, `statement-spine`, `exposition-standards`,
`writing-workflow`, `cross-section-consistency`, `referee-adjudication`, `honest-publication`. Elsewhere:
`math-paper-campaign` (packets, drift protocol, final audit; its reference `from-formalization.md` is the short
version of this campaign), `latex-math-writing` (prose and typesetting), `math-figures` (figures),
`visual-paper` (a companion website), `lean-statement-audit` and `manuscript-audit` (audits).
