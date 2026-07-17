---
title: POST /admin/properties/bulk is fully synchronous — timeout risk and proposed async-batch refactor
captured-from: conversation
captured-on: 2026-07-16
participants: [raul, claude]
---

## Context
While wiring the front's CSV-import modal for `POST /admin/properties/bulk`, reviewing the endpoint surfaced a real reliability risk: the whole operation — including per-row network calls to `catalog-service` — runs synchronously inside the HTTP request/response cycle, and the front's axios timeout is shorter than a realistic worst case.

## Key conclusions
- `BulkCreatePropertiesUseCase.execute()` calls `catalog-service` once per CSV row (`_enrich_location`, bounded by a semaphore of 50 concurrent) before `bulk_insert` + `commit` — entirely inside the request. Confirmed the response is honest about durability: the route `await`s `uc.execute()` and returns its result directly, and `commit()` genuinely awaits `session.commit()` (via threadpool) before the use case returns — a `201` does mean the rows are durably committed, no discrepancy there.
- The front's `propertiesApi` axios instance has `timeout: 8000` (8s). For any CSV beyond a handful of rows, cumulative network latency to `catalog-service` across enrichment calls can easily exceed 8s — the client reports a timeout error while the backend keeps running (and committing) regardless. Real mismatch between what the client believes happened and what actually happened.
- Reviewed a sibling project's (a prior Globant technical-challenge submission, `hiring-service`) established pattern for this exact class of problem: synchronous validate/parse → create a batch record (`status: pending`) → return `202` with a `batch_id` immediately → process (enrichment + bulk insert + commit) in a background task → expose a status-polling endpoint → finalize the batch to `completed`/`failed`.
- Two implementation details worth carrying over from that prior solution:
  1. FastAPI's `yield`-dependencies close **before** `BackgroundTasks` execute (since 0.106) — a background worker must open its own DB session/UoW, not reuse one obtained via the request's `Depends` chain.
  2. Without a real task queue, a lightweight self-healing mechanism (treat a `pending` batch older than a timeout threshold as `failed` on the next status poll) covers the process dying mid-task.
- Decision: this is real refactor work, not a small fix — deferred, to be planned jointly (backend contract: what `/admin/properties/bulk` returns on `202`, shape of the status endpoint, where batch state lives) before implementing. The front's currently-built synchronous modal (`BulkUploadPropertiesModal.vue`) will need to change to a submit-then-poll flow once the backend contract exists.
- Logged in `wiki/_shared/open-items.md` under "properties-service — arquitectura interna", flagged **IMPORTANTE**.

## Open questions
- Where batch status/state should live: a new DB table (durability/auditability, matches the sibling project's approach) vs. Redis with TTL (lighter-weight, matches this project's existing cache-aside conventions) — not decided.
- Whether to use FastAPI `BackgroundTasks` (in-process, matches this project's existing fire-and-forget pattern used for POI resolution in `catalog-service`) or something heavier — leaning `BackgroundTasks` per project precedent, not finalized.

## Next steps
- Plan the `/admin/properties/bulk` `202` + `batch_id` contract and the status-polling endpoint together before implementing.
- Update `BulkUploadPropertiesModal.vue` to a submit → poll → show-result flow once the backend contract is settled.
