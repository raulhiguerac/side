---
title: /users/resolve flipped from account ids to emails
captured-from: conversation
captured-on: 2026-07-27
participants: [raul, claude]
---

## Context
The bulk property import in `properties-service` carries an owner **email** per CSV row and needs the matching `account_id` to set `Property.owner_id`. The existing bulk endpoint resolved the opposite direction (id → email), so it could not serve that flow.

## Key conclusions
- `POST /v1/users/resolve` now takes `list[str]` (emails) instead of `list[uuid.UUID]`. **Breaking contract change**, safe only because a grep confirmed the worker stub was the sole consumer.
- The return shape is unchanged: `list[tuple[uuid.UUID, str]]` = `(account_id, email)`, which is exactly what the consumer needs to build its owner lookup.
- Changed the whole chain, params only: route `user.py` → `ResolveAccountsBulkUseCase.execute(*, emails)` → `AccountReaderPort.get_accounts_bulk(*, emails)` → `SqlAccountReader` → `get_active_accounts_bulk` in `account_repository.py`, whose filter became `Account.email.in_(emails)`. The `is_active.is_(True)` filter is retained.
- Emails with no active account are simply absent from the response rather than raising. Consumers depend on this: `properties-service` turns a missing email into a per-row "owner not resolved" error instead of assigning the wrong owner.
- On the consumer side, `UsersClient.get_user_ids(ids=...)` was renamed to `resolve_by_emails(emails=...)` — keeping the old name while posting emails would have been actively misleading.

## Open questions
- Lookup is case-sensitive; if the CSV casing differs from the stored account email it will silently not match. Undecided whether to normalize on write, on read, or both.

## Next steps
- None for this contract; the consumer side is already wired.
