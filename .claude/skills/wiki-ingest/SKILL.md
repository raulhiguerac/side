---
name: wiki-ingest
description: Process a source file in docs/sources/, propose updates to 1-5 wiki pages under docs/wiki/, and apply the approved changes following docs/CONVENTIONS.md (front-matter, atomic claims, [[slug]] links).
argument-hint: relative path to docs/sources/<service>/<file>.md
disable-model-invocation: false
---

You will ingest a new source into the wiki.

## Required steps

1. **Read the full source** from `docs/sources/...`. The path comes via `$ARGUMENTS`. If it doesn't exist, ask for clarification — don't proceed.

2. **Read `docs/CONVENTIONS.md`** and `docs/INDEX.md` to understand the current structure.

3. **Identify affected pages.** For each concept or fact in the source:
   - If a wiki page already exists, propose an update (don't edit yet).
   - If not, propose creating a new page using `docs/wiki/_templates/page.md`.

4. **Present a change plan to the user** before touching files: list of pages to create and pages to update, with a one-line summary per item. Wait for confirmation.

5. **Apply the approved changes.** For each page touched:
   - Update `last-verified` to today's date.
   - Set `status` accordingly (`stable` if verified, `draft` if TODOs remain).
   - Add the source path to `sources:` in the front-matter (or the ADR slug if applicable).
   - Respect the `## Claims` section — only add/modify claims that are verifiable against code.

6. **Update `docs/INDEX.md`** if new pages were created.

## Rules

- Never modify files in `docs/sources/` — they are immutable.
- If a source claim contradicts an existing wiki claim, stop and ask the user which version is correct.
- Don't invent claims unsupported by the source or by the repo code.
- If the source isn't in `docs/sources/` and the user passed raw text/URL, suggest running `wiki-capture` first to archive it.
