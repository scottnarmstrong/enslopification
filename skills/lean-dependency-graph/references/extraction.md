# Extracting declarations and references from compiled files

How `Extract.lean`, `extract.py` and `build_graph_db.py` turn a compiled build into the graph, what each choice is
for, and the counts from the Yang–Mills campaign. Lessons:
[L3](../../lean-to-manuscript/references/lessons-learned.md#l3),
[L34](../../lean-to-manuscript/references/lessons-learned.md#l34).

## Why not the source text

Before compiled files were available, the Yang–Mills graph was parsed from the source text: 0.96 million
references, of which about 57,000 resolved to the wrong declaration (heuristic resolution of short and dotted
names). The graph read from the compiled files had 2.26 million references; 1.36 million of them were missing from
the text graph, nearly all of them implicit: names made available by section variables and `open`, definitions
and abbreviations unfolded by elaboration or automation, structure projections, constructors and coercions,
instances found by type-class search. In the other direction, a text graph also holds references that the
compiled files do not have: mentions that elaboration eliminated (an unused `simp` argument, a dead term) and
false resolutions.

The consequences reached the published map: one dependency between units was missing, and several published links
between units rested on wrongly resolved names. **If only a text graph is available, label it as such** and treat
unit-level conclusions as provisional.

## What Extract.lean reads

`Extract.lean` calls `readModuleData` on each `.olean`: the module's constants (name, kind, elaborated type, value)
and the entries that persistent environment extensions stored in it. It loads no imports, so it needs neither
`LEAN_PATH` nor the dependencies, and it never runs `lake`. It must run with the toolchain that wrote the files,
and that toolchain must provide `readModuleDataParts`, without which the file does not compile.

| Record | Source in the module data | Meaning |
|---|---|---|
| `decl` | `constants` | name and kind (theorem, def, abbrev, opaque, axiom, inductive, ctor, rec, quot) |
| `type` | `ConstantInfo.type` | a constant used in the elaborated statement |
| `value` | value of a theorem, definition or opaque | a constant used in the proof term or definition body |
| `range` | `Lean.declRangeExt` entries (`Name × DeclarationRanges`) | line of the declaration's name, last line |
| `doc` | `Lean.docStringExt` entries (`Name × String`) | the docstring, escaped |
| `tag` | `Lean.Meta.instanceExtension`, `Lean.projectionFnInfoExt` | instance, projection |
| `parent` | constructor info | the inductive type of a constructor |

The range starts at the line of the declaration's name, so a docstring above it is not counted and the link
`#L<line>-L<end>` matches what a reader expects; the end is the last line of the declaration. A plain `.olean`
holds all these entries. With the module system, the range and docstring entries are not in the exported part:
when `M.olean.private` exists, `Extract.lean` reads `M.olean`, `M.olean.server` and `M.olean.private` together and
uses the private part (check this branch on one module before a full run: `nodes_with_range` must count its
declarations). If a future Lean version renames an extension, the ranges or docstrings disappear from the output
(the build reports `nodes_with_range` in `meta`); the fallback is to take ranges from the `.ilean` files or from
the source text, and to say which.

## Statement and proof references

A reference in the elaborated type of a declaration is a **statement** reference; a reference in its value is a
**proof** reference (for a definition, its body). References made by an auxiliary constant belong to its owner
and count as proof references, whatever part of the auxiliary they come from. A pair of declarations gets
`part = both` when it has both kinds.

Use the split when it matters: the objects needed to *state* a theorem are its statement closure
(`closure.py --statement-closure`), much smaller than everything its proof uses. Since the body of a definition is
recorded as proof references, the statement closure follows those for definitions; following statement references
alone (`--parts statement,both`) misses a definition used only inside another definition's body.

## Chunks, one process at a time

`extract.py` lists the `.olean` files under the build's library directory, splits them into chunks of
`--chunk-size` modules and runs one Lean process per chunk, sequentially, at low priority. A finished chunk is never
redone; a failed one leaves a `.part` file and a log. Most of a chunk's peak memory is the Lean runtime itself, so
larger chunks cost little more than small ones; never run chunks in parallel on a shared machine.

## Attribution of auxiliary constants

Lean generates many constants that nobody wrote. `build_graph_db.py` attributes each to the declaration that owns
it by stripping auxiliary name components until a real declaration remains:

| Family | Examples | Owner |
|---|---|---|
| abstracted proofs | `foo._proof_3`, `foo.proof_1`, `foo._simp_1_2`, `foo._abel_1` | `foo` |
| pattern matching | `foo.match_1`, `foo.match_1.splitter`, `foo.match_1.eq_2` | `foo` |
| equation lemmas | `foo.eq_1`, `foo.eq_def`, `foo.eq_unfold` | `foo` |
| recursion | `foo._unary`, `foo._sunfold`, `foo.induct`, `foo._unsafe_rec` | `foo` |
| inductive types | `Foo.rec`, `Foo.casesOn`, `Foo.below`, `Foo.noConfusion`, `Foo._sizeOf_1` | `Foo` |
| constructor lemmas | `Foo.mk.injEq`, `Foo.mk.inj`, `Foo.mk.sizeOf_spec` | `Foo.mk` |
| private names | `_private.A.B.0.foo` | `foo` (kept in full if the short name collides) |

Further rules:

- **A constant with a source range is real**, whatever its name: a lemma that a person named `inj` keeps its node.
- **Dead auxiliaries are dropped.** Lean generates equation lemmas, recursors and the like whether or not they are
  used; an auxiliary counts only if a real declaration reaches it through references.
- **Auxiliaries without a project owner are expanded.** An equation lemma of a library definition can be generated
  inside a project module when a project proof first needs it; its users inherit its references.
- **Metaprogramming is set apart.** Parsers, macros, unexpanders and elaborators (their type mentions
  `Lean.ParserDescr`, `Lean.Macro` and similar) are not mathematics; they are dropped unless `--keep-meta`.
- **Kinds.** An instance is tagged `instance`, a projection `field`, an inductive type with projections
  `structure`, a definition with abbreviation hints `abbrev`. Constructors are nodes of their own; an inductive type
  does not reference its constructors, so a constructor enters the closure only when something uses it (or its
  recursor) — `--link-ctors` adds an edge from each inductive type to its constructors if you prefer to count them
  with the type. Record the choice: it changes the comparison with a usage record.
- **A name declared twice stops the build.** A reference challenge file often declares the headline theorem with
  a placeholder proof, and the solution declares the same name; the Yang–Mills build contained both. Exclude the
  module the roots do not import (`--exclude-module '^Challenge$'`); `nodes.sorry` marks any declaration whose
  proof still uses `sorryAx`.

In the Yang–Mills build, after attribution, the closure of the 17 headline results had 74,093 declarations, while
the authors' record listed 100,151 used constants (plus the 17 headline constants) that collapse to 74,115 owners.

## Checks after building

- Read the `meta` table: constants read, nodes with ranges, live and dead auxiliaries, expanded auxiliaries,
  metaprogramming constants dropped, duplicates, edges by part. Explain any count that looks wrong.
- Open three declarations you know (a theorem, a structure, an instance) in the source and compare their edges
  with what the source mentions; expect more edges than names written (implicit references), not fewer.
- Look at the real declarations without a range (`SELECT name FROM nodes WHERE line IS NULL`): some are
  generated on purpose (a derived instance, a lemma made by an attribute); others are auxiliaries whose name
  pattern is missing. Add a missing pattern with `--extra-aux` and rebuild.
