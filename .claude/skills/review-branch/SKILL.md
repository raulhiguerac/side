---
name: review-branch
description: Use this skill to review code changed in the current session — checks for layer inconsistencies, import issues, missing error handling, and deviations from project patterns
argument-hint: optional focus area (e.g. "only UCs", "imports", "error handling")
disable-model-invocation: true
---

Run `git diff HEAD` and `git status` to see what changed in the current session.

Then review the changed files and give feedback on:
1. **Layer inconsistencies** — port signatures not matching adapter/UC implementations
2. **Imports** — unused, unsorted, or importing from the wrong layer
3. **Error handling** — missing try/except, unhandled edge cases, exceptions not registered in exception_handlers.py
4. **Pattern deviations** — anything that doesn't follow the hexagonal architecture style of the project (ports → adapters → use_cases → api)
5. **Bugs or edge cases** — logic issues, missing guards, incorrect field names

Be direct and concise. Group findings by file. Skip files that look correct.
