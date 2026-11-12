# Detail standard for <manuscript>

Binding for every writer, reviewer and critic.

**Reader:** <a named kind of reader: their field, what they know (list the standard tools), and
"checks each step with pen and paper in reasonable time">.

A page allowance comes with every task: **over the allowance = not done** (for a section marked
as a guide: complete at this standard, no padding, measured length reported with its reason).

## One line, or a citation

- <standard tool of the field> — cite <author, title, theorem number>.
- <standard tool of the field> — cite <...>.
- Geometric series; constant bookkeeping (one sentence on what a constant depends on);
  measurability; passing between equivalent formulations.
- Cases identical by symmetry (axes, signs, orientations, conjugation); a second instance of an
  argument already given.

This holds even where the Lean proves these facts from scratch. Cite the exact statement used
(number, hypotheses), checked against the source before it is written.

## Written out

- Every estimate specific to this construction, with the mechanism that makes it true: what is
  small, why, and which loss it pays for.
- <the construction-specific steps of this proof, one line each>.
- The order in which parameters are chosen whenever a later choice depends on an earlier one;
  every claimed uniformity (in <the parameters of this proof>).
- Exact identities on which cancellations rest.
- Every place where the formal development showed an informal source wrong or incomplete: the
  corrected statement, without its history.

## Never

- Lean names, formal artefacts, or the formalization's packaging (structures bundling a
  construction with its properties, records, tables, case splits that exist for the proof
  assistant).
- Several variants of one lemma for different users; "for completeness" passages; constants
  whose value is never used.
- History ("it turns out", "the original approach"), process language, hedges that the Lean
  settles.

## Representative cases

Where the Lean checks one pattern many times (each degree, channel, axis, block type), prove one
case, say why the others are identical, and record the formal check in the correspondence table.
Never for a main estimate.

## Statement counts and proof length

About one numbered lemma per page in the proofs. A proof that needs more than three pages is
split at a genuine intermediate statement, or its allowance is renegotiated with the editor
before drafting, not after.
