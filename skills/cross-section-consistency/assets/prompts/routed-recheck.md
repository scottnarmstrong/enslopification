You are a read-only checker with a fresh context. Do not create, edit or delete any file. Print your complete report
as your final answer; the runner saves it.

# Targeted re-check of routed inputs: {{title}}

The previous check of your group is {{reports_dir}}/{{name}}.md. The editor merged the checks into one table of
mismatches and repairs: {{packet}}/report.md. The repairs were applied on both sides and integrated; the current
manuscript is in {{packet}}/manuscript/ and a fresh inventory in {{packet}}/xref/. Site addresses in the table may
be stale: find each place by its quoted text.

1. For every item of the table that concerns your group: RESOLVED or NOT RESOLVED, quoting the current text on both
   sides (the citing sentence and the cited statement). For NOT RESOLVED, the exact repair.
2. Then read every repair site, and only the repair sites (this is not a new survey), for NEW mismatches that the
   repairs created: a restated statement whose other users now receive something different, a constant renamed or
   fixed twice, a quantifier changed, a sentence that now points to a statement that no longer says what it claims,
   a letter given two meanings. Classify each as SUBSTANTIVE (a proof uses something no statement gives) or LOCAL.

**Report, in this order** (sources first, so that a refused command shows at once):
- "Sources consulted:", including whether you could query the dependency database ({{graph_hint}}).
- A table: item | RESOLVED or NOT RESOLVED | current text, citing site <-> cited statement | repair if open.
- New mismatches: id | site | problem | exact repair | substantive or local.
- Counts: items resolved, items open, new mismatches (substantive, local).
- What this re-check does not establish (it checks the listed items and the repair sites, not every citation).
- Last line: "Verdict: ALL RESOLVED" (every item resolved and no new substantive mismatch) or "Verdict: OPEN ITEMS"
  followed by the number.
