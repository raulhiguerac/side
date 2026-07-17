---
title: Bulk create properties conflates owner_id with the importing admin — resolve by email instead
captured-from: conversation
captured-on: 2026-07-16
participants: [raul, claude]
---

## Context
Follow-up to the same-day finding that `POST /admin/properties/bulk` is synchronous (see the paired `2026-07-16-bulk-create-sync-timeout-risk.md` capture). Reviewing `BulkCreatePropertiesUseCase`/`seed_mapper.py` surfaced a second, unrelated issue in the same code path: every bulk-imported property is owned by the admin who ran the import, not by a real property owner.

## Key conclusions
- `build_models(item=item, owner_id=principal.sub, created_by=principal.sub)` uses the same UUID (the logged-in admin) for both fields — today every bulk-imported property shows up under the importing admin's own `GET /properties/me`.
- `created_by=principal.sub` is correct as-is — it's a legitimate audit trail of who executed the write, consistent with the `created_by`/`updated_by` pattern already used across the model.
- `owner_id` is wrong: it should resolve to the actual property owner's account, not default to the importer.
- Decision: resolve `owner_id` by **email** against `users-service`'s `Account.email` (already unique + indexed, zero schema migration needed). Rejected resolving by a national-ID-style field ("cédula") — checked `users-service/src/app/models/account.py`, no such field exists today (`account_id`, `email` are the only unique identifiers); adding one would require a migration plus deciding what to do on a no-match, more scope than needed right now.
- The bulk CSV would need an email column per row for this resolution to work. What happens when no account matches that email (auto-create a placeholder account vs. reject the row) is an open question, not decided.
- Batch traceability for bulk imports doesn't need a separate mechanism — it can reuse the batch entity already planned for the async-batch refactor (the `202 { batch_id }` + background processing + status-polling pattern from the paired sync/timeout capture). If that entity records which `property_id`s it created, both problems (async processing, ownership/import traceability) share one piece of infrastructure.
- Side benefit noted: unblocks realistic demo data — today a seeded dataset looks unrealistic because every imported property belongs to a single admin "mega-owner"; resolving by email allows attributing imports to varied (real or fabricated demo) accounts instead.
- Logged in `wiki/_shared/open-items.md`, second **IMPORTANTE** item under "properties-service — arquitectura interna", directly below the sync/timeout item (same endpoint, same use case).

## Open questions
- No-match-on-email handling: create a placeholder account vs. reject the row — not decided.
- Whether/when to expand identity resolution beyond email (e.g. a real "cédula" field collected via onboarding later) — flagged as a possible future direction, not planned.

## Next steps
- Design `owner_id` resolution alongside the async batch refactor when that work is picked up — natural to build together since both changes touch the same use case (`BulkCreatePropertiesUseCase`) and the batch entity serves both purposes.
