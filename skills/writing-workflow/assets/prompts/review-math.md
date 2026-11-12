## Your review: MATHEMATICAL REVIEW against the Lean

For every lemma and every proof step, decide: is it correct; is it complete at the stated level of detail; and is it
no stronger than what the Lean proves?

- Check each row of correspondence.tsv: the declaration exists, the main theorem uses it, and it says what the row
  claims, with the stated relation (DIRECT, WEAKENING, COMPOSITION, CITED, NONE).
- Check each cited literature result: statement, hypotheses, numbering.
- Check every statement against the natural spine, and every clause the clause map assigns to it against the frozen
  contracts: quantifier order, existence against "for every", uniformity of constants, every hypothesis the Lean
  carries.
- Hunt for gaps written around in assertive prose: this is the main target. Also hand-waving ("one checks",
  "standard"), mechanisms described rather than shown, inputs assumed without a label or a request, and dependencies
  that run forward.
- Read NOTES.md: is the least certain sentence the writer named actually correct?

Name every statement you checked by its label. Report in the order of the preamble: sources consulted first.

Verdict line: "Verdict: CORRECT", "Verdict: CORRECT AFTER FIXES" or "Verdict: NOT CORRECT".
