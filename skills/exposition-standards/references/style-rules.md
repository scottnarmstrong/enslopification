# The style rules, with their numbers and reasons

Each rule answers a failure of the Yang–Mills campaign (2026), in which OpenAI's Lean proof of the
construction of four-dimensional quantum Yang–Mills theory was turned into a manuscript, or of the
earlier campaign on a Navier–Stokes formalization. General prose, statements, proofs and
typesetting follow `latex-math-writing` (its `writing-rules.md`, the "Craft statements" section of
`artisan-writing.md`, and `house-style.md`); the rules here are what a formal source adds. Both
campaigns had their rules written down before they started and broke them anyway; what worked was
a program that measures, run after every round
([L1](../../lean-to-manuscript/references/lessons-learned.md#l1)).

## Statements

- **One idea per statement**, in its natural form, not the shape of its proof or of the Lean
  declaration ([L9](../../lean-to-manuscript/references/lessons-learned.md#l9)).
- **Words: target 100, cap 150** for theorems, propositions, lemmas and corollaries. The first
  Lean-shaped propositions ran to nearly a page. Over the cap means not done: split the statement,
  or set its objects up before it.
- **Setup outside, quantifiers first, conclusion displayed.** Objects and standing hypotheses in
  the prose before the statement; every constant declared with its dependence; no trailing
  conditions and no commentary inside.
- **No packaging statements** ("there is a family such that the following assertions hold"); the
  conditions of a construction go in the setup where its objects are introduced.
- **Hypotheses stay** ([L13](../../lean-to-manuscript/references/lessons-learned.md#l13)). A
  statement carries every hypothesis its users rely on. After the referee round, hypotheses that
  had been moved from lemmas into the surrounding prose were restored inside the statements. The
  cap is met by splitting or by defining objects earlier.
- **A principal statement** gets one or two sentences on its role before it and a precise pointer
  to its proof after it.

## References per statement, and main theorems

- **At most 4 cross-references or statement tags per statement, 6 per definition**; a range such as
  "Lemmas 3.2–3.5" counts once ([L10](../../lean-to-manuscript/references/lessons-learned.md#l10)).
  A statement must state, not list.
- **Main theorems: at most 250 counted tokens, formulas included, and at most 8 references.** A
  main theorem whose conclusion listed about forty labels went through the faithfulness reviews
  while the shape checker skipped its environment. Its rewrite states five clauses with formulas;
  the map to the supporting results follows the theorem. Put every main-theorem environment in the
  checker's list.

## Definitions

- **Words: target 120, cap 200.** In the first drafts one section was 92% definitions, one of them
  776 words long ([L14](../../lean-to-manuscript/references/lessons-learned.md#l14)).
- **Only what the reader needs at that point.** The opening part defines the public objects needed
  to state the main theorem; machinery is defined where it is used.
- **Concrete, by formula, with one sentence of purpose**, followed by one to three interpreting
  sentences. Never a translation of a Lean structure, never a list of types, never a description in
  place of the formula. Give each item of a property list its own label.
- **Trace every chain**: a sum has its index set and summands, a recursion its initialization and
  update. A symbol is introduced only if a displayed definition, statement or identity uses it.

## Proofs

- **Dependency sentences, not reference lists.** Drafts written from a formal source tend to open
  proofs with "Use Definitions … and Lemmas …". Replace such openings by sentences that say what
  each input does:

  > By Lemma~\ref{lem:energy}, which bounds the energy of the background by its boundary values,
  > the integrand in~\eqref{eq:split} is at most $C\epsilon^2$.

  An optional "Inputs:" line may close the proof; delete closing tails that repeat the references.
- **One interpreting sentence after a dense estimate**: what is small, why, and which loss it pays
  for ("the factor $L^{-1}$ per relative coordinate beats the $L^{2}$ choices of anchor; this is the
  contraction").
- **"Idea of the proof. Step 1 … Step k"** before a long proof, one display per step.
- **About one numbered lemma per page.** A proof longer than three pages is split at a genuine
  intermediate statement, or its allowance is renegotiated with the editor before drafting.
- **Standard results cited exactly**: name, hypotheses, numbering, checked against the source
  before the citation is written, even where the Lean proves the result from scratch.
- **Representative cases**: one case written out, the reason the others are identical, the formal
  check recorded in the correspondence table; never for a main estimate.

## Vocabulary

- **No Lean names, Lean syntax, file paths or process words in the TeX, comments included**
  ([L28](../../lean-to-manuscript/references/lessons-learned.md#l28)). Comments travel with the
  source. The one exception is the source-disclosure text, delimited by marker comments and
  bounded in length; in the Yang–Mills manuscript there are two such regions, the end of the
  abstract and the source paragraph of the introduction. The formal development appears nowhere
  else; the correspondence table is published separately.
- **No banned words** (`latex-math-writing`'s list) and no habitual machine phrasing.
- **Terminology from the literature**, from the terminology table; every term a human reader uses
  is kept ([terminology](terminology.md)). In prose, cite a result by number and name ("Theorem 4.2
  (fixed-volume limit)"); statement tags stay in titles.

## Numbering

- **Never redefine counters or `\the…` macros; numbering is global; refer to every numbered item by
  `\ref`, never by a typed number** ([L17](../../lean-to-manuscript/references/lessons-learned.md#l17)).
  Writers of parallel sections restyled their own counters; later-part numbers collided with
  addresses used in the opening part, and typed numbers went stale. The later part continues the
  opening part's section numbering.
- **Keep reader-facing tags in statement titles** (axiom labels, principal tags) and remove only
  internal codes ([L18](../../lean-to-manuscript/references/lessons-learned.md#l18)). An integration
  stripped axiom labels from definition titles although the main theorem refers to them; its owner
  caught it.

## Figures

A figure expresses one mathematical idea in the paper's notation, as editable TikZ; the text refers
to it; it counts against its section's pages; it is reviewed for truth like a sentence: a phase
is not drawn as a set of configurations, and a quantity not proved monotone is not drawn as
monotone. Design and review: `math-figures`.

## Length

Every section has a page allowance, measured on the compiled PDF
([L7](../../lean-to-manuscript/references/lessons-learned.md#l7)). Over a cap means not done. For
the hardest sections make completeness binding and the figure a guide, and police padding instead
([L23](../../lean-to-manuscript/references/lessons-learned.md#l23)): a plan made before the pilots
can be far too small for them. In an editorial pass every section has a page budget, additions are
offset by cuts in the same section, figures count, any single addition over one page needs a
reason, and the whole manuscript has a ceiling agreed with the author. Measure before and after
every pass: an agent that reports a cutting pass done may have added pages
([L2](../../lean-to-manuscript/references/lessons-learned.md#l2)).
