## Common rules for every section writer (binding)

You write a PROPOSAL for one section of a mathematical manuscript that gives a complete natural-language proof of the
result formalized in the Lean development at {{lean}} (commit {{lean_commit}}). The editor integrates proposals into
the manuscript; you never edit the manuscript. Write only inside your proposal directory, {{stage_dir}}. No version
control commands, no Lean builds.

**Read first:** the style rules {{style}} (binding), the detail standard {{detail}}, the notation and terminology
table {{notation}}.

**Authorities.** Statements: the approved natural spine {{spine}}, the frozen text of every definition, main
theorem and principal statement (and the later lemmas, as targets). Typeset its statements faithfully; improve the
wording only where the mathematics is unchanged; report a problem with a statement in NOTES.md instead of changing
the mathematics. The frozen contracts (`SPINE.md`, kept with the natural spine: Lean-shaped, every clause tagged
`[clause:ID]`) and the clause map are the record that the natural spine must cover, not text to typeset: a lemma you
restate keeps every clause the clause map assigns to it. Mathematics: the Lean. Only declarations that the main
theorem uses count as evidence ({{graph_hint}}). Outlines, summaries and earlier drafts are maps for finding things,
never evidence.

**Writing.** Introduce each object before its first use, by formula, with one sentence saying what it is for.
Introduce each principal statement with one or two sentences on its role, and follow it with an exact pointer to its
proof. Write out every
estimate specific to this construction with the mechanism that makes it true; cite standard results exactly (name,
hypotheses, numbering, checked against the source). Every explanatory sentence must be literally true: each one will
be checked against the proofs and the Lean.

**Never in the TeX:** Lean names or syntax, file paths, process words (proposal, packet, reviewer, spine, owner review), TeX
comments with process content.

**Numbering.** Never redefine counters or `\the...` macros. Refer to every numbered item by `\ref` to its label,
never by a typed number. Keep every label you were given.

**Inputs from other sections.** Cite them by label. If you need a result that no section states, prove it here as a
short lemma when its proof takes under a page; otherwise write a request in REQUESTS.md and list it in NOTES.md as an
open dependency. Never assume an input silently and never present an unproved input as a fact. One block per
request, addressed to the unit key of the section that should prove it:

```
## R1
- To: <unit key, from the list below>
- Needed by: <label of the statement whose proof uses it>, at <file:line of the use>
- Statement: <the exact statement, with every hypothesis and quantifier; it may continue on the next lines>
- Lean: <declarations (used = 1) with module:line, or "none found">
- Why no existing statement serves: <the closest existing statement, by label, and what it lacks>
```

The unit keys of this manuscript (key, then the section's title):
{{unit_keys}}

**Self-checks before you finish.** Compile your section standalone, with the manuscript's preamble, to
`standalone.pdf` in your directory and read its page count; `{{standards}}/check_section.sh -m {{manuscript}}/main.tex
-k {{stage_dir}} <your section file>` does this and also runs the shape and vocabulary checks. A check you could not
run is reported in NOTES.md.

**Deliverables in {{stage_dir}}**, besides the section file:
- `correspondence.tsv`: one row per numbered statement and definition, with a first line `# commit: {{lean_commit}}`
  and the header `label	kind	Lean declarations used=1	relation	file:line	notes` (declarations separated by `;`,
  only names in the closure of the main theorem; relation DIRECT, WEAKENING, COMPOSITION, CITED or NONE in exactly the
  sense of the relations table of honest-publication, `references/correspondence-and-statement.md#relations`;
  file:line at the pinned commit; notes: a bibliography key for a standard result, or empty);
- `NOTES.md`: (1) every change relative to the spine, with the reason; (2) any statement you could not typeset as
  given, and why; (3) what you could not do; (4) your least certain sentence, quoted, and why it is the least
  certain; (5) the measured page count and the shape-check result;
- `REQUESTS.md`: your requests to other sections, or the single line "None.";
- `partI-edits.md`: exact old and new text for any sentence of the opening part that is inaccurate about this
  section, or the single line "None." (you never edit the opening part yourself).
