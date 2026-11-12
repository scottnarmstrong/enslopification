{{common}}

# Task: write Section {{number}}, "{{title}}", of the opening part (a proposal; the editor integrates it)

The opening part states the result and the architecture of its proof: the definitions needed to state the main
theorems, the main theorems, the principal statements with the idea of each proof, the deduction of the main
theorems from the principal statements, and the constants with the order of their choice. The later sections prove;
this part states, and its statements are frozen in the natural spine {{spine}}.

Your proposal directory {{stage_dir}} contains the placeholder file {{file}}: the section's `\section` line and the
labels of its statements. Write the complete section into this file; keep the `\section` line and every label. This
section contains: {{contents}}. Put nothing here that the spine places in another section.

Rules for the opening part:
1. **The main theorems ({{main_theorems}}) are byte for byte the environments of the approved natural spine**: copy
   each one character for character, label included. Before each, a short paragraph says in words what it states;
   after it, remarks say what it does and does not claim and in which order the objects and constants are chosen.
   A problem with a main theorem goes to NOTES.md, never into the text; a check compares them with the spine.
2. **Definitions: only those needed to state the main theorems and the principal statements**, in dependency order,
   each by formula with one sentence of purpose and at most three sentences of interpretation. Machinery that only
   proofs use is defined in the section that uses it. A section that is mostly definitions has failed.
3. **Principal statements**, typeset faithfully from the spine (one result per statement, quantifiers first,
   conclusion displayed). Before each, one or two sentences on its role; after it, the idea of its proof in about 5
   to 12 lines (the mechanism, the key estimate, where the smallness comes from) and a pointer to the section that
   proves it, by `\ref`. Each principal statement gets its own owner review: correct against the spine and the
   Lean; understandable from the text before it; giving each of its uses what it needs.
4. **The deduction**: a complete proof of the main theorems from the principal statements, in numbered steps, each
   citing what it uses by `\ref`, with the order in which objects and constants are chosen; then each clause of the
   main theorems matched with the step that gives it.
5. **The constants**: one table (constant, what it depends on, where it is chosen, whether it is chosen to exist or
   holds for every admissible choice) and a sentence on why the order of choices has no cycle.

Sources: the natural spine (statements, order, ideas of proof, deduction, constants); the frozen contracts and the
clause map next to it, for what each statement must carry; the outline units and the Lean they link, for the ideas
of proof. The integrated manuscript ({{manuscript}}) shows the voice.

**Allowance: {{pages}} pages**, measured on standalone.pdf. Over the allowance means not done. If the section cannot
be complete within it, stop at the allowance, say in NOTES.md what is missing and how many pages it needs, and why.

Deliverables in {{stage_dir}}: {{file}}, standalone.pdf, correspondence.tsv, NOTES.md, REQUESTS.md, partI-edits.md
(exact edits to other sections of the opening part, or "None.").
