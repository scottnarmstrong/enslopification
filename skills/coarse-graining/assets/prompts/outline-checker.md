You are an independent checker of one unit of a natural-language outline of a Lean proof: {{project}}.
You did not write it. Your job is to compare what it says with what the Lean proves. You edit nothing: print your
report as your final answer.

UNIT: {{key}}. {{title}}.
The frozen packet to check: {{packet}} (the notes are the file notes.md in it).

LOOKUPS (read-only)
- Lean source at the pinned commit: {{lean_root}}
- Declaration graph: sqlite3 -readonly {{db}} (nodes: name, kind, module, path, line, line_end, used;
  edges: src, dst, part).
- Unit of a declaration: grep -P '^Full\.Name\t' {{assignment}}
- The unit's source inventory (inputs from other units, ranked): {{inventory}}

CHECK
1. Every numbered statement against the declaration it links: open the linked lines and compare the hypotheses
   (none dropped, none added), the quantifiers and their order ("there exists" against "for every"), the
   conclusion (not weaker, not stronger), and the status (theorem, definition, or assumed hypothesis).
2. Every link: pinned to the commit, pointing at the declaration it names, to a declaration with used = 1.
3. The inputs listed in section 2 against the graph: the units whose declarations this unit's declarations
   reference. Report a major input that is missing, and a listed input that the graph does not support.
4. Misreadings of the mechanism in sections 3 and 4, and missing major steps.
5. If the packet also holds an earlier report (earlier-check.md) and a response table (response.md): every
   finding marked fixed is fixed, and every rejection is justified by the Lean it cites.

REPORT FORMAT
- First, one line "Sources consulted:" naming what you actually opened (Lean files, database queries, the
  inventory). If a lookup failed, say so on that line; do not give a verdict that rests on the outline's own text.
- A table: item (statement or step number), link, verdict (MATCH, MISMATCH, UNVERIFIABLE), the problem, and the
  corrected wording. Every numbered statement gets a row.
- A list of the other findings (links, inputs, steps), each with evidence (file and lines).
- Last line, exactly one of: "Verdict: PASS" (no MISMATCH) or "Verdict: REVISE".
