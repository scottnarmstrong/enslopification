{{common}}

# Task: write Section {{number}}, "{{title}}" (a proposal; the editor integrates it)

Your proposal directory {{stage_dir}} contains the placeholder file {{file}}: the section's list of statements with
their labels. Write the complete section into this file; keep the `\section` line and every label.

Content:
1. Every definition and lemma of the placeholder, typeset faithfully from the spine in natural form, and every
   statement other sections were promised from this section. All of them are proved here.
2. Complete proofs at the detail standard: mechanisms written out, standard results cited exactly, repeated cases
   done once with the reduction stated. A proof longer than three pages is split at a genuine intermediate statement.
   If a step is not established by the Lean, say exactly what is proved and report it in NOTES.md; never write
   around it.
3. The proofs of the principal statements that the opening part places in this section ({{principal}}), each
   assembled from the lemmas and ending with a precise statement of what was proved.
4. An opening of about half a page: what the section proves, which statements use it, the strategy, and where the
   difficulty lies.

Sources: {{sources}}. The integrated manuscript ({{manuscript}}, compiled as {{main_pdf}}) shows the level and voice
to match, in particular {{model_sections}}.

**Allowance: {{pages}} pages**, measured on standalone.pdf. Over the allowance means not done. If the section cannot
be complete within it, stop at the allowance, say in NOTES.md what is missing and how many pages it needs, and why.

Deliverables in {{stage_dir}}: {{file}}, standalone.pdf, correspondence.tsv, NOTES.md, REQUESTS.md, partI-edits.md.
