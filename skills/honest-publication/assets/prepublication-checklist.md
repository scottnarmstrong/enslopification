# Pre-publication checklist

Run before **every** push to the public repository. Copy this list into the push notes, mark each item, and give
the command output where there is one. An unchecked item blocks the push; an item that does not apply is marked
"n/a" with a reason. The author signs off on any push that changes a claim, the disclosure, the author line or the
markers.

## Content and vocabulary

- [ ] Only public files are staged: compare the list of changed files with the public allowlist (`git status
      --short`, `git diff --cached --name-only`); no brief, plan, prompt, review, ledger, morning list or private
      script.
- [ ] The vocabulary check of `exposition-standards` passes on every staged TeX file, comments included: no process
      words, no Lean names outside the paragraph on sources.
- [ ] No staged file (TeX, Markdown, data, metadata) contains a file path of the working machine, an account,
      machine or wrapper name, or an e-mail address that the author has not chosen to publish.
- [ ] No link points into the private repository; no review report, prompt or human reader's note is quoted.

## Claims

- [ ] The disclosure sentence is identical in the abstract, the introduction, the title page (if any), the
      manuscript README and `CITATION.cff`: `grep -rF "<first sentence>" <those files>` finds it in each.
- [ ] The author line is the author's choice; no persona.
- [ ] The three kinds of checking are named separately wherever checking is mentioned; no sentence says the text
      was "checked against", "verified by" or "proved by" the Lean.
- [ ] The wording matches the state: the under-construction wording while markers are up; the finished wording
      only after the author removed them.
- [ ] Every number on a public page is measured, dated where it changes, and given with its scope (agreement is not
      accuracy; a set comparison is not an edge check; loading a build is not a rebuild).
- [ ] Nothing is claimed beyond the statement page; the nonclaims are unchanged or updated with a changelog entry.

## Correspondence and pins

- [ ] `check_correspondence.py TABLE --db GRAPH --tex MANUSCRIPT --commit PIN [--lean-repo SOURCE]` exits 0; paste
      its summary line.
- [ ] The pin in the table equals the commit cited in the abstract, the introduction, the README and every Lean
      link (full hash in URLs).
- [ ] The table is public before any page says it is "published separately".

## The manuscript

- [ ] It compiles from the pushed sources; no `??`, no undefined or duplicate labels; the pushed PDF was built from
      exactly these sources.
- [ ] The main theorems are byte for byte the approved text (`compare_statements.py` of `referee-adjudication`
      with `--labels`), or the author approved the change.
- [ ] Changed pages were rendered and looked at (before a release, the typography pass of `referee-adjudication`,
      with `check_coverage.py --pages` showing every page in a report).

## Status, markers, records

- [ ] The status table is updated and dated; every status word used has a definition.
- [ ] Under-construction markers are in place (banner, title-page note, repository description, links from
      companion pages), unless the author removed them for the whole text.
- [ ] The changelog has an entry for every reader-facing change and correction in this push.
- [ ] `CITATION.cff` is current; licences of the formal source are respected (copyright line, licence named).
- [ ] The author has signed off, if this push changes a claim, the disclosure, the author line or the markers.
