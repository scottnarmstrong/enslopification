# Requests, repair rounds and convergence

How inputs are routed while sections are written, how a repair round runs on both sides, how the targeted re-check
works, and when the rounds stop. The check itself is in [the routed-inputs check](routed-inputs-check.md).

## While writing: requests and inboxes

Every writer cites inputs from other sections by label. A writer who needs a result that no section states proves
it in its own section as a short lemma when the proof takes under a page; otherwise it writes a **request** in
`REQUESTS.md` ([template](../assets/REQUESTS.template.md): the exact statement with every hypothesis, the Lean
source, the owning section, the statement whose proof needs it, the closest existing statement and what it lacks)
and lists it in `NOTES.md` as an open dependency. It never assumes an input silently and never presents it as proved
([L19](../../lean-to-manuscript/references/lessons-learned.md#l19)).

After each writer stage the editor lists the requests (`route_requests.py WORKDIR --config CONFIG.json --stage w1`:
the units of the rollout config are the valid addresses; without `--config`, only units that already have a
directory are), decides on each (the owner proves it; an existing statement already says it; the requesting section
proves it after all; the author decides), and delivers the accepted ones (`--deliver`, or `--select ID`) to the
owner's `INBOX.md`, creating the unit's directory if needed. The driver appends a unit's inbox to its next writer
prompt, the writer answers each request in its response table, and the driver archives what it delivered. A request
to a section not yet written waits in its inbox for the first draft.

A request answered on one side only is the failure to watch for: the cited section's notes can record that it does
not supply an estimate while the citing section's notes record that it cites the estimate from that section
([L21](../../lean-to-manuscript/references/lessons-learned.md#l21)). The routed-inputs check reads both sides'
notes.

## A repair round

Input: the merged mismatch table, each item with an id, the sites on both sides, the kind, and the exact repair.
Run one writer per affected section, all in parallel
([`rollout.repair.example.json`](../assets/rollout.repair.example.json), prompt
[`repair-section.md`](../assets/prompts/repair-section.md)). Each writer starts from the current integrated files of
its section and applies every item that touches them, **on both sides at once**:

- where its section is cited, it restates the cited statement to what its proof already gives and records the proof
  line in its notes ("say so"), or proves the missing part from the Lean, or writes a request;
- where its section cites, it changes the citation or the sentence to use exactly what the cited statement says,
  relying on the restated statements the table specifies, under their existing labels.

Each writer returns a response table: item, decision (applied, not applicable here, declined with a reason), exact
edit, check. A section with no response table has done nothing: count all its items as open until it delivers one.
A restatement keeps every hypothesis its users rely on; a hypothesis is never moved into the prose to meet a length
cap ([L13](../../lean-to-manuscript/references/lessons-learned.md#l13)). A repair that would change a frozen
statement is reported as drift and goes to the author.

The editor integrates all the proposals of the round together, compiles, runs the automatic checks, and runs
`cross_refs.py` again: a restated statement can change what its other users receive.

## The targeted re-check

The same groups, new contexts ([`rollout.routed-recheck.example.json`](../assets/rollout.routed-recheck.example.json),
prompt [`routed-recheck.md`](../assets/prompts/routed-recheck.md)). For every item of the table: RESOLVED or NOT
RESOLVED, quoting the current text on both sides. Then the repair sites, and only those, for new mismatches the
repairs created, each classified substantive or local. A verdict stage turns each group's verdict line into a STATUS
(RESOLVED or OPEN).

Repairs create mismatches. Expect the re-check after a first repair round to find items still open and new
mismatches at the repair sites, most of them created by the repairs themselves: a restatement reaches every other
user of the statement, and a rewritten citing sentence can ask more of another statement than before.

## Convergence

**The rounds stop when a targeted re-check confirms every item resolved and finds no new substantive mismatch.**
Remaining local items found at the repair sites (a constant fixed twice, a letter with two meanings, a threshold
named in one place and not another) are applied by the editor and listed. Run a full survey with fresh groups,
instead of a targeted re-check, after any round that changed many statements, such as a referee round.

What successive rounds find ([L21](../../lean-to-manuscript/references/lessons-learned.md#l21)):

| round | what the check finds |
|---|---|
| first check | mismatches clustered in a few citing sections, the missing content mostly already in the cited proof or in the Lean; candidate cycles, rarely genuine |
| re-check after the first repairs | items still open, and new mismatches created by the repairs |
| full check after a round that changed many statements | further mismatches, mostly local, a few substantive (a lemma stated too narrowly for its uses) |
| last targeted re-check | every item resolved; small local items at repair sites, applied by the editor |

The Yang–Mills campaign (2026) needed three rounds of repairs and checks, the last confirming every item resolved;
its third round of repairs included "Lemma 11.3 stated for its uses". Rounds may run overnight under the rules of overnight mode: only reversible
decisions, no frozen statement changed, and every decision left to the author queued with its provisional choice and
how to revert it ([`lean-to-manuscript`](../../lean-to-manuscript/SKILL.md)).

## Numbering only by cross-reference

Typed numbers go stale and collide; the Yang–Mills proof sections first used numbers that collided with addresses in
the opening part ([L17](../../lean-to-manuscript/references/lessons-learned.md#l17)). Every numbered item is referred
to by `\ref`, no writer redefines counters, and range citations are replaced by lists. `cross_refs.py` then sees
every routed citation, and its exit status reports undefined and duplicate labels after each integration.
