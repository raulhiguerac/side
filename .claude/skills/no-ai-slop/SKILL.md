---
name: no-ai-slop
description: Edit prose so it reads sharp and human while keeping the author's voice, or audit it (detect mode) for AI-style patterns — in Spanish and English. Also audits code comments and docstrings that restate the code or run long. USE when the user asks to clean up, tighten or "de-slop" a text (wiki page, source, ADR, README, PR or commit body), asks whether something reads as AI, or from structural-review in detect mode. SKIP for writing new content from scratch and for code logic review.
argument-hint: detect or edit (default), then a file path or pasted text
disable-model-invocation: false
---

> Adapted from [petergyang/no-ai-slop](https://github.com/petergyang/no-ai-slop) (MIT, Peter Yang). Rewritten for this monorepo: Spanish patterns, wiki conventions and a code-comments section.

## Modes

- **Edit (default):** make the minimum effective edit, check it against `eval.md`, fix what fails, then return the edited text and a short **Qué cambió** list.
- **Detect:** for each problem, quote the line, name the pattern and give a fix in a few words. Don't rewrite, score, or guess whether an AI wrote it. Offer to edit afterwards.

If the audience or the goal of the text is unclear, ask before editing.

## What not to touch

- Front-matter, `[[slug]]` links, file paths, code identifiers, error codes, commands, tables' structure.
- `## Claims` in wiki pages: fix wording only; the claim and its code link stay intact (see `docs/CONVENTIONS.md`).
- The author's opinions, bluntness, humor, real uncertainty and characteristic phrasing. Don't polish every paragraph into the same shape.
- Meaning: never add claims, examples, numbers, sources or opinions.

## Editing principles

- Lead with the point when the setup adds nothing; keep asides that add context.
- Active voice, with people or components doing the verb ("el adapter traduce el error", not "el error es traducido").
- Concrete over abstract: names, numbers, dates, files, mechanisms.
- Portability test: if a sentence fits any project unchanged, cut it or make it specific.
- Strong verbs: "decidimos", not "tomamos la decisión de".
- Cut sentences that add nothing; keep hedges that express real uncertainty.
- Split tangled sentences; keep clear long ones and natural fragments.
- Repeat the precise term instead of rotating synonyms.
- Keep the structure unless it hurts the text, and say why if you reorganize.

## Words to cut

Remove unless quoted as an example.

- **ES:** potenciar, aprovechar (como "leverage"), robusto, sinergia, ecosistema (figurado), paradigma, de vanguardia, innovador, transformador, integral, holístico, sin fisuras, empoderar, crucial, fundamental o clave como relleno, "llevar al siguiente nivel", "sumergirnos en".
- **EN:** delve, foster, leverage, utilize, facilitate, empower, streamline, robust, cutting-edge, game changer, seamless, paramount, transformative, elevate, harness, ever-evolving.
- **Empty adverbs** (keep only if they carry contrast or rhythm): simplemente, realmente, básicamente, literalmente, claramente, sencillamente; just, actually, truly, simply, fundamentally.
- **Filler phrases:** "cabe destacar", "vale la pena mencionar", "es importante señalar", "en el mundo actual", "a fin de cuentas", "sin duda", "en lo que respecta a"; "it's worth noting", "when it comes to", "at the end of the day", "let's dive in".

## Patterns to cut

1. **Binary contrast:** "No es X, es Y" / "It's not X, it's Y". State Y.
2. **Throat-clearing:** "Aquí está la cosa", "Seamos claros", "Here's the thing". State the point.
3. **Faux insight:** "Lo que casi nadie entiende es…". Make the claim alone.
4. **Colon reveal:** "Lo mejor: aprende solo." Write a plain sentence. Colons are for lists, labels and quotes.
5. **Hollow "-ing"/gerund tails:** "…, lo que resalta / subrayando la importancia de…". Say the actual effect.
6. **Puffery:** "marca un antes y un después". State the fact.
7. **Metadiscourse:** "El punto clave es", "Como se puede ver", "Es importante entender que". Delete.
8. **Weasel attribution:** "Los expertos coinciden", "studies show". Name the source or flag the missing one; never invent it.
9. **Fake-strong verbs:** "funge como hub centralizado". Use "es" or "tiene".
10. **Negative listing:** "No es un X. No es un Y. Es un Z." Say Z.
11. **Dramatic fragments and robotic rhythm:** "X. Y. Y Z." or the same sentence shape repeated. Use complete, varied sentences.
12. **Rhetorical setups:** "¿Y si te dijera que…?", "Plot twist:". Make the point.
13. **Kicker and recap endings:** a closing aphorism, "En resumen", "En conclusión", "Overall". End on the last concrete point or next step.
14. **Formatting slop:** emoji in headings, bold mid-sentence for emphasis, bullets where a sentence works, a header over two lines of text.
15. **Em dashes as rhythm:** none in short text, one or two in long text, only where they clearly beat a comma or parentheses.

## Code comments

Default: no comment. Code that needs one usually needs a better name first.

When a comment earns its place, it says **why**, an invariant, or a non-obvious external constraint, and it is:
- preferably inline, at the end of the line it explains;
- one short line; **two lines maximum** only when the reason can't fit in one;
- in the language the file already uses.

Flag in detect mode, fix in edit mode:
- **Restating the code:** `# valida el token` above `validate_token()`, a name translated into words, "ahora iteramos sobre…".
- **Docstrings that repeat the signature** or the types the annotations already state.
- **Blocks:** three or more comment lines, `/** */` or `"""` paragraphs explaining design. The reasoning goes to the wiki, an ADR or the commit message.
- **History and conversation leftovers:** "nuevo:", "cambiado por el review", "antes hacíamos X".
- **Commented-out code** and `TODO` with no context or owner.
- **Stale comments** that no longer match the code.
- **Any comment in a Makefile.**

Keep: the why behind a workaround (with a link if there is one), `noqa`/`type: ignore`/`eslint-disable` with their reason, and one-line section labels in config files such as `.env.*`.

Fixes, in order of preference: delete it, rename the identifier so the comment becomes redundant, condense it to one line, move the reasoning to the wiki or the commit.

## Workflow

1. Read the whole text or diff.
2. Identify the core point and the voice traits to keep.
3. Detect: report and stop.
4. Edit: minimal changes, run `eval.md`, fix failures, recheck.
5. Output the edited text (or the diff for files) and **Qué cambió**.
