# Claims, disclosure and status

What to say about who wrote the text and what was checked, how to mark its status, and what never to say.
Examples come from the Yang–Mills campaign (2026) and its public repository.

## 1. Three kinds of checking, named separately

A sentence such as "written by checking every statement against the Lean" merges three different things
([L30](../../lean-to-manuscript/references/lessons-learned.md#l30)). Name each one, with its evidence:

| kind | done by | on record | evidence to link |
|---|---|---|---|
| kernel check of the formal proof | the Lean kernel | the formal proof terms check against the formal statements, with the listed axioms, trusting the kernel and the libraries | the formal source's verification log at the pin (in the campaign: a type comparison, an axiom check for seventeen named results, a kernel replay of 100,168 declarations, axioms `propext`, `Classical.choice`, `Quot.sound`) |
| comparison of statements with declarations | AI agents | reviewers were asked to compare each numbered statement with the declarations it rests on (hypotheses, definitions, quantifier order, normalizations, conclusions), using only declarations in the closure of the main theorem, and their reports and the table record what they found | the correspondence table, its check, the process page |
| the prose arguments | AI agents wrote and reviewed them | nothing mechanical; the reviews are recorded | the process page |

Add the sentence that ties them together: a correct formal declaration does not by itself show that an English
statement has kept its hypotheses and quantifiers, or that a prose proof proves that statement.

**What a script verified, and what it did not.** Of the agents' comparison only the record is checked
mechanically: `check_correspondence.py` verifies that every numbered statement has a row, that every listed name is
in the closure and that the pins hold; the driver of `writing-workflow` verifies that each review report has its
minimum length and a verdict line; its coverage check (`check_coverage.py`) lists the labels that no report
mentions. No script verifies that a reviewer compared a statement, nor that the comparison is right. Write "the
agents compared every numbered statement" only when the table has a row for each and the coverage check is clean.

## 2. Authorship

- **The author line is the author's decision**
  ([L31](../../lean-to-manuscript/references/lessons-learned.md#l31)). Agents never choose an author line or a
  persona. The Yang–Mills manuscript has a blank author line.
- **One wording, everywhere.** The abstract's last sentence, the introduction's paragraph on sources, the title
  page (if it carries a note), the README of the manuscript, the repository description and the abstract in the
  citation metadata say the same thing in the same words. Two places that describe authorship in different words
  are a defect that only a reading of every page finds
  ([L29](../../lean-to-manuscript/references/lessons-learned.md#l29)); check it mechanically as well: search every
  place for the exact sentence (the pre-publication checklist does).
- **What people did** (directed the work, approved the statements, read parts) is said in the author's words and
  no more strongly than it happened.
- **The paragraph on sources** in the introduction names the formal source with its commit and link, the three
  kinds of checking as three items, the process page, and collaborating projects. It is the one place where the
  vocabulary check allows "Lean" and links; mark it as an exception region.

## 3. Wordings: under construction, and finished

Fill in [the templates](../assets/disclosure-wordings.md). The abstract of the Yang–Mills manuscript (second
draft) ends with the wording for the period under construction:

> This paper was written entirely by AI agents from OpenAI's Lean code for the construction of four-dimensional
> quantum Yang–Mills theory (commit `3456e5e`). The Lean proof is kernel-checked, with only the standard axioms.
> The agents compared every numbered statement here with the Lean declarations used by the main theorem; the
> correspondence table is published separately. The prose arguments were written and reviewed by AI agents. They
> are not machine-checked and have not been refereed by human mathematicians.

It says that the correspondence table is published separately, so the table (3,232 rows for the whole
manuscript) is public with it.

The finished wording is shorter: three kinds of checking are involved; the kernel checks the formal proof; agents
compared each numbered statement with the declarations it rests on; the prose proofs are not machine-checked and
remain subject to mathematical review. Rules:

- Switch wordings only when the author declares the text finished and the markers come off.
- **Preconditions** before a wording goes into the PDF: publish the table before any text says it is published;
  "compared every numbered statement" only as section 1 allows; the axiom sentence matches the
  verification log; the section it points to exists.
- If human mathematicians later referee or read the text, say who read what, in the author's words.

## 4. Status words with defined meanings

Every status word on a public page is defined by the review it records and by what it does not mean
([L32](../../lean-to-manuscript/references/lessons-learned.md#l32);
[template](../assets/status-table.template.md)). The campaign's definitions:

| word | records | does not mean |
|---|---|---|
| section *reviewed* | the full review cycle ran: owner, fresh-reader and truth reviews, re-check, delivery review | that a human has read it |
| section *checked* | the project lead read it and the changes it led to were made | a referee's report |
| outline *draft* | a first account written from the source and the key statements | that the next two reviews ran |
| outline *compared* | a second model compared the numbered statements with the linked Lean, read the main steps, corrected the account | that subsidiary estimates were read |
| outline *edited* | a third model compared again and edited the exposition | an independent human proof review |
| glossary *certain*, *probable*, *tentative* | the strength of the interpretation of a nickname | a review status, or mathematical correctness |

The Yang–Mills map used "checked" for outlines and for sections, with two meanings; this collection keeps the
words apart: *checked* only for a section the author has read
([L32](../../lean-to-manuscript/references/lessons-learned.md#l32)).

Statuses are dated, with one line on what changed and what comes next. A status of the explanation never implies
that the formal result is unproved.

## 5. Under-construction markers

- **Where:** a banner at the top of the manuscript's page (state, date, what is under way, a link to the status
  table, "Do not cite it as a finished proof"); a note on the title page; the repository description; the links
  from companion pages ("under construction"); the process page's "it is not finished".
- **Removal:** only when the whole text is checked, by the author's decision; recorded in the changelog, together
  with the switch to the finished wording.
- The author may choose fewer markers; record the choice and keep the rest consistent. In the campaign the PDF's
  running footer and a longer title-page note were replaced by a dated draft line, while the banner and the status
  table stayed.

## 6. Never claim

| claim | why not | say instead |
|---|---|---|
| the prose is checked, verified or correct | AI reviews are not a referee's report; reviewers share training and blind spots | written and reviewed by AI agents; not machine-checked; not refereed by human mathematicians |
| an agreement statistic as accuracy | the campaign's κ = 0.72 measured agreement between two AI readers on importance labels; accuracy (14 of 15 sampled sentences) was measured only on an earlier project ([L8](../../lean-to-manuscript/references/lessons-learned.md#l8)) | κ measures agreement, not correctness; name the project on which accuracy was measured |
| the graph comparison checks the map | the reached sets matched the authors' record up to 50 of about 74,000 declarations; that compares sets ([L4](../../lean-to-manuscript/references/lessons-learned.md#l4)) | it tests coverage at those roots, not edges, roles or English text |
| a loaded compiled build is a rebuild | "all build jobs up to date" means nothing was recompiled ([L33](../../lean-to-manuscript/references/lessons-learned.md#l33)) | convenient for exploring; here is the rebuild recipe |
| anything stronger than the Lean | the main theorem's limits are part of the result | list the nonclaims on the statement page (for example: a limit taken only along a subsequence; one selected phase where the detailed construction gives every phase; no universality in the lattice data) |
| priority | a description of features is not a literature comparison | "not a systematic literature comparison or a claim of priority for each ingredient"; a table of mechanism, closest earlier result and present use |
| collaboration or a status as review | they record who took part and which agent review ran | say who read what |
| a complete or finished proof, while markers are up | the text is a draft | first draft, under construction |

## 7. The FAQ and its evidence table

Answer the questions readers ask (what exactly is proved, why a limit is only subsequential, what a technical
word means, what was checked by Lean and what by agents, whether the English statement is faithful, how far to
trust an outline status, whether the graph verifies the explanations, how to check something yourself, how to
report and cite) in a few sentences each, linking to the exact anchor, never claiming beyond the statement page.
End with the evidence table: one row per check, with what it establishes and what it does not
([template](../assets/faq-evidence-table.template.md)).
