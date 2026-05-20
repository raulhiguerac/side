---
name: wiki-query
description: Consult the wiki at docs/wiki/ before answering project questions about the side monorepo. USE when the user asks about monorepo architecture, the real-estate domain (AVM, habímetro, properties, listings), behavior of a microservice (analytics-service, properties-service, catalog-service, users-service), recorded decisions (ADRs), integrations (MLflow, MinIO, Redis, georef), local dev runbooks, or any topic covered by the wiki pages. SKIP for generic programming/framework questions, external tools not specific to this project, trivial questions answerable by reading a single file, or implementation / code-writing requests.
argument-hint: user question
---

You will answer the user's question using the wiki as the primary source.

## Required steps

1. **Read `docs/INDEX.md`** to know what's available.

2. **Search `docs/wiki/`** for pages relevant to the question. Grep aggressively over titles, claims, and body. Also check `docs/wiki/_shared/` and the ADR folders.

3. **Synthesize an answer** combining what you found. Always cite the pages used with their path and slug, e.g. `[[online-prediction]]` in `docs/wiki/analytics-service/flows/online-prediction.md`.

4. **If the answer needs to go beyond the wiki** (reading code, checking PRs, external sources), state it explicitly: "this wasn't in the wiki, I inferred it from reading X." Never silently mix wiki claims with your own inferences.

5. **If the wiki has nothing on the topic**, say so directly. Answer with what you can derive from code, making clear the wiki doesn't cover this yet (candidate for documenting).

## At the end, offer to archive

If the Q&A has reusable value (non-trivial, non-ephemeral), ask the user:

> Want me to archive this Q&A? Options:
> - Append to an existing page (which one)
> - Create a new page (propose slug and location)
> - Don't archive

If they choose to archive, do it following `docs/CONVENTIONS.md`: full front-matter, atomic claims, `[[slug]]` links.

## Rules

- Don't say "according to the wiki..." if the wiki doesn't have the info. Be honest about the source.
- If the wiki contradicts current code, mark the page as a `stale` candidate and warn the user.
- If this skill was auto-invoked and the question turns out to be unrelated to the project (generic programming, external tool), abandon the skill silently and answer normally.
