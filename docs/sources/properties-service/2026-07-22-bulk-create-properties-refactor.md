---
title: Bulk create properties — streaming worker refactor
captured-from: conversation
captured-on: 2026-07-22
participants: [raul, claude]
---

## Context
Refactor of the properties-service bulk-create worker (`workers/bulk_create_properties.py`)
to process a CSV uploaded to object storage: stream rows, validate, resolve
catalog + owners in parallel, and bulk-insert. Work on branch `refactor/bulk-async-processing`.

## Key conclusions
- **Storage-agnostic streaming**: the row generator (`workers/helpers/chunking.py`)
  depends on the `StoragePort` port, not MinIO. MinIO only lives in the adapter;
  swapping to S3 is an adapter change. Generator stays "dumb": generic CSV → `dict`.
- **Validation at the worker edge**, not in the generator: each raw `dict` is fed to
  `BulkPropertyCsvRow(**row)`. `StrictBase` (`extra="forbid"`, no `strict=True`) so
  coercion still turns CSV strings into `float` for `lat`/`lon`. A failing row is
  caught (`ValidationError`), turned into a `BulkRowError`, and skipped (`continue`) —
  one bad row must not abort the 2500-row batch.
- **Wrapper row shape chosen (typed/nested)**: batch items are
  `{"line": int, "id": str(uuid4), "value": BulkPropertyCsvRow}`. All CSV data is
  accessed via `row["value"].campo` (model attribute). Chosen over the flat-dict
  alternative despite more accessor churn.
- **Per-row UUID generated at read time** = correlation key for catalog resolution
  and future `property_id`. Must be `str(uuid.uuid4())` (not the `uuid.UUID` class,
  not a raw `UUID`) because `PointToResolve.id` is `str`; `result.id` returns `str`,
  so `rows_by_id` keys must be `str` or the lookup `KeyError`s.
- **Structured errors**: new `BulkRowError(line, ref, issues)` schema replaces
  `list[str]`. `issues` derived from `e.errors()` as `f"{err['loc'][-1]}: {err['msg']}"`.
  `line` is a monotonic counter over generator output (NOT the batch index, which is
  windowed 0–2499 and would report the wrong number). `ref` = human id from the raw
  row (`email @ lat,lon`), extracted via `row_ref` helper.
- **Alignment**: `BulkCreatePropertiesResult.errors` migrated to `list[BulkRowError]`
  to match `BulkJob.errors` which is Postgres `ARRAY(JSONB)` (`jsonb[]`) — a real
  typed array, correct here because errors are written once at job close, not appended.
  Serialize with `[e.model_dump() for e in result.errors]` at the DB boundary; the
  model keeps `list[dict]`, no schema import in the domain model.
- **Extractions**: `row_ref(row: dict) -> str` → `workers/helpers/row_ref.py` (takes a
  flat dict; in the batch pass `row["value"].model_dump()`). `process_location_batch`
  extracted to `workers/helpers/location_batch.py`, decoupled from the class via a
  `catalog: CatalogGateway` parameter. Resolves the whole batch in one catalog call,
  correlates by uuid, merges geo ids into the row root.

## Open questions
- **`ARRAY(JSONB)` vs flat `JSONB`** for `BulkJob.errors` — confirmed staying as
  `jsonb[]`; array tracking non-issue since it's written whole at close.
- **`confirmed_at`** on `BulkJob` is defined but never set — semantics vs `status`
  undecided.
- **Users resolution direction**: `UsersGateway.resolve_accounts` is id→account and
  `get_user_ids` is id→email, but the seed needs **email→owner_id**. No method exists
  yet. Today the worker hardcodes `owner_id=principal.sub` (all props owned by the
  uploading admin).

## Next steps
- **Close the BulkJob** (highest-impact gap): the worker never writes back
  `status`/`errors`/`confirmed_at`, so the front always sees `pending` + empty errors.
  Add a write-back method to `BulkJobRepository` (e.g. `mark_finished(job_id, status,
  errors)`) and decide when status is `failed` (e.g. `inserted == 0`).
- **Rewrite the second half of `execute`**: still contains dead per-row design code
  (`sem`, `records`, `self._enrich_location`, `row_to_item(row=result, ...)`) that
  doesn't match the per-batch approach. Wire the `asyncio.gather` of catalog + users
  in parallel here; pass the pre-generated `id`/`owner_id` into `build_models`.
- **Finish `_process_users_batch`** (currently truncated to a half signature),
  correlated by email (dedup emails → resolve → fan out to rows), pending the
  email→owner_id method.
- **Config**: add `BUCKET_BULK_PROPERTIES` setting + import `StorageMisconfiguredError`
  in the worker `__init__` (both referenced but missing; only `BUCKET_PHOTOS_PROPERTIES`
  exists in settings).
- Rename for clarity: worker class `BulkCreatePropertiesUseCase` collides with the
  admin use case of the same name; adapter `SqlBatchRepository` vs port `BulkJobRepository`
  (batch vs job).
