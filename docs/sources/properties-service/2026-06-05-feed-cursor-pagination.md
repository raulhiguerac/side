---
title: Feed cursor pagination — opaque base64 cursor
captured-from: conversation
captured-on: 2026-06-05
participants: [raul, claude]
---

## Context
The feed endpoint (`GET /search/feed`) returned `list[PropertyCardSchema]` with no pagination token, making infinite scroll impossible. The cursor fields existed internally (`FeedCursor`) but were never exposed to the client.

## Key conclusions

- **Opaque cursor pattern adopted**: `FeedCursor` is serialized as `JSON → UTF-8 → base64url` and returned as a single `next_cursor: str | None` field. The client passes it back as `?cursor=<token>` without needing to know its internal structure.
- **`FeedPage` schema**: replaces `list[PropertyCardSchema]` as the response. Fields: `items: list[PropertyCardSchema]`, `next_cursor: str | None = None`.
- **`get_organic` signature changed**: returns `tuple[list[PropertyCardSchema], tuple[datetime, UUID] | None]`. The second element carries `(last.created_at, last.id)` for cursor construction; `None` when no results.
- **`position` counts only organics**: tracks total organic items seen across pages, used for `FEED_MAX_RESULTS` guard and ad rotation. Ads injected in `_inject_ads` are not counted.
- **Next cursor calculation**: `position = (cursor.position if cursor else 0) + len(cards)`. Computed before ad injection.
- **`parse_feed_cursor` dep eliminated**: replaced with `cursor: Optional[str] = Query(default=None)` directly on the endpoint. No wrapper needed.
- **`InvalidCursorError`**: added to `core/exceptions/validation.py` with code `"INVALID_CURSOR"`, registered as `400` in `ERROR_CODE_TO_HTTP_STATUS`. Raised in `decode_cursor` on any decode/validate failure.
- **Keyset pagination stability**: using `created_at < cursor_created_at` means new properties entering the top of the feed never shift existing pages. Pull-to-refresh (clearing the cursor) is the intended path for seeing new listings.

## Relevant files
- `src/app/services/search/helpers/feed/encoding.py` — `encode_cursor`, `decode_cursor`
- `src/app/services/search/use_cases/get_feed.py` — UC with full pagination logic
- `src/app/services/search/helpers/feed/organic.py` — returns `(cards, last_fields)` tuple
- `src/app/services/search/schemas/feed_schemas.py` — `FeedPage`, `FeedCursor`
- `src/app/api/routes/search.py` — `response_model=FeedPage`, single `cursor` query param
- `src/app/core/exceptions/validation.py` — `InvalidCursorError`
- `src/app/api/handlers/exception_handlers.py` — `"INVALID_CURSOR": 400`
- `tests/unit/services/search/helpers/test_encoding.py` — encode/decode roundtrip + error cases
- `tests/unit/services/search/use_cases/test_get_feed.py` — updated for `FeedPage` return type

## Open questions
- None — backend implementation complete and tests passing (20/20).

## Next steps
- Frontend: handle `FeedPage` response shape, implement `loadMore()` that appends `items` and passes `next_cursor` as `?cursor=` on the next request. Hide load-more trigger when `next_cursor` is `null`.
