---
title: Moderation lifecycle closed — verified is no longer terminal, edits degrade it, and actions are signed
captured-from: conversation
captured-on: 2026-08-02
participants: [raul, claude]
---

## Context

Before wiring the admin panel's moderation actions, the backend side of moderation was audited end to end. The trigger was a product question: what happens to a property that passes verification and *then* violates the rules — and what happens when its content changes after approval.

## Key conclusions

### `verified` is no longer terminal

`VerifyPropertyUseCase._ALLOWED_TRANSITIONS` now maps `verified → [pending, rejected]`. Approving stopped being irreversible: a violation found after approval revokes the badge, and a material content change sends it back to the queue.

The only transition still forbidden out of `verified` is back to `unverified`, which exists solely as an initial state — nothing points to it.

### Takedown is `status → inactive`, not a new state

Rejected as a design: adding a `removed`/`deleted` verification state. Publication and verification are independent axes and both already exist:

- Removing a listing from view is `ListingStatus: active → inactive`.
- Removing the badge is `VerificationStatus: verified → rejected`.

`inactive` works as a real takedown for free, because the owner's own machine (`SetPropertyVisibilityUseCase`) only does `draft ↔ active`: once an admin deactivates something, only an admin can republish it.

`rejected` is reused for post-approval revocation instead of introducing `revoked`. Splitting them only pays off if rejection metrics or an appeals flow need to tell the two apart.

### Frozen edit fields are now enforced server-side

ADR-0006 froze `location`, `area_m2`, `bedrooms`, `bathrooms`, `property_type`, `listing_type`, `stratum`, `year_built`, floors and `parking_spots` — but as a **frontend-only** restriction; `UpdatePropertyRequest` still accepted them, so any client hitting `PATCH /v1/properties/{id}` directly could move a verified property to another city.

Fixed by deleting those fields from the schema. `StrictBase` already sets `extra="forbid"`, so a client sending them now gets a 422 with no extra validator. The request is down to `condition`, `currency`, `price`, `admin_fee`, `description` — exactly what `PropertyEditForm.vue` captures.

Rejected alternative: keep accepting them and degrade verification on change. That turns a request that should not exist into moderation work.

### `UpdatePropertyUseCase` lost its catalog dependency

With `location` gone from the schema, the whole `if loc_data is not None` block became unreachable: the catalog guard, the `PropertyLocation` writes and the `compute_h3` recompute. All removed, along with the `CatalogGateway` constructor arg and its wiring in `deps/listing.py`.

The general rule established: **catalog is called when a write creates or changes a reference to an external id.** It stays in `CreatePropertyUseCase` — the front resolves the ids for UX, but the guard exists for referential integrity (the neighborhood must exist, and must belong to that city), which is the de-facto FK across services. If a write can no longer touch that reference, the validation is dead weight.

### Only image changes degrade verification

Of the five still-editable fields, none justify re-moderation: price, currency, admin fee and condition don't change what was verified about the property. Two candidates were considered:

- **Images** — the real vector: `confirm_image_uploads` and `delete_property_images` can replace the whole photo set on a `verified` property. **Degrades.**
- **`description`** — 2000 chars of free text. **Does not degrade**, at least initially: it would push properties into a queue nobody is working yet, and text spam is better handled by reports than by preventive re-verification.

Implemented as `services/listing/helpers/verification_guard.py` → `degrade_verification(*, prop)`. It mutates in place and does **not** commit: the caller already has a transaction open, so the photo change and the loss of the badge land or fail together. It is a no-op outside `verified`, which also makes it idempotent.

Deliberately not hooked into `request_presigned_urls` (nothing lands there — it would punish someone who opened the form and gave up), `update_property`, or the import worker (rows are born `pending`, there is no badge to lose).

Chosen over routing the change through `_ALLOWED_TRANSITIONS`: the table validates transitions someone *requests*, and here both source and target are fixed in the code. The `if` also provides the "only from verified" rule for free, which the table version would still need on top.

### `rejection_reason` is bound to the target in the schema

`VerifyPropertyRequest` gained a `model_validator(mode="after")`: required when rejecting, forbidden otherwise — including `pending`, since requeueing is not rejecting. Two asymmetric holes closed at once: approving with a reason left a self-contradicting row, and rejecting without one left the owner with nothing to fix.

Placed in the schema, not the use case: it is payload shape validation, and it keeps the unconditional assignment in `verify.py` correct by construction. Blank strings count as missing, because `StrictBase` sets `str_strip_whitespace=True` and `"   "` arrives as `""`.

### Moderation actions are now signed

Both moderation use cases were anonymous in the database: neither `verified_by` (a real column since the first migration, never written) nor `updated_by` was set, so `updated_at` moved without recording who or what.

`VerifyPropertyUseCase.execute()` and `SetPropertyStatusUseCase.execute()` now take `principal`. Both write `updated_by`; `verify` also writes `verified_by` when the verification is **resolved** (`verified` or `rejected`) and clears it when requeueing to `pending`, along with the reason — a property that is not resolved cannot have an approver.

`verified_by` earns its place over `updated_by` because the latter is overwritten by any later write, including the owner editing the price.

### The 204s stay as they are

`PATCH .../status`, `PATCH .../verification` and `POST .../estimated-price` keep returning `204` with no body. The consumer refetches.

Rejected: returning the updated row for the client to patch in place. With filters active the front would have to decide whether the row still matches and recompute the total — re-implementing the repository's `_apply_filters` `WHERE` in JavaScript, in a second place that has to be kept in sync.

## Open questions

- **`verified_at` does not exist.** We now know who approved but not when: `updated_at` is clobbered by the next write. Adding it means an Alembic migration — deferred.
- **No moderation history.** With `verified → rejected` open, a property can be resolved several times and only the last one survives in the columns. A moderation events table is the real answer; explicitly out of scope for now.
- **The error payload drops `context`.** `base_error_handler` returns only `{message, code}`, so a `409 INVALID_STATUS_TRANSITION` reaches the client without the `{current, target}` it carries internally, and the message is in English. Clients can't render a specific explanation.

## Next steps

- Still missing for the admin panel: `GET /admin/properties/bulk` (blocks the imports tab entirely), a promotions schema with `ends_at`/`priority`/`is_active` (the current endpoint returns the public card), `GET /admin/properties/stats` for the hub KPIs, `PATCH /admin/promotions/{id}`, and an admin-side property edit.
- `tests/integration/` is still an empty TODO. The first API-level tests were added under `tests/unit/api/` using `TestClient` + `dependency_overrides` (no DB, no Redis); suite is at 224 unit tests.
- Environment note: a stray `jwt` 1.4.0 was installed alongside PyJWT and shadowed the `jwt` module, breaking `deps/auth.py` at import and preventing the service from booting. Removed; PyJWT reinstalled.
