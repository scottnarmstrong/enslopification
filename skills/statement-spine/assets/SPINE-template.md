# Spine of Part I: <the result, in a few words>

<!--
Template of the statement-spine skill for the drafts, the reconciled merge and the frozen
contracts (SPINE.md). The natural spine (SPINE-NATURAL.md), which restates these contracts and
carries the clause map, has its own template: SPINE-NATURAL-template.md.
Replace every <...>. Keep the section order.
Statements and definitions are raw LaTeX environments with a label, so that pandoc passes them
through (typeset_spine.sh) and check_shape.py counts them. Writers do not typeset these contracts:
they typeset the natural spine, and the contracts are the record it must cover. Never put text in
square brackets right after \begin{...} unless it is the title.
In the frozen contracts, end every clause of every statement with a tag [clause:ID] (one
hypothesis, one conclusion, one quantifier binding or one uniformity per tag); the clause map of
the natural spine and clause_map_check.py use these ids. The relation words DIRECT, WEAKENING,
COMPOSITION, CITED, NONE mean exactly what the relations table of
honest-publication/references/correspondence-and-statement.md says.
-->

Status: <draft A | draft B | reconciled | frozen contracts, reviewed on <date>>
Approved file: SHA-256 <hash> (filled in when the author approves)
Authority: the Lean development <repository> at commit <hash>; declarations in the closure of
<root declarations> (`used = 1` in <dependency database>). Maps, never evidence: <outlines, summary>.
Reader: <named reader>. Binding: <STYLE.md>, <DETAIL-STANDARD.md>, exemplar <EXEMPLAR.md>.

## 0. Plan of Part I

| Section | Content | Principal statements | Proved in |
|---|---|---|---|
| <1> | <objects by formula> | <tags> | <Part II sections> |

## 1. Standing conventions

<At most half a page: the notation every statement uses; standing hypotheses stated once.>

## 2. Definitions

<Only the public objects needed to state the main theorems and the principal statements, in
dependency order. Machinery is defined in Part II where it is used.>

\begin{definition}[<name>]\label{def:<key>}
<the object, by formula>
\end{definition}

- Purpose: <one sentence>. Interpretation: <one to three sentences, each literally true>.
- Correspondence: `<Namespace.declaration>` (`used = 1`), <DIRECT | WEAKENING | COMPOSITION | CITED | NONE>.
- Could move to Part II: <yes / no, because ...>.

## 3. Main theorems

<The main theorems the reconciliation recommends: the theorem a reader wants (the detailed
construction) and the literal formal statement, every clause tagged. Their natural form, with the
caps, is written in SPINE-NATURAL.md.>

\begin{maintheorem}\label{thm:main}
<statement>
\end{maintheorem}

- Correspondence: <declarations, relation>. The map from its clauses to the supporting
  statements is in the text after the theorem, not inside it.

## 4. Principal statements

### <TAG>. <short name>

- **Role:** <what it is for; which deduction steps and statements use it>.
- **Statement:**

\begin{proposition}[<TAG>]\label{prop:<TAG>}
<hypotheses and quantifiers first, conclusion displayed, constants with their dependence>
\end{proposition}

- **Correspondence:** `<Namespace.declaration>` (<file>:<line> at <commit>), `used = 1`;
  relation <DIRECT | WEAKENING | COMPOSITION | CITED | NONE>. <Where the natural form would be
  stronger than the Lean's, the Lean's form is stated and one line says so.>
- **Consumers and dependencies:** used by <steps, statements>; uses <statements>; cites
  <standard result, exact source and number>.
- **Home and allowance:** Part II <section>, <pages> pages.
- **Idea of the proof:** Step 1. <...> Step k. <...> (five to ten lines; this becomes the
  Part I text after the statement).
- **Least certain point:** <where the sources are incomplete or the Lean is hard to read>.

## 5. Deduction of the main theorems

1. <Fix ...; choose ...; by Proposition <TAG> ...> (one step per choice, in the order in which
   objects and constants are chosen; each step cites the statements it uses).

| Clause of the main theorem | Steps | Statements |
|---|---|---|
| <clause> | <k> | <tags> |

## 6. Constants and order of choice

| # | Constant | Chosen after | Depends on | Fixed by |
|---|---|---|---|---|
| 1 | <constant> | <earlier constants> | <data> | <statement or step> |

## 7. Part II statements (editable targets)

| Label | Statement in one line | Carries clauses | Home | Lean (`used = 1`) |
|---|---|---|---|---|
| <lem:key> | <...> | <clause ids> | <section> | `<declaration>` |

## 8. Measured size and shape

| Block | Pages (typeset alone) | Environments | Over target | Over cap |
|---|---|---|---|---|

Commands: `typeset_spine.sh -p <main.tex> <this file>`; `check_shape.py <this file>`.

## 9. Decisions for the author

| # | Question | Options | Evidence | Recommendation | Ruling (date) |
|---|---|---|---|---|---|
