Condense the detailed notes of one unit of a natural-language outline of a Lean proof ({{project}}) into its
outline.

UNIT: {{key}}. {{title}}. About {{lean_lines}} lines of Lean.
Input, read it completely: {{stage_dir}}/notes.md (the detailed notes, compared with the Lean and edited; they
stay published unchanged). Output: {{stage_dir}}/outline.md. Write only that file.

LENGTH IS BINDING: at most {{words_max}} words, counting text and formulas but not link URLs. Over the allowance
the outline is not done. Measure it before you finish:
  python3 -I {{scripts}}/outline_budget.py {{stage_dir}}/outline.md --lines {{lean_lines}}

Keep the template's headings ({{template}}) at outline level:
- the title line exactly as in the notes, then the Part / Lean / Size line;
- section 1: every numbered output statement, stated completely (hypotheses and quantifiers), with its status
  and its main link. This section may stay close to the notes: other units use it;
- section 2: a short list of inputs (unit ids, standard results by name);
- section 3: one or two paragraphs; section 4: the main steps, one to three sentences each, with their links;
  drop routine steps and long sketches;
- sections 5 to 7: a few sentences each; notation only for symbols the outline uses;
- a last line linking the detailed notes.

RULES
- Say nothing that the notes do not say: no new claims, no strengthening. A shortened statement keeps every
  hypothesis; meet the allowance by cutting steps and sketches, never by moving hypotheses out of statements.
- Keep the notes' links exactly (pinned URLs with line ranges).
- Math that renders on GitHub; plain mathematical English; no remarks about the process.
