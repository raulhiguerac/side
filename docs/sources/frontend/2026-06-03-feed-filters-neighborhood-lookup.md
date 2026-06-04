---
title: Feed filters panel, neighborhood lookup, and composable refactor
captured-from: conversation
captured-on: 2026-06-03
participants: [raul, claude]
---

## Context
Session focused on wiring the feed view with a neighborhood name lookup, building a sidebar filter panel, and refactoring shared multiselect logic into composables.

## Key conclusions

### Neighborhood lookup (`useNeighborhoodLookup.ts`)
- `buildNeighborhoodMap(localityIds: string[]): Promise<Record<string, string>>` — calls `getNeighborhoodsByLocalities`, flattens with `Object.values(result).flat()`, reduces to `id → name` map.
- Called inside `useFeed.load()` after fetching properties: extract unique `city_id`s from results → build lookup → store in `neighborhoodLookup` ref.
- `toCard` in `FeedView` resolves: `neighborhoodLookup.value[p.location?.neighborhood_id ?? ''] ?? ''`.

### Axios array serialization bug
- FastAPI `Query(default=[])` does NOT parse `city_ids[]=uuid` (bracket notation). It treats `city_ids[]` as an unknown param and falls back to the default empty list.
- With all three preferences empty, `parse_feed_preferences` returns `None` → `_build_phases(None)` → phase 3 (no filters) → all 20 results including houses.
- Fix: `paramsSerializer: { indexes: null }` in axios call → serializes as `city_ids=v1&city_ids=v2` (no brackets), which FastAPI parses correctly.

### Feed preferences timing bug
- `preferences` was computed once at composable init (before store had user data). Fix: move the store read inside `load()` so it's fresh on every call.

### FeedFilters sidebar (`FeedFilters.vue`)
- Layout: `flex` with `aside w-1/4 sticky` + feed `w-3/4`. On `< lg` breakpoint the sidebar hides and feed takes full width.
- Grid drops from 4 to 3 columns max to accommodate sidebar.
- Sections: **Preferencias** (ciudad, barrio, tipo) + **Filtros** (precio min/max, área min/max, habitaciones, baños) + button "Aplicar filtros".
- Neighborhood multiselect populates after city selection via `watch(selected, ...)` → `loadNeighborhoods(localities)`.

### Composable structure
- `useCities.ts` — singleton module: `export const cities`, `export async function load()`. Shared across components.
- `useMultiselect.ts` — two factory functions:
  - `useCityMultiselect()` → `{ selected: string[], removeCity }` — per-instance state.
  - `useNeighborhoodMultiselect()` → `{ cities, selectedByCity, allSelected, allNeighborhoodOptions, removeNeighborhood, load(localities) }` — per-instance state.
- `NeighborhoodSelector` migrated to use `useNeighborhoodMultiselect` — removed ~30 lines of inline logic.

### Chip layout fix
- City chips were siblings of the multiselect div (not children), so they received `gap-4` from the parent flex container instead of being tightly grouped. Fixed by nesting chips div inside the city section div.

## Open questions
- Emits from `FeedFilters` to `FeedView` not yet wired — "Aplicar filtros" button has no handler.
- Pre-populating filters with user preferences from store (props down to `FeedFilters`) not yet implemented.

## Next steps
- Wire `FeedFilters` emits → `FeedView` calls `load()` with new preferences + filters.
- Pass user interests as props to `FeedFilters` to pre-populate on mount.
- Natural language search feature (LLM + tool use → `FeedPreferences`/`FeedFilters` struct) added to roadmap Fase 4.
