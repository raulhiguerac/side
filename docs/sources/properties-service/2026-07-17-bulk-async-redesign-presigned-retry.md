---
title: Bulk-create async redesign — job tracking table, presigned-upload retry, no dedup hash
captured-from: conversation
captured-on: 2026-07-17
participants: [raul, claude]
---

## Context
Follow-up design discussion to the 2026-07-16 items (`2026-07-16-bulk-create-sync-timeout-risk.md`, `2026-07-16-bulk-create-owner-id-resolution.md`). Before starting the branch `refactor/bulk-async-processing`, worked through the concrete shape of the fire-and-forget refactor for both properties-service (`bulk create properties`) and catalog-service (`bulk create neighborhoods`, `bulk enrich neighborhood geometries`) — all three run fully synchronous in-request today, confirmed by re-reading the code (`admin.py` in each service, `bulk_create_properties.py`, `bulk_create_neighborhoods.py`, `bulk_enrich_neighborhood_geometries.py`).

## Key conclusions

**Job tracking table.** No existing table in the codebase tracks multi-row progress (`total/processed/error` counts) — closest precedents are `kc_compensation_tasks` (users-service, retry-queue shape: `task_type`, `status`, `attempts`, `last_error`) and `property_image_upload_batches` (properties-service, `pending → terminal` status shape, `expires_at`). Decision: one `bulk_jobs` table per service (can't share across services — separate DBs), with a `job_type` enum discriminator (mirrors `kc_compensation_tasks.task_type`) so catalog-service's two bulk endpoints share one table instead of two. Shape: `id` (uuid, returned to the caller), `job_type`, `status`, `total_rows`, `processed_count`, `success_count`, `error_count`, `created_by`, `created_at`/`started_at`/`finished_at`, `errors` (JSON list of per-row messages). Execution via FastAPI `BackgroundTasks` (matches existing `ResolvePoiUseCase` fire-and-forget precedent) — background worker must open its own DB session, since `yield`-dependencies close before `BackgroundTasks` run (FastAPI ≥0.106, already flagged in the 07-16 source). Self-healing timeout (treat a `pending`/`processing` job older than a threshold as `failed` on next poll) covers a process dying mid-job, since there's no real task queue.

**Bulk is create-only.** No "bulk update" verb. If an admin needs to correct a batch, the flow is delete-by-`bulk_job_id` + a fresh create job — not an in-place merge/update.

**Dedup: explicitly rejected a hash-based approach.** `Property.id` is a randomly generated UUID with no natural/external key in the CSV (unlike POIs, which have a real `external_id`+`source` from OSM). Explored and rejected, in order:
1. Content-hash of the full row as a synthetic idempotency key + `ON CONFLICT DO UPDATE` — rejected because any legitimate field edit (typo fix, and critically **price**) changes the hash and silently produces a duplicate instead of an update.
2. Excluding `price` from the hash (identity key = stable fields only, e.g. address + owner email) so retries survive price edits, combined with excluding `price` from the `DO UPDATE SET` clause to prevent bulk-import from becoming a backdoor around the price-change governance rule (price changes must go through user edit or admin moderation, not bulk). Explored a batch-level heuristic (ratio of "identity-match + price-only-diff" rows over total, two-tier response: few = informational warning, majority = hard policy-violation error) — judged over-engineered for the actual need and dropped.
3. **Final decision**: no automatic dedup at all. Retrying with the same file without using the redo action can produce duplicates — documented as expected behavior (front-end hover/tooltip warning), not silently prevented. Mitigation is `bulk_job_id` traceability + an explicit redo action (see below), not detection/hashing.

**Redo flow.** `Property` gets a nullable `bulk_job_id` FK. The job detail endpoint (`GET /admin/bulk-jobs/{uuid}`) returns the `property_id`s it created (also serves the already-decided owner-traceability need from the 07-16 owner_id item — same entity covers both). A "redo" action soft-deletes (reusing the existing `delete_property.py` soft-delete pattern, not a hard delete — some of those rows might already have real engagement) all properties with that `bulk_job_id`, then reprocesses. The delete must filter server-side by `bulk_job_id` directly — not accept a client-supplied id list, even though the front receives the ids for display. Retry creates a **new** job id with a `retry_of_job_id` pointer back to the original, rather than mutating the failed job in place, so failed attempts stay in the audit trail.

**Presigned-upload retry (biggest simplification).** Instead of proxying the CSV bytes through the API request (today's `file.read()` in `admin.py`, sync, up to 10MB/50MB), the browser uploads the CSV directly to MinIO via presigned URL — same pattern already used for property images (`property_image_upload_batches`). The bulk endpoint receives only the storage key, not file bytes, and the background job reads from storage. Consequence: retry doesn't need a new upload at all — the front can re-trigger processing pointing at the same already-stored object, with zero bandwidth cost on retry. Open detail: the stored file needs a retention TTL (reuse `expires_at` idiom) so an old job's storage key can't be replayed indefinitely with stale data.

**catalog-service scope.** `bulk_create_neighborhoods` already has real dedup via `ON CONFLICT (locality_id, code) DO UPDATE` (`sql_neighborhood_repository.py`) — resubmitting the same file is already safe/idempotent there. It only needs the `bulk_jobs` table + background wiring, none of the dedup/redo design above applies. `bulk_enrich_neighborhood_geometries` needs the same async wiring. Neither was previously logged as its own open item (only the properties-service one was, from 07-16) — added to `open-items.md` now.

## Open questions
- TTL for the presigned-upload's stored file (how long a retry can reuse the original upload without forcing a fresh one) — not decided.
- Whether `retry_of_job_id` chains (retry-of-a-retry) need a cap or just follow the pointer back arbitrarily — not discussed.
- Presigned-URL flow details (content-type validation before issuing the URL, expiry of the presigned URL itself) — not discussed, flagged as a detail to close before implementing.

## Next steps
Not started — branch `refactor/bulk-async-processing` created but no code written yet ("hoy no lo voy a hacer pero ya sé cómo se hace"). Plan jointly for both services before implementing: `bulk_jobs` migration (both services), `bulk_job_id` FK migration (properties-service only), presigned-upload endpoint + status/detail/redo endpoints, background task wiring.
