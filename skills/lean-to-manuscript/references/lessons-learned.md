# Lessons learned

The failures met when turning OpenAI's Lean proof of the construction of four-dimensional quantum Yang–Mills theory
into a natural-language manuscript (2026), and the fix adopted for each. Every skill in this collection cites these
lessons by ID. Facts about that campaign come from its public repository (its pages, data, process page, changelog
and history) and from the public Lean source; the rest of each entry is the general rule. Each entry says what
happens, the fix, and which skill carries the fix.

Two lessons stand above the others. Rules that nobody measures are not followed ([L1](#l1)). Reviews that check
faithfulness do not check readability, and the reverse ([L10](#l10)).

## Method

<a id="l1"></a>
### L1. Written rules were not followed until a program measured them

The campaign repeated two failures of an earlier project of the same kind (a paper written from a completed Lean
proof): statements shaped like the formal code ([L9](#l9)) and text that grew without limit ([L7](#l7)). The rules
against both were already written down. What works is a program that measures (statement length, cross-references
per statement, forbidden vocabulary, pages per section) run after every round, and a reviewer whose only job is the
rule.
**Fix:** every binding style rule that can be measured is enforced by a script run after every integration
(see `exposition-standards`); the rest get a dedicated reviewer.

<a id="l2"></a>
### L2. An agent's "done" is not evidence of work done

An agent reports a pass complete when it stops, whether or not the pass did its job; a pass meant to shorten a text
can return it longer.
**Fix:** measure pages before and after every pass; a pass is done when its measured allowance is met and its
response table is complete, not when the agent stops (`writing-workflow`, `lean-to-manuscript`).

## Mapping the Lean

<a id="l3"></a>
### L3. A dependency graph read from source text was wrong in bulk

Before compiled files were available, the graph was parsed from the source text: 0.96 million references, of which
about 57,000 resolved to the wrong declaration. The graph read from the compiled `.olean` files added 1.36 million
references that the text missed, nearly all implicit (section variables, structure projections, instances, unfolded
definitions, notation). One dependency between units was missing, and some published links between units rested on
wrongly resolved names.
**Fix:** extract references from elaborated types and proof terms in the compiled files, attribute generated
auxiliary constants to their owners, and label any text-derived graph as such (`lean-dependency-graph`).

<a id="l4"></a>
### L4. The graph was compared with the authors' own record, and every difference explained

The release contained a usage record of the declarations reached from seventeen headline results. The compiled
closure from the same roots had 74,093 declarations; the record, after attribution of auxiliaries to their owners,
74,115. The sets differed by 50: 36 constructors that the record reaches through recursors, and 14 small definitions
reached through shared auxiliary constants.
**Fix:** compare the closure with any record the authors publish, explain each class of difference, and say what the
comparison does not check: individual edges, mathematical necessity, any English text (`lean-dependency-graph`,
`honest-publication`).

<a id="l5"></a>
### L5. The development contains routes that the main theorem does not use

The process page says it plainly: the source contains alternative routes that the main theorem does not use, and they
are not evidence for anything in the manuscript. The headline list itself can mix them in: the data notes of the
Yang–Mills map point out that the closure of all seventeen headline roots is broader than the closure of the main
construction alone and includes alternative constructions. A description read from such code can be fluent, precise
and wrong about the theorem.
**Fix:** cite as evidence only declarations in the closure of the main theorem (`used = 1`); when the headline roots
include alternative constructions, compute the main theorem's own closure separately; check before writing "the Lean
does X" (`lean-dependency-graph`, `statement-spine`).

<a id="l6"></a>
### L6. Folders and names record the history of the code, not its mathematics

About three quarters of the code filed under "full volume" belongs to the ultraviolet construction; the genuinely
infinite-volume argument is about 7,000 lines. The code names its objects by nicknames (`Treasury`, `Jewel`,
`Sheet`, `sails`). On the other hand, about seventy numbered "work items" in the code (each one obligation, proved in
its own file) gave a ready-made skeleton for three parts of the proof.
**Fix:** cut parts and units from the graph and the mathematics, not from folders; translate nicknames in a glossary
with a confidence label (certain, probable, tentative); reuse any decomposition the authors made explicit
(`coarse-graining`).

<a id="l7"></a>
### L7. Outlines grew 4.4 times past their template because nobody measured

The unit outlines grew to 4.4 times their intended length over several rounds of review (draft, comparison with the
Lean, editing): each round added detail and none measured the total.
**Fix:** an allowance from the size of the unit (this collection uses one page, about 500 words, per 4,000 Lean
lines, between 3 and 10 pages), measured when a draft lands, with one retry that quotes the measured overrun; the long
version kept separately as detailed notes; the condensed outline checked against the notes for fidelity
(`coarse-graining`).

<a id="l8"></a>
### L8. Agreement between AI readers is not accuracy

Two independent readers labelled 2,424 candidate statements (main result, key result, technical lemma,
bookkeeping); Cohen's κ = 0.72 on "main or key" against the rest. On an earlier Navier–Stokes formalization, whose
human paper is known, selection matched that paper about twice as well as graph ranking alone, and 14 of 15 sampled
summary sentences were accurate; those spot checks were not repeated on Yang–Mills.
**Fix:** publish κ as agreement only; measure accuracy separately and say on which project (`coarse-graining`,
`honest-publication`).

<a id="l36"></a>
### L36. A release can declare its headline theorem twice

The Yang–Mills release contains a reference challenge file that states the main theorem with a placeholder proof
(`sorry`), and the solution, which proves it under the same name. Read side by side from the compiled files the two
collide, and an extraction that kept the first one would mark the placeholder as the main theorem.
**Fix:** stop on any name declared in two modules; exclude the module that the roots do not import; flag every
declaration in the closure whose proof uses `sorry` (`lean-dependency-graph`).

## Statements

<a id="l9"></a>
### L9. Statements took the shape of the Lean

The first drafts copied the Lean's long conjunctions and packaging structures: propositions ran to nearly a page, and
one section was 92% definitions, one of them 776 words long. The drafts were faithful and unreadable, and were
rejected.
**Fix:** natural form (one result per statement, quantifiers first, conclusion displayed, objects set up in the prose
before it, side conditions moved to later lemmas) with caps enforced by a program (statements: target 100 words, cap
150; definitions: target 120, cap 200), and a clause map showing that the union of the natural statements equals
what the Lean proves (`statement-spine`, `exposition-standards`).

<a id="l10"></a>
### L10. A main theorem that listed about forty labels passed the faithfulness reviews

The first version of the detailed main theorem (Theorem B) had a conclusion that listed about forty labels of other
results (it is in the public history of the manuscript). It went through the owner and fresh-reader reviews, which
judge faithfulness, and the shape check did not yet cover main theorems. It was restated as a theorem of five
clauses.
**Fix:** the shape check covers main theorems (this collection's defaults: at most 250 counted tokens, formulas
included, and 8 references); every other statement has at most 4 cross-references or tags (definitions 6): a
statement must state, not list. A main theorem states its conclusions in clauses with formulas; the map to supporting
results is in the text after it. Ask of every main theorem: would a referee accept this as the statement of the
paper's result? (`statement-spine`, `exposition-standards`)

<a id="l11"></a>
### L11. A principal statement was weaker than the Lean

Theorem B as first written said that data with the required properties exist, not that they are the objects
constructed. Its owner rejected it on correctness; the repair changed a frozen statement and went to the project lead.
**Fix:** owner reviews check strength in both directions; every change to a frozen statement follows the drift
protocol (`statement-spine`, `writing-workflow`).

<a id="l12"></a>
### L12. "There exists" against "for every" is settled by the Lean, not by the natural reading

A natural reading can strengthen a statement without anyone noticing: a construction that the formal proof shows to
work for one admissible choice of its constants reads naturally as working for every choice.
**Fix:** the clause map records quantifier order and existence or universality for every clause, and scope-sensitive
clauses cite the declarations that fix them (`statement-spine`).

<a id="l13"></a>
### L13. Hypotheses moved out of statements had to be put back

After the referee round, hypotheses that had been moved from lemmas of the ultraviolet sections into the surrounding
prose were restored inside the statements. A statement shortened that way still passes a word cap and reads well;
its users silently lose a condition.
**Fix:** a statement carries every hypothesis that its users rely on; a cap is met by splitting the statement or by
defining objects earlier, never by moving hypotheses out (`exposition-standards`, `statement-spine`).

<a id="l14"></a>
### L14. Definitions crowded out the theorem

One section of the first drafts was 92% definitions. The second draft rebuilt Part I around the main theorem, which
now appears on page 14.
**Fix:** the opening part defines only the public objects needed to state the theorem, each by formula with one
sentence of purpose and one to three interpreting sentences; machinery is defined where it is used; the literal formal
statement goes to a section of its own (`statement-spine`, `exposition-standards`).

<a id="l15"></a>
### L15. The formal statement is not the theorem a reader wants

The literal formal statement (Theorem A) follows the exported formal specification; the theorem a reader wants is the
detailed construction (Theorem B). The second draft states Theorem B first and gives the formal statement, compared
definition by definition, in a section of its own at the end of Part I.
**Fix:** state the natural main theorem first and keep the literal formal statement in a separate section or
appendix (`statement-spine`, `honest-publication`).

<a id="l16"></a>
### L16. One drafter's spine is one opinion

The choice of principal statements fixes the architecture of the whole paper, and a single drafter fixes it on one
reading of the code.
**Fix:** two independent spine drafts, a reconciliation listing the structural decisions, and author approval before
freezing (`statement-spine`).

## Writing

<a id="l17"></a>
### L17. Numbering broke between parallel sections

The proof sections were first lettered and later numbered to continue the opening part. Part II numbers collided
with addresses used in Part I, and typed numbers went stale.
**Fix:** writers never redefine counters or `\the…` macros; numbering is global; every numbered item is referred to
by `\ref`, never by a typed number; the proof part continues the opening part's section numbering (`writing-workflow`,
`exposition-standards`).

<a id="l18"></a>
### L18. The editor's integration introduced errors

Integration stripped axiom labels from definition titles although Theorem A refers to them, and a deletion left a
sentence broken; the reviews caught both.
**Fix:** keep reader-facing tags in statement titles and remove only internal codes; the integrated text goes through
the same frozen-packet reviews as proposals; the main theorems are compared byte for byte with the approved text
after every pass (`writing-workflow`).

<a id="l19"></a>
### L19. A pilot assumed what it had to prove; another dropped a hypothesis

The first draft of the infinite-volume pilot used two inputs as hypotheses with no statement to cite; the mathematical
review found the declarations proving them. The first draft of the coupling-reset pilot omitted a bound on a kinetic
constant that the Lean carries, without which one of its identities fails.
**Fix:** every input is a labelled statement that exists, or a written request to the section that must prove it;
the mathematical review checks every step against the Lean (`writing-workflow`, `cross-section-consistency`).

<a id="l20"></a>
### L20. Fluent explanatory sentences were false

For example, a sentence attributed a smooth extension to the wrong estimate, and a unit was stated so that, read
naturally, one axiom would be false for fields of positive degree. An earlier project of the same kind found roughly
one false explanatory sentence per ten to fifteen pages after a style pass.
**Fix:** a prose-truth review marks every explanatory sentence true, false or unsupported, with evidence, and traces
every removed condition to its uses (`writing-workflow`).

<a id="l21"></a>
### L21. Parallel sections cited each other for more than the cited statements said

Ten proof sections were written in parallel. Their proofs cited each other's lemmas for more than the lemmas stated
(typically for something the cited proof gives but its statement omits), and one lemma had to be restated for its
uses.
Three rounds of checks and repairs were needed; the last confirmed every item resolved.
**Fix:** the routed-inputs check (MATCH or MISMATCH for every citation across sections), repairs on both sides, and
rounds until a targeted re-check confirms every item (`cross-section-consistency`).

<a id="l22"></a>
### L22. Reviewer failures are silent

A reviewer that runs with read-only tool permissions cannot write a report file it was asked to write, and a lookup
it is not allowed to run is simply skipped; the verdict then rests on the text alone, and nothing fails visibly.
**Fix:** reviewers print their report as their final answer and the driver saves it; the driver checks a minimum
length and a verdict line; every report states first which sources it actually consulted; test a reviewer profile's
permissions before a round (`writing-workflow`).

<a id="l23"></a>
### L23. Page plans made before the pilots were too small for the hardest sections

The process page planned the proofs at about 120 pages; the first complete draft had about 190 and the second about
220, most of the growth in the sections of the ultraviolet construction, which carries about 70% of the formal
development. A complete proof at the agreed level of detail can need far more room than a plan made before anything
was written.
**Fix:** derive allowances from the measured frozen statements and the pilots; for the hardest sections make
completeness binding and police padding instead; bring a projected overrun to the author with measured options
before continuing (`writing-workflow`, `lean-to-manuscript`).

<a id="l24"></a>
### L24. The author's calibration of the pilots is the most valuable input

Two pilot sections, one on each side of the proof, went through the whole review cycle and were read by the project
lead before the other eight sections were written; comments on level and length became binding rules for the sections
not yet written.
**Fix:** pilots first; turn calibration comments into the binding style file the same day and review later drafts
against it (`writing-workflow`).

## Review and revision

<a id="l25"></a>
### L25. Referees find real gaps; their proposed fixes are often wrong in detail

Three referees read the whole first draft (Part I; Sections 10–14; Sections 15–19), and every suggestion was
adjudicated against the text and the Lean before anything was applied. In the ultraviolet sections this filled real
gaps from the Lean's own arguments: a single-valued step map, the convergence of the free forms, the leading map of
the marked expansion, the block-to-fine comparison, the torus localization. A referee's diagnosis can be right while
the change it proposes says more, or less, than the Lean proves.
**Fix:** never apply referee text directly: adjudicate every suggestion (accept, accept modified, reject, author),
apply through writers, confirm before integration (`referee-adjudication`).

<a id="l26"></a>
### L26. Human readers outrank agent reviewers

Agent reviewers and human readers often comment on the same passages and sometimes disagree; agents also propose
renaming terms that a human expert uses on purpose.
**Fix:** editorial plans rank human readers above agents, keep every term a human reader uses, and record the source
of every planned change (`referee-adjudication`).

<a id="l27"></a>
### L27. Another draft of the same proof may have better devices and weaker statements

When another draft of the same proof exists, its presentation can be better (an "Idea of the proof, Step 1…k"
paragraph with one display per step, interpreting sentences after each definition, labels for each item of a property
list) while its statements are weaker or its proofs incomplete.
**Fix:** compare with any other draft; adopt devices, import no statements (`referee-adjudication`).

<a id="l28"></a>
### L28. Code vocabulary leaks into the paper

Writers who read the code reuse its words: nicknames, names of packaging structures, private technical terms. Each is
defined somewhere and still reads as jargon, and many have a standard name in the literature.
**Fix:** a terminology table before the editorial pass; the vocabulary check rejects Lean names and process words in
the TeX, comments included (`exposition-standards`).

<a id="l29"></a>
### L29. Typography needs eyes on every page

A clean compile says nothing about the pages: broken displays, floats leaving a third of a page blank, a one-word line
before a display, and two passages that say the same thing in different words are found only by looking.
**Fix:** a typographic pass over the rendered pages, with a defects table (page, quote, defect, fix) and a list of
clean pages, before any release (`referee-adjudication`, `honest-publication`).

## Publication

<a id="l30"></a>
### L30. One sentence merged three kinds of checking

A draft abstract said that the text was written by checking every statement against the Lean. That merges the kernel
check of the formal proof, the agents' comparison of statements with declarations, and the prose, which nothing
checked mechanically.
**Fix:** name each separately: the formal proof is kernel-checked, with the axioms used; agents compared each
numbered statement with the declarations it rests on; the prose arguments were written and reviewed by AI agents,
are not machine-checked and have not been refereed by human mathematicians (`honest-publication`).

<a id="l31"></a>
### L31. Authorship is the author's decision

Who is named on a text written by agents, and how the agents are credited, is the author's decision alone. The
Yang–Mills manuscript has a blank author line, and its abstract ends by saying that the paper was written by AI agents
from the Lean code.
**Fix:** agents never choose an author line or a persona; one disclosure wording, used everywhere
(`honest-publication`).

<a id="l32"></a>
### L32. Status words must each mean one thing

Outline statuses (draft, checked, edited), glossary confidence labels (certain, probable, tentative) and section
statuses (reviewed; checked only after the project lead's reading) each needed a published definition stating which
review the label records and what it does not mean. Even so, "checked" ended up meaning an agent's comparison with
the Lean for an outline and the project lead's reading for a section.
**Fix:** a status table with defined meanings and one meaning per word (this collection calls the outline status
"compared"); under-construction markers until the whole text is checked (`honest-publication`).

<a id="l33"></a>
### L33. Loading a compiled build is not rebuilding it

The compiled build was released for readers: 2.2 GB compressed in two parts, 8.8 GB unpacked. Its instructions say
that the commands check the download's checksum and reuse the compiled files, and do not rebuild the proof; the
rebuild recipe is given separately.
**Fix:** release builds with checksums and a check in a fresh clone, and state what loading them establishes
(`lean-dependency-graph`, `honest-publication`).

<a id="l34"></a>
### L34. A shared machine limits what may run at once

Compiling a development of about one million lines takes hours, and reading the compiled files of thousands of
modules takes gigabytes of memory per process; two such jobs at once starve every other user of a shared machine.
**Fix:** one heavy job at a time, throttled; chunked extraction; never rebuild what an official cache provides
(`lean-dependency-graph`).

<a id="l35"></a>
### L35. Work done while the author is away needs a list of decisions

Long unattended runs (review rounds, adjudications, repairs) meet decisions that are the author's. Taken silently,
they change the text without approval; left untaken, they stop the run.
**Fix:** take only reversible provisional decisions, never change a frozen statement, and queue each decision in a
list for the author as you go, with the provisional choice and how to revert it (`lean-to-manuscript`).

## Adding a lesson

Append a new lesson with the next free ID at the end of its group; never renumber or delete one (other skills link to
the IDs). Give what happened, the fix as a rule, and the skill where the rule now lives; then add the rule to that
skill and cite the ID there.
