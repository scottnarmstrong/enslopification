# Freezing, drift, and the later lemmas

## Freezing

The author approves the spine; agents do not freeze it. Before asking, have ready: the natural
spine, a clean `clause_map_check.py` run, the clause-map review with its responses, the measured
pages and shape, and the list of decisions with recommendations. Record the approval in the
campaign brief with the date and the SHA-256 of the approved file.

What is frozen: the main theorems, the principal statements and the opening definitions they
use. From then on the natural spine is the authority for statements, and the frozen contracts
remain the record it must cover. Writers typeset the frozen statements faithfully; they may
improve wording only where the mathematics is unchanged, and they report a problem instead of
fixing it ([writing-workflow](../../writing-workflow/SKILL.md)).

What is not frozen: the later lemmas. They are targets that the proofs will refine.

## Changes to a frozen statement

Follow the drift protocol of `math-paper-campaign` (reference `shared-controls.md`; the skill is in
the collection *math-paper-skills*, which this collection requires): stop the affected work, record
old and proposed contracts, find every dependent, route the question to the author, re-review,
reintegrate. Reshaping for readability is drift too. A Lean source adds the following.

- **Evidence is a declaration.** The entry names the `used = 1` declarations, with file:line at
  the pinned commit, and says what each one fixes. An outline or a summary is not evidence.
- **Strength is checked in both directions**
  ([L11](../../lean-to-manuscript/references/lessons-learned.md#l11)). A statement weaker than the
  Lean breaks the author's approval and may starve a consumer. In the Yang–Mills campaign (2026)
  the detailed main theorem, as first written, said that data with the required properties exist,
  not that they are the objects constructed; its owner rejected it on correctness, and the repair
  went to the project lead.
- **The author decides.** The old text, the new text, the reason and the Lean evidence go to the
  author; nothing changes before approval. In overnight mode never change a frozen statement:
  queue it, with the evidence, on the morning list of decisions for the author
  ([L35](../../lean-to-manuscript/references/lessons-learned.md#l35)).
- **Every occurrence changes.** Search the spine, the sections, the introduction, the constants
  table and the deduction for the old wording. An approved change must reach every line that still
  implies the old content; a final search finds the lines that a first pass missed.
- **The clause map follows.** Update the rows of the changed clauses, re-run
  `clause_map_check.py`, and have the owner of the statement re-check it.
- **Scope moved is not scope lost, if recorded.** When a main theorem is rewritten so that some
  conclusions are no longer packaged into it, record that they remain separately proved results,
  cited in the deduction, and log the change as part of the approved shape, not as a weakening, so
  that the owner's re-check finds the record instead of a silent loss.

Keep every entry in a drift log (`assets/drift-log-template.md`): old text, new text, change of
content in which clause, reason, Lean evidence, who found it, dependents re-checked, rows of the
clause map changed, status. Entries are never rewritten; a correction is a new entry.

## Owner reviews

Give every principal statement one owner: a reviewer who reads the manuscript in order up to the
statement before opening any source, then maps each clause to the spine and the Lean and tries to
break it. It judges (i) correct against the spine and the Lean, in both directions; (ii)
understandable from the text before it; (iii) serves the statements that use it. The review cycle
is in [writing-workflow](../../writing-workflow/SKILL.md); the owner is the check that catches
drift the writer did not declare.

## The later lemmas are editable targets

The later lemmas can be split, added, removed or reworded as the proofs are written. Each change
needs:

- a drift-log entry (no approval, unless it changes a frozen statement or an opening definition);
- the clause map updated, if the lemma carries a frozen clause, and the check re-run;
- the users of the lemma in other sections checked against the new text
  ([cross-section-consistency](../../cross-section-consistency/SKILL.md)).

In the Yang–Mills campaign one pilot section first used two inputs as hypotheses with no
statement to cite; the revision states them as labelled lemmas matching the Lean
([L19](../../lean-to-manuscript/references/lessons-learned.md#l19)). The other pilot omitted a
bound on a constant that the Lean carries; the bound was added to the definition and propagated to
the opening part, which uses the same constant, and to the constants table.

Every input a proof uses is a labelled statement that exists, or a written request to the section
that must prove it. A writer who needs a lemma that does not exist adds it as a target with its
Lean source, and the log records it.

## Hypotheses do not move to meet caps

A cap is met by splitting a statement or defining objects earlier, never by moving a hypothesis
into the surrounding prose ([L13](../../lean-to-manuscript/references/lessons-learned.md#l13)).
In the Yang–Mills campaign, hypotheses that had been moved from lemmas of the ultraviolet sections
into the surrounding prose were restored inside the statements after the referee round. Treat a
hypothesis moved into prose as drift: the clause map must still point to the statement that
carries it.
