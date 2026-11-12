# The routed-inputs check

How to inventory the citations between sections, group them for checkers, compare each use with the statement it
cites, and clear or confirm candidate cycles. The repairs and the rounds that follow are in
[repair rounds](repair-rounds.md).

## What is routed

When sections are written in parallel, each proof that cites a statement of another section relies on a statement
its writer did not write and may not have read in its final form. A **routed citation** is a `\ref`-family citation
whose label is defined in another section. Three kinds matter: citations between proof sections; the opening part's
pointers to the proof part (where each principal statement is proved, what the deduction uses); and the proof part's
uses of the opening part's definitions. The third kind is usually the most numerous.

## Inventory

Compile the manuscript, then run `cross_refs.py MAIN.tex --aux MAIN.aux --unit-map units.tsv --out xref/`. The unit
map gives one unit per section (a section spread over several files is one unit) and one for the opening part, or
one per opening section. Fix undefined and duplicate labels first (exit status 1). Then read:

- `pairs.tsv`: which section cites which, how often inside proofs, with how many ranges, and how many citations of
  displays that live inside a proof;
- `citations.tsv`, one row per routed citation. Column `cited_where = proof` marks a label inside the cited
  section's proof: the citing section uses something that no statement asserts, a mismatch until shown otherwise;
- `ranges.tsv`, `cycles.tsv`, and `labels.tsv` for lookups.

The inventory sees only `\ref`-family citations. Typed numbers ("Lemma 3.2"), and phrases such as "the bound above"
across sections, are invisible to it; numbering only by cross-reference
([L17](../../lean-to-manuscript/references/lessons-learned.md#l17)) is what makes the inventory complete, so search
the TeX for typed numbers first, for instance
`grep -nE '(Lemma|Theorem|Proposition|Corollary|Definition|Section)s?~?[0-9]+\.[0-9]+' part*/*.tex`.

## Groups and checkers

Split the routed citations into groups and give each group to one read-only checker, from a model family other than
the writers' ([`rollout.routed-check.example.json`](../assets/rollout.routed-check.example.json), prompt
[`routed-check.md`](../assets/prompts/routed-check.md)). Group by cited section, so that one checker reads each
cited statement once against all its uses; split a section with very many citers; keep the opening part's pointers
in a group of their own. Give groups disjoint scopes, or state the overlap, so that their counts add up. A full check
after a round of repairs has four kinds of group: the items still open from earlier rounds, the opening part's
citations of the proof part, the proof sections' citations of each other, and the proof part's citations of the
opening part together with the candidate cycles.

Each checker states which sources it consulted and **whether it could query the dependency database**. A checker
whose shell commands are refused still answers: its verdicts then rest on the manuscript text and the writers' notes,
and only a sentence in its report says so ([L22](../../lean-to-manuscript/references/lessons-learned.md#l22)). Run
the permission preflight before the round.
After the round, `check_coverage.py` of [`writing-workflow`](../../writing-workflow/SKILL.md) lists what a group's
report never names: the cited labels of its rows (`--register xref/by-pair/<pair>.tsv --column cited_label`, once
per by-pair file of the group) and its own candidate cycles (`--labels` with the ids of the group's `cycles`
variable). To find the cycles that no report names, give it every report at once
(`--register xref/cycles.tsv --column cycle <workdir>/*/check/routed.md`); on one group's report that form flags the
other groups' cycles too. A label named is not thereby checked.

The editor reads the largest findings and every cycle verdict against the text before merging: a reported mismatch
can disappear under the correct reading of the citation, and is then recorded as disputed, with that reading, not as
confirmed. Then the editor merges the group reports into one table with stable ids
([`mismatch-table.template.md`](../assets/mismatch-table.template.md)).

## The comparison rule

**Compare what the citing proof uses with what the cited statement says, never with what the cited proof gives.**
A property that appears only inside the cited proof is a mismatch even when it is true and proved: the reader of the
citing section is sent to the statement.

Kinds of mismatch such checks find, in sections that have each passed their own reviews:

| kind | example |
|---|---|
| scope of the inputs | a lemma stated for one class of inputs, cited for a wider class, with a bound that appears only inside its proof |
| quantifier order | the statement gives a constant for each value of a parameter; the citing proof needs one constant for several values at once |
| arity | a statement for two points, used for any number of points |
| geometry and uniformity | one notion of separation stated, another used; a local statement used uniformly |
| quantitative use of a qualitative statement | a statement that a limit exists, cited for a rate of convergence it does not state |
| growth against boundedness | the statement allows coefficients that grow; the use needs them bounded |
| wrong attribution | facts cited from one lemma that are stated in another the section never cites |
| stale description | a constant changed in the cited section, its old value still quoted by the citing one |
| display inside a proof | a citation of a display in a proof where the exported statement says the same |

Routing can break on both sides at once: the cited section's notes say it does not supply an estimate, and the
citing section's notes say it cites the estimate from that section
([L21](../../lean-to-manuscript/references/lessons-learned.md#l21)); read the notes of both. The missing content is
usually already in the cited proof or in the Lean, so most repairs restate a statement or redirect a citation; new
mathematics is the exception, not the rule.

Repairs, in order of preference: **say so** (restate the cited statement to what its proof already gives); change
the citing sentence; a new proof from the Lean; a request to the owning section. A repair that would change a frozen
principal statement or a main theorem is marked DRIFT and goes to the author.

## Range citations

A range prints whatever lies between its ends: "Lemmas X–Y" can span many statements of which the citing proof uses
a few, and can include a definition or a lemma that the citing section does not use. Ranges also rot: inserting a
statement changes what they span. `ranges.tsv` lists what each one spans; the repair is the list of the statements
actually used.

## Cycles

`cross_refs.py` builds the lemma-level graph from citations inside proofs and statements (remarks and examples give
no edges; a citation of a display inside a proof counts as a use of that proof's statement) and lists every cycle,
up to a cap. Each is a candidate: the checker marks it CLEARED (one edge is a forward pointer, a placement remark, or
uses a part that does not depend on the cycle) or CONFIRMED (a statement must change). Most candidates are not
genuine. Watch for one hazard: a statement with a clause completed only after a lemma that silently reuses the
statement's other part, so that adding the honest citation would create a cycle; the repair moves the clause into a
separate corollary.

## The opening part and the crosswalk

The opening part says where each principal statement is proved and which proof-part results the deduction of the main
theorems uses. Check these pointers like any routed citation, in both directions, and keep a **crosswalk**: every
input the opening part takes from the proof part, including unnumbered estimates, against the proof-part statement
that exports it, with a verdict. When the opening part's citations are split between checkers by ranges of
sections, make the ranges disjoint, or state the overlap and report counts per checker, not as a partition. Edits to
the opening part that proof-section writers proposed against an older version are re-applied against the current
text, each recorded as applied, already met, or obsolete.

## What the check does not establish

A MATCH says that a statement says what one step of a proof takes from it. It is not a check of the citing proof,
of the cited proof, or of either against the Lean (unless the checker queried it and says so). The inventory covers
`\ref` citations only. Checkers are agents: their verdicts are evidence for the editor to read, not decisions.
