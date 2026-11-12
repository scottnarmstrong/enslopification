# Published data tables and their counting scopes

The map is published with three tab-separated tables and a data dictionary. Numbers that look alike count
different things; the dictionary says which. Lesson: [L4](../../lean-to-manuscript/references/lessons-learned.md#l4).

## The tables

**`units.tsv`**, one row per unit (`unit_tables.py`):

| Column | Meaning |
|---|---|
| `unit`, `part`, `title` | identifier, part, reader-facing title |
| `lines` | distinct source lines covered by the spans of the unit's declarations (the union, per file) |
| `declarations` | assigned declarations with a positive span (line-counted) |
| `names`, `used_names` | assigned names; those in the closure |
| `key_statements` | rows of `key-statements.tsv` in this unit |
| `builds_on`, `used_by` | units this unit references, and that reference it, with at least the threshold of distinct declaration pairs (default 25), by decreasing count |

**`declaration-units.tsv`**: `declaration`, `unit`; one row per assigned name, each name once. Optionally a
`canonical` column when names are folded into canonical declarations; folded names stay listed and add nothing to
lines or counts (`unit_tables.py --canonical-col canonical`).

**`key-statements.tsv`**: `number` (a generated identifier such as `K-<unit>.<position>`, distinct from outline
proposition numbers), `unit`, `lean_name`, `link` (pinned file and lines), `importance` (the label rule of
[key-statements.md](key-statements.md)), `summary` (one sentence; not the full statement).

All three: UTF-8, one header row, no thousands separators, `;` between unit identifiers, an empty field for "none".

## Counting scopes

Publish a census with the tables. `unit_tables.py` prints one (`scopes.txt`); the Yang–Mills census:

| Quantity | Count | What it counts |
|---|---:|---|
| used rows | 74,171 | database rows with `used = 1` (78 names were repeated) |
| used declarations | 74,093 | distinct names with `used = 1`: the closure of the 17 roots |
| allocation | 77,099 | names in `declaration-units.tsv`, inherited from an earlier map |
| allocation ∩ closure | 73,669 | assigned and used |
| assigned, not used | 3,430 | allocation outside the closure |
| used, no unit | 424 | closure outside the allocation |
| attributed lines | 413,085 | `units.tsv.lines`, under the allocation's line convention |
| key statements | 989 | rows of `key-statements.tsv` |

Rules that follow from it:

- **Distinct names, not rows.** `COUNT(DISTINCT name)`; a database that merged sources can repeat names.
- **Allocation is not closure.** "77,099 declarations used by the main theorem" would be false: the allocation was
  inherited from an earlier graph and includes declarations outside the closure, and misses some inside it. Say
  which the published numbers are, and list the gaps (`unassigned.tsv`).
- **Union, not sum, for lines.** Spans nest (a field inside its structure); summing them overcounts.
  `unit_tables.py --scope used` takes the union of the spans of used declarations, as the Yang–Mills provenance page
  did for its size comparison (410,299 lines within the units); the `lines` column of the published unit table
  (413,085 in all) follows the allocation's convention instead. Say which convention each published total uses.
  Spans include statements, proofs and comment lines inside them: implementation weight, not proof-only lines.
- **Overlapping closures.** With several roots the closure is a union; sizes of separate closures do not add.
- **Thresholds hide pairs.** An empty `builds_on` means no pair reached the threshold, not independence; publish
  the threshold and the full pair table.
- **References are not prerequisites.** A code reference between units can be a shared definition, a record field
  or an alternative construction: not a reading order and not a minimal proof.

## Versions and citation

Give the tables a data version (date and revision) separate from the source commit and from outline statuses, and
change it when any count changes. A durable citation of a key statement names the data version, the full Lean
name, the source commit and the line link; generated numbers such as `K-III.9.4` keep their meaning only while the
selection order is unchanged.

When the graph is replaced (for example, from source text to compiled files), rerun the tables, and say in the
changelog which columns changed (in Yang–Mills only `builds_on` and `used_by` did) and which numbers were kept from
the earlier map and why.
