---
title: Bulk import now creates properties in `pending`, and publication stays orthogonal to verification
captured-from: conversation
captured-on: 2026-08-01
participants: [raul, claude]
---

## Context
Follow-up to the 2026-07-29 finding that the 18.744 bulk-imported properties sit in `unverified` with nothing to move them to `pending`, leaving them outside any moderation queue. Wiring the admin moderation UI forced the decision.

## Key conclusions

### The import writes `pending` directly
`seed_mapper.py:237` now builds each `Property` with `verification_status=VerificationStatus.pending` instead of `unverified`.

Rationale: the `unverified → pending` transition was designed as "the owner requests verification". A bulk import has no owner requesting anything — the admin uploading the CSV *is* the requester. Nacer en `pending` no saltea el paso, reconoce que ocurrió fuera del sistema.

Legal at the code level because **creation is not a transition**: the worker constructs the model and `bulk_insert`s it, never touching `VerifyPropertyUseCase` or its `_ALLOWED_TRANSITIONS`. Tests: 81 in `tests/unit/workers` + 43 in `tests/unit/services/admin` pass unchanged; no test asserted `unverified` on import.

### `status` stays `active` — the two axes are deliberately independent
Publishing and verifying are separate state machines and a listing can legitimately be visible *while* under review, disclosed with a badge. Coupling them was an incorrect assumption, not a domain rule. So the import keeps `status=ListingStatus.active` (`seed_mapper.py:236`), which also overrides the model default of `draft`.

### The disclosure exists in the detail but not in the feed
`usePropertyDetail` maps `pending → "En revisión"` with its own style and `PropertyOverview` renders it, so the public *detail* already discloses. But `PropertyCardSchema` carries no `verification_status`, so the feed and the map — where people actually browse — cannot show it. If the position is "publish with a caveat", the caveat must live where browsing happens.

### The badge only means something once a fraction is `verified`
After this change 100% of the inventory is `pending`. A seal everyone holds communicates nothing; its value depends on the queue actually being worked, not on being displayed.

### Admin detail is coupled to the public one
`GET /admin/properties/{id}` returns the same `PropertyDetailSchema` **and shares the `cache_property` key** with the public endpoint. This blocks adding admin-only fields (documents, `owner_id`, `rejection_reason`) without splitting the schema — adding them would publish them and poison the shared cache.

### Storage reads are direct URLs, not signed
`PropertyImage.url` is a stored URL read straight from the bucket; presigning is only used for the upload `PUT`. Fine for listing photos, unusable for verification documents (escritura, cédula), which would need short-TTL presigned `GET` generated per request and admin-only — that read path does not exist yet.

## Open questions
- **Backfill**: the 18.744 already imported remain `unverified` and nothing will ever move them. Needs an `UPDATE ... WHERE verification_status = 'unverified'` or they stay a second population with different rules.
- **A queue of 18.744 is not workable.** Should verification be exhaustive or sampled/prioritized — by price outliers against the AVM, missing photos, owners with many listings? That would yield tens instead of thousands.
- `set_estimated_price` does not invalidate cache, unlike `verify` and `set_status`. `admin_estimated_price` is not part of `PropertyDetailSchema`, so it may not need to — to confirm when wiring that action.
- Requiring documents for approval would give the queue its natural trigger (owner uploads papers → `pending`), but costs a new model + migration, an admin-only detail schema, and the signed-read path above.

## Next steps
- Add `verification_status` to `PropertyCardSchema` and a badge on the feed card.
- Decide and run the backfill for the already-imported rows.
- Wire the three moderation endpoints (`PATCH /verification`, `PATCH /status`, `POST /estimated-price`), all `204` with no body, so acting requires a refetch.
