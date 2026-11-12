---
name: referee-adjudication
description: Run independent referee reviews of a complete draft written from a Lean development, adjudicate every suggestion against the text and the Lean before anything is applied, apply the accepted changes through section writers with a confirmation review, and run the later passes (typography over rendered pages, exposition reviews, editorial plans that merge human and agent reviews, comparison with another draft). Use once a complete first draft exists, whenever referee, reader or reviewer comments arrive, and before any release.
---

# Referee adjudication

A complete draft needs readers who did not write it: referees, later human readers, agent reviewers of the
exposition. Their diagnoses are often right and their proposed fixes often wrong in detail
([L25](../lean-to-manuscript/references/lessons-learned.md#l25)). **Never apply review text directly: adjudicate
every suggestion against the text and the Lean, apply it through the writer who owns the section, and confirm the
result before integration.** The same discipline governs the typography, exposition and editorial passes: each
produces a table of findings with exact fixes, and nothing changes an approved statement without the author.

## When to use, and when not

Use this skill after the draft has been through the section cycle and the cross-section rounds, when comments
from readers arrive, and before every release. Use instead:

- `writing-workflow` for the review cycle of a section while it is written, and for the driver;
- `cross-section-consistency` for citations between sections;
- `lean-statement-audit` to audit one statement against one declaration in depth;
- `latex-math-writing` for prose style; `math-paper-campaign` for the final audit and the completion test.

## Procedure

### The referee round

1. **Freeze and assign scopes.** Freeze the whole draft (PDF and sources) with `make_packet.py`. Cut it into
   scopes a referee can read completely; each referee reads the whole snapshot but reports on its scope, as a
   referee from the field would. The Yang–Mills campaign (2026) used three referees: Part I, the ultraviolet
   Sections 10–14 and Sections 15–19. Use a model family other than the writers'.
   *Deliverable:* one report per scope: sources consulted and coverage first, numbered suggestions, the last
   line `Suggestions: N`.
2. **Adjudicate every suggestion.** One adjudicator per report, in a fresh context, separate from the referee
   and the writers, reads the snapshot, the Lean and the graph (`used = 1` only,
   [L5](../lean-to-manuscript/references/lessons-learned.md#l5)). For each suggestion: is the diagnosis true of
   the text (quote it)? Does the change say exactly what the Lean proves, never more? Does it break a
   cross-reference, a main theorem or another section? Verdict: `ACCEPT`, `ACCEPT MODIFIED` (with the exact
   corrected change), `REJECT` (with the reason) or `AUTHOR` (it changes a main theorem, the scope of the result,
   removes a proved result, or touches authorship). The adjudication lists first its sources, then the Lean facts
   the verdicts rely on. Then run `adjudication_summary.py --expect NAME=N`: no suggestion may lack a verdict.
   *Deliverable:* one adjudication per report and the summary.
3. **Send AUTHOR items to the morning list** with the adjudicator's recommendation and the provisional default,
   which is "not applied" ([L35](../lean-to-manuscript/references/lessons-learned.md#l35)). *Deliverable:* one
   entry per item, with how to revert the default.
4. **Apply by section.** One writer per section applies, in its own files, every `ACCEPT` item as proposed and
   every `ACCEPT MODIFIED` item exactly as adjudicated; never a `REJECT` or `AUTHOR` item. An item for another
   section is written as a proposal to that section's owner. A repair that needs an argument is written from the
   Lean's own argument. *Deliverable:* proposals, a response table with one row per item, cross-section proposals.
5. **Confirm before integration.** A separate reviewer compares each proposal with the live text: edits against
   the adjudication; statements against the Lean, including **hypotheses moved out of a statement to meet a
   word cap** ([L13](../lean-to-manuscript/references/lessons-learned.md#l13)); new sentences true or false;
   references; cross-section proposals. *Deliverable:* `Verdict: INTEGRATE` or `Verdict: NOT YET` per section,
   with exact fixes; for every NOT YET a fix-up (`f2`, `apply-fixup.md`) and a re-confirmation (`c2`, `v2`).
6. **Integrate and check.** The editor integrates (`writing-workflow`), lands edits that depend on each other in
   one commit, compiles, runs the shape and vocabulary checks, and compares the main theorems byte for byte with
   the approved text after every pass (`compare_statements.py --labels`,
   [L18](../lean-to-manuscript/references/lessons-learned.md#l18)). *Deliverable:* the integrated text, a status
   line and a changelog entry worded as `honest-publication` requires.

Details and verdict examples: [adjudication](references/adjudication.md).

### Later passes

7. **Typography, before any release** ([L29](../lean-to-manuscript/references/lessons-learned.md#l29)). Render every
   page (`render_pages.sh`); reviewers take page ranges and return a defects table (page, quote, defect, suggested
   fix) and a last line `Clean pages: …`; `check_coverage.py --pages` of `writing-workflow` lists any page missing
   from both; one writer fixes the defects; `compare_statements.py` confirms that no statement or label changed.
   *Deliverable:* defects tables, a response table, re-rendered pages. [Typography](references/typography.md).
8. **Exposition reviews and the editorial plan** ([L26](../lean-to-manuscript/references/lessons-learned.md#l26)).
   Agent reviewers apply the exposition checklist (density, misallocated detail, notation, terminology, structure
   and signposting, readability; exact rewrites, ranked; no praise). Merge their findings with the human readers'
   in an editorial plan: a source key per reviewer; human readers win conflicts; every term a human reader uses is
   kept; no claim becomes stronger than the Lean; changes to approved statements listed for approval; decisions
   for the author with options and a recommendation; correctness-of-exposition fixes first; a plan per section
   with page budgets (additions offset by cuts, any addition over one page justified, figures counted); execution
   order and writer split. ★ The author rules before writing starts. *Deliverable:* the plan, then its execution.
   [Editorial pass](references/editorial-pass.md).
9. **Comparison with another draft**, if one exists
   ([L27](../lean-to-manuscript/references/lessons-learned.md#l27)). Adopt its devices, import none of its
   statements, and where it is weaker say so with evidence. *Deliverable:* a comparison report and a porting order.

## Scripts and assets

- `scripts/adjudication_summary.py ADJ.md ... --expect NAME=N` reads the Markdown verdict tables; prints counts per
  verdict and report, the AUTHOR items for the morning list and the accepted items grouped by file for the
  writers; exits 1 if a suggestion number lacks a verdict, a verdict is unknown or an item has two verdicts. It
  assumes the table of the adjudicator template; it does not read the edits, open the Lean or judge a verdict.
- `scripts/render_pages.sh -f FIRST -l LAST -r DPI -o DIR PDF` writes page images with `pdftoppm` and prints their
  paths. It assumes poppler-utils; it inspects nothing.
- `scripts/compare_statements.py OLD NEW [--labels L1,L2]` compares statement environments by label, byte for
  byte, and the set of labels; exits 1 if a statement changed or a label disappeared. It assumes statements carry
  their `\label`; it says nothing about prose outside statements or about whether a change is right.
- `assets/prompts/`: referee, adjudicator, application writer, confirmation reviewer, fix-up writer and its
  re-confirmation, typography reviewer, exposition reviewer (the checklist), comparison with another draft;
  `{{...}}` placeholders. Every reviewer prompt asks for the sources consulted first
  ([L22](../lean-to-manuscript/references/lessons-learned.md#l22)).
- `assets/rollout.*.example.json`: configs for the shared driver of `writing-workflow` (referees; one adjudicator
  per report; one writer per section, a confirmation review and a verdict, then for NOT YET a fix-up and a
  re-confirmation; typography by page range).
  Replace every `SET-ME` value and dry-run first. The referee config needs a `referee` profile in your agents file
  (`"extends": "reviewer"` with the referee's model). `assets/editorial-plan.template.md`: the plan's skeleton.

## What this establishes and what it does not

On record: a verdict with a reason for every suggestion (`adjudication_summary.py --expect` verifies only that no
suggestion number lacks a row); the adjudicator's report of the Lean facts it relied on and of the names it
confirmed by query; the confirmation reviewer's report that the applied edits match the adjudication and that each
changed statement is implied by the Lean. The driver verifies only that each report is long enough and has its
verdict line; no script verifies that an agent made the comparison it reports, or that it is right. None of this is
a human referee's report. Referees, adjudicators and confirmers are AI models, independent of the writers but not of
each other's training; agreement between a referee and an adjudicator is agreement, not correctness. The adjudicator
can be wrong: its own wording can narrow a definition, which only the confirmation against the Lean catches. A
referee round samples: text that every referee only spot-checked was read closely by nobody in that round, and the
coverage statements say which. In a typography pass reviewers report each page as defective or clean;
`check_coverage.py --pages` verifies that no page is missing from the reports, not that a page was looked at; the
pass checks no mathematics. `compare_statements.py` establishes byte equality of statements and labels, not the
correctness of anything. An editorial plan's page figures are estimates until measured, and a comparison with
another draft validates neither draft.

## Related skills

This collection: `writing-workflow` (driver, review cycle, integration), `cross-section-consistency`,
`exposition-standards` (shape and vocabulary checks, terminology), `honest-publication` (disclosure, changelog,
status), `lean-to-manuscript` (overnight mode and the morning list). Elsewhere: `math-paper-campaign` (final
audit, completion test), `latex-math-writing`, `math-figures`, `manuscript-audit`, `lean-statement-audit`.
