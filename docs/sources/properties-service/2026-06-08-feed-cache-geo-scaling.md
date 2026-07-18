---
title: Feed Redis cache + geo query scaling
captured-from: conversation
captured-on: 2026-06-08
participants: [raul, claude]
---

## Context
Feed endpoint had no server-side cache. Also discussed scaling strategy for ST_Contains geo queries under load.

## Key conclusions

### Feed Redis cache (properties-service)
- Cache aside on `GetFeedUseCase.execute()` — only organic items cached, not ads (ads are re-injected on cache hit to preserve rotation).
- Cache key: `feed:page:{sha256[:16](cursor + preferences + filters)}` — must include all params to avoid collision between users with different preferences hitting the same `cursor=None` ("first page").
- TTL: 300s (5 min). No proactive invalidation — eventual consistency acceptable.
- `model_dump(mode="json")` required when serializing to Redis — plain `model_dump()` leaves `Decimal` and `UUID` unserializable.
- Cache key helper: `feed_page(cursor_str, preferences, filters)` in `services/shared/helpers/cache_keys.py`.

### Geo query scaling (catalog-service)
- `get_location_by_point` does `ST_Contains` over all neighborhoods with no pre-filter — expensive under load.
- Fix: pre-filter by H3 cell (`WHERE h3_index = ANY(Neighborhood.h3_cells)`, GIN index) before running `ST_Contains` on candidates.
- Scaling strategy: read replicas + PgBouncer (transaction pooling) in front. Eventual consistency acceptable for geo reads (neighborhood boundaries change rarely).
- HPA scales pods but DB is the bottleneck — replicas absorb read load without touching primary.

## Open questions
- H3 pre-filter optimization for `get_location_by_point` not yet implemented.

## Next steps
- Implement H3 pre-filter in `SqlGeoreferentiationRepository.get_location_by_point`.
