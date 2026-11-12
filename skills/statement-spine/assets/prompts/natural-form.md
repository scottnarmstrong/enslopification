Restate the frozen spine {{frozen_spine}} in natural form, with the same mathematics. Write only
{{output}}. Do not run git, lake or builds.

## Why

The frozen spine is faithful to the Lean but has the Lean's shape: {{measured_shape}}. A reader
cannot use it. The binding rules are {{style}}; read them first, with the detail standard
{{detail_standard}} and the exemplar notes {{exemplar}}.

## Rules for every statement

- One result per statement. Quantifiers first, each with its range; the conclusion displayed.
- Objects, notation and standing hypotheses are set up in the prose or in a definition before
  the statement. Side conditions of the formal version go to later lemmas.
- No packaging statements ("there is a family such that the following assertions hold"): the
  conditions of a construction belong in the setup where its objects are introduced.
- Existence or universality exactly as the frozen spine states it, with the order in which
  choices are made; the frozen spine follows the Lean, not the natural reading.
- Statements: target {{stmt_target}} words, cap {{stmt_cap}}. Definitions: target
  {{def_target}}, cap {{def_cap}}. Main theorems: at most {{main_cap}} counted tokens and
  {{main_refcap}} references; they state their conclusions as clauses with formulas, never as a
  list of labels of other results. Other statements cite at most four results.
- A cap is met by splitting a statement or by defining objects earlier, never by moving a
  hypothesis out of a statement that relies on it.

## Definitions of the opening part

Only the public objects needed to state the main theorems and the principal statements; each
by formula, with one sentence of purpose and one to three interpreting sentences; never a
translation of a Lean structure. Machinery is defined in the later part where it is used. The
literal formal statement goes to an appendix "Correspondence with the formal statement"; the
natural main theorem comes first.

## What {{output}} contains

1. The plan of the opening part. 2. The definitions. 3. The main theorems. 4. The principal
statements (role in one sentence, statement, pointer to its proof). 5. The later lemmas that
carry every remaining clause. 6. The clause map. 7. The deduction of the main theorems.
8. The measured shape: run `{{shape_cmd}}` and paste its summary line.

Write every statement and definition as a raw LaTeX environment with a label, for example
`\begin{proposition}[TAG]\label{prop:TAG} ... \end{proposition}`. Square brackets right after
`\begin{...}` are read as the title.

## The clause map

A table with the columns "clause | destination | scope retained | note": one row for every
clause id of the frozen spine (its [clause:ID] tags). The destination is the label of the
statement, definition, later lemma or labelled setup passage that now carries the clause; the
scope column says in words what is retained (quantifier order, existence or universality,
uniformities, constant dependence); a clause in several rows needs a note. The union must equal
the frozen contract: nothing dropped, nothing strengthened. Scope-sensitive clauses cite the
used = 1 declarations that fix them, in a source-evidence table. Where you believe a frozen
clause is wrong or unnecessary, list it under "Clauses requiring care" with the Lean evidence
(used = 1, file:line); never change it silently. Run `{{check_cmd}}` and fix every problem it
reports before you finish.
