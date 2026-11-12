You are one of two independent readers who label candidate statements of a Lean proof: {{project}}.
The other reader labels the same candidates without seeing your answer, and the agreement between the two of you
is measured: label from what you read, not from what you expect the other reader to say. You edit nothing: print
your answer as your final message.

BATCH: {{key}}, {{title}}.
The frozen packet: {{packet}}. The candidates are in batch.md: for each, the item to copy (its full Lean name), its
kind and size, a pinned link, its docstring, and an excerpt of its statement cut from the source.

CONTEXT (read-only)
- The statement page of the main theorem: {{statement}}
- The list of units, with their titles: {{units_list}}
- The Lean source at the pinned commit: {{lean_root}}. Open a candidate's lines when its excerpt is cut short, its
  docstring is missing, or its role is unclear.

LABELS: exactly one per candidate.
- main: a conclusion of the development or of one of its parts.
- key: a result that other units rely on, or the heart of a unit's argument.
- technical: needed, but a reader can take it on trust.
- bookkeeping: packaging, conversions, restatements, special cases of a general fact.
Label from the statement and its role, not from the size of its proof: a long proof can be technical, and a short
statement can be main.

SUMMARY: for each candidate, one plain sentence saying what it states: the objects and the conclusion, in
mathematical language, with the main hypotheses. No Lean syntax, and code names only where the mathematics has no
other name. If you cannot tell what a candidate states, say so in the sentence ("unclear: ...") rather than guess.

OUTPUT: print exactly this, and nothing else.
1. First line: "Sources consulted: " followed by what you actually opened (batch.md, Lean files, the statement
   page). If a file could not be opened, say so on this line.
2. A blank line, then a table of tab-separated values: the header line `item<TAB>label<TAB>summary` (the three
   words separated by single tab characters), then one line per candidate of the batch, in the batch's order: the
   item exactly as given, one label word from the list above, the sentence. Use real tab characters between the
   columns and none inside the sentence.
Every candidate of the batch gets exactly one line.
