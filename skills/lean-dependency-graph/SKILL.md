---
name: lean-dependency-graph
description: Compile a Lean development (or load its released build), extract every declaration and reference from the compiled .olean files into a SQLite graph with statement and proof edges, mark the closure of the headline theorems, and compare it with any usage record the authors publish. Use before mapping, outlining or writing about a large Lean proof, when releasing a compiled build for readers, or whenever someone needs to know which declarations a theorem rests on.
---

# Lean dependency graph

Turn a completed Lean development into a database of its declarations and of the references between them, read
from the compiled files at a pinned commit, with the closure of the main theorem marked. Every later step of a
manuscript campaign (units, outlines, statements, reviews against the Lean) looks things up in it.

**Read the graph from the compiled files, never from the source text, and cite as evidence only declarations in
the closure of the main theorem (`used = 1`).** A graph parsed from source text was wrong in bulk
([L3](../lean-to-manuscript/references/lessons-learned.md#l3)); the code contains routes that the main theorem
does not use ([L5](../lean-to-manuscript/references/lessons-learned.md#l5)).

## When to use

- At the start of a campaign that turns a Lean development into a paper, an outline or a map.
- When a reader, reviewer or writer asks what a theorem depends on, or whether a declaration is used.
- When releasing a compiled build so that others can load the development without recompiling it.

Not for: a dependency graph of a *prose* proof whose nodes are anchored to Lean declarations (that is
`build-proof-dependency-graph`, which does something different); auditing one declaration against a source
(`lean-statement-audit`); dividing the closure into parts and units ([coarse-graining](../coarse-graining/SKILL.md)).

## Procedure

1. **Pin the source.** Record the commit id (never a branch name), the toolchain in `lean-toolchain` and the
   dependency revisions in `lake-manifest.json`. *Deliverable:* a status file with these three facts.
2. **Get a compiled build, without rebuilding what a cache provides.** Fetch dependencies from the official
   cache (`lake exe cache get` for Mathlib), then build only the headline targets, once, throttled (`nice`,
   a CPU limit), measured with `/usr/bin/time -v`, with every log written outside the checkout; or load a released
   build and check its checksums (recipe in [build-and-release.md](references/build-and-release.md)). One heavy
   job at a time on a shared machine ([L34](../lean-to-manuscript/references/lessons-learned.md#l34)): a
   development of about one million lines, such as the Yang–Mills one, takes hours to compile.
   *Deliverable:* build log with wall time and peak memory; all targets up to date.
3. **Release the build for readers (optional).** `package_build.sh`: archive, checksums, parts under the 2 GiB
   hosting limit, a test in a fresh clone with `lake build --no-build`, and release notes that say what loading
   it does and does not establish ([L33](../lean-to-manuscript/references/lessons-learned.md#l33)).
   *Deliverable:* parts, `SHA256SUMS`, a `STATUS` that contains `TEST_PASS` and ends with `DONE`, release notes.
4. **Extract.** `extract.py` runs `Extract.lean` on chunks of modules (`--chunk-size`), one Lean process at a
   time, resumably. It reads each `.olean` directly: no `lake` call, no imports, so it can run against a
   checkout you must not modify. *Deliverable:* raw chunk files and per-chunk logs with time and memory.
5. **Build the database.** `build_graph_db.py` attributes generated auxiliaries to their owners, drops dead ones,
   separates statement from proof references, and records ranges, docstrings and kinds. A name declared in two
   modules stops the build: exclude the module the roots do not import (a challenge file with a placeholder
   declares the same headline name as the solution; [L36](../lean-to-manuscript/references/lessons-learned.md#l36)).
   *Deliverable:* `graph.sqlite` with its `meta` table.
6. **Mark the closure.** Take the roots verbatim from the authors' headline list; `closure.py` sets `used = 1` on
   the union of their closures and records the roots. It fails if a used declaration relies on `sorry`.
   `closure.py --statement-closure` lists, without writing, what is needed to *state* the roots.
   *Deliverable:* closure size by kind, the root list with its hash, an exported used list.
7. **Compare with the authors' record.** If the release lists the declarations it uses, `compare_usage.py`
   attributes its names to owners and classifies every difference; explain each class in writing
   ([L4](../lean-to-manuscript/references/lessons-learned.md#l4)). In the Yang–Mills campaign the closure had
   74,093 declarations, the record 74,115 after attribution, and they differed by 50 (36 constructors the record
   reaches through recursors, 14 small definitions reached through shared auxiliaries). Without a record:
   spot-check chains of a random sample (`closure.py --why`), recompute the closure by a second route
   (`ClosureCheck.lean`: a cross-check through the same compiled files, not an independent proof), and check that
   every declaration the main statement names has `used = 1`. *Deliverable:* a comparison note with counts,
   classes, examples and the scope sentence.
8. **Hand over.** Give writers and reviewers read-only access to the database, the query recipes, and the rule:
   before writing "the Lean proves X", check that the declaration has `used = 1`. Label any graph read from
   source text as such. *Deliverable:* the database and a short README stating its counting scopes.

## References

- [build-and-release.md](references/build-and-release.md): compiling on a shared machine; loading a released
  build; releasing one with checksums, split parts and a fresh-clone test; what loading a build establishes.
- [extraction.md](references/extraction.md): what `Extract.lean` reads; statement and proof edges; attribution of
  auxiliary constants; why a source-text graph is not enough; the Yang–Mills counts.
- [closure-and-comparison.md](references/closure-and-comparison.md): roots, the statement closure, the `used = 1`
  rule, alternative routes, comparison with a usage record and what to do without one, counting scopes.
- [schema-and-queries.md](references/schema-and-queries.md): the SQLite schema and the SQL for common questions.

## Scripts

| Script | What it does | Assumes | Does not |
|---|---|---|---|
| `Extract.lean` | Reads one or more `.olean` files; writes declarations, type and value references, ranges, docstrings, tags | the toolchain that built the files, which must provide `readModuleDataParts` | load imports, run `lake`, or attribute auxiliaries (the next script does) |
| `extract.py` | Lists the build's modules, runs `Extract.lean` on chunks, one process at a time, resumable, `--dry-run` | a Lean command (`ENSLOP_LEAN_CMD`) | run two Lean processes at once |
| `build_graph_db.py` | Raw chunks to SQLite: owners of auxiliaries, liveness, statement/proof parts, kinds, ranges, `meta` | chunks from `Extract.lean` | decide which modules belong to the proof (use `--exclude-module`) |
| `closure.py` | Sets `used = 1` from the roots; `--why X` prints a chain from a root to X; `--statement-closure` lists what stating the roots needs | the roots are nodes | check proofs (only flags `sorryAx` users) |
| `compare_usage.py` | Compares the closure with a published usage record; classifies differences | a TSV or name list (header detected, or `--header`/`--no-header`) | check individual edges |
| `ClosureCheck.lean` | Recomputes the closure by importing the root modules and walking the constants each type and value uses; output for `compare_usage.py` | the imports resolve (`lake env`); memory to import the roots | check anything independently: it reads the same compiled files |
| `package_build.sh` | Archives a compiled Lake build, checksums, fresh-clone `--no-build` test, split parts; `--dry-run` | a clean checkout at the commit; `--out` outside it | recompile anything or verify proofs |

The SQL for common questions is in [schema-and-queries.md](references/schema-and-queries.md).

## What this establishes and what it does not

- **Establishes:** which project declarations are referenced, at a pinned commit, by the elaborated statements
  and proof terms of the compiled files, including references that Lean inserts (instances, coercions,
  projections, unfolded definitions); which declarations are reachable from the given roots; and, when the
  authors publish a usage record, how far the reachable set agrees with theirs, with each difference explained.
- **Does not establish:** that any proof is correct (the Lean kernel and the authors' verification programs do
  that); that a reference is a mathematical prerequisite (references include record fields, instances and
  definitions carried through a construction); that every individual edge is right (a comparison of reached
  sets tests coverage at the roots, not edges; `ClosureCheck.lean` reads the same compiled files, so its agreement
  is a cross-check, not an independent proof); anything about English explanations. Line spans measure
  implementation size, not mathematical ideas. Loading a released build and finding all targets up to date is
  not an independent rebuild, and a checksum checks the download, not the build.

## Related skills

[coarse-graining](../coarse-graining/SKILL.md) (parts, units, outlines from this graph),
[lean-to-manuscript](../lean-to-manuscript/SKILL.md) (the campaign),
[statement-spine](../statement-spine/SKILL.md) (cites only `used = 1` declarations),
[honest-publication](../honest-publication/SKILL.md) (how to word the comparison and the release);
`lean-public-release` and `lean-workflow` (preparing and building Lean repositories).
