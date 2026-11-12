# The correspondence table and the statement page

Both pages tie English text to the formal source at one pinned commit. The table covers every numbered item of the
manuscript; the statement page covers the main theorem in full. `math-paper-campaign` (reference
`from-formalization.md`) states the core rules briefly; this file gives the format, the check and the campaign's
numbers.

## 1. The correspondence table

**Rows.** One row per numbered statement, definition and labelled display of the manuscript, and more than one
where a statement has parts. Columns, tab-separated, with metadata lines above the header
([template](../assets/correspondence.template.tsv)):

| column | content |
|---|---|
| `label` | the `\label` of the item in the TeX |
| `kind` | definition, lemma, identity, deduction step, ... |
| `Lean declarations used=1` | the declarations, separated by `;`; external ones tagged, e.g. `Foo.bar (Mathlib)` |
| `relation` | one word from the list below; notes go in another column |
| `file:line` | where each declaration is, at the pinned commit; `file:start-end` for ranges |
| `notes` | free text: the bibliography key of a standard result, how a statement is split over rows |

<a id="relations"></a>
**Relations.** This is the one definition of the five words in this collection: the correspondence notes of
`statement-spine`, the writers' tables and the [template](../assets/correspondence.template.tsv) refer here. The
definitions follow the use of the words in the Yang–Mills campaign's correspondence tables.

| relation | meaning | declarations listed |
|---|---|---|
| `DIRECT` | the item states what the listed declaration states, up to notation | at least one |
| `WEAKENING` | the item is implied by the listed declarations and is weaker or more natural, never stronger | at least one |
| `COMPOSITION` | the item follows from several listed declarations by elementary steps given in the text | at least one |
| `CITED` | the text points to the listed declaration as the place where a step is proved (a proof pointer, a step of the deduction), without restating its content | at least one |
| `NONE` | no formal counterpart: a remark, a convention, or an explanatory argument of the text; never a numbered claim that a proof relies on (such a claim needs a declaration, or it is a gap to report) | none; `file:line` points into the TeX |

A standard result cited from the literature still gets the declarations that prove it in the Lean, with one of the
first four relations; its bibliography key goes in the `notes` column. A statement may be weaker than the Lean,
never stronger: an item stronger than every listed declaration is a finding for the drift protocol, not a row.

**The closure.** Every name must be in the closure of the main theorem, `used = 1` in the compiled graph of
`lean-dependency-graph` ([L5](../../lean-to-manuscript/references/lessons-learned.md#l5)). The development
contains routes the main theorem does not take; a declaration on such a route proves nothing about the text.

**Who writes it.** Writers deliver rows with every proposal; reviewers check them with the statements; the editor
merges them. The campaign's Part I table had 657 rows and 807 name references, all in the closure.

## 2. The check

```
check_correspondence.py correspondence.tsv --db graph.sqlite --tex manuscript/ \
    --commit 3456e5e --lean-repo path/to/lean-source --check-graph-locations
```

It prints one line per failure (`NOT-IN-GRAPH`, `UNUSED`, `BAD-RELATION`, `NO-NAMES` for a row of one of the first
four relations without a declaration, `NO-PIN`, `PIN-MISMATCH`, `LABEL-NOT-IN-TEX`, `NOT-IN-TABLE`, `BAD-LOCATION`,
`STALE-LOCATION`) and a summary line: rows, name references, distinct project and external names, and how many
are in the closure. Options:

- `--envs` chooses the statement environments whose labels must have rows (default: every environment declared
  by `\newtheorem`); `--displays` adds labelled displays; `--exclude-label` exempts labels by pattern.
- `--table`, `--name-col`, `--used-col`, `--path-col`, `--line-col` adapt to the graph's schema; `--col-*` to the
  table's headers.
- `--lean-repo` checks with `git` that every cited file exists at the pin and every cited line lies inside it;
  rows with relation `NONE` point into the TeX and are skipped.
- `--check-graph-locations` compares each name's file and line in the graph with the row: a mismatch means the
  row is stale.

Run it before every public push and after every round that adds or renames statements. On a working table in the
middle of a revision it typically finds statement labels without rows (statements added by a referee round), stale
locations after the Lean or the text moved, and relation cells holding free-text notes instead of one of the five
words; each of these blocks publication until it is fixed.

**What it does not establish:** that the listed declarations prove the item, that the relation is the right
word, or that the row lists everything the item needs. Those are judgments of the writer and the reviewer. It
also inherits the graph's limits ([L3](../../lean-to-manuscript/references/lessons-learned.md#l3),
[L4](../../lean-to-manuscript/references/lessons-learned.md#l4)).

## 3. Pins, re-pins, protected roots

- Record the full commit in the table (`# commit:`), and cite the same commit in the abstract, the introduction,
  the README and every link.
- **Re-pin on every change of either side.** A changed text adds, removes or relabels items; a new formal commit
  moves files and lines. Re-run the check, with `--lean-repo` and `--check-graph-locations`, and record the new pin
  in the changelog.
- **Protect the paper-facing declarations** as roots of every later dead-code sweep of the formal development, so
  that a declaration the table cites is not deleted because the top theorem does not use it (see
  `from-formalization.md`).
- **Publish the table before any text says it is published.**

## 4. The statement page

The first level of the public repository ([template](../assets/statement-page.template.md)). In order:

1. **The formal statement, verbatim**: the top-level theorem and the definitions at its core, copied exactly, each
   with a link to its lines at the pin; long structures in collapsible blocks. Copying follows the source's
   licence.
2. **What it says, in words**: a commentary in numbered clauses, each precise, for a reader who will not read Lean.
3. **A guide from each clause to the explanations** (outline units, the summary, the manuscript).
4. **The precise statement in ordinary mathematics**: conventions; each object defined with its own anchor; the
   main theorem with every quantifier, domain and order of limits as in the Lean; where the construction proves
   more than the formal statement, a detailed theorem with its narrower review scope stated (in the campaign some
   additional clauses were summarized without unfolding every definition, and the page says so).
5. **What is not claimed**: numbered, each saying exactly what is not asserted and citing where the formal source
   or an assessment of it says so. The campaign's page lists thirteen, among them uniqueness of the
   infinite-volume limit or independence of the subsequence, universality in the lattice data, values at
   coincident points, agreement with perturbation theory to all orders, and analyticity beyond what is stated.
6. **Correspondence with the source**: one row per item of the precise statement, with its declaration and
   pinned lines.

State how the page was checked: in the campaign, the public theorem was transcribed and compared definition by
definition with the pinned Lean, including quantifiers, spaces and the order of choices. That is an interpretation
check by agents, separate from the kernel check, and the FAQ says so.

**The formal statement is not the reader's theorem**
([L15](../../lean-to-manuscript/references/lessons-learned.md#l15)). In the manuscript the natural main theorem
comes first and the literal formal statement stands apart, in a section of its own or an appendix, checked
definition by definition; the statement page gives both, the formal one verbatim.
