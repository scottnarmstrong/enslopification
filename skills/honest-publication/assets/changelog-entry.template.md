# Changelog entry template

The changelog records publications and corrections that affect a reader's understanding, newest first. It is not a
commit log: no process vocabulary, no internal names, no agent names unless the author wants them.

```markdown
## {{YYYY-MM-DD}}

- **{{What happened, in a few words}}.** {{What a reader can now find or must now understand differently, with a
  link to the page.}} {{For a correction: what the page said before, what it says now, and why, citing the
  pinned Lean lines or the evidence.}} {{For a review round: what was done, in exact words, e.g. "every suggestion
  was adjudicated against the text and the Lean before being applied, and a separate agent review compared the
  applied changes with the adjudication"; never "refereed", and never "checked", which is the status word for a
  section the author has read.}} {{Measured size where it matters, e.g. the page count.}}
```

Rules:

- One bullet per reader-facing event; corrections first when they change what a reader would have believed.
- A correction says what was wrong, without hiding it ("the earlier sentence assigning these terms to the forced
  remainder was wrong"), and links the corrected place.
- A change of pin, of status vocabulary, of the disclosure wording, or the removal of the under-construction
  markers always gets an entry.
- End the file with links to the README, the citation metadata and the issue tracker ("Report a correction").
