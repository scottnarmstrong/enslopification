# The main theorem

This page gives the exact statement proved by {{source}} (released as [`{{repo}}`]({{source_url}}/tree/{{commit_full}}),
commit `{{commit}}`).

1. [**The formal statement:**](#1-the-formal-statement) the Lean theorem and the definitions at its core, verbatim.
2. [**What it says, in words:**](#2-what-it-says-in-words) a commentary.
3. [**The precise statement:**](#3-the-precise-statement) the theorem in ordinary mathematics, definition by
   definition, with every quantifier, domain and order of limits as in the Lean.
4. [**What is not claimed.**](#4-what-is-not-claimed)

How this page was checked: {{e.g. "transcribed and compared definition by definition with the pinned Lean by AI
agents, including quantifiers, spaces and the order of choices; this is an interpretation check, separate from the
kernel check"}}. {{Scope limits, e.g. "the additional clauses D1–Dk were summarized without unfolding every
definition"}}.

## 1. The formal statement

The headline theorem ([`{{file}}`]({{source_url}}/blob/{{commit_full}}/{{file}}#L{{a}}-L{{b}})):

```lean
{{the theorem, copied exactly}}
```

The proposition it proves, and the definitions at its core, each copied exactly with a link to its lines. Put long
structures in collapsible blocks:

<details>
<summary>{{name of the structure}} ({{items}})</summary>

```lean
{{copied exactly}}
```
</details>

## 2. What it says, in words

**The main theorem.** {{Setting in one sentence.}} Then the following hold.

1. **{{Clause name}}.** {{Precise plain-language statement of the clause.}}
2. ...

## Clause-to-explanation guide

| clause | precise definition | explained in | Lean |
|---|---|---|---|
| {{clause}} | [Definition 1.k](#anchor) | {{outline unit / summary section / manuscript section}} | [{{decl}}]({{pinned link}}) |

## 3. The precise statement

### 0. Conventions
### 1. The objects

<a id="{{anchor}}"></a>
**Definition 1.1 ({{name}}).** {{definition in ordinary mathematics}}

### 2. The main theorem

<a id="public-theorem"></a>
**Theorem 2.1.** {{statement, every quantifier and order of limits as in the Lean}}

<a id="detailed-theorem"></a>
**Theorem 2.2 (additional conclusions of the construction).** {{if the construction proves more than the formal
statement; state the narrower review scope}}

## 4. What is not claimed

1. **{{Topic}}.** {{Exactly what is not asserted.}} {{Where the formal source or an assessment says so, quoted with
   its reference.}}
2. ...

## Correspondence with the Lean source

| item | Lean declaration | where |
|---|---|---|
| Def 1.1 {{name}} | `{{Decl.name}}` | [{{file}}:{{a}}-{{b}}]({{source_url}}/blob/{{commit_full}}/{{file}}#L{{a}}-L{{b}}) |

The Lean source is {{copyright and licence of the source}}; the excerpts above are quoted under that licence.
