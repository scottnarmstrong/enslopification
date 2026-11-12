# Confirmation review before integration: {{title}}

Read-only, fresh context. A writer has applied an adjudicated referee report to this section. Decide whether the
result can be integrated. Read only the frozen packet {{packet}}: the proposal in `proposal/` (with its response
table, `NOTES.md` and `CROSS-EDITS.md`), the live files it replaces at the top of the packet, the adjudication
`adjudication.md` and the referee report `referee-report.md`. Authority: the Lean in {{lean}} at commit
{{lean_commit}}; {{graph_hint}}.

Compare each proposal file with the live file it replaces (`diff`, or Python `difflib` if the shell is restricted),
then run five checks.

1. **Edits against the adjudication.** Every `ACCEPT` and `ACCEPT MODIFIED` item located in this section is applied
   as given, or the departure is small and justified (say why). No `REJECT` item is applied. No `AUTHOR` item is
   applied, and no new sentence settles one in effect (for example by asserting a bound the author has not
   approved).
2. **Statements against the Lean.** Every changed or new statement is implied by used declarations: name them.
   None is stronger than the Lean. Compare each statement environment before and after: **no hypothesis,
   quantifier or clause may have moved out of a statement into the prose around it**, even to meet a word cap.
   A new definition is neither narrower nor wider than the Lean's.
3. **Explanatory sentences.** Mark every new or changed sentence outside the statements true, false or
   unsupported, with evidence. Check every claim about a table, a row or another section against what it says.
4. **References and mechanics.** Every new `\ref` resolves; no label is lost or duplicated; `\input` paths are as in
   the manuscript; the main theorems ({{main_theorems}}) are byte for byte unchanged.
5. **Cross-section edits.** Each entry of `CROSS-EDITS.md` transcribes an accepted item faithfully; none
   transcribes a rejected one. Name edits that must land in the same commit as this section.

## Output

- First, `Sources consulted:` the files and declarations you read; which Lean names you confirmed as `used = 1` by
  a database query, and which only by other means; every source you tried and could not use (state it if a query
  was blocked).
- A bottom line in two or three sentences.
- The five checks, each with its findings and the exact fix (file:line, old -> new).
- The last line exactly `Verdict: INTEGRATE` or `Verdict: NOT YET`.

Print the review as your final answer (do not write files).
