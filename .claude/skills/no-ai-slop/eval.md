# no-ai-slop eval

> Adapted from [petergyang/no-ai-slop `eval.md`](https://github.com/petergyang/no-ai-slop/blob/main/skills/no-ai-slop/eval.md) (MIT, Peter Yang).

Answer each check pass or fail. Fix every fail before returning the edit, then recheck.

## Meaning and voice
1. No claim, example, number, source or opinion was added.
2. The author's vocabulary, cadence, bluntness, humor and real uncertainty survive; they would recognize it as theirs.
3. Strong human sentences were left alone; cuts match the actual slop.
4. Front-matter, `[[slug]]` links, paths, identifiers, error codes and claim links are intact.

## Sentences
5. The text leads with what the reader needs; setup that adds context stays.
6. Every sentence carries a concrete fact, mechanism or decision; generic ones failed the portability test and were cut or made specific.
7. Active voice and strong verbs where possible.
8. Only genuinely tangled sentences were split.
9. One precise term per concept, no synonym rotation.

## Words and patterns
10. No banned words, filler phrases or empty adverbs (ES or EN) outside quoted examples.
11. No binary contrasts, negative listings, rhetorical setups or throat-clearing openers.
12. No colon reveals, hollow gerund tails, fake-strong verbs, puffery or metadiscourse.
13. Weasel attributions are named or flagged, never invented.
14. No kicker line or recap ending; the text closes on a concrete point or next step.
15. No emoji headings, decorative bold, prose-worthy bullets or headers over tiny sections.
16. Em dashes: none in short text, at most one or two in long text.
17. No robotic symmetry or stacked punchy fragments.

## Code comments
18. No comment restates the code or the signature.
19. Every remaining comment says why, an invariant or an external constraint.
20. Comments are one short line, preferably inline; two lines only where one can't hold the reason.
21. No commented-out code, contextless `TODO`, history notes, stale comments or Makefile comments.

## Output
22. Edit: the full edited text (or diff) followed by a short **Qué cambió**.
23. Detect: each finding has a quoted line, the pattern name and a short fix, with no rewrite, score or AI-authorship claim.
