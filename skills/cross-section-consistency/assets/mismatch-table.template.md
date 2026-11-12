# Routed inputs: mismatches and repairs (round <n>, snapshot <packet path and hash of manifest.json>)

Merged by the editor from the group checks. One row per mismatch; rows are never deleted: a later round adds a
status. Ids are stable across rounds (M-<cited section>-<n>; N<n> for mismatches found at repair sites).
Kind: S = substantive (a proof uses something no statement gives), L = local (pointer, name, stale text, range).
Repair: SAY-SO (restate the cited statement to what its proof gives), CITING (change the citing sentence), PROOF (new
proof from the Lean), REQUEST (to the owning section), DRIFT (a frozen statement would change: to the author).

| id | citing site (file:line, quoted) | cited label | used by the citing proof | said by the cited statement | kind | repair | exact text | sides | status (round 2, round 3, ...) |
|---|---|---|---|---|---|---|---|---|---|

## Candidate cycles

| id | cycle | CLEARED / CONFIRMED | reason (the edge that is a pointer, a remark, or an independent part) |
|---|---|---|---|

## Crosswalk: opening-part inputs and proof-part exports

| opening-part statement | what its proof or the deduction uses from the proof part | proof-part label | what that statement says | verdict | repair |
|---|---|---|---|---|---|
