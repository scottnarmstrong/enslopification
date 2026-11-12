# Typographic inspection: pages {{first_page}}-{{last_page}}

Read-only. Look at **every** page image of pages {{first_page}} to {{last_page}} of `{{packet}}/main.pdf`: the images
are in `{{packet}}/images/`, one PNG per page. Also search the extracted text of these pages (for example
`pdftotext -layout -f {{first_page}} -l {{last_page}} {{packet}}/main.pdf -`) for `??`, doubled words and leftover
notes. If you can run `pdftoppm`, zoom on a suspect page at about 130 dpi; otherwise list the page under
"Zoom needed" and the editor will render it.

## Look for

- displays broken across lines, over-wide displays whose tag is pushed onto its own line, stray operators;
- blank areas left by floats or forced page breaks; headings stranded at the bottom of a page;
- a one-word line before a display; an end-of-proof box alone on its line;
- an inline formula split across lines or pages, especially at a minus sign or inside parentheses;
- text in the margin; unresolved references; redundant references ("Lemmas 3.2 and 3.1-3.4");
- inconsistent headings (numbered and unnumbered mixed), numbering that skips or repeats;
- leftover editing or checking notes, process language, draft lines, version hashes or internal labels;
- statements about authorship, sources or checking that differ between the title page, the abstract and the
  introduction (they must use one wording).

## Output, in this order

1. `Sources consulted:` the page images you looked at and at what resolution, the text search, the zooms, and
   every page you could not open or render (list those under "Zoom needed").
2. The defects table, one row per defect:
   `| Page | Quote | Defect | Suggested fix |`. One page number per row (a defect across a page break goes under
   its first page). Quote enough text to locate the place; give the fix as TeX where possible.
3. `Needs the editor:` any defect whose fix would change a statement, a label or the mathematics, with the reason.
   A typographic pass never changes those; propose no such change in the table.
4. The last line of the report, on one line: `Clean pages:` followed by every page of the range with no defect, as
   ranges separated by commas, e.g. `Clean pages: 2-5, 7-13, 15` (or `Clean pages: none`). Every page from
   {{first_page}} to {{last_page}} must be in the defects table or on this line; a page in neither counts as not
   inspected.

Print the report as your final answer (do not write files, other than zoom images).
