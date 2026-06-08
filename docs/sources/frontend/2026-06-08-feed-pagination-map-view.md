---
title: Feed pagination via URL + PropertiesView subroutes
captured-from: conversation
captured-on: 2026-06-08
participants: [raul, claude]
---

## Context
Feed view needed pagination and a map toggle. Initially implemented an in-memory cursor stack; later concluded URL query params are the standard approach.

## Key conclusions
- **Feed pagination**: cursor lives in `route.query.cursor` (URL), not in-memory. Browser history handles back/forward natively. Redis cache on the back already covers performance.
- **In-memory cursor stack was a learning exercise** — the pattern (Record cache keyed by cursor, push-before-advance stack) is valid but overkill when URL state suffices.
- **PropertiesView** is the parent view at `/feed` with a Lista/Mapa toggle. Children: `/feed/list` → `FeedView`, `/feed/map` → `MapView`.
- Toggle active state derived from `route.name` (computed), not a local ref.
- `isAuthenticated` subtitle (`v-if`) lives in `PropertiesView` (parent), not in `FeedView`.
- `<router-view />` sits outside the padded header div to avoid double padding.
- `MapView.vue` created as stub placeholder.

## Open questions
- MapView implementation: Leaflet vs Mapbox GL, pins from `/search/feed/map` endpoint.

## Next steps
- Refactor `useFeed` to use `route.query.cursor` instead of in-memory cursor stack.
- Implement `MapView.vue` with map library.
