---
name: audit-service
description: Use this skill to do a full audit of a microservice — finds bugs, code smells, layer inconsistencies, cross-domain imports, and deviations from established patterns across the entire service
argument-hint: service name (e.g. "properties-service", "catalog-service", "users-service")
disable-model-invocation: true
---

The user wants a full audit of a microservice. The service name is given as the argument (e.g. "properties-service").

The service lives at `backend/{service-name}/src/app/`.

Use the Glob and Read tools to explore the full service structure. Read the files across all domains and layers. Do NOT just look at the diff — read the actual files.

Audit across these dimensions:

1. **Port ↔ Adapter consistency** — for every method in a port (Protocol), verify the adapter implements it with the same signature (param names, types, return type). Flag any mismatch.

2. **Cross-domain imports** — check that no domain imports from another domain (e.g. `listing` importing from `search`). Shared code must live in `services/shared/`.

3. **UC pattern deviations** — every UC should follow: inject deps in `__init__`, single `execute()` method, `run_in_threadpool(partial(...))` for sync repo calls, cache-aside pattern. Flag UCs that deviate.

4. **Error handling gaps** — check that exceptions raised in UCs are registered in `exception_handlers.py`. Flag any domain error that has no HTTP mapping.

5. **Code smells** — repeated logic that should be a helper, hardcoded values that should be in settings, silent `except Exception: pass` that swallows real errors, unused imports.

6. **Model / schema mismatches** — fields used in schemas that don't exist in the ORM model, or ORM fields never exposed in any schema.

Be direct. Group findings by file. Skip files that look correct. Prioritize bugs over style issues.
