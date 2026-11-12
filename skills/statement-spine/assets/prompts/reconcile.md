Reconcile two independent drafts of the statement spine of {{project}} and check both against the
dependency database. You are read-only: edit no file. Print the reconciliation as your final
answer; the driver saves it. Do not run git, lake or builds; you may query {{db}} with sqlite3
and read the Lean at {{lean_repo}} (commit {{commit}}), which is the authority.

Inputs: draft A {{draft_a}}; draft B {{draft_b}}; the drafting task {{drafter_task}}; the
detail standard {{detail_standard}}; the exact theorem {{statement_file}}.

Begin with "Sources consulted:": every file you actually read, every database query you ran, and
every source you tried and could not use (a refused command, a file you could not read). Then
produce, in this order:

1. **Used-check.** Look up every Lean name cited in A and in B (exactly, then by suffix). List
   each name that is not used = 1, the claim resting on it, and the used declaration that
   establishes the same content (or "no used producer": then the claim goes). A structure field
   can have used = 0 because the main route never reads it although the structure is built;
   name the producer that the main route consumes. Give the counts of names checked.
2. **Map A to B.** One row per principal statement: A's item, B's item, relation (same, split in
   one, merged in one, missing in one, different), note.
3. **Statement by statement.** Where the drafts differ, which form is right against the Lean
   (with file:line) and which is more natural for the reader {{reader}}.
4. **The merged spine.** The principal statements, each with its envelope (role, statement,
   correspondence with used = 1 names only, dependencies, home, least certain point); the
   deduction of the main theorems with the order of choices; the recommended content of the main
   theorems.
5. **Decisions for the author.** Numbered; each with its options, the evidence and your
   recommendation. Include the granularity of the principal statements where the drafts differ,
   and every place where "for every admissible choice" against "for one choice made by the
   construction" is not settled; settle it from the Lean.
