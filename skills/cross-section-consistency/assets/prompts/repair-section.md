{{common}}

# Task: cross-section repairs in Section {{number}}, "{{title}}" (a proposal; the editor integrates it)

Your proposal directory {{stage_dir}} contains the CURRENT integrated files of this section ({{files}}). Edit only
these copies. The sections were written in parallel; a check compared every place where one section cites a statement
of another section with what that statement says. Its table of mismatches and exact repairs is {{report}}. Site
addresses there are file:line in the integrated manuscript; find each place by its quoted text, not by its line
number.

Apply EVERY repair whose site or whose cited statement lies in this section's files, on BOTH sides:
- Where this section is CITED: when the cited statement's own proof already gives what the citing sections use,
  restate the statement so that it says it, and record in NOTES.md the line of the proof that gives it ("say so").
  When the proof does not give it, prove it from the Lean (name the declaration) or write a request in REQUESTS.md.
- Where this section CITES: change the citation or the sentence so that it uses exactly what the cited statement
  says. Other sections are applying their own repairs from the same table at the same time: rely on the restated
  statements the table specifies, under their existing labels.
- Apply the pointer, range and notation items that concern this section. A range citation ("Lemmas X--Y") becomes the
  list of the statements actually used.

Never change a frozen principal statement or a main theorem: report a repair that needs one in NOTES.md as DRIFT,
for the editor. Keep every label; refer to numbered items only by \ref.

Write `response-{{stage}}.tsv`, header `item	decision	edit	check`, one row per item of the table that concerns this
section: the item id; applied, not applicable here (why), or declined (the mathematical reason); the exact edit (old
text, new text); how you checked it. For this task the deliverables are the edited files, `response-{{stage}}.tsv`,
`NOTES.md` (every "say so" with its proof line, every DRIFT item, the least certain edit), and `REQUESTS.md` (or
"None.").
