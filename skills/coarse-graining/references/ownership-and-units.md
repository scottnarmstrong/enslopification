# Ownership, scales and units

From the closure of the main theorem to parts and units with an owner for every declaration. Lesson:
[L6](../../lean-to-manuscript/references/lessons-learned.md#l6).

## Roots

Use the roots of the closure (the authors' headline list, recorded in the graph's `roots` table). With several
roots, the dominator tree hangs under a virtual root joined to all of them, so material shared between two root
theorems belongs to neither. If the union of roots includes an alternative construction the main theorem does not
need, keep it as a root but give it its own unit, labelled as such; do not let it shape the main line.

## Ownership by the dominator tree

A declaration d **dominates** v if every chain of references from the roots to v passes through d: v is reached
only through d. Helpers reached only through one result are folded into it. `own_and_scale.py` computes the
dominator tree with the standard iterative algorithm (immediate dominators refined in reverse postorder until
nothing changes), then:

- **mass(v)** = lines of v plus lines of everything v dominates: the size of the proof v carries;
- at **scale M**, a node is **retained** if it is a root or a proof node (a theorem) with mass at least M; retained
  sets nest, so a ladder of scales gives views from fine to coarse;
- every other node is labelled from its users, users first: **private** to K when all its users lie in K's region
  (K and the nodes private to K), otherwise shared: **toolbox** for a proof node (or anything used only by toolbox
  material), **concept** for a definition or type used from several regions. Cycles are labelled as one block.

The region of a retained result is the result with its private helpers; its folded lines are what a reader of
that result must also read. Edges between regions are counted (all references, and those in statements), with a
transitive-reduction flag for drawing.

`own_and_scale.py` does not first fold fields, constructors, instances and short wrapper theorems into the
declarations they serve. A pipeline that folds them gets different counts at every scale: say which convention a
published ladder uses.

Read the ladder from the top: at 3,200 lines the retained results are the chapters of the proof; at 100 they are
its lemmas. A result that stays retained over a wide range of M is a natural unit boundary.

Line counts are source spans: implementation weight, not a measure of mathematical content. A definition-heavy
area weighs little in mass but can carry most of a statement's meaning; look at the concept layer separately.

## The toolbox

Material used from several regions is the development's toolbox: estimates, algebra, bookkeeping. In Yang–Mills
much of it was renormalization-group estimates. Group it, do not scatter it:

- first by source folder (authors usually file tools together), then
- by similarity of use (two tools used by the same results belong together), and by the words of file titles and
  docstrings;
- a toolbox group that still depends on a retained main-line result is a corollary of that result, not a tool:
  move it next to the result.

Automatic community detection gives one candidate partition, not structure. When the graph changes (for example,
when a text graph is replaced by the compiled one), an automatic partition can change almost completely while the
coarse shape (a large toolbox, the assembly on top) stays. Never publish automatic pieces as the structure of the
proof.

## Cutting units

A unit is a mathematically coherent piece that one outline can explain, typically 4,000 to 40,000 lines (Yang–Mills:
32 units from 232 to about 49,000 lines; the ultraviolet construction alone took 16).

1. **Start from the retained results at a coarse scale** (around M = 3,200) and from the toolbox groups.
2. **Cut along the mathematics:** one unit answers one question ("how is the stationary background field
   constructed and bounded?"). Write the question in the unit catalogue and show it on the index next to the
   unit's title.
3. **Respect dependency order where the mathematics allows,** so that each unit uses earlier ones. Where it does
   not (definitions needed before the part that explains them), say so on the architecture page.
4. **Reuse the authors' own decomposition.** Numbered work items, each one obligation proved in its own file, gave
   the Yang–Mills map a ready-made skeleton for three parts (about seventy items).
5. **Distrust folders and names.** About three quarters of the Yang–Mills code filed under "full volume" belongs to
   the ultraviolet construction; the infinite-volume argument proper is about 7,000 lines. Place each folder by its
   graph (who uses it, what it uses), not by its name.
6. **Give every used declaration exactly one unit** (`declaration-units.tsv`), by region where the dominator labels
   decide, by toolbox group otherwise; then run `unit_tables.py` and resolve every used declaration it reports
   without a unit.
7. **Allocation is not explanation.** A unit's declarations and the subject its outline explains can differ (a
   result can be explained in one unit and concluded in another). Say so in the data dictionary.

Grouping declarations into units can create apparent cycles between units (A references B and B references A at the
threshold) even though the declaration graph has none; `unit_tables.py` lists them. They are not circular proofs.

## Parts and interfaces

Group the units into parts that a reader can name (Yang–Mills: setting, data of the construction, ultraviolet
construction, infinite volume, phases and reconstruction, symmetry, identification, assembly). For each pair of
consecutive parts, write **what one hands to the next**: the short list of statements the later part uses.

The Yang–Mills ultraviolet construction hands the infinite-volume part five properties: the specification of the
Wilson family; a chessboard (reflection-positivity) bound, uniform in the volume, for every renormalized
observable; the same for difference quotients, so that correlation kernels at separated points are bounded
uniformly in the volume; convergence at each fixed volume as the spacing tends to zero; the same estimates for
corrected fields. Stating this interface made the order of the two limits, and which inputs each uses, visible
in a few lines.

Find interface statements with the graph: the declarations of the earlier part that the later part references,
ranked by how many declarations of the later part use them; then read them.

## The architecture page

One page: the parts in a table (what each does, its share of the lines), the interfaces, and a section on what does
not follow the order of the parts: definitions needed early (records of the whole construction, basic types),
code filed far from its mathematical home. It is level 3 of the published levels of detail (the main theorem; the
proof in one reading; the architecture; the units; the full proof), and it is the first page a writer reads.
