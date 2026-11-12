# Glossary of the code's names, and where the ideas come from

Two reference pages that every level of the map links to. Lessons:
[L6](../../lean-to-manuscript/references/lessons-learned.md#l6),
[L28](../../lean-to-manuscript/references/lessons-learned.md#l28),
[L32](../../lean-to-manuscript/references/lessons-learned.md#l32).

## Glossary

Large formal developments often name their objects by nicknames chosen to be distinct, not descriptive (the
Yang–Mills code: `Treasury`, `Jewel`, `Sheet`, `sails`). Nobody can read the code, or an outline that quotes it,
without a translation.

**Selection.** Every declaration needed to state the main theorems: their statement closure
(`closure.py --statement-closure` of [lean-dependency-graph](../../lean-dependency-graph/SKILL.md), which follows
the statements and, for definitions, their bodies, so a definition used inside another one is not missed); then,
per part, the most used declarations of the closure (the in-degree query of the graph's query recipes). The
Yang–Mills glossary had 276 entries; it said that it was not exhaustive.

**Entry.** The pinned link to the declaration (name and lines), a confidence label, a marker if it occurs in a
main statement, and one or two sentences: the mathematical object, in standard terms, with notation where it
helps. Group entries by part; within a part, main-statement entries first, then by number of users.

**Confidence labels,** with their meanings published at the top of the page:

| Label | Meaning |
|---|---|
| certain | read from the definition and its uses |
| probable | inferred from the fields and the documentation |
| tentative | partly guessed; where the role is unknown, the entry says "unclear" |

About a third of the Yang–Mills entries were probable or tentative, mostly in the renormalization-group estimates.
State that the labels describe the strength of the interpretation, that even *certain* is not a proof audit, and
that they are separate from unit review statuses.

**Families.** Nicknames are often systematic even when each word is arbitrary: an economic vocabulary for the
order in which constants are chosen (a "price" or "budget" is a numerical bound), a weather vocabulary for contact
terms, rooms and halls for the passage from Euclidean to Hilbert space. A short section describing each family as a
pattern of the code (not a documented convention) teaches more than fifty entries. List also the folder names that
carry no meaning (`Next/`, `Extra/`, numbered work folders).

**Uses downstream.** The glossary feeds the outlines' notation sections, and later the manuscript's terminology
table: code vocabulary must not leak into the paper
([L28](../../lean-to-manuscript/references/lessons-learned.md#l28)). Where a term from the literature exists, the
glossary gives it.

## Provenance: where the ideas come from

A component-by-component account of which parts of the proof follow which earlier programme, which are standard
and which appear new, with the evidence on both sides. It answers the first question a mathematician asks about a
machine-written proof, and its limits must be as visible as its conclusions.

**Method.**

1. **Sources.** List the candidate antecedents (the programmes the field associates with the problem, recent
   papers of the same authors or groups, standard texts) and read them; record for each what was read and what
   was not (pages, sections).
2. **Components.** One component per unit or half-unit. For each: the mechanism in the Lean, with pinned links to
   the declarations that implement it; the closest antecedent among the sources read, with page, theorem or
   equation numbers; what matches and what differs.
3. **Classes,** defined at the top of the page: *standard* (textbook mathematics), *adapted from programme X* (a
   specific mechanism closely matching X), *adapted, other* (an identified older method), *candidate new* (no
   matching construction found in the sources read: a bounded claim, not priority). Distinguish "same device" (a
   specific construction with the same role), "same general method" (an established technique), and "superficial
   resemblance" (shared vocabulary only).
4. **Evidence on both sides.** For every attribution, also what argues against it: an apparently distinctive
   device that an older source already has, an endpoint that differs, a hypothesis the antecedent assumes and the
   Lean proves.
5. **Confidence,** stated per conclusion: high for individual formula matches, lower for rankings of closest
   antecedents, lowest for claims of novelty.
6. **Size comparison, labelled.** Lines of used declarations per group of units are an implementation weight:
   publish the table with the groups' membership, and say that it is not a measure of intellectual ownership and
   not an exclusive attribution.

**Limits to state at the top.** Who wrote it (which model, from which sources); that it identifies the closest
antecedents among the sources read, not borrowing, intention or priority; that chronology alone proves no
dependence; that the authors of the works discussed have not reviewed it; which comparisons an expert should check
first. Keep claims about the proof's mechanisms tied to the Lean, not to the outlines: the outlines are orientation,
not evidence.
