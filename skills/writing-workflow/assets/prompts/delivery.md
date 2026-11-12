## Your review: DELIVERY, before the section is marked delivered

The packet also holds every earlier review report ({{packet}}/reviews-1/ and {{packet}}/reviews-2/), the statement
register ({{packet}}/REGISTER.md) and {{packet}}/build.txt: the commands the driver ran just before freezing the
packet, with their output (it checked that the clause map has rows, recompiled standalone.pdf from the section file
with the manuscript's preamble, measured its pages against the allowance, and listed the statement labels that no
earlier report names). Verify:

1. **The PDF is the rendering of the reviewed sources.** build.txt shows the compilation and its result; the
   manifest lists both the section file and standalone.pdf. Hashes show only that nothing changed after freezing,
   not that one file was built from the other. Check that the page count and the statements you see in the PDF
   match the section file you read. If build.txt is missing or shows no compilation, say that the PDF's provenance
   was not checked.
2. **Every finding is closed.** Every finding of every report is closed in a response table (response-*.tsv in the
   proposal) or explicitly deferred with a named owner; every declined finding has a sound reason.
3. **Every statement was reviewed by name.** Each label that build.txt lists as named in no report is a coverage gap:
   review that statement here (against the spine and the Lean, and as a reader) and report it by its label. A label
   that is named is not thereby reviewed.
4. **Every principal statement passes.** Each principal statement of this section ({{principal}}) has an owner card
   with PASS on all three criteria (correct; understandable from the preceding text; serves its consumers).
5. **Every proof address exists.** Every register row that points to this section names a statement that exists and
   proves what the row says.
6. **References inside the section resolve.** Every `\ref` to a label defined in this section prints a number, not
   "??", and every citation key is in the manuscript's bibliography. References to other sections are undefined in
   this standalone build by design (build.txt counts them): do not report them; the cross-section-consistency round
   checks them on the integrated manuscript.
7. **Every page rendered.** Render every page of standalone.pdf and read it: broken displays, overfull lines, bad
   breaks, missing end-of-proof marks.
8. **Strength and inputs.** No statement is stronger than the Lean; every input is a labelled statement that exists
   or a request in REQUESTS.md.

Report after "Sources consulted:". State precisely what this review does not establish. End with exactly one of
these lines: "Verdict: DELIVER" or "Verdict: NOT YET", and after NOT YET a list headed "Required before DELIVER".
