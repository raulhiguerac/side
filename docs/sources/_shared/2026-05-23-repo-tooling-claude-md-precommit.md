---
title: Repo tooling — CLAUDE.md workflow rule + pre-commit wiki staleness hook
captured-from: conversation
captured-on: 2026-05-23
participants: [raul, claude]
---

## Context
Two repo-level tooling decisions made to improve dev workflow: enforce discuss-before-code discipline via CLAUDE.md, and prevent wiki staleness via a pre-commit hook.

## Key conclusions

### CLAUDE.md at `.claude/CLAUDE.md`
- Created `.claude/CLAUDE.md` (project-level, loaded at session start) with a hard rule: zero code without prior discussion.
- Mandatory flow: user describes → Claude states understanding + trade-offs → user confirms → code written.
- Written in English for better model adherence.
- File lives at `.claude/CLAUDE.md` — loaded automatically by Claude Code at session start for this repo.

### Pre-commit wiki staleness hook
- `.pre-commit-config.yaml` at repo root — versioned, defines the local hook.
- `scripts/wiki-lint-hook.sh` — warns (exit 0, never blocks) when staged files touch a service whose wiki pages have `last-verified` > 30 days.
- Logic: get staged files → map to service (`backend/analytics-service/` → `analytics-service`) → find wiki pages for that service → check `last-verified` → print warning if stale.
- Hook is local (`.git/hooks/` not versioned) — each dev must run `pre-commit install` once.
- `uv tool install pre-commit && pre-commit install` added to `devcontainer.json` `postCreateCommand` for container users.
- Commits happen from host (not container) → install via `pipx install pre-commit` on host, then `pre-commit install` from repo root.
- `pipx` is the correct tool: installs CLI tools in isolated venvs, binary available globally in PATH.

## Open questions
- None — hook is implemented and devcontainer is updated.

## Next steps
- Each dev (and host machine) needs `pipx install pre-commit && pre-commit install` once to activate the hook locally.
