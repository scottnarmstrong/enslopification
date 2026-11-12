{{common}}

# Task: write the introduction (Section {{number}}) and the abstract (a proposal; the editor integrates it)

The introduction is written last, once the main theorems and the principal statements have stopped moving. Read the
integrated manuscript first ({{manuscript}}, compiled as {{main_pdf}}): the opening part for the statements, the
proof sections for the structure. Your proposal directory {{stage_dir}} contains the placeholder {{file}}; write the
introduction into it, in this order:

1. **The result in plain words**: the problem, and the main theorems ({{main_theorems}}) stated informally, each
   with a `\ref` to the formal statement. An informal statement says what the formal one says, no more: its owner
   checks it against the formal statement.
2. **What is not claimed**: the scope of the main theorems and what they leave open, as precisely as the remarks
   after them in the opening part.
3. **The source of the result and of this text**: the paragraph "Introduction: the paragraph on sources" of the
   approved disclosure wordings {{disclosure}}, copied exactly as filled in there, between a line
   `% BEGIN-DISCLOSURE` and a line `% END-DISCLOSURE`. These are the exception markers of the vocabulary check: the
   paragraph names agents and reviews, words allowed nowhere else. Change nothing in it; its wording and the author
   line are the author's decisions. If the file is missing or still has unfilled placeholders, put only the comment
   line `% disclosure paragraph: awaiting the author` between the markers and say so in NOTES.md.
4. **Earlier work**: the results and methods this proof builds on, each cited exactly (checked against the source);
   a claim of novelty only where a source supports it.
5. **An outline of the proof**, one to two pages, following the deduction in the opening part: the chain of
   principal statements and which section proves each.
6. **A reading guide and the conventions** (if the conventions move here from another section, give the exact
   deletion in partI-edits.md).

Also write `abstract.tex`: one paragraph of at most about 200 words, ending with the abstract sentences of the same
disclosure wordings ("Abstract, last sentences", in the version the author approved), copied exactly, between the
same two marker lines.

Never state a theorem more strongly, or more generally, than the opening part does; never call the prose proofs
checked, verified or refereed.

**Allowance: about {{pages}} pages**, measured on standalone.pdf. Over the allowance means not done.

Deliverables in {{stage_dir}}: {{file}}, abstract.tex, standalone.pdf, correspondence.tsv (its header line only if
the introduction has no numbered statement), NOTES.md, REQUESTS.md ("None." if none), partI-edits.md.
