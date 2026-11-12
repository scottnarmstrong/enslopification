{{common}}

# Task: revise Section {{number}}, "{{title}}", after its reviews (a proposal; the editor integrates it)

Your proposal directory {{stage_dir}} contains your previous version and its notes. The reviews read the frozen
snapshot {{packet}}; their reports are the files `*.md` in {{reports_dir}} (mathematical review, fresh reader, prose
truth, and one owner card per principal statement).

Answer every finding, BLOCKER and MAJOR first: apply it, or decline it with a mathematical reason. A finding that
needs a change to a frozen statement is not yours to apply: quote it in NOTES.md for the editor (drift protocol).

Write `response-{{stage}}.tsv` with the header `finding	decision	edit	check` and one row per finding: the finding
(report name and finding id), the decision (applied, or declined: the reason), the exact edit (old text, new text,
located by quoted text, never by line number), and how you checked it. Never delete or rewrite a finding.

Keep every label, the shape limits and the allowance of {{pages}} pages. Update standalone.pdf, correspondence.tsv,
NOTES.md (including the least certain sentence of the new version), REQUESTS.md and partI-edits.md.
