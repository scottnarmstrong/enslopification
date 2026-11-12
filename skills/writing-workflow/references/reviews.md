# The reviews

Five kinds of review, each by a separate agent with a fresh context, on a frozen packet. They exist because a review
that checks faithfulness does not check readability, and the reverse: a main theorem that listed about forty labels
passed every faithfulness review ([L10](../../lean-to-manuscript/references/lessons-learned.md#l10)). Prompt templates:
[`assets/prompts/`](../assets/prompts/) (`review-preamble.md` is shared). Reviewer rules that hold for any paper
(give the actual text bound to a revision, read a returned finding before acting on it) are in the shared controls of
`math-paper-campaign`.

## Common rules

- **Read-only, report printed.** The reviewer cannot write; it prints its report and the driver saves it. A prompt
  that asks a read-only reviewer to write a file produces nothing visible
  ([L22](../../lean-to-manuscript/references/lessons-learned.md#l22)).
- **Frozen snapshot.** The verdict applies to the packet named in its manifest. `verify_packet.py --sources` later
  says whether the text has changed since.
- **Another model family** than the writer of the packet.
- **Report format:** "Sources consulted" first, before any finding, including every source the reviewer tried and
  could not reach, so that a refused tool shows at once
  ([L22](../../lean-to-manuscript/references/lessons-learned.md#l22)); findings with id, severity (BLOCKER, MAJOR,
  MINOR), quoted location, evidence and exact repair; what was checked and found correct, every statement named by
  its label; what the review does not establish; a final verdict line. The driver refuses a report below the length
  minimum or without its verdict line and retries once; it reads nothing else in it.
- **Authorities:** the natural spine for the text of every frozen statement; the frozen contracts and the clause map
  for what each statement must carry (both copied into the packet); the Lean, read at the pinned commit, for the
  mathematics.
- **Never retract silently.** A reviewer that changes its mind says so in the report.

## Owner of a principal statement

One reviewer per principal statement, as a separate job, with three criteria:

1. **Correct** against the natural spine (a main theorem byte for byte), against every clause of the frozen
   contracts that the clause map assigns to it, and against the Lean: quantifier order, existence against "for
   every", uniformities, the order in which constants are chosen, every hypothesis; strength in both directions.
2. **Understandable from the preceding text.** The owner reads the manuscript in order up to the statement before
   opening any source, then inventories every symbol, object and quantifier and where it was defined.
3. **Serves its consumers.** The owner maps every use of the statement and tries to break the implication each use
   needs.

The criteria catch different things. In the Yang–Mills campaign (2026) the owner of Theorem B failed it on
criterion (i): as written it said that the required data exist, not that they are the objects constructed
([L11](../../lean-to-manuscript/references/lessons-learned.md#l11)). A statement can also be correct and serve its
consumers yet fail (ii), when it uses a term that the text before it never defines.

## Mathematical review

Every proof step against the Lean: correct, complete at the stated level of detail, never stronger than what is
proved; each correspondence row (the declaration exists, the main theorem uses it, it says what the row claims) and
each cited literature result. **Gaps written around in assertive prose are the main target.** In the Yang–Mills
campaign the first mathematical review of the infinite-volume pilot found two inputs used with no statement to cite,
and the Lean declarations that prove them ([L19](../../lean-to-manuscript/references/lessons-learned.md#l19)). Read
the writer's notes beside the TeX: the notes can admit a gap that the TeX writes around.

## Fresh reader

An expert in the field, with no project context and no access to the Lean, the spine or the notes, reads the opening
part and then the section in order. **Every guess is a finding**, even when every symbol is technically defined.
The reader also judges length against the approved pilots and ends with two sentences on what the section proves and
how; the editor compares them with what the section is meant to prove. A summary that differs is a finding about the
section, not about the reader.

## Prose truth

Every explanatory sentence outside statements and displayed computations, and every table entry, is marked TRUE,
FALSE or UNSUPPORTED with evidence (a proof in the text, a Lean declaration, a cited source). **Every condition
removed or moved in a rewrite is traced to every place that uses it.** Fluent explanatory sentences were false in the
Yang–Mills drafts, for example one attributing a smooth extension to the wrong estimate, and such sentences survive a
style pass ([L20](../../lean-to-manuscript/references/lessons-learned.md#l20)). The same reviewer checks that every
"proved in Section X" points to a statement that exists and says that, and that each proposed edit to the opening
part is true.

## Re-check

The same reviewers (same roles, new contexts) read the new version against their own earlier reports: each finding
RESOLVED or NOT RESOLVED with the current text quoted; each declined finding's reason judged; new problems reported,
especially those the fixes created. A reason given for declining is a claim, and claims get checked.

## Delivery

The last review before a section is marked delivered. Hashes show that a file did not change after freezing, not
that the PDF was built from the TeX, and a read-only reviewer cannot recompile; so the stage's `build` has the
driver recompile `standalone.pdf` from the section file just before freezing, measure its pages, and list the labels
no earlier report names (`build.txt`, frozen into the packet). The reviewer checks the build and that the PDF's page
count and visible statements match the TeX; that every finding is closed or deferred to a named owner; reviews each
label no report named; and checks the owner cards, the register's proof addresses, references, and every rendered
page. It ends with DELIVER or NOT YET and what is required, and lists what it did not check: for example proofs
deferred to another section, correspondence rows outside the manifest, sources it did not reopen.

## Coverage

A report says what its reviewer did; nothing else does. `check_coverage.py` compares what the reviews were asked to
cover with what their reports name:

- **labels** from the register (`--register REGISTER.md --where section=15`), the section's statement environments
  (`--tex`), or a list: a label no report names is a gap. The delivery stage runs it over `r1` and `r2`, the editor
  again before integrating.
- **pages** (`--pages 1-50`): every page of a range must appear in a typography report's defects table or on its
  "Clean pages:" line ([`referee-adjudication`](../../referee-adjudication/SKILL.md)). A report that lists only its
  defects and says in one sentence that it found nothing serious elsewhere leaves every other page unaccounted for;
  the check names those pages.

A gap is a fact about the reports. A label named or a page listed is only a claim: the check reads text, not work.

## Asking for the least certain sentence

Writers name their least certain sentence in `NOTES.md`; reviewers are asked whether it is correct. One line points
the review at the place the writer doubted, and the reviewer answers with the reason, whichever way it goes.

## Failure modes of reviewers

| failure | guard |
|---|---|
| asked to write a report file without write permission; nothing visible | the report is printed and saved by the driver |
| a tool refused (database, PDF renderer); verdicts silently rest on less | preflight before the round; "Sources consulted" with what could not be reached |
| the reviewer read a stale copy (an old placeholder of the section in the manuscript) | the prompt names the copy under review; the packet holds both |
| a confident finding about a statement the reviewer reconstructed rather than read | the editor reads every finding against the cited text before acting |
| agreement between reviewers taken as correctness | reviewers are independent of the writers, not of each other's training; record that |

## What reviews do not establish

A report says what its reviewer did; nothing verifies the work behind it. What the scripts did verify is listed in
the skill's [honesty section](../SKILL.md#what-this-establishes-and-what-it-does-not); `check_coverage.py` shows
which labels no report names, not which were examined. Reviews are not a referee's report and not machine checks,
and agents can share blind spots.
