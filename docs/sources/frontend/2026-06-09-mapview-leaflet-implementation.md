---
title: MapView — Leaflet implementation decisions and vue-leaflet race condition fix
captured-from: conversation
captured-on: 2026-06-09
participants: [raul, claude]
---

## Context
MapView.vue was built as a split-layout feed+map view. Several non-obvious issues appeared around Leaflet reactivity and initial centering.

## Key conclusions
- **Layout**: flex h-[80vh], left half = scrollable 2-col card grid + pagination buttons, right half = sticky MapUser component.
- **useFeedMap composable**: fetches `/v1/search/feed/map` with bbox + h3_resolution (zoom≥15 → r9, else r7). Client-side pagination slices `_allItems` (Fisher-Yates shuffle on fetch to desegregate H3-grouped results). PAGE_SIZE is a `computed` (not a constant) so it reacts to zoom changes.
- **Marker hover**: `hoveredId` ref in MapView flows as prop to MapUser → conditional icon size/color per marker. Active = 48px green, normal = 24px dark blue. Building icon uses wrapping div with bg color (Lucide Building is stroke-only, fill has no effect).
- **MapUser**: `zoom` and `center` both use `defineModel` + `v-model:` on `<l-map>` for two-way reactivity.
- **URL state**: `onBbox` wrapper calls `router.replace({ query: bbox params })` then `fetchByBbox`. No watcher on route.query needed — map drives URL, not the reverse.
- **vue-leaflet race condition (critical)**: vue-leaflet registers its center watcher *inside* an async `onMounted` (awaits dynamic Leaflet import). If the parent also updates `center.value` in `onMounted`, the watcher may not be registered yet → map ignores the programmatic pan. Fix: initialize `center` ref **synchronously** from localStorage in script setup (before the map mounts), so the map starts at the correct location without needing a post-mount `setView`.

```ts
function getInitialCenter(): [number, number] {
  try {
    const raw = localStorage.getItem(STORAGE_KEYS.USER_LOCATION);
    if (raw) {
      const loc = JSON.parse(raw);
      if (loc.latitude && loc.longitude) return [loc.latitude, loc.longitude];
    }
  } catch {}
  return [4.681414, -74.046864]; // Bogotá fallback
}
const center = ref<[number, number]>(getInitialCenter());
```

- **onMounted**: calls `store.detectLocation()` (reads localStorage or fetches IP API) → `fetchByBbox` around user location ±0.05°. No need to update `center` after mount since it's already initialized correctly.
- **usePropertyMapper**: shared composable used by both FeedView and MapView. Watches `items` ref → resolves unique city_ids → builds `neighborhoodLookup` map → `toCard()` maps `FeedCard` to `Property` with resolved neighborhood name.

## Open questions
- First-time users (no localStorage): map starts at Bogotá, fetch is around IP location — acceptable for MVP.

## Next steps
- Add error/loading states to MapView (currently no skeleton or error boundary).
- Smoke test at different zoom levels with real data.
