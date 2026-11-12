---
name: writing-workflow
description: Write the sections of a manuscript from a frozen statement spine and a completed Lean development with several agent families - writers propose in their own directories, one editor integrates, independent reviewers read frozen snapshots (an owner per principal statement, the mathematics against the Lean, a fresh reader, prose truth, delivery) - with response tables, re-checks, pilots, measured page allowances and a resumable roll-out driver. Use when drafting or revising sections of a Lean-derived paper, setting up writer and reviewer agents, running or resuming a parallel roll-out, or writing a config for the shared agent driver.
---

# Writing workflow

Turn a frozen spine into reviewed sections, one section at a time or many in parallel, with agents that write and
agents that check. **Writers propose, one editor integrates, reviewers of another model family read frozen
snapshots; a section is done when its measured allowance is met, every finding has a recorded decision and the
delivery review says DELIVER, not when an agent stops.** The scripts here are also the shared agent layer of the
whole collection: every other skill runs its agents through them.

## When to use it, and when not

Use it after the spine is frozen ([`statement-spine`](../statement-spine/SKILL.md)) and the style rules and checks
exist ([`exposition-standards`](../exposition-standards/SKILL.md)): for the opening part, the pilots, the roll-out
of the proof sections, and the introduction.

Use instead: [`lean-to-manuscript`](../lean-to-manuscript/SKILL.md) for the campaign's phases and the author's
decisions; [`cross-section-consistency`](../cross-section-consistency/SKILL.md) once sections cite each other;
[`referee-adjudication`](../referee-adjudication/SKILL.md) for referee reports and editorial passes;
`latex-math-writing` for prose, notation and displays inside a section; the shared controls of `math-paper-campaign`
for the drift protocol, packets and ledger statuses that hold for any paper. A single local edit needs none of this.

## Roles

| role | who | does | never |
|---|---|---|---|
| project lead (author) | a person | approves the spine and every change to a frozen statement, reads the pilots and finished parts, rules on length | — |
| editor | the orchestrating agent | writes tasks, integrates delivered proposals, runs checks, keeps records, decides findings | writes sections itself; lets anyone else edit the manuscript |
| writers | one model family | write a proposal per section in their own directory, with notes, a correspondence table and requests | edit the manuscript or another section |
| reviewers | another model family, fresh contexts | read a frozen packet and print a report | edit anything |

In the Yang–Mills campaign (2026) the writers came from one model family and the reviewers from another, each
reviewer read-only in a fresh context.

## Procedure

1. **Set up the agents.** Copy [`agents.example.json`](assets/agents.example.json); give every profile a model
   `family` (a review stage refuses a profile without one, or a reviewer of the writer's family, unless it sets
   `allow_same_family`); writers write only in their stage directory, reviewers cannot write at all. Run the
   permission preflight for every profile before every round
   ([L22](../lean-to-manuscript/references/lessons-learned.md#l22)). *Deliverable:* `agents.json` whose preflight
   passes. Details: [agent profiles](references/agent-profiles.md).
2. **Fix allowances from measurement.** Typeset the frozen statements of each section, use the pilots' ratios, and
   keep the history of every allowance and who changed it
   ([L23](../lean-to-manuscript/references/lessons-learned.md#l23)). Over the allowance means not done
   ([L2](../lean-to-manuscript/references/lessons-learned.md#l2)), except where the author made the figure a guide.
   *Deliverable:* the allowance table; register rows for every numbered statement.
3. **Write the opening part** through the cycle below, as units with the task
   [`w1-opening.md`](assets/prompts/w1-opening.md): only the definitions needed to state the main theorems
   ([L14](../lean-to-manuscript/references/lessons-learned.md#l14)), the main theorems byte for byte as in the natural
   spine (a unit check compares them), the principal statements with the idea of each proof, the deduction, the
   constants and the order of their choice; one owner review per principal statement. *Deliverable:* the opening
   part delivered and integrated.
4. **Pilots.** Two proof sections on different sides of the proof go through the whole cycle; the author reads them;
   the comments become binding rules in `STYLE.md` the same day
   ([L24](../lean-to-manuscript/references/lessons-learned.md#l24)). *Deliverable:* two delivered pilots, the
   updated style file.
5. **Roll out the other sections** with `rollout.py` and
   [`rollout.section-cycle.example.json`](assets/rollout.section-cycle.example.json): proposal (`w1`) → reviews
   (`r1`: mathematics, fresh reader, prose truth, one owner job per principal statement) → revision with a response
   table (`w2`) → re-check by the same reviewers (`r2`) → last fixes (`w3`) → delivery (`d`: the driver first
   recompiles and measures the section and lists the labels no review names) → verdict. Run `--dry-run` first. *Deliverable:*
   every section with STATUS DELIVER or NOT YET, and its records.
6. **Fix up** the sections marked NOT YET with
   [`rollout.fixup.example.json`](assets/rollout.fixup.example.json) (`w4` → `d2`). *Deliverable:* STATUS DELIVER.
7. **Integrate** each delivered section: keep reader-facing tags
   ([L18](../lean-to-manuscript/references/lessons-learned.md#l18)), never redefine counters, refer to numbered items
   by `\ref` only ([L17](../lean-to-manuscript/references/lessons-learned.md#l17)), locate edits by content, compile,
   run the checks, compare the main theorems byte for byte. *Deliverable:* the integrated section, checks clean,
   register updated.
8. **Reconcile the sections** ([`cross-section-consistency`](../cross-section-consistency/SKILL.md)), then the
   project lead reads. *Deliverable:* the author's comments turned into rules.
9. **Write the introduction and the abstract last**, once the statements have stopped moving
   ([`w1-introduction.md`](assets/prompts/w1-introduction.md)): the disclosure wording approved by the author
   ([`honest-publication`](../honest-publication/SKILL.md)) copied between the vocabulary check's exception
   markers; the owners of the main theorems check the informal statements. *Deliverable:* both delivered.

The cycle step by step, requests between sections, integration rules and records:
[section cycle](references/section-cycle.md). The five reviews, their report format and their failure modes:
[reviews](references/reviews.md).

**Rules that answer failures.** The natural spine is the authority for statements; the frozen contracts and the
clause map are the record it must cover, read by the owner and mathematical reviews
([`statement-spine`](../statement-spine/SKILL.md)). A writer's input is a labelled statement that exists or a
written request, never an assumption ([L19](../lean-to-manuscript/references/lessons-learned.md#l19)). Owner
reviews check strength in both directions ([L11](../lean-to-manuscript/references/lessons-learned.md#l11)). Prose
truth checks every explanatory sentence and traces every removed condition
([L20](../lean-to-manuscript/references/lessons-learned.md#l20)). Findings are never deleted; every one gets a
decision with a reason. Writers name their least certain sentence.

## Scripts

All in [`scripts/`](scripts/); Python 3.10+, standard library; `--help` gives examples. Format of agent profiles
and rollout configs, every field: [driver](references/driver.md).

- `agent_cli.py` runs one agent job, or a permission preflight. Assumes a non-interactive agent CLI that reads the
  prompt and exits. Retries once, stops on quota messages, checks report length and verdict line, hashes protected
  paths, adopts a job left running by a killed driver. Does not judge content.
- `rollout.py` runs write, review and verdict stages for many units in parallel, resumably, with semaphores, frozen
  packets (after optional build commands), checks with one retry, inboxes and STATUS files. Assumes Unix process
  groups. Does not edit the manuscript or decide findings.
- `make_packet.py` freezes files into a review packet with a SHA-256 manifest and git HEADs; `verify_packet.py`
  reports changed or missing copies and sources. They assume `git` for the HEADs. They show whether text changed,
  nothing about its content.
- `check_allowance.py` compares the pages of a PDF (from its LaTeX log, `pdfinfo`, or the PDF itself) or the words of
  text files with an allowance. It counts; it does not say what to cut.
- `check_coverage.py` lists the labels (from a register, the statement environments of TeX files, or a list) that no
  report names, or the pages of a range that no typography report lists. Assumes reviewers name statements by label.
  A label named, or a page listed, is not evidence that it was reviewed.

Assets: agent profiles, the cycle config (opening, proof and introduction units), the fix-up config, and the prompt
templates in [`assets/prompts/`](assets/prompts/): writer rules, tasks for a proof section, the opening part and the
introduction, the five reviews, the re-check.

## What this establishes and what it does not

Reviewers of another model family than the writer were asked to compare every numbered statement with the natural
spine, the clauses the clause map assigns to it and the Lean declarations it rests on, to classify every explanatory
sentence, and to check that every finding has a recorded decision; their reports are the only record of what they
did. The scripts verified less: each report exists, has the minimum length and a verdict line; each packet was
frozen with hashes after a check that the clause map has rows; each write stage ended with the section compiling
with the manuscript's preamble, its PDF within the page allowance (only reported where the author made it a guide),
the shape and vocabulary checks passing and, in the unit that states them, the main theorems identical to the
natural spine; the driver compiled and measured the section again before the delivery review; and
`check_coverage.py` listed the statement labels that no report names, for the delivery reviewer to review. A label
that a report names was not thereby reviewed.

It does not establish correctness in the sense of a human referee's report. Reviewers are AI models, independent of
the writers but not of each other's training, and agreement between them is not accuracy. The theorem rests on the
Lean, which is machine-checked; the faithfulness of the prose to the Lean rests on these reviews, which are not. A
DELIVER status is a regex on a reviewer's verdict line.

## Related skills

[`lean-to-manuscript`](../lean-to-manuscript/SKILL.md) (the campaign), [`statement-spine`](../statement-spine/SKILL.md),
[`exposition-standards`](../exposition-standards/SKILL.md),
[`cross-section-consistency`](../cross-section-consistency/SKILL.md),
[`referee-adjudication`](../referee-adjudication/SKILL.md), [`honest-publication`](../honest-publication/SKILL.md);
elsewhere `math-paper-campaign` (shared controls, the drift protocol) and `latex-math-writing` (prose and typesetting).
