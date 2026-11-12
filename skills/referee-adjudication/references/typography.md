# The typographic pass

Compilation and automatic checks do not see a display broken across lines, a third of a page left blank, or two
pages that describe the authorship of the text differently. Only eyes on every rendered page do
([L29](../../lean-to-manuscript/references/lessons-learned.md#l29)). Run this pass before every release and after
any pass that moves much text; it changes layout and wording around statements, never a statement, a label or the
mathematics.

## Render and divide

- Compile the release candidate and freeze it (`make_packet.py`).
- Render every page with `scripts/render_pages.sh`, one directory per reviewer, each reviewer taking a page
  range it can inspect completely. Sweep at 60 dpi (enough for layout) and zoom at about 130 dpi on suspect
  pages:

  ```
  render_pages.sh -f 1 -l 60 -o typo/img-1-60 snapshot/main.pdf
  render_pages.sh -f 14 -l 14 -r 130 -p hi -o typo/img-1-60 snapshot/main.pdf
  ```

- Reviewers also search the extracted text (`pdftotext -layout`) for `??`, doubled words and leftover notes.
- Run with `assets/rollout.typography.example.json` (units are page ranges; the packet holds the PDF and the
  images). A reviewer that cannot render its own zooms lists the pages under "Zoom needed" and the editor renders
  them. Then run `check_coverage.py --pages 1-60 <workdir>/p001/inspect/typography.md` (`writing-workflow`) for
  each range.

## The report

`assets/prompts/typography-reviewer.md` asks for four parts, in this order:

1. `Sources consulted:` the images looked at and their resolution, the text search, the zooms, and the pages that
   could not be opened ([L22](../../lean-to-manuscript/references/lessons-learned.md#l22));
2. the defects table, `| Page | Quote | Defect | Suggested fix |`, one page per row, with enough quoted text to
   find the place in the source and the fix in TeX where possible;
3. `Needs the editor:` defects whose fix would change a statement, a label or the mathematics;
4. as the last line, `Clean pages: 2-5, 7-13, 15`: every page with no defect, as ranges.

The clean-pages line records that the reviewer reports having looked at those pages; it is not evidence that it
did. `check_coverage.py --pages A-B` of `writing-workflow` verifies mechanically that every page of the range is
in a defects table or on a clean-pages line; a page in neither was not reported as inspected and goes back to a
reviewer.

## What to look for

- displays broken by the layout: one factor alone on a line and the rest of the formula pushed far to the
  right, stray multiplication dots, equation tags pushed onto their own line under a brace;
- floats and forced breaks leaving a large part of a page blank, for instance around a long table;
- a one-word line before a display; end-of-proof boxes alone on a line;
- inline formulas split across lines at a minus sign inside a parenthesis, or across a page break;
- unnumbered bold headings mixed with numbered subsections;
- redundant references (a lemma cited both alone and inside a range that contains it);
- leftover checking notes in the text, version hashes or internal labels set as link text, stray draft lines;
- **two passages that say the same thing in different words**, above all on authorship and on what was checked.
  The wording itself is the author's decision, and `honest-publication` keeps one wording everywhere.

## Fixing the defects

- One writer works on a copy of the whole manuscript with all the defects tables, and returns the edited files
  and a response table: defect, then fixed (exact edit) or kept (reason).
- The task names the deliberate exceptions, so the writer does not "fix" them: for example a dated draft line on
  the title page, links and scope remarks placed on purpose; and it says that no lemma is deleted or moved.
- Typical fixes: `aligned` or `multline` for over-wide displays so tags stay on their line; `\qedhere` for
  end-of-proof boxes; a display instead of an inline formula that breaks badly; `\paragraph` run-in headings for
  unnumbered headings; table breaking instead of forced page breaks.

## Checks after the pass

```
compare_statements.py before/ after/          # no statement changed, no label lost
```

Then compile (no `??`, no undefined or duplicate labels), compare the page count with the one before, run the
shape and vocabulary checks of `exposition-standards`, re-render the changed pages and look at them, and record
that no statement or label changed.

## What the pass establishes

What is on record: reviewers were asked to look at every page image of their range at the stated resolution, and
each reported its defects and its clean pages; the writer's response table answers every reported defect. What a
script verified: with `check_coverage.py --pages`, that no page of the range is missing from the reports; with
`compare_statements.py`, that no statement or label changed. Not verified: that a reviewer looked at a page it
listed, or that a page reported clean has no defect ("clean" means no defect was reported at that resolution).
The pass checks no mathematics; a sentence it rewords still needs the prose-truth check of `writing-workflow` if
its meaning could have changed.
