---
title: Bulk property import — async worker, chunking, idempotent retry
captured-from: conversation
captured-on: 2026-07-27
participants: [raul, claude]
---

## Context
Finishing the half-written bulk CSV import on branch `refactor/bulk-async-processing`. The worker existed but was never wired: the endpoint still ran the old synchronous in-memory path, nothing triggered the worker, and the `bulk_jobs` row was never closed out. Review also surfaced that a retry would have duplicated every row the original run had already inserted.

## Key conclusions

### Flow and wiring
- Three-step flow: `POST /v1/admin/properties/bulk/upload-url` (201, presigned PUT) → front PUTs the CSV straight to storage → `POST /v1/admin/properties/bulk` with `storage_key` (202 + `batch_id`, schedules `BackgroundTasks`) → `GET /v1/admin/properties/bulk/{job_id}/status` (200) for polling.
- The endpoint no longer accepts `UploadFile`. Upload bypasses the API to save bandwidth, so the request body is just the `storage_key` the front got back.
- The background runner opens **its own `Session(engine)`**, not the request-scoped one — the task outlives the request that scheduled it. Pattern copied verbatim from the `hiring-service` (globant) `run_process_employees_chunk` / `get_process_employees_runner` pair.
- `RequestBulkUploadUrlUseCase` creates no DB row: the `BulkJob` is born only when the client returns with the key, so an abandoned upload leaves nothing behind.

### Worker structure
- File renamed to `workers/bulk_create_properties_worker.py`, class to `BulkCreatePropertiesWorker` — it previously collided by name with the admin `BulkCreatePropertiesUseCase` that only enqueues the job.
- `execute(*, principal, job_id) -> None`. Nobody receives a return value in fire-and-forget, so the outcome is written to the `bulk_jobs` row instead. The worker reads `storage_key` off the job row rather than receiving it.
- Persistence happens **per chunk of 2500**, inside the streaming loop (enrich → map → persist → repeat). Chunking only bounded the gateway calls before; accumulating every enriched row first made memory and transaction size O(file).
- Consequence accepted: the import is no longer atomic across the file — earlier chunks are committed when a later one fails.
- Helpers reorganized into `workers/helpers/{chunking,enrichment,mapping,persistence}/` plus a shared `row_ref.py`. Worker dropped from 236 to 159 lines.
- `seed_mapper.py` moved from `services/admin/helpers/` to `workers/helpers/mapping/`, and worker-only schemas (`BulkPropertyCsvRow`, `BulkCreatePropertyItem`, `BulkRowError`, `BulkCreatePropertiesResult`) moved from `admin_schemas.py` to `workers/schemas/bulk_schemas.py`. No worker → admin UC/helpers/schemas imports remain; only the `AdminUnitOfWork` port.
- `enrich_chunk` takes `resolve_emails` as an injected callable rather than importing the worker method — keeps the helper testable with a fake.

### Idempotent retry (the substantive bug found)
- `build_models` generated `uuid.uuid4()` per row, while `bulk_insert` upserts on `index_elements=["id"]`. The conflict target could never fire, so re-running a file inserted duplicates. `Property` has no business `UniqueConstraint` to catch it either.
- Fix: CSV now carries a required `external_id`, and `derive_property_id()` returns `uuid5(settings.BULK_PROPERTY_ID_NAMESPACE, external_id)`. Same input always yields the same id, so the existing upsert works and retry becomes idempotent.
- `external_id` is `Field(min_length=1)` on purpose: blank values would all hash to one id and silently overwrite each other — worse than duplicating.
- `BULK_PROPERTY_ID_NAMESPACE` lives in settings and must be treated as **frozen**: changing it re-keys every property and past imports come back as new records. Moving it to settings made it env-overridable, which is the accepted cost.
- Whole chain now dedupes: `Property` by `id`, `PropertyLocation` by `property_id`, `PropertyImage` by `url`. `_PROPERTY_UPSERT_FIELDS` excludes `created_at`/`created_by`, so a re-import updates data but preserves the original creation audit.

### Job lifecycle
- `update_status(job_id, status, errors=None, confirmed_at=None)` added to the port and `SqlBatchRepository`. It writes **only the columns actually passed** — the previous unconditional `values(status=..., errors=errors or [])` would have wiped already-recorded errors when marking a job failed.
- `finalize_job` (happy path only) sets `completed` + serialized errors + `confirmed_at`. `mark_job_failed` sets `failed`, is best-effort, and swallows its own failure so it can't mask the original exception.
- `completed` means "the run finished", not "every row succeeded" — a job with 400 row errors is still `completed`.
- `expires_at` was decorative: the enqueue UC read `target_job.expires_at` only to inherit it. Added the guard (`BulkJobExpiredError`, 409), mirroring `confirm_image_uploads.py`. Check order is: exists → not a retry-of-retry → not expired.
- `retry_of_job_id` is written at row creation, not by the worker; the "retry the original, not a retry" rule was already enforced by `RetryOfRetryNotAllowedError`. Rows stay independent — the chain lives only in the FK.
- `GetBulkJobStatusUseCase` copies the globant `_is_stale` pattern: a job still `pending` past `BULK_JOB_TIMEOUT_SECONDS` (600) is reported and persisted as `failed`. This matters more here than in globant because `BackgroundTasks` die with the process, so nothing else would ever move that row.

### Savepoint leak
- `begin_nested()` stored the savepoint but nothing released it on success, so each row of the row-by-row fallback opened a savepoint *inside* the previous still-open one.
- Added `release_savepoint()` to the `AdminUnitOfWork` port and `SqlAdminUnitOfWork` (calls `self._savepoint.commit()`); the fallback now calls it on every success.

## Open questions
- Seed CSVs (`seed_bogota_500.csv`, `seed_bogota_5k.csv`) lack both `external_id` and `email` columns; with `StrictBase(extra="forbid")` and both fields required, 100% of rows would fail validation today.
- `BUCKET_BULK_PROPERTIES` has an empty default, is absent from the root `.env`, and nothing in the repo creates MinIO buckets. `backend/properties-service/.env.example` is stale (lists neither bucket).
- Upload size cannot be enforced on a plain presigned PUT — `max_size_bytes` travels to the client as a hint only. A hard limit would require migrating to presigned POST with `content-length-range`.
- Owner lookup is case-sensitive end to end; undecided whether to normalize emails to lowercase in `BulkPropertyCsvRow` and in users-service storage.
- `JobStatus` has only `pending/completed/failed` — no `processing` (a running job is indistinguishable from a queued one except via `_is_stale`) and no `expired` (so the image-flow symmetry of persisting `expired` was deliberately not copied).
- ORM construction still happens in the UC/worker rather than behind the repo. Pre-existing debt, already flagged by the `# TODO: refactor` in `create_property.py`; deferred so both the single and bulk paths get fixed together.

## Next steps
- Add `external_id` and `email` columns to the seed CSVs.
- Set `BUCKET_BULK_PROPERTIES` in `.env`, create the bucket in MinIO, refresh `.env.example`.
