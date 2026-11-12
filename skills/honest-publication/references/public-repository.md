# The public repository

How the Yang–Mills campaign (2026) published its work, generalized. Its public repository is
`https://github.com/scottnarmstrong/yang-mills-informalization` (README, `statement.md`, `method.md`, `faq.md`,
`CHANGELOG.md`, `manuscript/PROCESS.md`).

## 1. Public and private

- **★ Visibility is the author's decision.** In the campaign the author chose to write the manuscript in public:
  TeX, PDF and a reader-facing README in the public repository; the brief, plans, spine drafts, prompts, reviews
  and working scripts in a private one. The manuscript began in its own public repository and later joined the
  companion repository as its most detailed level, with its history imported; the old repository was archived
  with a pointer.
- **Every public commit passes the vocabulary check** of `exposition-standards` (`check_vocabulary.py`) on the
  manuscript's TeX, comments included: no process words (packet, spine, owner review, proposal), no banned words
  (ledger, gate), no Lean names outside the paragraph on sources
  ([L28](../../lean-to-manuscript/references/lessons-learned.md#l28)). That paragraph is the one marked exception
  region, where "Lean", the commit and links are allowed. The process page may name the process; no public file
  may contain private paths, account names, machine names or names of wrapper programs.
- **Nothing private leaks.** No links into the private repository; review reports, prompts and human readers'
  notes are not quoted publicly without permission; working numbers are published only with their scope.
- Run the [pre-publication checklist](../assets/prepublication-checklist.md) before every push.

## 2. Levels of detail

Present the same proof at several levels, each linking down to the next, so that a reader can stop at any depth.

| level | page | what it gives | Yang–Mills |
|---|---|---|---|
| 1 | the main theorem | the formal statement verbatim, a commentary in words, the full statement in ordinary mathematics, what is and is not claimed | `statement.md` |
| 2 | the proof in one reading | the strategy, the key mechanism of each part, what is new, where the difficulty lies, which steps are not yet explained | `summary.md` |
| 3 | the architecture | the parts, what each hands to the next, the interfaces | eight parts |
| 4 | the units | per unit: an outline of three to ten pages, detailed notes, a Lean map with every key statement linked to its lines | 32 units; 989 key statements over 413,000 attributed lines; outlines as one 164-page PDF, notes as a 595-page PDF |
| 5 | the full manuscript | the complete proof for a specialist reader | 265 pages (second draft) |

- From level 3 down, every claim about the code links to the exact lines at the pinned commit.
- Each page states its own review scope and status; different levels have different scopes, and the README
  says so.
- Levels 2–4 are built with `coarse-graining`; level 5 with `writing-workflow`; level 1 with
  [the statement page](correspondence-and-statement.md).

## 3. Reference material

| page | contents | rule |
|---|---|---|
| provenance | which parts follow which earlier programmes, which are standard, which appear new, component by component, with the evidence on both sides | not a claim of priority (see [claims](claims-and-status.md)) |
| glossary | the code's nicknames translated into mathematics, each with a confidence label (certain, probable, tentative) | the labels are defined and are not review statuses |
| work items | the code's own decomposition into stated obligations, with what each proves | quote the code's numbering |
| method | separate sections for the kernel check, the interpretation of the statement, the dependency graph and its comparison with the authors' record, the selection of key statements, the review of the explanations | each section ends with what it does not establish |
| FAQ | questions readers ask, each answered with links to the exact place, ending with the evidence table | [template](../assets/faq-evidence-table.template.md) |
| changelog | reader-facing publications and corrections, dated | [template](../assets/changelog-entry.template.md) |
| data | the tables behind the map, with a dictionary | below |
| process page | how the manuscript is written: roles, the review cycle, the automatic checks, the records, what the process caught, what it does and does not establish, dated changes to the process | public version of the working method, without private material |

**The data dictionary** lists every file; states the format (UTF-8, tab-separated, one header row, counts exclude
the header); defines each counting scope with the query that produces it; and gives a data version that is
separate from the source commit and from any review status. The campaign's dictionary distinguishes 74,171 rows
flagged as used from 74,093 distinct used declarations (78 repeated names) and shows the
`COUNT(DISTINCT name)` query. Publish the tables only with their scopes: a count of allocated declarations is not
a count of the closure.

## 4. Pins and links

- Fix one commit of the formal source and link every Lean reference to it with the full hash; say so in the
  README. Link the formal source's own verification log and usage record at that commit.
- When the pin changes, re-pin every link and the correspondence table, re-run its check, and record the change
  in the changelog.
- A compiled build released for readers comes with checksums, a fresh-clone test and the sentence that loading it
  is not an independent rebuild ([L33](../../lean-to-manuscript/references/lessons-learned.md#l33);
  `lean-dependency-graph`).

## 5. Corrections, citation, licences

- **Reporting a correction.** Every page ends with a link to the issue tracker and the instruction: give the page
  and heading, quote the sentence, and propose a correction or give a pinned Lean link; include the repository
  revision and the unit or result identifier, so the wording can be found after later edits. A correction is
  applied through the same reviews as any other change and, if a reader could have been misled, recorded in the
  changelog.
- **Citation metadata.** A `CITATION.cff` with title, type, repository, an abstract that uses the disclosure
  wording, the authors as the author decides, keywords, licence, and references to the formal source and to
  collaborating projects. The README's "How to cite" asks for the revision consulted and the fixed Lean commit, and
  says to cite the Lean source separately when referring to the formal proof.
- **Licences.** Quoting formal statements verbatim and redistributing a compiled build are uses of the formal
  source: follow its licence, keep its copyright notice, and say under which licence it is released (in the
  campaign, Apache 2.0 for both the source and the companion repository). Releasing a Lean repository itself is
  the subject of `lean-public-release`.

## 6. Companion pages and collaborating projects

- A companion website with audited summaries and Lean badges is built with `visual-paper`, whose integrity
  controls apply there: a page that describes its checks must still be true of every claim it shows after later
  edits, and edits published without a new audit are recorded as such, never counted as audited. An automatically
  generated HTML rendering of the repository may be linked, saying how it is generated.
- Name collaborating projects and what they contribute, in the author's words. Collaboration is not review: the
  campaign's FAQ says that collaboration does not mean every outline has received an independent human proof
  review.
- Every companion page that links to the manuscript repeats its status ("under construction") until the author
  removes the markers.
