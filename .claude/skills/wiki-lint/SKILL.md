---
name: wiki-lint
description: Audit the wiki at docs/wiki/ for stale pages (last-verified > 30 days with recent commits on referenced code), orphans (no inbound [[links]]), broken links, and potential contradictions across claims. Report findings without applying changes; offer fixes one by one at the end.
argument-hint: (no arguments)
disable-model-invocation: true
---

You will run a health-check over the wiki. **Do not edit files automatically** — only report findings and, at the end, offer to apply fixes one by one.

## Steps

1. **List all pages** under `docs/wiki/` (excluding `_templates/`).

2. **Detect stale pages.** For each page:
   - Parse `last-verified` from the front-matter.
   - If more than 30 days have passed relative to today, flag it as a stale candidate.
   - Extra heuristic: if there are recent commits (`git log --since`) on files the page references, raise priority.

3. **Detect orphans.** Build the `[[slug]]` link graph between pages. Report pages with zero inbound links (excluding `00-*` overviews and files in `_shared/` reached from INDEX).

4. **Detect broken links.** For each `[[slug]]` found, verify a `slug.md` exists somewhere under `docs/wiki/`. Report those that don't resolve.

5. **Detect contradictions (heuristic).** Concatenate all `## Claims` sections. Report pairs of claims that look contradictory — the user decides which is correct, not you.

6. **Report everything in a single structured summary** with this shape:

   ```
   ## Lint report — <date>

   ### Stale (N pages)
   - <path> — last-verified N days ago, M recent commits touched referenced code

   ### Orphans (N pages)
   - <path> — no inbound links

   ### Broken links (N)
   - <path>:<line> — `[[broken-slug]]`

   ### Potential contradictions (N)
   - <page-A> says: "..." vs <page-B> says: "..."
   ```

7. **Offer fixes one by one** if the user wants. Never apply mass changes without per-finding confirmation.

## Rules

- Don't mark `stale` based on age alone — there must also be evidence of code change in referenced files, or ask for confirmation.
- Contradictions are reported, never resolved without the user.
