Review the clause map of the natural spine {{natural_spine}} against the frozen spine
{{frozen_spine}}. You are read-only: edit no file. Print your report as your final answer; the
driver saves it. Do not run git, lake or builds; you may query {{db}} with sqlite3 and read the
Lean at {{lean_repo}} (commit {{commit}}).

The mechanical check has already run; do not repeat it (every clause has a row, every
destination exists): {{check_output}}

For every row, open the destination and check that it carries the clause with the same
hypotheses, quantifier order, existence or universality, uniformities and constant dependence.
Then look for:

- frozen clauses split across destinations that together say less than the clause;
- natural statements stronger than the clause, or weaker than the Lean without a note;
- hypotheses that moved into the surrounding prose;
- packaging statements, and definitions that translate a Lean structure;
- main theorems whose conclusions are lists of labels rather than statements with formulas;
- scope-sensitive clauses (order of choices, one run of the construction against every
  admissible choice, a full sequence against a subsequence, every case against a selected one)
  that do not cite a used = 1 declaration fixing them;
- statements that cannot be understood from the text before them.

Begin your report with "Sources consulted:": every file you actually opened, every database
query you ran, and every source you tried and could not use (a refused command, a file you could
not read). Then report findings with stable IDs (MAJOR-1, MINOR-1, ...), each with the row or
clause, the evidence (frozen text, natural text, Lean file:line) and the smallest repair. End
with one line "Verdict: APPROVE", "Verdict: APPROVE AFTER FIXES" or "Verdict: REJECT".
