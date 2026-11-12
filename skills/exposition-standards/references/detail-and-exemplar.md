# The detail standard and the exemplar

Both are fixed before the first section is written, and both go into every writing and review
task.

## The detail standard

`math-paper-campaign` (reference `from-formalization.md`, "Write a detail standard before writing")
gives the general form: what is one line or a citation, what is written out, what never appears,
and representative cases. Start from `assets/DETAIL-STANDARD-template.md` and add the following,
which a Lean source makes necessary.

- **Name the reader.** Not "an expert" but a kind of reader: their field, the standard tools they
  know, and that they check each step with pen and paper in reasonable time. For a construction in
  quantum field theory, for example: a constructive field theorist who knows the standard
  renormalization programme, cluster expansions, reflection positivity and Osterwalder–Schrader
  reconstruction. Every list below is decided against that reader.
- **The Lean proves everything; the paper does not.** A formal development proves Gaussian
  integration, cluster-expansion criteria, the implicit function theorem or a reconstruction
  theorem from scratch. The paper cites them, with the exact statement used, checked against the
  source. The detail standard says so in one sentence, or writers transcribe the formal proofs of
  textbook facts.
- **Written out: what the construction owns.** List the steps specific to this proof by name, so
  that a writer cannot treat one of them as routine: every estimate specific to the construction
  with its mechanism (what is small, why, which loss it pays for); the order of choices whenever a
  later choice depends on an earlier one; every claimed uniformity; the exact identities on which
  cancellations rest; every place where the formal development showed an informal source wrong.
- **Never: the formalization's packaging.** Structures that bundle a construction with its
  properties, the code's bookkeeping objects (the Yang–Mills Lean has receipts, ledgers, budgets,
  certificates, records and tickets), case splits that exist for the proof assistant,
  several variants of one lemma for different users, and hedges that the Lean settles.
- **Representative cases point to the formal check.** Where the Lean checks one pattern for every
  degree, axis or block type, the paper proves one case, says why the others are identical, and
  the correspondence table records the formal check of all of them. Never for a main estimate.
- **Counts.** About one numbered lemma per page in the proofs; a proof longer than three pages is
  split at a genuine intermediate statement or its allowance is renegotiated before drafting.

A fresh reviewer whose only job is the detail standard (a detail critic) finds what the
mathematical reviews do not: passages that spend a page on measurability while the key estimate
gets one line. Give it the detail standard, the section and its allowance, and ask for
dispositions (keep, shorten to a sentence, expand) with exact replacement text.

## The exemplar

Choose one or two published papers whose exposition the manuscript should imitate before anything
is written, and record what to copy in `EXEMPLAR.md` (at most about 120 lines): each pattern with a
line or page reference into the exemplar, then the features not to copy. In the Yang–Mills
campaign (2026) the model was the presentation of the renormalization group in a standard
monograph. It fixed the order of the opening part: the objects, the inductive step, the multiscale
theorem, the continuum results, the deduction of the main theorem, the constructions.

Patterns worth recording are concrete:

- the object is introduced by its formula before any theorem about it;
- the transformation is displayed as an operation that a reader could compute;
- a sentence explains why new coordinates are needed before they are introduced;
- each scale or parameter gets one sentence on its job;
- exact identities are kept apart from estimates;
- norms are defined by explicit sums and suprema;
- the inductive step states its input, its output and the recursion of the parameters;
- the base case comes before the iteration;
- constants and the order of their choice are recorded once, in order;
- the gain or cancellation that drives each estimate is named.

**Copy patterns, never statements.** The exemplar is an expository precedent, not a mathematical
input; no estimate of the manuscript may rest on it. Measure the exemplar with the manuscript's own
shape checker before calling it a model of length: a good exemplar can still have statements far
over the caps, and those go under "not to copy". Check every bibliographic detail of the exemplar
(chapter, theorem number, edition) against the source before the notes cite it.

Writers read `EXEMPLAR.md` and the exemplar itself for tone and structure; reviewers compare
passages with it.
