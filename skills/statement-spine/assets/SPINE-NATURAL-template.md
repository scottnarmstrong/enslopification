# Natural spine of Part I: <the result, in a few words>

<!--
Template of the statement-spine skill for the natural spine (SPINE-NATURAL.md): the frozen
contracts of SPINE.md (template SPINE-template.md) restated in natural form, with the same
mathematics. Once the author approves this file it is the authority for statements; SPINE.md
stays the record it must cover, through the clause map in section 6.
Replace every <...>. Keep the section order: it is the order that assets/prompts/natural-form.md
asks for. Every statement and definition is a raw LaTeX environment with a label, so that pandoc
passes it through (typeset_spine.sh), check_shape.py counts it, and writers copy it verbatim.
Never put text in square brackets right after \begin{...} unless it is the title. The relation
words mean exactly what the relations table of
honest-publication/references/correspondence-and-statement.md says.
-->

Status: <natural draft | clause map reviewed | approved by the author on <date>>
Approved file: SHA-256 <hash> (filled in when the author approves)
Restates: SPINE.md, SHA-256 <hash>. Lean: <repository> at commit <hash>; closure of <root
declarations> (`used = 1` in <dependency database>).
Binding: <STYLE.md>, <DETAIL-STANDARD.md>, exemplar <EXEMPLAR.md>. Caps: statements <100>/<150>
words, definitions <120>/<200>, main theorems <250> counted tokens and <8> references, other
statements <4> references.

## 1. Plan of Part I

| Section | Content | Statements | Proved in |
|---|---|---|---|
| <1> | <objects by formula> | <labels> | <Part II sections> |

## 2. Definitions

<Only the public objects needed to state the main theorems and the principal statements, in
dependency order. Machinery is defined in Part II where it is used; section 6 says where each
frozen definition went.>

\begin{definition}[<name>]\label{def:<key>}
<the object, by formula>
\end{definition}

- Purpose: <one sentence>. Interpretation: <one to three sentences, each literally true>.
- Correspondence: `<Namespace.declaration>`, <relation>.

## 3. Main theorems

<The natural main theorem first, its conclusions stated as clauses with formulas; the map from its
clauses to the supporting statements goes in the text after it, never inside it. The literal formal
statement goes to the appendix "Correspondence with the formal statement".>

\begin{maintheorem}\label{thm:main}
<statement>
\end{maintheorem}

- Correspondence: <declarations, relation>.

## 4. Principal statements

<The prose that sets up the objects and the standing hypotheses of the statement.>

\begin{proposition}[<TAG>]\label{prop:<TAG>}
<quantifiers first, each with its range; the conclusion displayed; constants with their dependence>
\end{proposition}

- Role: <one sentence: what it is for; which steps of the deduction use it>.
- Proof: <Part II section, and the later lemmas it combines>.
- Correspondence: `<Namespace.declaration>` (`used = 1`), <relation>.

## 5. Later lemmas and definitions (editable targets)

| Label | Statement in one line | Carries clauses | Home | Lean (`used = 1`) |
|---|---|---|---|---|
| <lem:key> | <...> | <clause ids> | <Part II section> | `<declaration>` |

<Write a later lemma as a raw LaTeX environment under the table when its exact wording is fixed
now; the writers of its home section refine the rest.>

## 6. Clause map

<One row for every clause id of SPINE.md: in the table below, or in CLAUSE-MAP.tsv (header:
assets/clause-map-header.tsv) with one line here pointing to it; clause_map_check.py reads both.>

| clause | destination | scope retained | note |
|---|---|---|---|
| <ID> | <label> | <quantifier order, existence or universality, uniformities, constant dependence> | <required if the id has several rows> |

### Source evidence for scope-sensitive clauses

| Key | Used declaration and location | What the source check fixes |
|---|---|---|
| <key> | `<declaration>`, <file>:<line> | <e.g. one run of the construction, not every admissible choice> |

### Definition relocation

| Frozen definition | Kept in Part I | Part II home or prose |
|---|---|---|

### Clauses requiring care

| Issue | Decision and Lean evidence |
|---|---|

## 7. Deduction of the main theorems

1. <Fix ...; choose ...; by Proposition <TAG> ...> (one step per choice, in the order in which
   objects and constants are chosen; each step cites the statements it uses).

| Clause of the main theorem | Steps | Statements |
|---|---|---|
| <clause> | <k> | <labels> |

## 8. Measured shape

| Block | Pages (typeset alone) | Environments | Over target | Over cap |
|---|---|---|---|---|

Paste the summary line of each command: `check_shape.py <this file>`;
`typeset_spine.sh -p <main.tex> <this file>`;
`clause_map_check.py --map <this file> --spine SPINE.md --labels-from <this file> --used-names <used.txt>`.
