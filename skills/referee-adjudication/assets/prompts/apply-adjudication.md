{{common}}

# Task: apply the adjudicated referee suggestions to {{title}} (a proposal; the editor integrates)

Your proposal directory is {{stage_dir}}. It holds copies of the current files of this section: {{files}}. Edit only
these copies; never edit the manuscript itself or another section.

- Referee report: {{report}}.
- Adjudication (binding): {{adjudication}}. It gives one verdict per suggestion and the exact edit text.
- Main theorems, never to be changed: {{main_theorems}}.

## What to apply

1. Every `ACCEPT` item exactly as the referee proposed it, and every `ACCEPT MODIFIED` item exactly as the
   adjudication modifies it (use its exact edit text), whose location is in your files.
2. Never apply a `REJECT` or `AUTHOR` item, and never write text that decides an `AUTHOR` item in passing.
3. An accepted item that edits another section, the opening part or a shared table: do not edit those files. Write
   the exact proposed change in `CROSS-EDITS.md`, with the item number and the owning section.
4. Where an accepted repair needs an argument, write it from the Lean's own argument ({{lean}} at commit
   {{lean_commit}}; {{graph_hint}}), at the level of detail of the rest of the section. Never state more than the
   Lean proves. Record the declarations in `NOTES.md`.

## Rules that the confirmation review checks first

- **A statement keeps every hypothesis, quantifier and clause its users rely on.** To meet a word cap, split the
  statement or define objects earlier; never move a hypothesis into the surrounding prose.
- Keep every `\label`; add new labels only for new items. Never change the main theorems.
- Keep `\input` paths exactly as they are in the manuscript.
- Run the shape and vocabulary checks on your `.tex` files (`python3 -I {{standards}}/check_shape.py` and
  `check_vocabulary.py` in the same directory; the driver runs them too) and compile; report the measured pages.

## Deliverables

For this task the deliverables in {{stage_dir}} are exactly:

- the edited files;
- `response-{{stage}}.tsv` with the columns `item`, `verdict`, `action` (applied / not in this section / could not
  apply), `edit or reason`: one row for every item of the adjudication;
- `CROSS-EDITS.md` (possibly empty) and `NOTES.md` (declarations used, with the relation of every new or changed
  numbered statement for the editor's correspondence table; measured pages; anything the editor must do outside
  your files; your least certain sentence).

The other deliverables of the common rules (`correspondence.tsv`, `REQUESTS.md`, `partI-edits.md`) are not part of
this task: an edit to the opening part or to another section goes to `CROSS-EDITS.md`.
