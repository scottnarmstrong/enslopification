{{common}}

# Task: fix-up of {{title}} after the confirmation review (a proposal; the editor integrates)

Your proposal directory {{stage_dir}} holds your previous proposal for this section, copied from {{prev_dir}}: the
edited files, `response-{{prev_stage}}.tsv`, `NOTES.md` and `CROSS-EDITS.md`. Edit only these copies; never edit the
manuscript itself or another section. The confirmation review {{reports_dir}}/confirm.md says NOT YET.

## What to do

1. Read {{reports_dir}}/confirm.md completely. Apply every fix it requires for this section exactly as it gives it
   (file:line, old -> new); find each place by its quoted text, not only by its line number.
2. Put back inside its statement every hypothesis, quantifier or clause that the review found moved into the prose.
   To meet a word cap, split the statement or define objects earlier; never move a hypothesis out.
3. Rewrite or delete every sentence the review marks false or unsupported. A repair that needs an argument is
   written from the Lean's own argument ({{lean}} at commit {{lean_commit}}; {{graph_hint}}); never state more than
   the Lean proves.
4. Correct every entry of `CROSS-EDITS.md` that the review flags.
5. A required fix you decline needs a mathematical reason with its Lean evidence (declaration, file:line).

The adjudication {{adjudication}} still binds: never apply a `REJECT` or `AUTHOR` item, and never write text that
decides an `AUTHOR` item in passing. Never change the main theorems ({{main_theorems}}). Keep every `\label` and the
`\input` paths exactly as they are in the manuscript. Run the shape and vocabulary checks on your `.tex` files
(`python3 -I {{standards}}/check_shape.py` and `check_vocabulary.py` in the same directory; the driver runs them
too) and compile; report the measured pages.

## Deliverables

For this task the deliverables in {{stage_dir}} are exactly:

- the edited files;
- `response-{{stage}}.tsv` with the columns `fix`, `decision` (applied / not in this section / declined), `edit or
  reason`: one row for every fix the confirmation review requires;
- `NOTES.md` and `CROSS-EDITS.md`, updated (in `NOTES.md`: the declarations and relation of every new or changed
  numbered statement, the measured pages, your least certain sentence).

The other deliverables of the common rules (`correspondence.tsv`, `REQUESTS.md`, `partI-edits.md`) are not part of
this task.
