# Working Rules — Side Monorepo

## RULE #1: ZERO CODE WITHOUT PRIOR DISCUSSION

**Before writing a single line of code, the problem and approach MUST be discussed and agreed upon.**

No exceptions. This applies to:
- New features
- Changes to existing features
- Refactors
- Bug fixes
- Migrations
- Infrastructure or service configuration

### Mandatory workflow

1. **User describes the problem or task.**
2. **Claude states its understanding** — what needs to be done, why, what it implies, what trade-offs exist.
3. **User confirms or corrects** the understanding.
4. **Only after explicit confirmation** is any code written.

### What NOT to do

- Do NOT propose inline code as an initial response to a problem.
- Do NOT assume the approach is obvious and skip the discussion.
- Do NOT write "here's the code" before the approach has been agreed upon.
- Do NOT start editing files because it "seems clear" what to do.
- Do NOT treat a vague task description as implicit approval to start coding.

### What TO do

- Answer open-ended questions with 2-3 sentences: understanding of the problem + recommendation + main trade-off.
- Present options when more than one valid approach exists.
- Wait for explicit green light from the user before touching any file.

## RULE #2: DONE MEANS AUDITED

**When a piece of work is finished — by Claude or by the user — audit its quality and iterate until it is production grade, or very close and with what's missing stated explicitly.**

### Mandatory checks on what was touched

All tooling runs inside the devcontainer (`docker compose exec -T develop bash -lc 'cd /workspace/...'`), never on the host.

- **Frontend:** `npm run lint:check` and `npm run typecheck` (vue-tsc). The build does NOT typecheck `.vue` files and `tsc` does not read them — a green build proves nothing about types.
- **Backend:** `uvx ruff check` and `pytest tests/unit` in each touched service.
- **Wiki:** `/wiki-lint` if pages were touched; `make audit` for the whole picture.

The project hooks (`.claude/settings.json`) lint each edited file and block finishing a turn with vue-tsc errors; they are a floor, not the audit.

### Then review, then iterate

1. Read the diff looking for bugs, smells and gaps (error handling the user can see, types without casts, no hand-written routes, layer violations).
2. Fix what is in scope; for what isn't, say it and record it in `docs/wiki/_shared/open-items.md`.
3. Repeat until the checks are green and the review finds nothing new.
4. Before opening a PR, run `/structural-review` on the branch; a PreToolUse hook blocks `gh pr create` until it has run on HEAD.

### Before stating facts or acting on shared state

- **Check the wiki** (`/wiki-query`) before claiming how the project works.
- **Check the PR/branch state** (`gh pr view`) before pushing or rebasing.
- **Report verification honestly:** name the exact command that ran and its result; never claim a check that didn't run.
