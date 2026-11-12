You are writing the detailed notes of one unit of a natural-language outline of a Lean proof: {{project}}.
The notes are for a mathematician who will later write the full proof. They must be faithful to the Lean and
readable without it.

UNIT: {{key}}. {{title}}. About {{lean_lines}} lines of Lean.

READ FIRST
1. The template you must follow, section by section: {{template}}
2. The unit's source inventory, written by inventory.py: size and largest files; its results by mass, each with a
   pinned link, its docstring and an excerpt of its statement (source text, not the elaborated statement); the
   definitions it introduces; the declarations of other units it uses, most used first; what other units use from
   it; its key statements: {{inventory}}
3. The architecture of the whole proof and the interfaces between its parts: {{architecture}}
4. The statement page of the main theorem (written at the start of the campaign: the formal statement verbatim, a
   commentary in words, the statement in ordinary mathematics, what is not claimed): {{statement}}
5. The glossary of the code's nicknames, with confidence labels: {{glossary}}
6. The list of units, to name inputs from other units by their ids: {{units_list}}

LOOKUPS (read-only)
- Lean source at the pinned commit: {{lean_root}} (module A.B.C is the file A/B/C.lean). Read the module
  docstrings, the statements you cite, and the proofs whenever the mechanism is not clear from the statements.
- Declaration graph: sqlite3 -readonly {{db}} (nodes: name, kind, module, path, line, line_end, doc, used;
  edges: src, dst, part). Only declarations with used = 1 are in the closure of the main theorem.
- Pinned links: grep -P '^Full\.Name\t' {{links_tsv}} (columns: name, url, kind).
- Unit of a declaration: grep -P '^Full\.Name\t' {{assignment}}

RULES
- Every numbered statement carries all its hypotheses, its quantifiers in their order, and its conclusion, with a
  status (theorem, definition, or hypothesis carried as an assumption) and a pinned link to the exact lines.
- Cite only declarations with used = 1 as establishing a statement. The code contains alternative routes that the
  main theorem does not use; check before writing "the Lean proves".
- Mark each step (proof read) or (statement only), and each uncertain statement (probable) or (tentative).
- Plain mathematical English; no Lean syntax in statements; code names only in links and in the notation section.
- Math that renders on GitHub: no \operatorname, no # inside math, no \newcommand, \label or \ref.
- No remarks about your process; no promotional or filler vocabulary.

OUTPUT: write the notes to {{stage_dir}}/notes.md, starting with the line "# {{key}}. {{title}}". Write no other
file. Do not run git and do not build the Lean project.
