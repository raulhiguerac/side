---
title: Property creation multi-step form + NearbyPlaces fixes
captured-from: conversation
captured-on: 2026-06-25
participants: [raul, claude]
---

## Context
Built a multi-step property creation form accessible at `/dev/create-property` (no auth required for dev). Also fixed Leaflet gray map and added a loading spinner to `NearbyPlaces`.

## Key conclusions

### Public profile pagination (frontend)
- `useProfileListings` composable: accumulator array `all_listings[]` + `listings` ref (current page slice). Page ref starts at 0, incremented after each fetch.
- `previousListings(page)`: guard `page < 2`, slices `all_listings[(page-2)*20 : (page-1)*20]`.
- `activeListingsCount`: shows `"+20"` if `hasMore`, else `listings.length` — avoids lying on non-first pages.
- `usePropertyMapper` bridges backend `PropertyCard` → UI `PropertyCardUI`; PublicProfileView uses it the same way as FeedView.

### Router navigation on cards
- Added `@click="router.push('/listing/${card.id}')"` to `FeedView`, `MapView`, `MyPropertiesView`, `PublicProfileView`.

### Multi-step form (`/dev/create-property`)
- 4 steps: Tipo, Detalles, Ubicación, Imágenes (step 4 not yet built).
- Thin orchestrator `CreatePropertyDevView.vue` passes `form` ref down via `:form` + `@update:form="form = $event"` pattern.
- `CreateSummary` sidebar hidden on step 2 (Ubicación takes full width).
- Components: `StepIndicator`, `StepTipo`, `StepDetalles`, `StepUbicacion`, `CreateSummary`.

### StepUbicacion layout
- Row: Google `PlaceAutocompleteElement` (3/4 width) + "Barrio detectado" card (1/4 width).
- Below: `NearbyPlaces` full width after address selected; placeholder with copy explaining value prop before.
- `getNeighborhood(lat, lon)` from `useLocation.ts` resolves neighborhood name for the card.
- `previewId = crypto.randomUUID()` passed as `property-id` to NearbyPlaces (backend requires valid UUID).

### NearbyPlaces spinner + Leaflet gray map fix
- Spinner: `v-show="loading"` / `v-show="!loading"` — must use `v-show` not `v-if` so Leaflet's container exists in DOM during init.
- Gray map fix: `watch(loading, async (val) => { if (!val) { await nextTick(); window.dispatchEvent(new Event("resize")); } })` — Leaflet listens to window resize and calls `invalidateSize` itself.

## Open questions
- Why does the map initialize gray: Leaflet reads container size at mount time; `v-show` hides it with `display:none` so size is 0×0. The `resize` event forces recalculation after the container becomes visible.

## Next steps
- StepImagenes (step 3): presigned URL upload flow — not started.
- Form submission: POST to `/v1/properties` with full `CreatePropertyForm`.
- Wire `neighborhood_id` / `city_id` / `country_id` into form after geo-resolution resolves in StepUbicacion.
