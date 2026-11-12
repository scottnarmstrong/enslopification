# Adjudication of a referee report: {{title}}

Read-only, fresh context. You adjudicate the referee report `{{packet}}/referee-report.md` on {{scope}} of
{{paper}}. The text is the frozen snapshot in `{{packet}}/manuscript/`; quote it from there, by file and line.

**Authority.** The Lean source in {{lean}} at commit {{lean_commit}}. Only declarations in the closure of the main
theorem count as evidence: {{graph_hint}}. A declaration with `used = 0` belongs to a route the main theorem does
not take; it proves nothing about this text.

## For each numbered suggestion, and each sub-item

1. **Is the diagnosis true of the text?** Quote the passage (file:line). For a mathematical claim, check the
   mathematics and what the Lean proves.
2. **Does the proposed change say exactly what the Lean proves, never more?** A stronger statement is acceptable
   only if a used declaration proves it: name it. Check the referee's own text in detail; it is often right in
   diagnosis and wrong in detail (a wrong formula, an unsupported constant, a quantifier in the wrong place).
3. **Does it break anything?** Cross-references, the main theorems, statements of other sections that rely on
   the old wording, and these binding constraints: {{constraints}}.
4. **Verdict:**
   - `ACCEPT`: correct and safe as proposed.
   - `ACCEPT MODIFIED`: the diagnosis is right; give the exact corrected change.
   - `REJECT`: give the reason (the diagnosis is false, the change claims more than the Lean, or it breaks
     something you name).
   - `AUTHOR`: the change would alter a main theorem or another approved statement, the scope of the result,
     remove a proved result, or touch authorship or disclosure. Say what you recommend and, if one exists, offer a
     true sentence the author may choose. Never decide such an item through the wording of another item.
   A split verdict is written in one cell, e.g. `ACCEPT MODIFIED (a-c); REJECT (d)`.

## Output, in this order

1. `## Sources consulted`: the files, declarations and database queries you actually used, and every source you
   tried and could not use (a refused command, a file you could not open).
2. `## Lean facts the verdicts rely on`: each fact with its declaration names and file:line. Say which names you
   confirmed as `used = 1` by a database query and which only by reading the source.
3. `## Verdicts`: one Markdown table with exactly these columns:
   `| # | Verdict | Reason | Where to edit |`. One row per suggestion or sub-item (`13a`), the reason in one or two
   sentences, the locations as file:line. Every suggestion number of the report must have a row.
4. `## Exact edits`: for every ACCEPT and ACCEPT MODIFIED item, the exact text: insertions with their anchor,
   replacements as old -> new, each located by file:line and a quoted phrase.
5. `## Interactions`: items that must land together, and items that edit another section (name the owner).

Stay under {{max_lines}} lines. Print the adjudication as your final answer (do not write files).
