/-
ClosureCheck.lean: a second computation of the closure of the roots, by another route through the compiled files.

Run it with the toolchain that built the modules it imports.

Usage (where the imports resolve: inside the project through `lake env`, or with LEAN_PATH set):
  lake env lean --run ClosureCheck.lean OUT.txt --import Root.Module [--import ...] [--module-prefix P ...] ROOT...
  LEAN_PATH=build/lib/lean lean +leanprover/lean4:v4.32.0 --run ClosureCheck.lean out.txt --import Tiny.Basic Tiny.main

It imports the given modules (and everything they import), then walks from the roots along the constants that
occur in each constant's type and value (`Expr.getUsedConstants`), through every constant declared in a project
module, and writes the names reached, one per line, sorted: raw names, with generated auxiliaries and private
prefixes, as a published usage record would list them. Project modules: a module named P given with
--module-prefix, or below it (P.A.B); by default P is the first component of each --import module.

Compare with the graph:   compare_usage.py --db graph.sqlite --record OUT.txt --no-header

What it is: a cross-check of the extraction (Extract.lean, build_graph_db.py) and of the attribution of auxiliary
constants, through Lean's own import instead of a direct read of each module's data. What it is not: an
independent check of the proof or of the compiled files, since both routes read the same .olean files.
Memory: as much as importing the root modules (several GB for a development built on Mathlib): run it alone.
Exit codes: 0 written, 2 usage error or a root not found.
-/
import Lean
open Lean

def usage : String :=
  "usage: lean --run ClosureCheck.lean OUT.txt --import MODULE [--import ...] [--module-prefix P ...] ROOT [ROOT ...]"

structure Opts where
  out      : String := ""
  imports  : Array Name := #[]
  prefixes : Array Name := #[]
  roots    : Array Name := #[]

partial def parseArgs : List String → Opts → Except String Opts
  | [], o => .ok o
  | "--import" :: m :: rest, o => parseArgs rest { o with imports := o.imports.push m.toName }
  | "--module-prefix" :: p :: rest, o => parseArgs rest { o with prefixes := o.prefixes.push p.toName }
  | a :: rest, o =>
    if a.startsWith "--" then .error s!"unknown option or missing value: {a}"
    else if o.out.isEmpty then parseArgs rest { o with out := a }
    else parseArgs rest { o with roots := o.roots.push a.toName }

/-- Constants occurring in the type and in the value (proof term, definition body) of a constant. -/
def usedConsts (ci : ConstantInfo) : Array Name :=
  let v := match ci with
    | .defnInfo d   => d.value.getUsedConstants
    | .thmInfo t    => t.value.getUsedConstants
    | .opaqueInfo o => o.value.getUsedConstants
    | _             => #[]
  ci.type.getUsedConstants ++ v

unsafe def main (args : List String) : IO UInt32 := do
  let o ← match parseArgs args {} with
    | .ok o => pure o
    | .error e => IO.eprintln s!"ClosureCheck.lean: {e}\n{usage}"; return 2
  if o.out.isEmpty || o.imports.isEmpty || o.roots.isEmpty then
    IO.eprintln usage
    return 2
  let prefixes := if o.prefixes.isEmpty then o.imports.map (·.getRoot) else o.prefixes
  initSearchPath (← findSysroot)
  let env ← importModules (o.imports.map fun m => { module := m }) {}
  let modNames := env.allImportedModuleNames
  let inProject (n : Name) : Bool :=
    match env.getModuleIdxFor? n with
    | some idx => prefixes.any (·.isPrefixOf (modNames[idx.toNat]!))
    | none     => false
  let projectModules := modNames.filter fun m => prefixes.any (·.isPrefixOf m)
  for r in o.roots do
    unless inProject r do
      IO.eprintln s!"ClosureCheck.lean: root {r} is not a constant of a project module (prefixes {prefixes})"
      return 2
  -- breadth-first walk through project constants only: a library constant cannot use a project one
  let mut seen : NameSet := {}
  let mut todo : Array Name := #[]
  for r in o.roots do
    unless seen.contains r do
      seen := seen.insert r
      todo := todo.push r
  let mut i := 0
  while h : i < todo.size do
    let n := todo[i]
    i := i + 1
    if let some ci := env.find? n then
      for u in usedConsts ci do
        if !seen.contains u && inProject u then
          seen := seen.insert u
          todo := todo.push u
  let names := (todo.map toString).qsort (· < ·)
  IO.FS.writeFile o.out (String.join (names.toList.map (· ++ "\n")))
  IO.eprintln s!"ClosureCheck: {names.size} project constants reached from {o.roots.size} roots \
    ({projectModules.size} project modules among {modNames.size} imported) -> {o.out}"
  return 0
