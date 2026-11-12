# The closure, the authors' record, and counting scopes

How to choose roots and mark the closure, why only `used = 1` declarations may be cited, how to compare the closure
with a usage record that the authors publish (and what to do when they publish none), and how to state what each
count counts. Lessons:
[L4](../../lean-to-manuscript/references/lessons-learned.md#l4),
[L5](../../lean-to-manuscript/references/lessons-learned.md#l5).

## Roots

Take the roots from the authors, verbatim: a headline list shipped with the release, the targets of their
verification program, or the theorems their README names. Do not choose them by hand. The Yang–Mills release
named seventeen headline results in one file (the public theorem, the detailed construction, results for SU(2),
short-distance comparison results, and an alternative family of constructions); the campaign used all seventeen.

- The closure is the **union** of the roots' closures, roots included. Shared declarations count once: never add
  the sizes of separate closures.
- The union can be broader than the closure of the public theorem alone. With seventeen roots it contained an
  alternative construction that the public theorem does not need. Say which roots a count refers to.
- `closure.py` records the roots in the `roots` table and in `meta` (count, SHA-256 of the sorted list, parts
  followed, size). Quote the hash with any published count.
- The statement closure (`closure.py --statement-closure`, which writes nothing) is what is needed to *state* the
  roots: from every declaration reached it follows the statement references, and from a definition (def, abbrev,
  opaque, instance, field, structure, inductive type, constructor) also its body, which the graph records as proof
  references; a structure brings its constructors. A theorem reached this way contributes its statement only.
  `--parts statement,both` is not the same set: it misses a definition used only inside another definition's body.
  The statement closure is the natural starting list for the definitions a manuscript's first part must give; the
  script lists its members with `used = 0` (constructors that no proof reaches).

## Cite only used declarations

A large development keeps what it no longer needs: earlier attempts, a second construction of the same object,
general versions next to specialised ones. The Yang–Mills source, too, contains alternative routes that the main
theorem does not use. A draft written while browsing such code can cite unused declarations as evidence; each such
citation must be replaced by a used one.

**Rule:** a declaration may be cited as establishing a statement only if `used = 1`. Before writing "the Lean
proves X by Y", look Y up (`SELECT used FROM nodes WHERE name = ?`), and when the reason for a dependency is
unclear, print a chain from a root (`closure.py --db graph.sqlite --why Y`). Writers and reviewers need read-only
access to the database for this; a reviewer whose database queries are blocked must say so in the report.

## Comparing with the authors' usage record

Some releases list the declarations their verification reached. When they do, compare: it is the one independent
check of the extraction that is cheap. `compare_usage.py` does it in four steps.

1. **Select the rows.** Keep what the record counts as used (in the Yang–Mills record, a `status` column with the
   values `used`, `headline` and `outside`: `--filter status=used,headline`).
2. **Attribute to owners** with the graph's own rule (the `aux` table, then the auxiliary and private-name patterns
   stored in `meta`): the record lists constants, auxiliaries included. The Yang–Mills record listed 100,151 used
   constants plus 17 headline constants; attributed to owners, 74,115 declarations.
3. **Compare the sets.** The Yang–Mills closure had 74,093 declarations; the intersection 74,079; 14 were only in
   the closure and 36 only in the record. The symmetric difference is 50 although the totals differ by 22: always
   report both sides, not the difference of totals.
4. **Explain every class of difference**, with examples:
   - constructors whose inductive type is in the closure: the record counts a constructor when the recursor is
     reached; the graph links an inductive type to its constructors only through references (36 in the
     Yang–Mills comparison);
   - declarations reached only through auxiliary constants (`direct = 0` on every edge into them from a used
     declaration): a shared `_proof_N`, `match_N` or `_simp_N` constant can carry a reference that the record
     attributes differently (14 in the Yang–Mills comparison);
   - names of the record that are not in the graph: metaprogramming constants, auxiliaries of library
     declarations, or a module left out of the extraction.

   A class you cannot explain is a finding: look for an extraction bug before publishing anything.

Write the result in one paragraph: the two counts, the intersection, both one-sided differences, the classes, and
the scope sentence: **this compares reached-name sets; it does not check individual edges, mathematical necessity,
or any English text.** Do not call the agreement a percentage of correctness.

## Without a usage record

Then nothing outside this pipeline checks the closure. Do three things, and report each as what it is:

1. **Spot-check chains.** Draw a random sample of used declarations
   (`SELECT name FROM nodes WHERE used = 1 ORDER BY random() LIMIT 20`), print a chain from a root to each
   (`closure.py --why`), and open every step of each chain in the source: each must be a real reference. Publish
   the sample, the chains and the result.
2. **Recompute the closure by a second route.** `ClosureCheck.lean` imports the root modules and walks the
   constants used in each type and value (`getUsedConstants`) through the project's modules:
   `lake env lean --run ClosureCheck.lean out.txt --import <root module> <roots>` (or `lean --run` with `LEAN_PATH`
   set to the build's library directories, where `lake` must not run), then
   `compare_usage.py --db graph.sqlite --record out.txt --no-header`, and explain every class of difference as
   above. It imports the whole development: run it alone. Both routes read the same compiled files: call the
   result **a cross-check of the extraction and the attribution, not an independent proof**.
3. **Check the main statement's names.** Every project declaration that the formal statement of the main theorem
   names (read from the source or the statement page) must have `used = 1`; one that does not means a missing
   edge.

## Counting scopes

Several counts look alike and are not. Publish a table that names each one, its number, and what it counts; the
Yang–Mills data dictionary had one ([L4](../../lean-to-manuscript/references/lessons-learned.md#l4)).

| Quantity | Yang–Mills value | Counts |
|---|---:|---|
| used rows | 74,171 | database rows with `used = 1`, including 78 excess rows for repeated names |
| used declarations | 74,093 | **distinct names** with `used = 1`: always `COUNT(DISTINCT name)` |
| record, attributed to owners | 74,115 | the authors' used and headline constants after attribution |
| kernel replay | 100,168 | project declarations replayed by the authors' checker: a different convention |
| allocation | 77,099 | names assigned to units, inherited from an earlier map; not the closure |
| attributed lines | 413,085 | source lines under the allocation's convention, not lines of the closure |

Rules: count distinct names; say which roots; never present an allocation or a line total as "declarations used by
the main theorem" unless it is exactly that; when an older graph is replaced, say which published numbers changed
and which did not.

## Replacing a text graph

When a compiled graph replaces a text graph, compare them before switching: node sets, closure flags, edges by part,
and links between units. In the Yang–Mills campaign some published links between units turned out to rest on
wrongly resolved names, and one real dependency between units (V.3 on II.1) appeared. Publish the changes with the
switch, in the changelog of whatever the graph feeds.
