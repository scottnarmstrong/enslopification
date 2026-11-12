# Editorial plan: {{paper}} ({{pages_now}} pp -> about {{pages_target}} pp)

Date: {{date}}. This plan merges {{n_sources}} review sources. Human readers outrank agent reviewers. Lean
statements were checked only against the pinned commit `{{commit}}`.

**Source keys** (one key per reviewer; every planned change cites its keys)
- **H1-n:** notes of {{human reader 1}} (human).
- **H2-n:** review by section of {{human reader 2}} (human).
- **A1-n, A2-n, ...:** agent exposition reviews, model family {{family}}, pp. {{range}}, pp. {{range}}, ...
- **-T** marks a reviewer's closing list of renamings.

**Rules applied**
- Where agent reviewers conflict with the human readers, the human reading wins.
- Every term the human readers use is kept (part A(iii)).
- No claim may become stronger than what the Lean proves.
- A change to an approved statement is listed for the author's approval (part A, "Approvals").

**Approvals this plan needs before any writing starts**
1. The decisions of A(i)-(v).
2. Each change to an approved statement, with old and new text.
3. One abstract wording (A(iv)).

---

## A. Decisions for the author

### A(i) {{decision title}}

**The problem.** What is wrong, with source keys and page numbers.

**A dependency to note.** What else the change touches (statements that refer to it, the deduction, the README).

**Options** (each with its page effect)
- **(a) Status quo**, with ... 0 pp.
- **(b)** ... ±x pp.
- **(c) Recommended (keys):** ... ±x pp.

**Changes to approved statements:** old text -> new text; why the Lean allows it (declaration, file:line).
**Knock-on edits:** ...

### A(iii) Terminology and notation: one table

"Keep" means a human reader uses the term; a gloss is added once at the definition.

| # | Current | Proposed | Sources (n) | Recommendation |
|---|---|---|---|---|
| 1 | {{code-inherited word}} | {{term from the literature}} | {{keys}} (n) | adopt / **keep** / merge |

### A(iv) The abstract's checking sentence

Two wordings (under construction; finished) from `honest-publication`, and the preconditions for each (for
example: the correspondence table is published before the abstract says "published separately").

### A(v) Other architectural choices

| # | Choice | Options | Recommendation | Pages |
|---|---|---|---|---|

---

## B. Correctness-of-exposition fixes (first, before any polishing)

Each fix is checked at `{{commit}}` before it is edited, and recorded as finding -> decision -> edit -> check.

**B1. {{statement}}, {{file:line}}.**
- **Problem.** The sentence and why it is false or unsupported (keys).
- **Lean (verified).** Declarations (used = 1) with file:line, and what they show.
- **Fix.** Exact text.

## C. {{Part I}} plan, section by section
## D. {{Part II}} plan, section by section

Per section: **current -> target pages (+additions / -cuts)**, then
- **Add:** item (keys) ...
- **Cut:** item (keys) ...
- **Move:** item -> destination (labels kept).

## E. Figures

| # | Section | The one idea | Misreading to avoid |
|---|---|---|---|

## F. Budget (pages; "current" measured from the compiled PDF)

| Section | Current | + | - | ± moved | Target |
|---|---:|---:|---:|---:|---:|
| ... | | | | | |
| **Total** | | | | **0** | |

- Additions are offset by cuts; state the net against the agreed total ({{ceiling}} pp).
- **Additions over one page, with reasons:** ...
- Figures count. Writers report measured length per packet; a packet more than 0.5 pp over its target goes to the
  editor before integration.

## G. Execution order, writer split, review steps

- **Step 0, the author's decisions** (part A and the approvals), recorded in the brief.
- **Step 1, part B fixes** (editor and a mathematical reviewer; each checked at the pin first).
- **Step 2, structural moves** (labels preserved; compile; checks; pages measured).
- **Step 3, terminology and notation sweep** (scripted renames from A(iii), with before/after counts; a
  do-not-rename list holding the human readers' terms).
- **Step 4, figures.**
- **Step 5, writing packets** (at most {{k}} writers at once; writer and reviewer from different model families):

| Packet | Scope | Prerequisites | Target pp |
|---|---|---|---:|

- **Step 6, review of each packet** on a frozen snapshot: Lean check of every changed statement (weaker allowed,
  stronger never); prose truth of every new sentence, table entry and caption; owner review of each changed
  principal statement; shape and vocabulary checks; rendered pages.
- **Step 7, fresh readers**, each asked to explain named points from the text alone.
- **Step 8, delivery:** pages against part F, findings closed, status table and markers updated, the author's
  sign-off before the public commit.
