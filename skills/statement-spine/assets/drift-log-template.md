# Drift log

Every change to a frozen statement (main theorems, principal statements, the Part I definitions
they use) and every change to a Part II target (a lemma split, added, removed or reworded).
Newest last. Never delete or rewrite an entry: correct it with a later entry.
A frozen statement changes only after the author approves the entry; a Part II target changes
with a log entry and an updated clause map.

## D-<n>. <item label> — <date>

- **Kind:** frozen statement (needs the author's approval) | Part II target (log entry only)
- **Old text:** <quote, or file#anchor with the SHA-256 of the approved version>
- **New text:** <quote>
- **Change of content:** <weaker | stronger | same content reworded | split | added | removed>,
  in clause(s) <ids>: <one sentence saying exactly what changes>
- **Reason:** <the finding that requires it>
- **Lean evidence:** `<declaration>` (<file>:<line> at <commit>, `used = 1`): <what it fixes>
- **Found by:** <review and round>
- **Dependents:** <statements, deduction steps, introduction claims, other sections' citations>;
  each re-checked by <reviewer>, result <...>
- **Every occurrence updated:** <places that repeat the old wording, searched for and changed>
- **Clause map:** rows <ids> changed; `clause_map_check.py` result: <summary line>
- **Status:** proposed | approved by the author on <date> | rejected (<reason>) | applied in <file> at <revision>
