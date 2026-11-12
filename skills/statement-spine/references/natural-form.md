# Natural form, not the Lean's shape

A formal statement is shaped by the proof assistant: long conjunctions, structures that package a
construction with its properties, side conditions that one later proof needs, existence of
witnesses that a reader would call "the" objects. Copied into a paper it is faithful and
unreadable. In the Yang–Mills campaign (2026) the first drafts' propositions ran to nearly a page,
one definition had 776 words, and one section was 92% definitions; the drafts were rejected
([L9](../../lean-to-manuscript/references/lessons-learned.md#l9)). Restate the frozen contracts
in natural form, with the same mathematics, before any prose is written.

## The rules

1. **One result per statement.** A statement asserts one thing a reader can name. A list of
   assertions (a), (b), (c) with different uses is several statements.
2. **Quantifiers first, conclusion displayed.** Each variable with its range, every constant with
   its dependence, then the conclusion as a display. No trailing conditions, no commentary inside.
3. **Objects set up before the statement.** Notation, the objects and the standing hypotheses of a
   section go in the prose or in a definition before the statement ("Throughout this section …").
4. **Side conditions to later lemmas.** Auxiliary conclusions and uniformities that the formal
   version carries for one later proof go to a later lemma, where that proof can cite them. The
   clause map records where each went.
5. **No packaging statements.** Never "there is a family such that the following assertions
   hold". The conditions of a construction belong in the setup where its objects are introduced;
   the statements are then about those objects.
6. **Existence against every, as the Lean decides**
   ([L12](../../lean-to-manuscript/references/lessons-learned.md#l12)). If the Lean proves that one
   run of the construction works, write "there is a choice of the constants, made in the order of
   Appendix C, such that …" and afterwards "for the constants of Theorem X"; never "for admissible
   constants", which a reader takes as "for every choice above the thresholds". If the objects are
   chosen rather than defined, the setup says so ("the construction of Section 3 chooses …; fix
   this choice"); the statements must not turn the constructed objects into "some objects with
   these properties" ([L11](../../lean-to-manuscript/references/lessons-learned.md#l11)).
7. **Hypotheses stay with their users**
   ([L13](../../lean-to-manuscript/references/lessons-learned.md#l13)). A statement carries every
   hypothesis that its users rely on. Meet a cap by splitting the statement or by defining objects
   earlier, never by moving a hypothesis into the surrounding prose.
8. **Caps, measured.** Statements: target 100 words, cap 150; definitions: target 120, cap 200;
   counted by `check_shape.py` of [exposition-standards](../../exposition-standards/SKILL.md),
   whose counting rule includes formulas. Count every environment, axiom lists included; grant no
   exemptions.

## An example

Lean-shaped (89 counted words, five ideas):

> **Proposition 4.** There exist constants $c_0,C_0>0$ and, for each $N$, a family
> $(\rho_k)_{0\le k\le N}$ such that the following assertions hold: (a) $\rho_N=\rho^{\rm in}$;
> (b) for every $k<N$, $\rho_k=T_k\rho_{k+1}$ and $\rho_k\in\mathcal A_k$; (c) for every $k<N$
> with $\|\rho_{k+1}\|_{k+1}\le c_0$ one has $\|\rho_k\|_k\le C_0\|\rho_{k+1}\|_{k+1}^{3/2}$,
> where $C_0$ depends only on $d$ and $L$; (d) the map $\rho_{k+1}\mapsto\rho_k$ is measurable;
> (e) $c_0\le 1/(4C_0)$.

Natural (41 counted words, one idea). The prose before the statement defines $\rho_N=\rho^{\rm in}$ and $\rho_k=T_k\rho_{k+1}$
(clauses a, b). Then:

> **Proposition 4 (one step).** There are $c_0,C_0>0$, depending only on $d$ and $L$, such that for
> every $N$ and every $k<N$,
> $$\|\rho_{k+1}\|_{k+1}\le c_0\quad\Longrightarrow\quad\|\rho_k\|_k\le C_0\,\|\rho_{k+1}\|_{k+1}^{3/2}.$$

Membership in $\mathcal A_k$ becomes a later lemma; measurability, if no reader-facing proof uses
it, is one sentence of the setup with its Lean declaration in the correspondence note; clause (e)
goes to the constants table, and if a later proof relies on it, that proof's statement carries
it. Every one of the five clauses gets a row in the clause map.

## Main theorems state; they do not list

The main theorems are the statements a referee reads first. Their conclusions are clauses with
formulas, at most 250 counted tokens and 8 references; every other statement cites at most four
results ([L10](../../lean-to-manuscript/references/lessons-learned.md#l10)).

A theorem whose clauses only point to supporting statements by label can be under every word
cap. In the Yang–Mills campaign the first version of the detailed main theorem had a conclusion
that listed about forty labels of other results. It went through the owner and fresh-reader
reviews, which judge faithfulness, and the shape check did not yet cover main theorems.
Rewritten, it has five clauses, and the map to the supporting results is in the text after it.
A word cap does not catch a list; the reference cap does. Ask of every main theorem: would a
referee accept this as the statement of the paper's result?

## The literal formal statement stands apart

The exported formal statement is rarely the theorem a reader wants
([L15](../../lean-to-manuscript/references/lessons-learned.md#l15)). In the Yang–Mills campaign
the formal specification asks only that some positive slope of the coupling exist and contains no
stress tensor; the construction gives more on both counts, and the detailed main theorem says so.
State the natural theorem first; put the literal one, with the formal conventions it needs, apart
from it ("Correspondence with the formal statement": an appendix, or, as in that campaign's second
draft, the last sections of the opening part), compared definition by definition. Define the
formal axioms first as counted definitions so that the literal statement is short.

## Definitions of the opening part

Define only the public objects needed to state the main theorems and the principal statements
([L14](../../lean-to-manuscript/references/lessons-learned.md#l14)). Each is concrete, by formula,
with one sentence of purpose and one to three interpreting sentences; never a translation of a
Lean structure, never a list of types. Give each item of a property list its own label so that the
text can cite it. Everything else is defined in the later part where it is used, and the
definition-relocation table of the clause map says where.

## The number of statements may change

Natural form merges and splits. In the Yang–Mills campaign the reconciled propositions became
fifteen principal statements (the ultraviolet part as an inductive one-step theorem followed by a
multiscale theorem, the order of a standard monograph on the renormalization group) and the two
main theorems; their side conditions went to later statements and definitions. This is allowed
because the clause map shows that the union of the new statements is the frozen contract, nothing
dropped and nothing strengthened ([clause map](clause-map.md)).

## Writing the natural spine

Start from `assets/SPINE-NATURAL-template.md` (the frozen contracts use `assets/SPINE-template.md`).
Write every statement and definition as a raw LaTeX environment with a label inside the Markdown
spine. Pandoc passes it through, `check_shape.py` counts it, `typeset_spine.sh` measures it, and
the writers of the sections copy it verbatim. Use `assets/prompts/natural-form.md`; the writer
runs the shape check and the clause-map check itself before it finishes, and an independent
reviewer then reads the clause map (`assets/prompts/clause-map-review.md`).
