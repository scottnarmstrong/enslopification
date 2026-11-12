## Your review: OWNER of one principal statement, {{item}}

You own this one statement. Judge it on three criteria.

**(i) Correct.** Compare it with its approved text in {{packet}}/SPINE-NATURAL.md: a main theorem must be byte for
byte identical; any other change of wording must leave the mathematics unchanged. Then take every clause of
{{packet}}/SPINE.md that the clause map assigns to {{item}} (the rows of {{packet}}/CLAUSE-MAP.tsv, or the table of
section 6 of {{packet}}/SPINE-NATURAL.md when the map is kept there) and check that the statement carries it, with
its scope (quantifier order, existence against "for every", uniformities, the order in which constants are chosen,
every hypothesis). Then check it against the Lean. Strength in both directions: weaker than the Lean or than its
contract is a finding, stronger is a blocker.

**(ii) Understandable from the preceding text.** READ THE MANUSCRIPT IN ORDER, FROM THE BEGINNING UP TO THE
STATEMENT, BEFORE YOU OPEN ANY SOURCE. Then inventory every symbol, object and quantifier the statement uses and where
it was defined; list everything used before its definition or defined in a way you could not follow.

**(iii) Serves its consumers.** Map every place that uses the statement (the deduction of the main theorems, later
statements, proofs in other sections) and try to break each implication it is used for: does the statement give
exactly what each use needs, no less? Then look for worthwhile improvements: a shorter form, a better split, a missing
sentence of interpretation, a clause that belongs elsewhere.

If the section under review only describes {{item}} in words (an introduction or an overview), judge that
description by the same criteria: it says what the statement says, no more and no less, and points to it.

Card format, after "Sources consulted:": the findings (id, severity, location, problem, minimal repair, alternatives
rejected and why); then PASS or FAIL for each of (i), (ii), (iii), each with one line of reason.

Verdict line: "Verdict: PASS" (all three criteria pass) or "Verdict: FAIL" followed by the failing criteria.
