---
title: Bulk import smoke test with 20k rows, and the admin listing endpoint
captured-from: conversation
captured-on: 2026-07-28
participants: [raul, claude]
---

## Context
First end-to-end run of the bulk property import against real services and real data (20k rows from the FincaRaíz scrape, 14k seeded accounts). Everything until now had been verified by unit tests and code reading; nothing had actually executed. The run surfaced a class of bugs that reading could not, and the follow-up work prepared the admin listing endpoint for a moderation table.

## Key conclusions

### What the run proved and cost
- End to end: presigned PUT → MinIO → `BackgroundTasks` with its own session → 8 chunks → job closed. **20.000 rows in 164s**, 18.744 written, 1.256 errors, all of them geo (**6,3%**), zero owner-resolution failures.
- Every failure mode reading had predicted was real; several more only appeared at runtime. The pattern is worth recording: unit tests that mock the UoW never touch Postgres, so contract, driver and config bugs are invisible to them.

### The dedup bug (the substantive finding)
- Postgres rejects an `INSERT` whose `ON CONFLICT` target row appears twice (`CardinalityViolation`). With ids derived from `external_id`, two duplicate rows inside the **same chunk** produce the same `property_id` and break the statement.
- This hit **all 8 chunks** (5–9 collisions each), so **every** `bulk_insert` failed and the run silently degraded to 20.000 single-row inserts. The result was still correct — which is exactly why it went unnoticed; only the 164s and the `WARNING` lines betrayed it.
- Fixed with `collapse_duplicate_ids` in `property_writer.py`, keeping the last row per id (matching what a later chunk's upsert would do anyway). The row-by-row fallback consumes the deduped rows too, so a retried chunk cannot write the same id twice.
- Residual, currently dormant: `PropertyImage` conflicts on `url`, a different axis. Two properties sharing an image URL in one chunk would fail the same way. Not triggered today because `image_urls` is empty in the seed.

### Bugs found only by running
- **catalog contract**: `CatalogClient.get_locations_bulk` posted a bare array; catalog expects `BulkResolveLocationsRequest`, i.e. the list wrapped under `points`. Returned 422.
- **storage adapter**: `MinioStorageAdapter.chunk_file` called `get_object` on the `StorageClient` wrapper instead of a wrapper method, so the read failed with `AttributeError` and skipped error translation. Fixed by adding `StorageClient.get_object_body`, following the pattern users-service already used for `upload_file`.
- **logging was blind**: properties-service's format string rendered only message/level/name, so every `extra={...}` the worker logged was silently dropped. Replaced with a `JsonLogFormatter`. Separately, `filename` is a reserved `LogRecord` attribute and passing it in `extra` raises `KeyError` inside `logging.makeRecord`, before any formatter runs — it took down the presigned-url endpoint. Guarded with an AST test over `src/`.
- **`@seed.test` emails were invalid**: `.test` is RFC 2606 reserved and `email-validator` blocks six special-use TLDs (`arpa, invalid, local, localhost, onion, test`). The import accepted them (plain `str`), but reading a profile failed on `CurrentUserOut.email` (`EmailStr`). Regenerated the seed with `example.com`, which is also RFC 2606 but passes the validator.
- **JWT**: `get_signing_key_from_jwt` decodes the token to read its `kid`, so a malformed one raises `DecodeError` — not a `PyJWKClientError`. It escaped the handler as a 500 with a stack trace instead of a 401. The same gap exists in catalog-service, analytics-service, and worse in users-service (which only catches `PyJWKClientConnectionError`).
- **`BackgroundTasks` re-raise**: re-raising after the 202 was sent reached Starlette with the response already started, producing `RuntimeError: Caught handled exception, but response already started` plus two extra tracebacks. Now logged and swallowed — the job row already carries the outcome.

### Alembic
- `bulk_jobs` had **no migration at all**; the model and `Property.bulk_job_id` arrived in `f3a0c4d` without one, and the service has no `create_all`. The dead column was worse than the missing table: SQLAlchemy emitted `properties.bulk_job_id` in every `SELECT`, so feed, detail and create would fail against a migrated DB, not just the import.
- `migrations/env.py` imported models as bare `models.*` while the models import each other as `app.models.*`, loading every model twice under two identities and dying with "Table 'properties' is already defined". Fixed by copying users-service's approach: insert `src` on `sys.path` and import `app.models.*`.
- Autogenerate proposed dropping ~40 PostGIS/tiger tables because they are reflected but absent from `target_metadata`. Postgres would have refused (extension-owned objects), but the migration ran in a transaction, so the whole thing — including `create_table('bulk_jobs')` — would have rolled back. Added an `include_object` hook scoping autogenerate to `target_metadata`.
- `ADD COLUMN ... NOT NULL` on a populated table needs a `server_default`; autogenerate omits it.

### Reporting
- `bulk_jobs` gained an `inserted` column, surfaced by the status endpoint: callers were seeing a list of failures with no denominator. `inserted + len(errors)` is the total the run read. `mark_job_failed` deliberately leaves it alone so a crash mid-run does not erase what already landed.

### Admin listing endpoint
- `GET /admin/properties` returned a bare `list[PropertyCardSchema]` — the **public feed card**, which hides exactly what moderation needs (`verification_status`, `owner_id`, `created_at`, `rejection_reason`) and carries no total. A table could filter by fields it could not display, and paginate without knowing how many pages exist.
- Added `AdminPropertyCardSchema` (new, not inheriting the public card, to avoid coupling moderation to feed changes) and `AdminPropertiesPage {items, total, page, page_size}`, plus `count_all` in the repository.
- `get_all` and `count_all` share `_apply_filters`: a filter added to one and not the other would make the total disagree with the rows, silently.
- Page and count run **sequentially, not gathered** — they share the UoW's `Session`, and a SQLAlchemy `Session` is not safe across threads.
- `noload` on `images`, `location` and `promotions` in `get_all`: `Property` eager-loads all three with `selectin`, so every page also fetched image rows, PostGIS geometries and promotions that the admin schema discards. 5 queries per request → 2.
- **Offset pagination, not the opaque cursor** the feed uses. Not a shortcut: admin needs jump-to-page and a total, which cursors structurally cannot give — `useFeed` already keeps a `cursorStack` purely to support going back, and even that only does previous/next. Deep offset is cheap at ~19k rows; it would stop being true in the millions, where search replaces pagination anyway.

## Open questions
- The 6,3% geo failures mix three causes and have not been separated: scrape garbage (`0.0,0.0`), coordinates outside Bogotá (Cartagena, Pasto, Illinois, Spain), and genuine Bogotá coordinates that no neighborhood polygon contains. Only the third is a coverage gap worth fixing; the first two should fail.
- The idempotency re-run has not been done. Re-importing the same CSV should leave `count(*) FROM properties` unchanged with `created_at` intact — the empirical validation of [[adr-bulk-idempotent-external-id]].
- `inserted` counts rows written; with upsert semantics that is not the same as properties created. Naming it `written` or `processed` was raised and not decided.
- `JobStatus` still has no `processing`, so a running job is indistinguishable from a queued one except via the stale check.

## Next steps
- Separate the geo failures by cause before deciding whether catalog's neighborhood coverage needs work.
- Run the same CSV twice to close the idempotency question.
