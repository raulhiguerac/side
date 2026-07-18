---
title: Public user properties — has_more pagination
captured-from: conversation
captured-on: 2026-06-25
participants: [raul, claude]
---

## Context
The `GET /v1/properties/users/{user_id}` endpoint returned a flat list. The frontend needed a `has_more` flag to drive pagination without a `COUNT(*)` query.

## Key conclusions
- `PUBLIC_PROPERTIES_PAGE_SIZE = 21` in settings — fetch page_size+1 items; if `len == 21` then `has_more=True`, return only first 20. The comment in settings documents the +1 trick.
- New `PublicUserPropertiesResponse(items: list[PropertyCardSchema], has_more: bool)` DTO in `property_card.py`.
- Use case caches the full dict including `has_more`; old flat-list cache entries expire by TTL naturally.
- Route uses `response_model=PublicUserPropertiesResponse`.

## Next steps
- None — fully implemented and wired.
