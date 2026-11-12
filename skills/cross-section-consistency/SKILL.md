---
name: cross-section-consistency
description: Make sections written in parallel agree where they cite each other - route requests for missing results between sections, inventory every citation of one section's statements by another, compare what each citing proof uses with what the cited statement says (MATCH or MISMATCH), clear or confirm citation cycles, repair both sides, and re-check until every item is resolved. Use after parallel sections of a manuscript are integrated, after any round that restates statements, and while sections are being written to route requests through inboxes.
---

# Cross-section consistency

Sections written in parallel cite each other for more than the cited statements say. This skill finds every such
place and closes it. **Compare what the citing proof uses with what the cited statement says, never with what the
cited proof gives; repair both sides in the same round; stop only when a targeted re-check confirms every item
resolved and finds no new substantive mismatch.**

## When to use it, and when not

Use it while proof sections are being written (requests between sections), after a draft of all sections is
integrated, after every round that restates statements (repairs, referee changes), and before the proof part is
delivered as a whole.

Not for one section's internal correctness: that is the mathematical review of
[`writing-workflow`](../writing-workflow/SKILL.md). Not for comparing a statement with its Lean declarations:
[`statement-spine`](../statement-spine/SKILL.md) and, for one declaration, `lean-statement-audit`. Not for the shape
of statements: [`exposition-standards`](../exposition-standards/SKILL.md).

## Why

A section can pass its own reviews while its proofs use more than the statements they cite from other sections say:
a lemma stated for one class of inputs is cited for a wider class, with an estimate that appears only inside its
proof; a range citation prints a run of statements of which the proof uses a few. Repairs change statements that
other sections also cite, so a round of repairs creates mismatches of its own and one round is rarely enough. The
Yang–Mills campaign (2026) wrote its ten proof sections in parallel and needed three rounds of checks and repairs,
the last confirming every item resolved ([L21](../lean-to-manuscript/references/lessons-learned.md#l21)).

## Procedure

1. **Route inputs while writing.** A writer who needs a result no section states proves it as a short lemma when the
   proof takes under a page, otherwise writes a request (exact statement, Lean source, owning section) in
   `REQUESTS.md` ([template](assets/REQUESTS.template.md))
   ([L19](../lean-to-manuscript/references/lessons-learned.md#l19)). The editor lists and decides the requests and
   delivers accepted ones to the owner's `INBOX.md` with `route_requests.py --config` (the rollout config names the
   units, so a section not yet written can receive requests); the driver gives the inbox to the owner's next writer,
   who answers each request in its response table. *Deliverable:* every request delivered, declined with a reason,
   or left to the author.
2. **Inventory.** Compile; enforce numbering only by cross-reference (no typed numbers, no redefined counters:
   [L17](../lean-to-manuscript/references/lessons-learned.md#l17)); run `cross_refs.py` with one unit per section
   and the opening part as a unit. *Deliverable:* `xref/` with the routed citations, ranges, the lemma-level graph,
   its cycles and the per-pair split; no undefined or duplicate label.
3. **Check, one checker per group.** Group the routed citations by cited section; one read-only checker of another
   model family per group ([`rollout.routed-check.example.json`](assets/rollout.routed-check.example.json)) marks
   every citation MATCH or MISMATCH with the exact repair and its side, decides every candidate cycle (CLEARED or
   CONFIRMED), lists what each range citation actually uses, and states whether it could query the dependency
   database ([L22](../lean-to-manuscript/references/lessons-learned.md#l22)). The opening part's pointers into the
   proof part are checked the same way, with the crosswalk of the opening part's inputs against the proof part's
   exports. *Deliverable:* one report per group.
4. **Merge.** The editor runs `check_coverage.py` of [`writing-workflow`](../writing-workflow/SKILL.md) on each
   group's report, with the group's by-pair files and its own cycle ids (`--labels`), and once on all reports with
   `xref/cycles.tsv` (a cited label or cycle that no report names goes back to a checker), reads the largest
   findings and every cycle verdict against the text, then merges the reports into one table with stable ids
   ([template](assets/mismatch-table.template.md)). *Deliverable:* the mismatch table; drift items sent to the
   author.
5. **Repair both sides in parallel.** One writer per affected section applies every item that touches its files:
   the cited statement restated to what its proof already gives ("say so"), or the citing sentence changed, or a
   new proof from the Lean, or a request ([`rollout.repair.example.json`](assets/rollout.repair.example.json)). Each
   returns a response table. The editor integrates the round at once and reruns the inventory. *Deliverable:* the
   integrated repairs, a response table per section.
6. **Targeted re-check.** The same groups, new contexts: every item RESOLVED or NOT RESOLVED with both sides quoted,
   then the repair sites only, for new mismatches the repairs created
   ([`rollout.routed-recheck.example.json`](assets/rollout.routed-recheck.example.json)). *Deliverable:* a STATUS per
   group.
7. **Repeat 5–6 until convergence:** a targeted re-check confirms every item resolved and finds no new substantive
   mismatch. After a round that changed many statements, run a full check (step 3) instead. *Deliverable:* the
   closed table, with the last re-check's verdicts.

The comparison rule, the kinds of mismatch found in practice, grouping, ranges, cycles and the crosswalk:
[routed-inputs check](references/routed-inputs-check.md). Requests, repair rounds, the re-check and what each round
finds: [repair rounds](references/repair-rounds.md).

## Scripts and assets

- `scripts/cross_refs.py` lists every `\ref`-family citation whose label lies in another unit (file, section, or a
  unit map), with the citing context, the cited kind, whether the cited label lives inside a proof, printed numbers
  from the `.aux`, range citations with what they span, the lemma-level graph and its cycles. Assumes standard
  LaTeX environments; proofs without an explicit "Proof of" are attributed to the closest preceding statement. It
  does not read meaning: typed numbers and prose references are invisible to it.
- `scripts/route_requests.py` lists the requests in a rollout workdir and delivers accepted ones to inboxes, never
  twice, to any unit of the rollout config given with `--config` (without it, only to units that already have a
  directory). It does not judge whether a request is needed.
- Assets: the checker, re-check and repair prompts in [`assets/prompts/`](assets/prompts/), the three rollout
  configs (run with `rollout.py` of [`writing-workflow`](../writing-workflow/SKILL.md), whose
  [driver reference](../writing-workflow/references/driver.md) documents the format), the request and mismatch-table
  templates.

## What this establishes and what it does not

Checkers of another model family than the writers were asked to compare every routed `\ref` citation of their
group with the statement it cites and to decide every candidate cycle, and their reports give a verdict per citation
and per cycle; the reports are the only record of that work. The driver verified only that each report exists, has
the minimum length and the required verdict line, and was written on a frozen, hashed packet. `check_coverage.py`
(of `writing-workflow`) lists the cited labels and cycles that a group's report never names; a label it names was
not thereby checked. Mismatches, repairs and decisions are recorded in the merged table and the response tables, and
the last targeted re-check reported every item resolved.

It does not establish that the citing proofs are correct, that the cited statements are true, or that either agrees
with the Lean: a MATCH is a checker's comparison of a statement with one use of it. A citation without `\ref` escapes
the inventory. A targeted re-check covers the listed items and the repair sites, not every citation. Checkers that
could not query the dependency database judged from the text alone, and say so. Agreement among checkers is not
correctness.

## Related skills

[`writing-workflow`](../writing-workflow/SKILL.md) (the driver, the section cycle, requests in writers' notes),
[`lean-to-manuscript`](../lean-to-manuscript/SKILL.md) (when this phase runs, overnight mode),
[`statement-spine`](../statement-spine/SKILL.md) (the drift protocol for frozen statements),
[`referee-adjudication`](../referee-adjudication/SKILL.md) (rounds after which a full check is due);
elsewhere `math-paper-campaign` (shared controls).
