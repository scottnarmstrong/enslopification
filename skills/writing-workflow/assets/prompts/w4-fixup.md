{{common}}

# Task: apply the delivery review's required fixes to Section {{number}}, "{{title}}" (a proposal)

Your proposal directory {{stage_dir}} contains the current version of the section and its notes and response tables.
The delivery review {{reports_dir}}/delivery.md says NOT YET.

1. Apply every item it lists as required before delivery, exactly.
2. Then apply every deferred minor item you can apply without changing what any statement asserts (notation
   clashes, process phrases, orphaned end-of-proof marks, results cited from inside proofs, stale quotations).
3. Anything you decline needs a mathematical reason.

Write `response-{{stage}}.tsv` (header `finding	decision	edit	check`, one row per item). Keep every label, the shape
limits and the allowance of {{pages}} pages. Run the shape and vocabulary checks on every .tex file; update
standalone.pdf, correspondence.tsv and NOTES.md.
