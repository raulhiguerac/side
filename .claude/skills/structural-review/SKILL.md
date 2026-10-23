---
name: structural-review
description: Strict structural review of the current branch before opening a PR — hunts for complexity that can be deleted, logic in the wrong layer, ad-hoc branching, wrapper/cast churn and oversized files, then runs no-ai-slop in detect mode over the comments and the PR text. USE before every `gh pr create` (a PreToolUse hook blocks the PR until this ran on HEAD) and when the user asks for a deep, structural or "thermo-nuclear" review. SKIP for bug hunting on uncommitted work (review-branch) or a whole-service audit (audit-service).
argument-hint: optional base branch (default main) or focus area
disable-model-invocation: false
---

> Adapted from Cursor's [thermo-nuclear-code-quality-review](https://github.com/cursor/plugins/blob/main/cursor-team-kit/skills/thermo-nuclear-code-quality-review/SKILL.md) (cursor/plugins). Rewritten for this monorepo; the original declares no license, so nothing here is copied verbatim.

The goal is not "it works" but "the codebase got simpler or at least not messier". Behavior stays the same; structure is what's on trial. Prefer **deleting** complexity over moving it around: a refactor that relocates code without reducing what a reader has to hold in their head is not an improvement.

## 1. Gather the change

- Base: the argument, or the PR base if the branch is stacked (`gh pr view --json baseRefName`), else `main`.
- `git log <base>..HEAD --oneline` and `git diff <base>...HEAD --stat`, then the full diff.
- Read whole touched files when judging structure needs more than the hunk.
- This is not a bug hunt (`review-branch` does that), but report any bug you trip over.

## 2. What to look for, by priority

1. **Structural regressions:** a cohesive module became more coupled, stateful or hard to scan.
2. **Missed code judo:** a reframing that would make a branch, helper, mode or layer disappear. Ask: can fewer concepts reach the same result?
3. **New branching:** one-off `if`s, booleans or nullable modes added to flows that don't own the concept. They belong in a policy, a typed model, a dispatcher or their own module.
4. **Boundaries and types:** casts (`as`, `cast()`), `any`/`unknown`/`Any`, needless optionals, ad-hoc dict/object shapes where a typed model or shared contract exists, silent fallbacks.
5. **File size:** a file pushed past ~1000 lines by this branch is a presumptive blocker; ask for the split first.
6. **Ownership and duplication:** logic outside the module that owns it, near-duplicate helpers of a canonical one, feature logic leaking into shared code.
7. **Indirection:** pass-through wrappers, identity abstractions, generic "magic" that hides the data shape.
8. **Orchestration:** independent awaits run sequentially for no reason; related state updates that can be left half-applied.
9. **Legibility:** names, function length, edge cases buried in busy functions.

## 3. Project rules (the canonical layers)

Check the wiki (`/wiki-query`) when unsure how a service does something; don't invent a convention.

**Backend (`backend/*-service`)**
- Hexagonal: ports (`Protocol`) → adapters → use cases → api. Use cases depend on ports, never on adapters, SDKs or FastAPI.
- Adapters receive config through the constructor; env vars are read and validated in `api/deps`.
- Infra providers with `lru_cache` live in `api/deps/shared/<tech>.py` (users-service); `*_use_cases.py` only wire UoW, mailers and use cases.
- `api/routes` folders mirror the URL prefix.
- Domain errors subclass `BaseError` with a `code`; no bare `Exception` crossing layers.
- No imports across service contexts.

**Frontend (`frontend/src`)**
- Interfaces in `types/`, filters and constants in `constants/<domain>`, HTTP in `api/`; views and components don't define them.
- No hand-written routes or URLs where a named route or endpoint constant exists.
- No `as` casts, `any` or non-null `!` without a stated reason.

**Comments and text:** apply the code-comments section of `no-ai-slop` (step 4).

## 4. Run no-ai-slop in detect mode

Read `.claude/skills/no-ai-slop/SKILL.md` and apply its **detect** mode to:
- every comment and docstring added or changed in the diff;
- the PR title and body draft, and wiki/source pages touched by the branch.

Fold its findings into the report under their own heading; don't rewrite anything yet.

## 5. Report

- First line: **Ready to open** or **N blockers**.
- Findings ranked by the priority above. Each one: `file:line`, the problem in one sentence, and the concrete move (what to delete, merge, extract or move, and where). A handful of high-conviction findings beats a long list; skip cosmetic nits unless nothing else is left.
- Out-of-scope findings: propose the entry for `docs/wiki/_shared/open-items.md`.
- Tone: direct and serious. Don't soften a maintainability problem into "maybe consider".

Presumptive blockers, unless the author justifies them in the PR:
- incidental complexity a code-judo move would delete;
- a file pushed past ~1000 lines;
- ad-hoc branching tangled into an existing flow, or feature checks scattered across shared code;
- logic in the wrong layer, or a helper duplicating a canonical one;
- cast-heavy contracts or wrappers that add nothing.

## 6. Mark HEAD as reviewed

After reporting, record the reviewed commit so the hook lets `gh pr create` through:

```bash
git rev-parse HEAD > "$(git rev-parse --path-format=absolute --git-path structural-review-ok)"
```

If there are blockers, stop and wait for the user's decision before opening the PR. New commits change HEAD, so the hook asks again; on the re-run, focus on the commits since the last review.
