# The clause map and the correspondence notes

The natural restatement changes the shape of every statement. The clause map is the record that
it did not change what is claimed: every clause of every frozen contract is assigned a
destination, the union of the destinations equals what the Lean proves, nothing is dropped and
nothing is strengthened ([L9](../../lean-to-manuscript/references/lessons-learned.md#l9)).
Undeclared losses, such as a condition that silently disappears, are the main risk; the general
form of this rule is in the drift protocol of `math-paper-campaign` (reference
`shared-controls.md`).

## Clause ids

When the contracts are frozen, end every clause with a tag `[clause:ID]`: one hypothesis, one
conclusion, one quantifier binding or one uniformity per tag. Choose ids that say where the
clause lives: `T1.h2` (second hypothesis of Theorem 1), `P5.c3` (third conclusion of the fifth
proposition), `D7.f` (a formula in Definition 7). Tag the definitions the statements use as well
as the statements; tag the outer quantifiers of the main theorem separately ("one family is
chosen before every volume sequence" is a clause).

`clause_map_check.py --spine SPINE.md` reads the ids from these tags (`--clause-regex` changes the
form), or from a plain list with `--clauses`.

## The table

| clause | destination | scope retained | note |
|---|---|---|---|
| `T1.h2` | `thm:main`; `lem:energy` (hypothesis on the data) | for every $s>d/2+1$ and every datum in $H^s$; constants depend only on $s$, $d$ | |

(`assets/clause-map-header.tsv` has the header and two example rows.)

- **clause:** one or more frozen ids and nothing else.
- **destination:** the label of the statement, later lemma, definition, or labelled setup passage
  that now carries the clause; text after a label is a comment. A setup passage gets a `\label`
  or a heading so that it can be checked. A clause split between a statement and the setup before
  it has both destinations: splitting does not remove a hypothesis.
- **scope retained:** in words, what the destination keeps: quantifier order, existence or
  universality, the range of every parameter, uniformities, what constants depend on.
- **note:** required when a clause appears in more than one row, to say how it is split.

Keep two companion tables in the same section:

- **Definition relocation:** frozen definition, what the opening part keeps, the later home or
  the prose that replaces the rest.
- **Source evidence for scope-sensitive clauses:** key, the `used = 1` declarations with
  file:line, and what the check of the source fixes. A clause is scope-sensitive when a natural
  reading could change its strength.

## Scope-sensitive clauses

These are the clauses where a fluent restatement goes wrong. Each cites the declarations that fix
it ([L12](../../lean-to-manuscript/references/lessons-learned.md#l12)). The kinds to look for:

- one run of a construction against every admissible choice of its constants;
- the full sequence of a limit against a subsequence or an extraction;
- every case (every phase, every label, every volume) against a selected one, and how the
  selected one is chosen;
- uniqueness within a specified recursion against uniqueness from a weaker identity;
- two objects that the Lean chooses separately, which a reader would identify;
- the order of outer quantifiers: which objects are fixed before a sequence is given.

## Clauses requiring care

List, never change silently, every clause you believe is wrong, unnecessary, or tempting to
change, with the decision and its Lean evidence. Typical entries are rejected temptations (a
universal statement where the Lean's class carries an extra retained condition; full convergence
where the Lean extracts a subsequence; a later conclusion used as a selection criterion; two
objects identified that the Lean chooses separately; a stronger boundary statement) and
conventions dropped because they impose nothing, each with the reason why the claim is unchanged.
A clause that must change in content goes to the author under the drift protocol
([freezing and drift](freezing-and-drift.md)).

## Correspondence notes

Every statement and definition of the spine carries a correspondence note: the Lean declarations
it rests on and their relation to it, one of DIRECT, WEAKENING, COMPOSITION, CITED or NONE. The
words are defined once for the whole collection, in the
[relations table of honest-publication](../../honest-publication/references/correspondence-and-statement.md#relations);
use them in exactly that sense. Cite only declarations in the closure of the main theorem
(`used = 1`); the development contains routes that the main theorem does not use, and they are
evidence for nothing ([L5](../../lean-to-manuscript/references/lessons-learned.md#l5)).

**The paper claims nothing the Lean does not prove; weaker or more natural forms are allowed,
stronger never.** A WEAKENING needs no permission; a statement stronger than its declarations is
a finding. A principal statement or a later lemma is never NONE: a numbered claim that a proof
relies on needs a declaration, or it is a gap to report. The notes become rows of the
correspondence table, published with the manuscript and pinned to one commit (see
`honest-publication`, and the correspondence table of `math-paper-campaign`'s
`from-formalization.md`).

Check the names mechanically: export the closure (for example
`sqlite3 graph.sqlite "select name from nodes where used=1" > used.txt`) and run
`clause_map_check.py --used-names used.txt`, which flags every backticked dotted Lean name in the
map files that is not in it. In the campaign the correspondence table of the opening part had 657
rows citing 807 names, all in the closure.

## The mechanical check and the review

`clause_map_check.py` establishes four facts: every frozen clause has a row with a destination;
every destination exists; no clause is in several rows without a note; no row names a clause that
is not frozen. Only with `--used-names` does it add a fifth: every backticked dotted Lean name in
the map files is in the closure; a name written without backticks or without a namespace dot is
not seen. It cannot see whether a destination says what the clause says.

That is the review's job (`assets/prompts/clause-map-review.md`): a fresh reader opens every
destination and compares hypotheses, quantifier order, existence, uniformities and constant
dependence with the frozen clause. Typical findings: data of the main theorem left implicit; a
statement that depends on a definition given after it; the main theorem's scope mixed with its
proof inputs. A clause map checks faithfulness, not readability: a main theorem whose clauses only
point to supporting statements satisfies the map and is still a list
([L10](../../lean-to-manuscript/references/lessons-learned.md#l10)).

Run both again after every change to a frozen statement or to a later lemma that carries a clause.
