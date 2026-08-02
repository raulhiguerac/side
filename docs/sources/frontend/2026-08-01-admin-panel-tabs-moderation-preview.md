---
title: Admin properties split into tabbed nested routes, with a preview panel as the moderation surface
captured-from: conversation
captured-on: 2026-08-01
participants: [raul, claude]
---

## Context
`/admin/properties` was a single view holding the table, the CSV import button and everything else, heading toward one long scroll. Splitting it surfaced a second problem: the moderation rows were indistinguishable from each other.

## Key conclusions

### Tabs are nested routes, not a component switch
Chosen over `v-if`/`v-show` on one view because filters (`status`, `verification_status`, `owner_id`, page) belong in query params: state survives tab switches and reloads, is shareable, and the browser back button works. Otherwise a store would have to be invented to hold it. Also gives per-tab lazy chunks and one fetch per tab instead of three on open.

Structure: `AdminPropertiesLayout` (header + tab bar + `<RouterView />`) as parent at `/admin/properties`, children `""` (moderation, named `admin-properties`), `promotions`, `imports`. `AdminPropertiesView.vue` was split into three views and deleted.

- **The parent carries no `name`**: naming a parent that has a default child makes `push({ name })` ambiguous. The name lives on the `""` child.
- **`meta` only on the parent**: the guard uses `to.matched.some(...)` and `matched` includes parent records, so children are protected without repeating it.

### `RouterLink` with `custom` + `v-slot`, not `active-class`
With the `active-class`/`exact-active-class` props both variants coexist in the attribute (`border-transparent` and `border-brand-primary`), and which one wins is decided by Tailwind's CSS emission order, not the attribute. Reading `isExactActive` from the slot and applying a ternary is deterministic. Rendering a real `<a>` also keeps middle-click and "open in new tab".

**Exact and not `isActive`**: `/admin/properties` is a prefix of the other two, so prefix-matching would keep "Moderación" lit while standing on another tab.

### The rows cannot identify themselves — hence the preview panel
`Property` has **no title and no address**; the only identity is a UUID, and `location` is a relation holding more UUIDs. On top of that, the columns first chosen are exactly the ones that come out constant in CSV-imported data (same date, same status, all unverified), so 20 rows rendered identical except for price.

Resolved with a right-side preview panel showing what a user sees, rather than an extra id column. Splitting `Casa · Venta` into separate **Tipo** and **Operación** columns also helps scanning and prepares for filtering by operation.

### The panel reuses the public detail pieces
`PropertyOverview` (12 props derived from `usePropertyDetail`) and `PhotoGalleryPopup`, untouched — so what the admin sees is literally the public rendering. `usePropertyDetail` and `buildNeighborhoodMap` were already reusable; the only thing not extracted is the ~12-line fetch block, which the panel cannot share anyway (different endpoint, `watch` instead of `onMounted`, race guard).

- **Cover photo only, not `PropertyPhotoGrid`**: that grid spreads 5 photos over 4 columns with fixed `grid-area`; at 40% width they are illegible thumbnails. Click opens the same popup.
- **Hits `/v1/admin/properties/{id}`, never the public detail**: `GetPropertyUseCase` 404s when `status != active` and you are not the owner — precisely the drafts and inactives that need moderating.
- **`NearbyPlaces` deliberately excluded**: it fetches in its own `onMounted`, requesting 9 isochrones (3 ranges × 3 profiles) against ORS per property. Moderation never uses walkability, and moderating means visiting *new* properties, so the `property_id` cache is a miss almost every time. If ever added it must be behind `v-if` — `v-show` mounts the component and pays the cost anyway.

### Fast clicking makes stale responses a real bug
A `requestToken` counter guards the panel: each selection increments the shared counter and keeps a local copy; any response whose token is no longer current is discarded. Three discard points, because two awaits are chained (detail, then neighborhood name), and the `finally` compares too so a late response cannot switch off the spinner of the current one.

### `BaseTable` gained optional selection
`rowKey` + `selectedKey` props and a `rowClick` emit; without `rowKey` the behaviour is unchanged. Selected rows use `bg-brand-primary-light`, and **hover and selected are mutually exclusive on purpose**: Tailwind emits `.hover\:bg-brand-bg:hover` with higher specificity than `.bg-brand-primary-light`, so holding both classes would repaint the selected row grey exactly while reaching for another one.

### Layout details that are not cosmetic
- 60/40 via `flex-[3]`/`flex-[2]`, not `w-3/5` + `w-2/5`: percentages plus the `gap-6` exceed 100% and force uneven shrinking. Flex proportions divide the space *after* the gap.
- First row auto-selected through a `watch` on `rows`, not just on load: paging swaps the whole page, and the previous selection would stay marked on a row that is no longer visible.
- Panel hidden below `xl` — moderation is desktop-only by decision, not by accident.

### Drift found
`types/admin.ts` declares `currency` with 5 values; the backend `Currency` enum has 7 (`CLP` and `ARS` missing). `types/properties.ts` already lists all 7, so the admin type is the stale one.

## Open questions
- No filter bar, although the backend accepts `status`/`verification_status`/`owner_id` and `useAdminProperties` already carries them. Without it there is no work queue.
- The imports tab shows a fixed empty state: only `GET /bulk/{job_id}/status` exists, there is no endpoint listing jobs, so history cannot be built.
- The bulk modal's `@queued` event is still unhandled, so the `batch_id` is dropped and the table does not refresh after an import.
- Whether `PropertyOverview`, designed full-width, holds up at 40%.
- A row thumbnail would let admins scan without opening each row, but needs `images` added to `AdminPropertyCardSchema`.

## Next steps
Filters → verification actions → the rest. Admin endpoints wired: 4 of 23 (`GET /admin/properties`, `GET /admin/properties/{id}`, and the two bulk-upload steps).
