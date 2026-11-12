# The cycle for each section

What each step of the cycle delivers, how pilots and allowances are set, how the editor integrates, and which
records the cycle keeps. The driver configuration that runs it is
[`rollout.section-cycle.example.json`](../assets/rollout.section-cycle.example.json); the review kinds are in
[reviews](reviews.md).

## Before the first section

These exist and are approved ([`statement-spine`](../../statement-spine/SKILL.md)): the natural spine
`SPINE-NATURAL.md`, the authority for statements; the frozen contracts `SPINE.md` (clauses tagged `[clause:ID]`)
and the clause map, the record it must cover;
`STYLE.md`, `DETAIL-STANDARD.md` and the automatic checks, running clean on the skeleton
([`exposition-standards`](../../exposition-standards/SKILL.md)); one register row per numbered statement; agent
profiles that pass the preflight ([agent profiles](agent-profiles.md)); and a placeholder file per section holding its
`\section` line and the labels of its statements, so that every section can cite every other one from the start.

## Allowances and their history

Derive each section's page allowance from measurement, never from a total divided by the number of sections: the
frozen statements of the section typeset alone, plus the pilots' ratio of proof to statement. Keep a table: section,
first allowance, measured length at delivery, revised allowance, who decided, why.

Allowances fixed before the pilots tend to be too small for the hardest sections, those that carry most of the
Lean, and drafts written under a tight allowance come back incomplete. For such a section the author can make the
page figure a guide: complete at the detail standard, no padding, measured length reported with reasons
([L23](../../lean-to-manuscript/references/lessons-learned.md#l23)). Elsewhere **over the allowance means not
done**: an agent can report a pass complete when the page count shows that it added material instead of cutting
([L2](../../lean-to-manuscript/references/lessons-learned.md#l2)). The driver measures every draft
(`check_allowance.py`) and gives one retry quoting the overrun; for a section the author made a guide, the check
only reports (`--report-only`) and a reviewer polices padding. A projected overrun of the whole part goes to the
author with measured options before the roll-out continues.

## The steps

| step | who | delivers | done when |
|---|---|---|---|
| 1. task | editor | the prompt: the statements from the spine, the sources (outline units, notes, the Lean they link), the allowance, the common rules, the unit's inbox | the dry run renders it |
| 2. proposal (`w1`) | writer, in its own directory | the section, `standalone.pdf`, `correspondence.tsv`, `NOTES.md`, `REQUESTS.md`, `partI-edits.md` | the files exist and the checks pass |
| 3. frozen snapshot | driver | the packet: proposal, integrated manuscript, natural spine, contracts, clause map, style, detail standard, with SHA-256 manifest | `manifest.json` written |
| 4. reviews (`r1`) | reviewers, fresh contexts | mathematical review, fresh reader, prose truth, and one owner card per principal statement, each a separate job | every report saved with its verdict line |
| 5. revision (`w2`) | writer | the new version and `response-w2.tsv` | every finding has a row |
| 6. re-check (`r2`) | the same reviewers | RESOLVED or NOT RESOLVED per earlier finding, verdicts on declined reasons, new problems | every report saved |
| 7. last fixes (`w3`) | writer | `response-w3.tsv` | every open item has a row |
| 8. delivery (`d`) | driver, reviewer | the driver recompiles and measures the section and lists the labels no report names (`build.txt`); then DELIVER or NOT YET, with what the review does not establish | STATUS written |
| 9. fix-up (`w4`, `d2`) | writer, reviewer | only for NOT YET: the required items, then confirmation | STATUS is DELIVER |
| 10. integration | editor | the section in the manuscript, checks clean, register updated | see below |
| 11. reading | project lead | comments on level and length | comments are rules in `STYLE.md` |

`NOTES.md` carries what the writer changed relative to the spine and why, every statement it could not typeset as
given, what it could not do, **its least certain sentence** (quoted, with the reason), and the measured pages and
shape. The least certain sentence tells the mathematical reviewer where to look first; a writer that names none is
asked again.

**Response tables** have one row per finding: the finding (report and id), the decision (applied, or declined with a
mathematical reason), the exact edit (old and new text, located by quotation), and how it was checked. Findings are
never deleted or rewritten; a later round adds rows. A finding that needs a frozen statement changed is not applied
by the writer: it goes to the author through the drift protocol (`math-paper-campaign`, shared controls;
[L11](../../lean-to-manuscript/references/lessons-learned.md#l11)).

**Requests.** A writer who needs a result no section states proves it as a short lemma (under a page) or writes a
request addressed to a unit key (`{{unit_keys}}` lists them); requests reach the owner's next writer through its
inbox ([`cross-section-consistency`](../../cross-section-consistency/SKILL.md)). An input with neither a label nor a
request is a blocker ([L19](../../lean-to-manuscript/references/lessons-learned.md#l19)).

## The opening part and the introduction

Both are units of the same config, run through the same cycle with three unit variables: `w1_task`
([`w1-opening.md`](../assets/prompts/w1-opening.md) or [`w1-introduction.md`](../assets/prompts/w1-introduction.md)),
`part_dir` (`part1`) and `unit_checks`. The unit holding the main theorems checks them against the natural spine
with `compare_statements.py` of [`referee-adjudication`](../../referee-adjudication/SKILL.md); every principal
statement, main theorems included, has its own owner. The introduction comes last: the disclosure wording of
[`honest-publication`](../../honest-publication/SKILL.md) goes between the vocabulary check's exception markers, a
unit check requires `abstract.tex`, and the owners of the main theorems check the informal statements.

## Pilots

Run two pilot sections, on different sides of the proof, through the whole cycle before any other section is
written, and give them to the author with measured pages. In the Yang–Mills campaign (2026) the first mathematical
reviews of the pilots (the coupling reset and the infinite-volume limit) found that one assumed two inputs no section
stated and the other dropped a hypothesis the Lean carries
([L19](../../lean-to-manuscript/references/lessons-learned.md#l19)); the project lead read both before the other
eight sections were written. **Turn the author's comments into binding rules in `STYLE.md` the same day** and review
every later draft against them ([L24](../../lean-to-manuscript/references/lessons-learned.md#l24)). Write each
comment as a general rule with its example, not as a quotation. The approved pilots become the model of level and
length that every later task and every fresh reader names.

## Integration rules

- Only the editor edits the manuscript. It reads each delivered proposal in context and rewrites what does not fit
  the manuscript's voice and notation; it never pastes text it has not read.
- **Keep reader-facing tags** in statement titles (principal tags, axiom labels the text refers to) and remove only
  internal codes: a first integration stripped axiom labels that a main theorem refers to
  ([L18](../../lean-to-manuscript/references/lessons-learned.md#l18)).
- **Never redefine counters** or `\the...` macros; numbering is global, the proof part continues the opening part's
  section numbers, and numbered items are referred to only by `\ref`: proof-part numbers once collided with
  addresses used in the opening part ([L17](../../lean-to-manuscript/references/lessons-learned.md#l17)).
- Locate every edit by quoted content, not by line number: files move while several proposals are integrated.
- After every pass, overnight passes included, compare the main theorems byte for byte with the approved text
  (`compare_statements.py SPINE-NATURAL.md part1/ --labels ... --allow-label-changes`: the spine's other labels live
  elsewhere).
- Proposed edits to the opening part (`partI-edits.md`) go stale when the opening part changes. Re-apply each against
  the current text and record it as applied, already met, or obsolete.
- Compile and run the automatic checks after every integration. Integrated text is edited text: it goes through the
  next frozen-packet review like a proposal (a deletion once left a sentence broken).

## Records

- **The statement register**, one row per numbered statement: owner card, mathematical status, exposition status,
  rendered status, proof address, open findings (template: `REGISTER.template.md` of
  [`lean-to-manuscript`](../../lean-to-manuscript/SKILL.md)). "Checked" is written only after the author's reading;
  every status word has one published meaning ([L32](../../lean-to-manuscript/references/lessons-learned.md#l32)).
- **The correspondence table**, merged from the writers' `correspondence.tsv` and checked with
  `check_correspondence.py` of [`honest-publication`](../../honest-publication/SKILL.md); for the Yang–Mills opening
  part it had 657 rows and 807 names, every one in the closure of the main theorem.
- **The response tables** of every round and **the drift log** of every change to a frozen statement.
- The driver's `progress.log` and `STATUS` files record what ran and what a regex read from a verdict line, nothing
  about the mathematics.
