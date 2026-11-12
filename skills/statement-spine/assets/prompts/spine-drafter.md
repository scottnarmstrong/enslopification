You are drafting, independently of another drafter, the statement spine of the opening part of a
mathematical manuscript: a human-readable proof of the result formalized in the Lean development
{{lean_repo}} at commit {{commit}} ({{project}}). The other drafter does the same task without
seeing your work; a reconciliation will compare the two drafts. Write only the file {{output}}.
Do not run git, lake or any build.

## The manuscript

{{manuscript_plan}}
Reader: {{reader}}. Binding rules: {{detail_standard}} and {{style}}; read both first.

## Your task

Propose the principal statements and the deduction of the main theorems from them. A principal
statement is a real interface of the proof: a large block of the proof establishes it, and the
deduction or another principal statement uses it. Reject component extractions, immediate
specialisations, identities local to one proof, and statements that exist for the convenience of
the formal proof. Prefer a small number of strong, natural statements.

For each principal statement give an envelope:

1. Role: what it is for, and which deduction steps or statements use it.
2. Statement: exact, in plain mathematical language with LaTeX: hypotheses, every quantifier in
   its order, the conclusion, uniformities, constants and what they depend on. Say whether it
   holds for every admissible choice or for one choice that the construction makes, as the Lean
   decides. Never state more than the Lean proves; where the natural form would be stronger,
   state the Lean's form and say so in one line.
3. Correspondence: the Lean declarations that establish it (full names, file:line at
   {{commit}}), each with used = 1 in {{db}}, and whether the statement is DIRECT, a WEAKENING
   or a COMPOSITION of them.
4. Dependencies: other principal statements; standard results it cites (exact statement, source
   and number).
5. Home: where its proof goes in the later part, with a page estimate.
6. Least certain point: where the sources are incomplete or the Lean is hard to read.

Then give the deduction of the main theorems, step by step, in the order in which every object
and every constant is chosen; the definitions the opening part needs, with a page estimate; and
open questions for the author.

## Sources (read in this order; cite paths)

- The exact theorem: {{statement_file}}.
- Maps, to find things (never evidence): {{maps}}.
- The authority: the Lean at {{lean_repo}}. Dependency database: {{db}}. Only declarations with
  used = 1 (in the closure of {{roots}}) may be cited. The development contains routes that the
  main theorem does not use; never cite them, and check every name before relying on it.

## Output

One Markdown file {{output}}, at most {{max_lines}} lines: (i) one paragraph on the shape of the
spine; (ii) the principal statements with their envelopes; (iii) the deduction; (iv) the
definitions needed; (v) page estimates for the opening part and for each later section;
(vi) open questions. No Lean syntax in mathematical statements (Lean names only in item 3).
Plain mathematical English; no process words in the statements.
