---
title: POI detail view, MapUser cluster, and internalCenter pattern
captured-from: conversation
captured-on: 2026-06-15
participants: [raul, claude]
---

## Context
`PropertyDetailView` needed a "Cerca del lugar" section showing reachable POIs by transport profile and time range, with isochrone polygons and clustered markers on a map.

## Key conclusions

### Types (`types/pois.ts`)
- `OrsProfile`: `"foot-walking" | "cycling-regular" | "driving-car"`
- `GeoJsonPolygon`: `{ type: "Polygon", coordinates: number[][][] }` — matches backend schema
- `CATEGORY_PRIORITY`: numeric priority per OSM category (hospital=1, school=2, restaurant=3, supermarket=4…)
- `CATEGORY_META`: maps OSM category → `{ label: string, icon: Component }` (Spanish labels, Lucide icons)
- `RangeGroup`: `{ profile, minutes, seconds, dot, count, pois[], isochrone }`

### Composable `useReachablePois` (`composables/pois/useReachablePois.ts`)
- Single POST to `/v1/geo-resolution/reachable-pois` with `range_seconds: [300, 600, 900]` and all 3 profiles — returns 9 results at once.
- `loadPois(lat, lon, propertyId)` fills `ranges` ref.
- `groupedByRange` computed: filters by `activeProfile`, groups POIs by category via `CATEGORY_META` lookup, max 8 groups × 2 POIs each, sorted by `CATEGORY_PRIORITY`. Filters out POIs where `name === category` (unnamed OSM nodes).
- `ISOCHRONE_COLORS`: `{ 5: "#ef4444", 10: "#22c55e", 15: "#6366f1" }` (red/green/indigo).
- `DOT_BY_SECONDS`: `{ 300: "bg-red-500", 600: "bg-green-500", 900: "bg-indigo-500" }`.

### PropertyDetailView POI section
- Profile chip buttons (A pie / En bici / En carro) toggle `activeProfile`.
- Accordion per range (5/10/15 min), default open = 5. Click toggles; clicking open one closes it (`openRange = -1`).
- Category cards grid (2 cols, max 8), each card shows label + icon + up to 2 POI names.
- Map uses `MapUser` with `:min-zoom="12"`. Isochrones rendered as `<l-polygon>` in the slot with `[...groupedByRange].reverse()` so 15-min polygon renders first (bottom layer), 5-min on top. Fill opacity 0.3, no border.
- `mapCenterCoords`: local `ref<[number, number] | undefined>()` initialized in `onMounted` — replaces the composable's `mapCenter` computed to avoid TypeScript cast in `v-model`.
- `poiMarkers` computed: deduplicates by `${lat},${lon}` key. `CATEGORY_TO_MARKER` maps OSM category → `MarkerImageType`.

### MapUser — cluster + internalCenter pattern (`components/map/MapUser.vue`)
- POI markers (non-special types) rendered imperatively via `leaflet.markercluster`:
  ```ts
  const { MarkerClusterGroup } = require("leaflet.markercluster");
  clusterGroup = new MarkerClusterGroup({ maxClusterRadius: 50, chunkedLoading: true });
  ```
  Each POI gets a `L.divIcon` 10px circle colored by `MarkerImageType` (`POI_COLORS` map).
- Special types (`subject`, `house`, `apartment`) stay declarative with `<l-marker>` + `<l-icon>`.
- **`internalCenter` pattern**: `defineModel center` from parent is NOT bound directly to `l-map`. Instead, `internalCenter = ref(center.value ?? defaultCoords)` is what `l-map` uses via `v-model:center`. A `watch(center, ...)` syncs parent changes to `internalCenter`. This prevents Leaflet `LatLng` objects (emitted on pan) from contaminating the parent's reactive state, which caused `Invalid LatLng object: (undefined, undefined)` crashes on the next render cycle.
- CSS imports: `"leaflet.markercluster/dist/MarkerCluster.css"` and `"leaflet.markercluster/dist/MarkerCluster.Default.css"`.
- `shims-vue.d.ts` extended with `declare module '*.css'` and `declare module 'leaflet.markercluster'`.
- `clusterGroup` typed as `any` — `L.MarkerClusterGroup` is not in `@types/leaflet`.

### ESLint
- `defineModel` added to `.eslintrc.js` globals (`"readonly"`) — Vue 3.4 macro not recognized by `eslint-plugin-vue` without it.
- `v-model` directives do not accept TypeScript `as` casts (invalid LHS) — use a properly typed ref instead.
- `catch {}` empty blocks: add a comment or ESLint will reject with `no-empty`.

## Open questions
- Left panel shows raw backend `count` (all POIs in range); map shows filtered/deduplicated markers — the numbers don't match. Decision pending on whether to show filtered count, dual count, or remove it.
- Hover tooltips on cluster markers (`.bindTooltip`) require `name` in `MarkerData` type — not implemented yet.

## Next steps
- Refactor the POI section (noted by user as needing cleanup).
- Resolve count mismatch display.
- Connect `PropertyDetailView` to real API (currently uses mock property data).
