/-
Extract.lean: declarations, reference edges, source ranges and docstrings from compiled Lean modules.

Run it with the toolchain that wrote the `.olean` files. The toolchain must provide `readModuleDataParts` (used for
module-system files); a toolchain without it cannot compile this file. The `ModuleData` layout and the names of
environment extensions can change between Lean versions: rerun tests/smoke_lean-dependency-graph.sh after a
toolchain change.

Usage (from any directory; no `lake build` is run and no imports are loaded):
  lean --run Extract.lean OUT.tsv Some.Module=path/to/Some/Module.olean ...
  lean +leanprover/lean4:v4.32.0 --run Extract.lean OUT.tsv @pairs.txt
  lake env lean --run Extract.lean OUT.tsv @pairs.txt          (inside the project, if that is allowed)
An argument `@FILE` reads `Module=path` pairs from FILE, one per line. The `extract.py` runner builds the
pairs and runs this program on chunks of modules, one process at a time.

Output: UTF-8, one record per line, five tab-separated columns `module, constant, record, a, b`:
  decl    a = kind: theorem, def, abbrev, opaque, axiom, inductive, ctor, rec, quot
  type    a = a constant used in the elaborated type          (a statement reference)
  value   a = a constant used in the value or proof term      (a proof reference; theorems, defs, opaques)
  range   a = line of the declaration's name, b = its last line (from the `Lean.declRangeExt` entries;
          a docstring or attributes above the name are not included)
  doc     a = the docstring, with backslash, tab, newline and carriage return escaped as \\ \t \n \r
  tag     a = instance (from `Lean.Meta.instanceExtension`) or projection (from `Lean.projectionFnInfoExt`)
  parent  a = the inductive type of a constructor
Names are printed with `Name.toString`; private names keep their `_private.<Module>.0.` prefix; generated
auxiliary constants (`_proof_1`, `match_1`, `eq_1`, `rec`, ...) are printed as they are: attributing them to
their owners is done afterwards by `build_graph_db.py`.

Module-system files: when `M.olean.private` exists next to `M.olean`, the three parts (`.olean`,
`.olean.server`, `.olean.private`) are read together and the private part is used; it holds all constants and
the range and docstring entries. A plain `.olean` (no module system) holds all of them itself. Check the
module-system branch on one module before a full run: its output must contain `range` and `doc` records.
-/
import Lean
open Lean

/-- Escape a docstring for one TSV field. -/
def escapeField (s : String) : String :=
  s.foldl (init := "") fun acc c =>
    if c == '\\' then acc ++ "\\\\"
    else if c == '\t' then acc ++ "\\t"
    else if c == '\n' then acc ++ "\\n"
    else if c == '\r' then acc ++ "\\r"
    else acc.push c

def kindOf : ConstantInfo → String
  | .axiomInfo _   => "axiom"
  | .defnInfo d    => match d.hints with
    | .abbrev => "abbrev"
    | _       => "def"
  | .thmInfo _     => "theorem"
  | .opaqueInfo _  => "opaque"
  | .quotInfo _    => "quot"
  | .inductInfo _  => "inductive"
  | .ctorInfo _    => "ctor"
  | .recInfo _     => "rec"

def emit (h : IO.FS.Stream) (m : String) (c : Name) (record a b : String) : IO Unit :=
  h.putStr s!"{m}\t{c}\t{record}\t{a}\t{b}\n"

def emitRefs (h : IO.FS.Stream) (m : String) (c : Name) (part : String) (e : Expr) : IO Unit := do
  for u in e.getUsedConstants do
    emit h m c part u.toString ""

/-- The entries that one persistent environment extension stored in this module. -/
def entriesOf (md : ModuleData) (ext : Name) : Array EnvExtensionEntry :=
  match md.entries.find? (fun p => p.1 == ext) with
  | some p => p.2
  | none   => #[]

unsafe def processModule (h : IO.FS.Stream) (m : String) (md : ModuleData) : IO Unit := do
  for ci in md.constants do
    let n := ci.name
    emit h m n "decl" (kindOf ci) ""
    emitRefs h m n "type" ci.type
    match ci with
    | .thmInfo t    => emitRefs h m n "value" t.value
    | .defnInfo d   => emitRefs h m n "value" d.value
    | .opaqueInfo o => emitRefs h m n "value" o.value
    | .ctorInfo c   => emit h m n "parent" c.induct.toString ""
    | _             => pure ()
  -- MapDeclarationExtension entries are pairs `Name × α`.
  for e in entriesOf md `Lean.declRangeExt do
    let (n, r) : Name × DeclarationRanges := unsafeCast e
    -- start: the line of the declaration's name (selection range), so a docstring above it is not counted;
    -- end: the last line of the whole declaration.
    emit h m n "range" (toString r.selectionRange.pos.line) (toString r.range.endPos.line)
  for e in entriesOf md `Lean.docStringExt do
    let (n, d) : Name × String := unsafeCast e
    emit h m n "doc" (escapeField d) ""
  for e in entriesOf md `Lean.projectionFnInfoExt do
    let (n, _) : Name × ProjectionFunctionInfo := unsafeCast e
    emit h m n "tag" "projection" ""
  -- A scoped extension stores `ScopedEnvExtension.Entry α`; for instances α = `Meta.InstanceEntry`.
  for e in entriesOf md `Lean.Meta.instanceExtension do
    let ent : ScopedEnvExtension.Entry Meta.InstanceEntry := unsafeCast e
    let ie := match ent with
      | .global x   => x
      | .scoped _ x => x
    if let some n := ie.globalName? then
      emit h m n "tag" "instance" ""

/-- Expand `@FILE` arguments into the `Module=path` pairs listed in FILE. -/
def expandArgs (args : List String) : IO (Array String) := do
  let mut out := #[]
  for a in args do
    if a.startsWith "@" then
      let file : System.FilePath := toString (a.drop 1)
      for l in (← IO.FS.lines file) do
        if l.any (fun c => !c.isWhitespace) then out := out.push l
    else
      out := out.push a
  return out

unsafe def main (args : List String) : IO UInt32 := do
  match args with
  | [] =>
    IO.eprintln "usage: lean --run Extract.lean OUT.tsv Module=path.olean ... | @pairs.txt"
    return 2
  | outPath :: rest =>
    let pairs ← expandArgs rest
    let handle ← IO.FS.Handle.mk outPath .write
    let h := IO.FS.Stream.ofHandle handle
    let mut n := 0
    for a in pairs do
      match a.splitOn "=" with
      | [m, p] =>
        let priv : System.FilePath := p ++ ".private"
        if ← priv.pathExists then
          let parts ← readModuleDataParts #[p, p ++ ".server", priv]
          match parts.back? with
          | some (md, _) => processModule h m md
          | none => pure ()
          for (_, region) in parts.reverse do region.free
        else
          let (md, region) ← readModuleData p
          processModule h m md
          region.free
        n := n + 1
      | _ =>
        IO.eprintln s!"Extract.lean: ignoring argument without a single '=': {a}"
    h.flush
    IO.eprintln s!"Extract.lean: {n} modules written to {outPath}"
    return 0
