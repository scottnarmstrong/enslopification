<!-- Template for the README of the public repository. Links are relative to that repository's root; fill every
{{...}}, keep the levels table, and delete rows for pages the repository does not have. -->

# {{Title}}

**{{One sentence: what this repository is, e.g. "A map of {{source}}, and a natural-language account of its proof
written from it."}}**

{{Who maintains it, in the author's words; collaborating projects and what they contribute.}}

{{Two or three sentences on the formal source: what it proves, its size, where it is, the pinned commit.}}

{{What was done, as a numbered list (map, outline, write), with the state of each. If a manuscript is in progress:
"A first draft is available ([PDF](manuscript/main.pdf), {{n}} pages, draft of {{date}}); it is still being
revised."}}

{{The text was written by AI agents: the disclosure sentence, word for word as in the abstract.}}

## The proof at {{k}} levels of detail

Each level links down to the next; from level 3 down, everything links to the exact lines of the Lean source at
commit [`{{commit}}`]({{source_url}}/tree/{{commit_full}}). Start at the top and go down as far as you need.

| level | | what you get |
|---|---|---|
| **1** | [**The main theorem**](statement.md) | the Lean statement verbatim, a commentary in words, the full statement in ordinary mathematics, what is and is not claimed |
| **2** | [**The proof in one reading**](summary.md) | the strategy, the key mechanism of each part, what is new, where the difficulty lies |
| **3** | [**The architecture**](outline/README.md) | the parts of the proof and what each hands to the next |
| **4** | [**The units**](outline/units.md) | per unit: an outline, detailed notes, and a Lean map with every key statement linked to its lines |
| **5** | [**The full proof**](manuscript/) *({{status, e.g. "under construction"}})* | the complete manuscript ([PDF](manuscript/main.pdf)) and [how it is written](manuscript/PROCESS.md) |

**Reference material**

| | |
|---|---|
| [**Where the ideas come from**](provenance.md) | component by component, with the evidence on both sides; not a claim of priority |
| [**Glossary**](glossary.md) | the code's names translated into mathematics, with confidence labels |
| [**Work items**](outline/work-items.md) | the code's own decomposition into stated obligations |
| [**How this was made**](method.md) | the kernel check, the graph and its comparison with the authors' record, the reviews, and what each establishes |
| [**FAQ and evidence guide**](faq.md) | questions about the result and the evidence |
| [**Changes**](CHANGELOG.md) | publications and corrections |
| [**Data**](data/) | the tables, with a dictionary |

## Status

| | |
|---|---|
| {{item}} | {{state, with a link to the definition of the status words}} |

[Report a correction]({{issues_url}}): give the page and heading, quote the sentence, and propose a correction or
give a pinned Lean link.

## How to cite

Use [CITATION.cff](CITATION.cff). Include the revision of this repository you consulted, the unit or result
identifiers, and the fixed Lean commit `{{commit_full}}`. Cite the Lean source separately when referring to the
formal proof.

## License

{{This repository's licence.}} The Lean source it describes is {{copyright and licence of the formal source}}.
