# Schema and queries

The database written by `build_graph_db.py` (and updated by `closure.py`), and the SQL for the questions that
writers, reviewers and the orchestrator ask. Open it read-only when you only look things up:
`sqlite3 'file:graph.sqlite?mode=ro'`.

## Schema

```sql
CREATE TABLE meta(key TEXT PRIMARY KEY, value TEXT);      -- commit, Lean version, counts, rules, closure roots
CREATE TABLE nodes(
  name TEXT PRIMARY KEY,   -- full Lean name (private prefix removed unless it would collide)
  kind TEXT,               -- theorem, def, abbrev, instance, structure, inductive, ctor, field, opaque, axiom
  module TEXT, path TEXT,  -- module A.B.C and its source file A/B/C.lean (with --path-prefix)
  line INTEGER,            -- line of the declaration's name (a docstring above it is not counted)
  line_end INTEGER,        -- last line of the declaration
  lines INTEGER,           -- line_end - line + 1: statement, proof and comment lines inside the span
  doc TEXT,                -- docstring
  used INTEGER,            -- 1 if in the closure of the roots (closure.py)
  n_aux INTEGER,           -- live auxiliary constants attributed to this declaration
  sorry INTEGER,           -- 1 if it or one of its auxiliaries uses sorryAx
  parent TEXT);            -- inductive type of a constructor, structure of a field
CREATE TABLE edges(
  src TEXT, dst TEXT,      -- src uses dst; both are nodes; one row per pair
  part TEXT,               -- statement (type only), proof (value or auxiliaries only), both
  direct INTEGER,          -- 0 if every reference came through auxiliary constants
  PRIMARY KEY (src, dst));
CREATE TABLE aux(name TEXT PRIMARY KEY, short TEXT, owner TEXT, status TEXT);  -- live, dead, expanded, meta
CREATE TABLE roots(name TEXT PRIMARY KEY);
CREATE TABLE ext_edges(src TEXT, dst TEXT, part TEXT);    -- only with --keep-external
```

Other databases (a graph from source text, or a merged one) may repeat a name in several rows. Count with
`COUNT(DISTINCT name)`, never `COUNT(*)`, unless you mean rows.

## Size of the closure

```sql
SELECT COUNT(DISTINCT name) FROM nodes WHERE used = 1;
SELECT kind, COUNT(*) FROM nodes WHERE used = 1 GROUP BY kind ORDER BY 2 DESC;
SELECT key, value FROM meta WHERE key LIKE 'closure%';     -- roots, their hash, parts followed, size
```

## What X uses, and what uses X

```sql
-- what X uses (statement references first), with whether each target is in the closure
SELECT e.dst, e.part, n.kind, n.used FROM edges e JOIN nodes n ON n.name = e.dst
 WHERE e.src = :x ORDER BY e.part, e.dst;
-- what the statement of X mentions directly (all it needs, through definitions: closure.py --statement-closure)
SELECT dst FROM edges WHERE src = :x AND part IN ('statement', 'both');
-- used declarations that use X
SELECT e.src, e.part FROM edges e JOIN nodes n ON n.name = e.src WHERE e.dst = :x AND n.used = 1;
```

In the `sqlite3` shell, replace `:x` by a quoted name, or use `.param set :x 'Full.Name'`.

## Lookups restricted to the closure

```sql
-- find a declaration by a fragment of its name, among used ones only, with its location
SELECT name, kind, path || ':' || line FROM nodes WHERE used = 1 AND name LIKE '%Casimir%' ORDER BY name;
-- is Y in the closure? (check before citing Y as evidence)
SELECT name, used, kind, path, line, line_end FROM nodes WHERE name = :y;
```

For a chain of references from a root to Y, run `closure.py --db graph.sqlite --why Y` (a breadth-first search).
The SQL below enumerates paths and is only usable with a small depth limit:

```sql
WITH RECURSIVE p(name, chain, depth) AS (
  SELECT name, name, 0 FROM roots
  UNION ALL
  SELECT e.dst, p.chain || ' -> ' || e.dst, p.depth + 1 FROM p JOIN edges e ON e.src = p.name
   WHERE p.depth < 6 AND instr(p.chain, e.dst) = 0)
SELECT chain FROM p WHERE name = :y ORDER BY depth LIMIT 1;
```

## Sizes and rankings

```sql
-- the longest used proofs (by source span), with a path#L anchor
SELECT name, lines, path || '#L' || line || '-L' || line_end FROM nodes
 WHERE used = 1 AND kind = 'theorem' ORDER BY lines DESC LIMIT 20;
-- the most used declarations inside the closure (candidates for a glossary of the code's names)
SELECT e.dst, COUNT(*) AS users FROM edges e
  JOIN nodes s ON s.name = e.src JOIN nodes d ON d.name = e.dst
 WHERE s.used = 1 AND d.used = 1 GROUP BY e.dst ORDER BY users DESC LIMIT 50;
-- the closure of one declaration: size and lines
WITH RECURSIVE c(name) AS (SELECT :x UNION SELECT e.dst FROM edges e JOIN c ON e.src = c.name)
SELECT COUNT(*), SUM(n.lines) FROM c JOIN nodes n USING (name);
-- used declarations and lines by top-level folder
SELECT substr(path, 1, instr(path || '/', '/') - 1) AS top, COUNT(*), SUM(lines)
  FROM nodes WHERE used = 1 GROUP BY top ORDER BY 3 DESC;
-- unused declarations by module: alternative routes, earlier attempts, tooling
SELECT module, COUNT(*) FROM nodes WHERE used = 0 GROUP BY module ORDER BY 2 DESC LIMIT 30;
```

`lines` is the span of one declaration. Spans of nested declarations (a field inside its structure) overlap: to
total the lines of a set, take the union of spans per file, as `unit_tables.py` of the coarse-graining skill
does, not the sum.

## Cycles

The Lean kernel accepts no circular proofs, but the graph has small cycles: mutual definitions, and pairs created
by attribution (a constructor's type mentions its inductive type, and the recursor attributed to the type mentions
the constructor). Find them before any computation that assumes a DAG.

```sql
-- pairs that use each other
SELECT a.src, a.dst, a.part, b.part FROM edges a JOIN edges b ON a.src = b.dst AND a.dst = b.src
 WHERE a.src < a.dst;
-- cycles through X of length at most 4
WITH RECURSIVE w(name, depth, chain) AS (
  SELECT dst, 1, :x || ' -> ' || dst FROM edges WHERE src = :x
  UNION ALL
  SELECT e.dst, w.depth + 1, w.chain || ' -> ' || e.dst FROM w JOIN edges e ON e.src = w.name
   WHERE w.depth < 4 AND w.name <> :x)
SELECT chain FROM w WHERE name = :x;
```

For all strongly connected components at once, use a program: `own_and_scale.py` of the coarse-graining skill
condenses them before labelling.

## Auxiliaries, metadata, external references

```sql
SELECT name, status FROM aux WHERE owner = :x;            -- generated constants attributed to X
SELECT status, COUNT(*) FROM aux GROUP BY status;         -- live, dead, expanded, meta
SELECT key, value FROM meta ORDER BY key;                 -- commit, Lean version, counts, attribution rules
-- with --keep-external: library results used by the closure, most used first
SELECT x.dst, COUNT(*) FROM ext_edges x JOIN nodes n ON n.name = x.src
 WHERE n.used = 1 GROUP BY x.dst ORDER BY 2 DESC LIMIT 50;
```
