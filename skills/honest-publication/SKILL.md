---
name: honest-publication
description: Publish a manuscript written by agents from a Lean development, and its repository, with exact claims about what was checked — levels of detail, one disclosure wording for AI authorship, the kernel check, the agents' statement comparison and the prose review named separately, defined status words and under-construction markers, a correspondence table checked against the main theorem's closure, a statement page with nonclaims, an FAQ evidence table and a changelog. Use before every public push and whenever a public page says what was proved, checked or written by whom.
---

# Honest publication

A manuscript written from a Lean development rests on three different things: a formal proof that the Lean kernel
checked; a comparison, made by agents, of each numbered statement with the declarations it rests on; and prose
that agents wrote and reviewed and that nothing checked mechanically. A reader can weigh the text only if these
are kept apart. **Name each kind of checking separately, in one wording used everywhere, and claim nothing
stronger than the check that was run.** The text stays marked as under construction until the whole of it is
checked; that decision, like the author line, belongs to the author.

## When to use, and when not

Use this skill before the first public push and before every later one; when writing the abstract's last
sentence, the introduction's paragraph on sources, a README, an FAQ, a status table, a changelog entry or citation
metadata; and when publishing a correspondence table. Use instead:

- `lean-public-release` (collection *LeanAutoformalizationSkills*) to release a Lean repository itself;
- `visual-paper` (collection *math-paper-skills*) for a companion website with audited summaries;
- `math-paper-campaign` for the final audit and the completion test before calling the text finished;
- `latex-math-writing` for the prose of the manuscript.

## Procedure

1. **Separate public and private.** ★ The author decides what is public. Reader-facing material (TeX, PDF, README,
   statement page, method, FAQ, changelog, data) goes to the public repository; working files (brief, plans,
   prompts, reviews, ledgers, morning list) stay in a private one. Every public commit passes the vocabulary check
   of `exposition-standards` and the [pre-publication checklist](assets/prepublication-checklist.md).
   *Deliverable:* the two repositories and the checklist in the push routine.
2. **Structure the public repository by levels of detail**: 1 the main theorem; 2 the proof in one reading; 3 the
   architecture; 4 the units, each with an outline, detailed notes and a Lean map; 5 the full manuscript; then
   reference material: provenance, glossary, the code's own work items, method, FAQ with an evidence table,
   changelog, data with a dictionary. Each level links to the next; from level 3 down, every claim links to pinned
   Lean lines. *Deliverable:* the README ([template](assets/public-readme.template.md);
   [public repository](references/public-repository.md)).
3. **Write the statement page**: the formal statement verbatim, a commentary in words, the full statement in
   ordinary mathematics with every quantifier and order of limits as in the Lean, explicit nonclaims, and an
   item-by-item correspondence with the source. *Deliverable:* `statement.md`
   ([template](assets/statement-page.template.md)).
4. **Disclose authorship and the checking in one wording.** ★ The author chooses the author line; agents never
   choose one, nor a persona ([L31](../lean-to-manuscript/references/lessons-learned.md#l31)). The abstract's last
   sentence and the introduction's source paragraph say that AI agents wrote the text from the Lean code, and
   name the three kinds of checking separately
   ([L30](../lean-to-manuscript/references/lessons-learned.md#l30)): the kernel check, with its axioms and
   verification log; the agents' comparison of every numbered statement with the declarations it rests on, with
   the correspondence table; and the prose, written and reviewed by AI agents, not machine-checked, not refereed
   by human mathematicians. Use the under-construction wording until the author declares the text finished, then
   the finished one. The same sentence appears on the title page, the README and the citation metadata
   ([L29](../lean-to-manuscript/references/lessons-learned.md#l29)). *Deliverable:* the
   [wordings](assets/disclosure-wordings.md) filled in and placed ([claims and status](references/claims-and-status.md)).
5. **Publish statuses with defined meanings, and the markers.** Every status word is defined by the review it
   records and what it does not mean ([L32](../lean-to-manuscript/references/lessons-learned.md#l32)).
   Under-construction markers (a README banner, a title-page note, the repository description, the links from
   companion pages) are removed only when the whole text is checked, by the author's decision. *Deliverable:* a
   dated [status table](assets/status-table.template.md).
6. **Publish the correspondence table and check it.** Every numbered statement and display, its declarations, the
   relation (`DIRECT`, `WEAKENING`, `COMPOSITION`, `CITED`, `NONE`, defined once for the collection in
   [the relations table](references/correspondence-and-statement.md#relations)), file and line at a pinned commit. **Every
   Lean name must be in the closure of the main theorem** (`used = 1`,
   [L5](../lean-to-manuscript/references/lessons-learned.md#l5)). Run `check_correspondence.py` before every push;
   re-pin whenever either side changes; publish the table before any text says it is published; keep the
   paper-facing declarations protected as roots in the formal development (`from-formalization.md` of
   `math-paper-campaign`). *Deliverable:* the table and the check's summary line, e.g. the Yang–Mills Part I table:
   657 rows, 807 name references, all in the closure ([correspondence and statement](references/correspondence-and-statement.md)).
7. **Answer readers with evidence.** An FAQ ending with the evidence table *check | what it establishes | what it
   does not* ([template](assets/faq-evidence-table.template.md)), a method page, and none of the claims below.
8. **Keep publishing honestly.** A dated changelog of reader-facing corrections
   ([entry template](assets/changelog-entry.template.md)); a way to report a correction (page, heading, quoted
   sentence, proposed correction or pinned Lean link); citation metadata; the formal source's licence respected.

## Never claim

- correctness of the prose in the sense of a human referee's report;
- that an agreement statistic (Cohen's κ between agents) is an accuracy
  ([L8](../lean-to-manuscript/references/lessons-learned.md#l8));
- that a comparison of reachable declaration sets with the authors' record checks edges or explanations
  ([L4](../lean-to-manuscript/references/lessons-learned.md#l4));
- that loading a compiled build rebuilds it ([L33](../lean-to-manuscript/references/lessons-learned.md#l33));
- anything stronger than the Lean proves, including by omitting a nonclaim;
- priority beyond what a systematic comparison with the literature supports;
- that a status label, a passed check or a review certifies correctness.

## Scripts and assets

- `scripts/check_correspondence.py TABLE.tsv --db GRAPH.sqlite --tex DIR --commit SHA [--lean-repo DIR]` checks
  that every Lean name of the table is in the graph with `used = 1`, every relation is allowed, the table's labels
  and the TeX's statement labels match both ways, a commit is pinned (and matches), and, with `--lean-repo`, that
  every cited file and line exists at the pin. It assumes a SQLite graph with a table of names and a closure flag
  (names configurable) built at the same pin; it does not judge whether a declaration supports a statement.
- `assets/`: disclosure wordings, status table, FAQ evidence table, statement page, public README, changelog entry,
  correspondence table header, and the pre-publication checklist an agent runs before every public push.

## What this establishes and what it does not

- `check_correspondence.py` establishes, for the table as written: each listed Lean name occurs in the graph
  database with `used = 1`; each relation is one of the five defined words, and every row of the first four lists a
  declaration; a commit is recorded and equals the expected one; with `--tex`, every table label is a `\label` of
  the TeX and every label of a numbered statement environment has a row; with `--lean-repo`, each cited file exists
  at that commit and each cited line lies inside it; with `--check-graph-locations`, each name's place in the graph
  lies in its row. It does not establish that the declarations prove the statement, that the relation is the right
  one, or that a row lists every declaration the statement needs: those are an agent's judgment. It inherits the
  graph's limits and does not check that the graph was built at the table's pin.
- The kernel check, as reported by the formal source, establishes that the formal proof terms check against the
  formal statement with the listed axioms, trusting the kernel and the libraries. It does not establish that the
  formal statement expresses the intended mathematics, nor anything about English text.
- The agents' comparison of statements with declarations is a recorded judgment by AI models, not a machine check.
  Scripts verify only the record: a row per numbered statement, a report of sufficient length with a verdict line,
  and, with the coverage check of `writing-workflow`, no label missing from the reports. The prose has been
  reviewed by AI models only; that is not a referee's report.
- A status label records which review ran, never that the text is right. The pre-publication checklist records
  that its items were checked at that push; the vocabulary check establishes only that the listed words are
  absent. The disclosure wordings describe checks; they add none.

## Related skills

This collection: `lean-to-manuscript` (phases, author decisions), `lean-dependency-graph` (the closure, the
comparison with the authors' record, the compiled-build release), `coarse-graining` (levels 2–4, glossary
labels), `statement-spine` (the natural and the formal main theorem), `exposition-standards` (vocabulary check),
`referee-adjudication` (typography pass, changelog lines after a round). Elsewhere: `math-paper-campaign` (final
audit, completion test, `from-formalization.md`), `visual-paper`, `lean-public-release`, `lean-statement-audit`.
