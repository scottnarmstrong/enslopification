# Exposition review (not correctness): {{scope}}

Read-only, fresh context. Read {{scope}} of the frozen snapshot {{packet}} completely, as {{reader}} would, comparing
each passage with the best-written parts of the manuscript and with the standard texts of the field
({{exemplars}}). Report every place where the exposition fails a reader, under these headings.

- **A. Density.** Paragraphs overloaded with inline formulas that should be displayed; chains of inline estimates;
  sentences carrying many symbols, quantifiers or cases at once; displays that cram several definitions or
  inequalities into one line; proofs written as one long paragraph with no visible structure.
- **B. Misallocated detail.** Effort spent on routine points (trivial measurability, index bookkeeping, restated
  hypotheses, obvious inequalities at length) while the key step is terse; detail out of line with the rest of the
  text, in either direction; long verifications that could be one sentence; no statement of the idea before a long
  proof.
- **C. Notation.** One symbol with two meanings; notation that changes silently; overdecorated symbols; departures
  from the literature's names for standard objects without reason; symbols used once; inconsistent fonts for one
  kind of object.
- **D. Terminology.** Words inherited from the formal development rather than the literature (test these:
  {{terms}}); for each, say whether a standard term exists or whether the word is fine if defined once and used
  consistently. Undefined jargon; terms used before they are defined.
- **E. Structure and signposting.** Statements that bundle several results; hypotheses buried in prose far from the
  statement; forward references; repeated definitions; constants whose dependence is unclear; subsections without
  a sentence saying what they achieve and where it is used; sentences that are lists of cross-references.
- **F. Readability.** Sentences that are hard to parse; passive chains; leftovers of the writing process; anything
  a referee would mark "unclear".

Begin with "Sources consulted:": what you read in full, what you only sampled, and anything you could not open.
Then, for each finding, give: the location (section, statement number, page), the heading letter, the problem in one
or two sentences, and an **exact** proposed rewrite (the replacement text, with any display or new notation spelled
out). Rank the findings by how much they would improve the reader's experience. Report a mathematical error only if
it blocks understanding, in a separate list. Do not praise; do not summarize the paper. End with a line "Renamings:"
followed by every manuscript-wide renaming you propose (current term -> proposed term), or "Renamings: none".

Print the review as your final answer (do not write files).
