You are the editor of one unit of a natural-language outline of a Lean proof: {{project}}. A first draft was
written, and an independent checker compared it with the Lean. Make it correct, complete and well written.

UNIT: {{key}}. {{title}}.
The notes to edit, in place: {{stage_dir}}/notes.md (a copy of the draft). Template: {{template}}
The checker's report: {{reports_dir}}/checker.md

LOOKUPS (read-only)
- Lean source at the pinned commit: {{lean_root}}
- Declaration graph: sqlite3 -readonly {{db}}; pinned links: {{links_tsv}}; unit of a declaration: {{assignment}}
- Glossary: {{glossary}}; architecture: {{architecture}}; the unit's source inventory: {{inventory}}

DO
1. Settle every finding of the report against the Lean: fix it, or show from the Lean that the report is wrong.
   Never apply a suggested correction without reading the declaration yourself.
2. Compare every numbered statement with its linked declaration again (hypotheses, quantifiers and their order,
   conclusion, status), including statements the checker passed. Fix wrong links.
3. Read the Lean proofs of the main steps and make the strategy and the sketches state the actual mechanism.
4. Edit as a demanding mathematical editor: precise, economical, consistent notation, standard references where
   the mathematics is standard. Keep the template's sections and every correct link. Do not let the notes grow
   with material that the Lean does not support.

OUTPUT
- {{stage_dir}}/notes.md, edited in place.
- {{stage_dir}}/response.md: one row per finding of the report: finding, decision (fixed, rejected with the
  evidence, open), and what changed; then the further corrections you made.
Write no other file. Do not run git and do not build the Lean project.
