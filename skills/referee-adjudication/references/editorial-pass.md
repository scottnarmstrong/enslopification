# The editorial pass: exposition reviews, the editorial plan, comparison with another draft

After the referee round the text is faithful; it is not yet easy to read. Reviews that check faithfulness do not
check readability ([L10](../../lean-to-manuscript/references/lessons-learned.md#l10)). The editorial pass merges
what human readers and agent reviewers say about the exposition into one plan, has the author rule on its
decisions, and executes it with the same packets and reviews as the writing.

## 1. Agent exposition reviews

- **The checklist** (`assets/prompts/exposition-reviewer.md`, the manuscript-wide variant of the section-level
  prompt `exposition-review.md` of [exposition-standards](../../exposition-standards/SKILL.md); keep their six
  headings identical): A density; B misallocated detail; C notation; D
  terminology (words inherited from the code, tested one by one); E structure and signposting; F readability. Each
  finding gives the location, the heading letter, the problem, and an exact rewrite; findings are ranked by how
  much they would help a reader. Mathematical errors are reported only when they block understanding, in a
  separate list. No praise, no summary.
- **The reader** is named, as a kind of expert (for a construction in quantum field theory: an expert in
  constructive field theory, renormalization and probability), measuring each passage against the standard texts
  of the field.
- **Coverage by page range.** Give each reviewer a page range it can read completely, cover the whole text, and
  use more than one model family where you can. Run them with the shape of the typography config (units are page
  ranges) and the exposition template.

## 2. Merging human and agent reviews

Merge every source into one plan: the human readers' notes and reviews, and the agent reviews
([L26](../../lean-to-manuscript/references/lessons-learned.md#l26)).

- **Source keys.** Give every reviewer a key and number its findings: `H1-n`, `H2-n`, … for the human readers,
  `A1-n`, `A2-n`, … for agent reviews by page range, with a suffix for a reviewer's closing list of renamings.
  Every planned change cites its keys, so that the author can see who asked for it and how many readers agree.
- **Rules**, stated at the top of the plan:
  1. where agent reviewers conflict with a human reader, the human reading wins;
  2. every term a human reader uses is kept, marked "keep" in the terminology table; elsewhere code words give way
     to terms of the literature ([L28](../../lean-to-manuscript/references/lessons-learned.md#l28));
  3. no claim may become stronger than what the Lean proves;
  4. every change to an approved statement is listed, old and new text, for the author's approval.
- **Approvals needed before writing starts** come next: the decisions of part A, each statement change, the
  abstract's wording.

## 3. The plan (`assets/editorial-plan.template.md`)

- **A. Decisions for the author.** For each: the problem with its keys; the dependencies it touches; options, each
  with its page effect; a recommendation; knock-on edits. Typical decisions: whether the natural main theorem
  comes first, with the literal formal statement, its conventions and its deduction in a section of their own
  ([L15](../../lean-to-manuscript/references/lessons-learned.md#l15)); moving preliminary material before the
  argument that uses it; the terminology table; the abstract's sentence on checking
  ([L30](../../lean-to-manuscript/references/lessons-learned.md#l30)); a table of other architectural choices
  (where the constants table goes, a worked example, subsections for long sections, results stated once and
  cited).
- **B. Correctness-of-exposition fixes, first.** Sentences the readers found false or unsupported, each checked
  against the Lean at the pin before it is edited, and recorded as finding, decision, edit, check. The Yang–Mills
  second draft, for example, corrected a proof sentence that assigned certain terms of an expansion to the wrong
  remainder. Quote the declarations that settle such a sentence, with file and line.
- **C, D. A plan per section:** current and target pages, then what to add, cut and move, each with its keys.
- **E. Figures:** for each, the one idea it expresses and the misreading to avoid (`math-figures`).
- **F. Budget.** A table per section: current pages (measured), additions, cuts, moves, target. Additions are
  offset by cuts; any single addition over one page carries a reason; figures count. State the net against the
  total agreed with the author. Writers report measured length per packet; a packet more than half a page over
  its target goes back to the editor before integration
  ([L2](../../lean-to-manuscript/references/lessons-learned.md#l2)).
- **G. Execution order and writer split.** Step 0, the author's decisions; then the correctness fixes; structural
  moves (labels kept); the terminology sweep (scripted renames with before and after counts, and a do-not-rename
  list of the human readers' terms); figures; writing packets (as many writers at once as the machine allows;
  writer and reviewer from different model families); the review of each packet on a frozen snapshot (Lean check
  of every changed statement, prose truth, owner review, shape checks, rendered pages); fresh readers; delivery.
  Ask the fresh readers to explain named mechanisms of the proof from the text alone, chosen where the human
  readers struggled; a wrong explanation sends the packet back.

## 4. The author's rulings and provisional decisions

Record the author's rulings verbatim in the brief. When the author approves "in principle" and leaves details to
the editor, list the editor's provisional decisions separately, numbered, reversible and marked for review: for
example the new shape of the opening part (keeping its statements and labels), the terminology, the abstract's
wording and the architectural choices.

## 5. Comparison with another draft

When someone else has drafted the same proof, compare
([L27](../../lean-to-manuscript/references/lessons-learned.md#l27); `assets/prompts/comparison.md`).

- **Organize** the comparison by area, with parallel readers on the large areas and one reviewer who integrates
  and spot-checks the findings the recommendations rest on.
- **Adopt devices; import no statements.** Devices worth adopting are matters of presentation: a short opening
  part (result, definitions, theorem, strategy with a diagram, principal statements); an "Idea of the proof, Step
  1...k" paragraph with one display per step; interpreting sentences after each definition; a label for each item
  of a property list. Statements are never imported: the other draft was not checked against the formal source,
  and it may have gaps, or statements weaker than the formal ones.
- **Say where the other draft is weaker, with evidence** (file and line, or the quoted statement). When it is
  shorter because its proofs are missing, say so: its form is the lesson, not its page count.
- **Keep the comparison private.** It judges a colleague's unfinished work; it informs the plan and is not
  published or quoted.

## 6. What the pass establishes

The plan records who asked for each change and what the author decided. Its page figures are estimates until the
packets are measured. The agent reviews are opinions about readability, ranked by the reviewer; the human readers'
notes are the evidence that a passage fails a reader. Executing the plan does not re-check the mathematics beyond
the review of each packet.
