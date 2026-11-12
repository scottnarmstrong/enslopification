# Phases of the campaign

Each phase lists its inputs, what it delivers, how it is checked, and the failure to watch. Times and sizes are those
of the Yang–Mills campaign (about one million lines of Lean in 9,477 files; see the
[worked example](worked-example.md)); use them to plan, not as targets.

## 0. Brief

- **Inputs:** the development at a pinned commit; its README and verification record (kernel replay, axioms,
  headline results); any usage record or informal notes the authors published; earlier campaigns' lessons.
- **Do:** read the top-level statement and the verification programs; list the headline results; measure the
  development (files, lines, imports); propose the decisions of [author decisions](author-decisions.md).
- **Deliver:** `BRIEF.md`, decisions only, each with its date and who approved it (progress lives in the register
  and the morning list, never in the brief); and a first **statement page**, `statement.md`: the formal statement
  verbatim, a commentary in words, the full statement in ordinary mathematics compared definition by definition
  with the Lean, and explicit nonclaims (format: `honest-publication`, `assets/statement-page.template.md`). The
  outline writers and the spine drafters read it; it is published when the author decides.
- **Yang–Mills:** the statement page was the first page published, before any outline.
- **Watch:** an unpinned source. Every later link, count and correspondence row refers to one commit.

## 1. Map the Lean

- **Inputs:** a compiled build (the official dependency cache plus one throttled build, or a build the authors
  release); the headline roots.
- **Do:** extract declarations and references from the compiled files, attribute auxiliary constants to their
  owners, mark the closure of the roots, compare it with the authors' usage record, and explain every difference
  ([`lean-dependency-graph`](../../lean-dependency-graph/SKILL.md)). Release the compiled build for readers if
  the author agrees.
- **Deliver:** the SQLite graph; a report with the closure size, the comparison and its limits.
- **Check:** closure against the authors' record ([L4](lessons-learned.md#l4)).
- **Watch:** text-derived graphs ([L3](lessons-learned.md#l3)); unused alternative routes cited as evidence
  ([L5](lessons-learned.md#l5)).
- **Yang–Mills:** 2.26 million references; 74,093 declarations in the closure of seventeen roots, within 50 of the
  authors' record; the compiled graph replaced a text graph on the day the source was released.

## 2. Coarse-grain and outline

- **Inputs:** the graph; the statement of the main theorem; any decomposition the authors made explicit (numbered
  obligations, named stages).
- **Do:** ownership by dominators, a ladder of scales, shared machinery grouped, parts and units cut along the
  mathematics, key statements selected by two independent readers, unit outlines written, compared with the
  Lean and edited, then condensed to a measured length; a one-reading summary, an architecture page, a glossary of
  the code's names, a provenance analysis, data tables with stated counting scopes
  ([`coarse-graining`](../../coarse-graining/SKILL.md)).
- **Deliver:** the map at several levels of detail, every statement linked to exact lines at the pinned commit.
- **Check:** every numbered outline statement compared with its declaration by a reviewer other than its writer;
  outline length measured on landing ([L7](lessons-learned.md#l7)).
- **Gate:** ★ the author approves the architecture: parts, units, and the interfaces between parts.
- **Yang–Mills:** 8 parts, 32 units, 989 key statements; outlines drafted, compared with the Lean and edited for all
  32 units, then condensed to 3–10 pages each, with the detailed notes kept separately.

## 3. Freeze the spine

- **Inputs:** the main statement, the architecture, the outlines (as maps), the graph (for `used = 1` lookups).
- **Do:** two independent spine drafts; a reconciliation listing structural decisions; natural-form statements; a
  clause map from every clause of the formal contracts to its new home; measured typeset size
  ([`statement-spine`](../../statement-spine/SKILL.md)).
- **Deliver:** the frozen spine, its clause map, the list of later lemmas that carry the side conditions, a drift
  log.
- **Check:** an independent clause-map review; the shape checker on every statement ([L9](lessons-learned.md#l9),
  [L10](lessons-learned.md#l10)).
- **Gate:** ★ the author approves the spine and its decisions.
- **Yang–Mills:** the first statements were faithful and Lean-shaped and were rejected; the natural form has
  fifteen principal statements.

## 4. Fix the standards

- **Do:** choose an exemplar paper whose exposition to copy (patterns, not statements); write `STYLE.md` and
  `DETAIL-STANDARD.md` for a named reader; build the terminology table; install the shape, vocabulary and compile
  checks ([`exposition-standards`](../../exposition-standards/SKILL.md)).
- **Deliver:** the binding files, and the checks passing on the manuscript skeleton.
- **Watch:** rules that are written and not measured ([L1](lessons-learned.md#l1)).

## 5. Write the opening part

- **Do:** one proposal per section of the opening part (setting, definitions, main theorems, principal statements
  with the idea of each proof, the deduction, constants and the order of their choice); integrate; review with one
  owner per principal statement, a fresh reader, a prose-truth check and a delivery review
  ([`writing-workflow`](../../writing-workflow/SKILL.md)).
- **Deliver:** the opening part, reviewed; the register rows of every numbered statement.
- **Watch:** definitions crowding out the theorem ([L14](lessons-learned.md#l14)); a statement weaker than the
  Lean ([L11](lessons-learned.md#l11)); tags stripped at integration ([L18](lessons-learned.md#l18)).

## 6. Pilots

- **Do:** write two proof sections, on different sides of the proof, through the full cycle (proposal, reviews,
  revision, re-checks, last fixes, delivery). Give the author both, with measured pages.
- **Gate:** ★ the author reads them and sets the level of detail and length. Turn every comment into a binding
  rule in `STYLE.md` the same day ([L24](lessons-learned.md#l24)).
- **Yang–Mills:** the reviews of the pilots found that one pilot assumed two inputs no section stated and the other
  dropped a hypothesis the Lean carries ([L19](lessons-learned.md#l19)).

## 7. Roll-out

- **Do:** run every remaining section through the same cycle in parallel with `rollout.py`, with allowances from
  the spine and the pilots; the editor integrates each section that the delivery review passes, and sends the others
  through a fix-up stage ([`writing-workflow`](../../writing-workflow/SKILL.md)).
- **Watch:** allowances below what a complete proof needs ([L23](lessons-learned.md#l23)); writers renumbering
  locally ([L17](lessons-learned.md#l17)).
- **Yang–Mills:** the eight other sections were written in parallel and integrated the same evening; the first
  complete draft (226 pages) was published on the day the Lean was released.

## 8. Reconcile sections

- **Do:** inventory every citation from one section to another; compare what the citing proof uses with what the
  cited statement says; repair both sides; re-check every item
  ([`cross-section-consistency`](../../cross-section-consistency/SKILL.md)).
- **Done when:** a targeted re-check confirms every item resolved and finds no new substantive mismatch.
- **Yang–Mills:** three rounds; the last confirmed every item resolved ([L21](lessons-learned.md#l21)).

## 9. Introduction and abstract

- **When:** after the main theorems and principal statements have stopped moving.
- **Do:** the problem and the result in plain words, an informal statement of the main theorem with a pointer, scope
  and nonclaims, the source of the result and of the text, the three kinds of checking named separately, earlier
  work, the proof outline, a reading guide, conventions ([`honest-publication`](../../honest-publication/SKILL.md)).
- **Check:** owner, fresh-reader and prose-truth reviews like any section.

## 10. Referees, adjudication, typography

- **Do:** independent referee reports by several models on a frozen snapshot; adjudicate every suggestion against
  the text and the Lean; writers apply the accepted ones; a confirmation review before integration; a typographic
  pass over every rendered page ([`referee-adjudication`](../../referee-adjudication/SKILL.md)).
- **Check:** main theorems compared byte for byte with the approved text after every pass.
- **Yang–Mills:** three referees (Part I; Sections 10–14; Sections 15–19); real gaps filled from the Lean
  ([L25](lessons-learned.md#l25)).

## 11. Human reading and the editorial pass

- **When:** whenever human readers (the author, colleagues) are available; if none is, skip the human part, run the
  agent exposition reviews, and say on the status page that no human has read the text beyond the author.
- **Do:** collect the human readers' notes and agent exposition reviews; merge them into one editorial plan with
  source keys, decisions for the author, correctness fixes first, a plan per section with page budgets
  ([`referee-adjudication`](../../referee-adjudication/SKILL.md)).
- **Gate:** ★ the author rules on the plan's decisions; then implement section by section, with the same reviews.
- **Yang–Mills:** the second draft (265 pages) rebuilt Part I around the main theorem, now on page 14, after expert
  and independent reviews ([L26](lessons-learned.md#l26)).

## 12. Publication

- **Do:** status table with defined meanings, process page, correspondence table pinned to the commit, changelog,
  under-construction markers until the author removes them ([`honest-publication`](../../honest-publication/SKILL.md)).
- **Before "finished":** the final audit and completion test of `math-paper-campaign`, and the author's reading
  of every part.

## Sizing the campaign

The phases above are sized for the Yang–Mills development (about one million lines; a manuscript of 265 pages). A
smaller development needs fewer agents and fewer levels, not weaker checks. Choose the column by the size of the
closure of the main theorem and the length the author wants.

| | small | medium | large (Yang–Mills) |
|---|---|---|---|
| closure of the main theorem | up to about 50,000 lines | 50,000–300,000 | more (Yang–Mills: about 410,000 attributed lines) |
| target text | up to about 60 pages | 60–150 | more (265 in the second draft) |
| units and outlines | units are the planned sections; one outline each, no condensed level | units of 5,000–40,000 lines; detailed notes, condensed outlines if a public map is wanted | parts and units; detailed notes and condensed outlines |
| key statements | the editor reads the inventories; no second reader, no κ | two readers on the largest units | two readers on all candidates, κ |
| spine | one draft and one independent review of it | two drafts and a reconciliation | two drafts and a reconciliation |
| pilots | one section | two | two |
| roll-out | sections one at a time through the cycle | the driver, two writer and three reviewer slots | the driver, more slots |
| referees | one referee, adjudication, confirmation | two | three |
| public levels | statement page, manuscript, process note, correspondence table | add the architecture and the unit outlines | five levels and reference material |

**Never drop, whatever the size** (the claims of [what this establishes](../SKILL.md#what-this-establishes-and-what-it-does-not)
depend on them): the compiled graph and the closure; the statement page; natural-form statements with a clause map,
the author's approval and the drift protocol; writers and reviewers of different model families; for every section
an owner review of each principal statement, the mathematical review against the Lean, a fresh reader, the
prose-truth check, response tables and a delivery review; the shape, vocabulary and compile checks after every
integration; one routed-inputs check of every citation between sections; the disclosure naming the three kinds of
checking; the correspondence table, pinned and checked.

Templates and examples name the parts as the Yang–Mills manuscript did (Part I: the theorem and the architecture of
its proof; Part II: the proofs). For a paper in one part, "the opening part" means the sections that state the
definitions, the main theorems and the principal statements; rename `part1/`, `part2/` and "Part II" in the
configs accordingly.

## The working repository

`scripts/init_campaign.py` creates this tree (private) next to the public manuscript:

```
BRIEF.md                decisions, dated, with who approved them
STYLE.md                binding style; the author's calibration comments become rules here
DETAIL-STANDARD.md      what is written out, what is cited, what never appears, for a named reader
NOTATION.md             symbols: one meaning each, where defined
TERMINOLOGY.tsv         code terms and the literature terms that replace them
MORNING.md              morning list and overnight log
REGISTER.md             one row per numbered statement (statuses, owner, proof address, open findings)
statement.md            the statement page (phase 0)
DISCLOSURE.md           the one disclosure wording, filled in (honest-publication), used everywhere
spine/                  drafts, reconciliation, SPINE.md (frozen contracts), SPINE-NATURAL.md (the authority for
                        statements), the clause map, DRIFT-LOG.md (the only drift log)
prompts/                writer and reviewer prompts; prompts/superseded/ is never reused
proposals/<section>/    writers' proposals: TeX, NOTES.md, correspondence.tsv, REQUESTS.md
reviews/<round>/        frozen packets with manifests, reports, response tables
rollout/                driver state (one directory per section and stage)
correspondence/         the correspondence table pinned to the commit
```

Keep the canonical manuscript in one place, edited by the editor only. Old drafts are sources to check, never
competing authorities.
