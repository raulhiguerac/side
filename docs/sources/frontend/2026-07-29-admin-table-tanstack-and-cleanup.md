---
title: Admin properties table on TanStack, formatter consolidation, and a dead typecheck
captured-from: conversation
captured-on: 2026-07-29
participants: [raul, claude]
---

## Context
Building the first admin moderation table meant settling the component-library question for real, and the cleanup around it surfaced that the project's typecheck had not been running at all.

## Key conclusions

### TanStack Table adopted — partially reversing ADR-0007
- ADR-0007 chose a hand-built table with `@tanstack/vue-table` as a later escape hatch. It was adopted **now** instead, on the argument "if I can use it, why build something I later migrate?".
- The counter-analysis was recorded and stands on the facts: TanStack is **headless**, so it does not replace the table markup — you still write `<table>`/`<td>` and still need a component. Its sorting is client-side, and `GET /admin/properties` has **no sort parameter**, so sorting would silently reorder only the 20 loaded rows. Pagination and filtering are server-side already. Adopting it later would have been cheap for the same reason it's headless.
- Verified compatible with the current stack: 8.21.3, peer `vue >=3.2` (project on 3.5.35), bundler-agnostic — unlike Nuxt UI, no Vite requirement.
- Only `getCoreRowModel` is registered, deliberately: adding `getSortedRowModel`/`getPaginationRowModel` would operate on the loaded page and produce results that look global without being so.

### The table components
- `BaseTable.vue` is dumb and generic (`<script setup generic="T">`): props `columns`/`data`/`loading`, plus `EmptyState` and `BaseSpinner` for the edge states.
- Each cell renders `<slot :name="cell.column.id">` with `<FlexRender>` as fallback — plain-text columns cost nothing, and badges stay as templates in the parent instead of `h()` render functions inside the column def.
- A `cell:` prefix on slot names was tried and **removed**: a `:` in the name forces Vue's dynamic-argument syntax (``#[`cell:status`]``) at every use site, and `BaseTable` has no other slots to collide with. Slots are now named exactly like their column.
- `AdminPropertiesTable.vue` shows 5 of the schema's 13 fields. `id`/`owner_id` are UUIDs that say nothing without a join that doesn't exist; area/bedrooms/bathrooms are detail, not moderation. The row id is still reachable in the `actions` slot via `row.original`, so actions never needed a visible id column.
- The actions column only renders when the parent passes the slot, so there is no empty column by default.

### The typecheck was never running
- `vue-tsc` **aborts** on a pre-existing `tsconfig.json` error (TS5101, deprecated `baseUrl`), so every "typecheck passes" reading in this project was a run that never started. Running it with `--ignoreDeprecations 6.0` reveals **2 real pre-existing type errors**: `HouseCard.vue:81` imports a default export `types/properties.ts` does not have, and `ResetPasswordView.vue:51` uses a `loginUser` that does not exist there.
- `vue-cli-service build` does not run `vue-tsc`, only ESLint — which is why those two never broke the build.

### Build is green again
- `npm run build` succeeds for the first time in this branch. It had been failing on 9 pre-existing lint errors, fixed in two parts: `lint --fix` for the formatting ones, plus two real bugs.
- `StepImagenes.vue` had a `computed` that read and wrote the same ref, so it self-invalidated and could revoke object URLs the thumbnails were still using. Replaced with a `watch`, collapsing two refs into one.
- `CreatePropertyView.vue`'s empty `catch` **was not** the bug it looked like. The `finally` advancing to step 3 unconditionally is deliberate: step 3 is a dual-purpose screen that renders the error state *or* the uploader, and the publish button is gated on `!error`, so the "broken state" was unreachable. Only the empty block was fixed.
- `no-undef` was turned off project-wide: `eslint-plugin-vue` is on v8 (2022) and does not understand `<script setup generic>` or `defineSlots`. The rule is redundant with `vue-tsc` and cannot see TS's type space, so every future generic component would false-positive.

### Formatters consolidated
- Money had **four** competing implementations: `utils/money.ts` (no symbol), two identical `Intl.NumberFormat` blocks in `usePropertyDetail`, `"$ " + Math.round(...)` in `AvmResult`, and a bare `toLocaleString` in `PropertyCard`. All now go through `formatCurrency(value, currency)` in `utils/money.ts`, which accepts strings because backend `Decimal`s serialize that way.
- One visible change: `PropertyCard` had `$` hardcoded in the template, so prices go from `$450.000.000` to `$ 450.000.000` — the `es-CO` locale output, which `AvmResult` already used.
- `formatMoney`/`parseMoney` were left alone on purpose: they are the input pair used by `StepDetalles` and `PropertyEditForm` on `@blur`, and adding a symbol would break `parseMoney` on the way back.
- Dates had **nothing** to reuse — no date formatting existed anywhere in `src/`. New `utils/date.ts` with `formatShortDate`, its `Intl.DateTimeFormat` built once at module level rather than per cell.
- Two near-duplications were caught before shipping: `LISTING_STATUS_LABELS`/`BADGE_CLASSES` already existed in `constants/propertyStatus.ts`, and the `verification_status` union already lived inline in `types/properties.ts` — extracted as a named `VerificationStatus` and given matching label/badge constants.

### Firebase removed
- Executed [[adr-firebase-removal]] 14 months after deciding it. Three things the ADR assumed turned out false, all pointing the same way: `initializeApp` was never called **and no `firebaseConfig` exists in the repo** (so `getAuth()` threw on any click), the endpoint `POST /v1/auth/login/google` **never existed** in users-service, and `RegisterView` had its own handler-less Google button the ADR didn't mention.
- Deliberate deviation from the removal plan: the buttons and dividers were **commented, not deleted**, in both views — the markup is what will be reused when Keycloak Identity Brokering lands. The handler could not survive the dependency going away.

### The admin view is wired
- `AdminPropertiesView` no longer says "En construcción": table, `PaginationArrows`, "Mostrando X-Y de Z" and an error banner, fed by `useAdminProperties`.
- The composable reuses `usePagination` with `fetchMore`, following the `PublicProfileView` precedent for offset-paginated endpoints. Going back never hits the network.
- The server `total` is kept **separately**, because `usePagination.total` is `allItems.length` — rows loaded so far, not rows that exist.

### Endpoint audit
- properties-service: 12 admin endpoints, **3 wired** (two bulk + the new listing), 9 pending — verification, status, detail, estimated-price, 4 promotions endpoints, and bulk job status.
- catalog-service: **11 admin endpoints, none wired**; `AdminCatalogView` is empty.
- `GET /admin/properties/bulk` still does not exist, which leaves `.../{job_id}/status` useless in practice since the modal discards the `batch_id`.

## Open questions
- Whether to migrate `PropertyCard` back to a symbol-less price format, now that the space is visible.
- Whether `PropertyCardUI` should carry `currency` — the mapper drops it, so feed cards assume COP while the backend supports five currencies.
- Whether to wrap TanStack's `getHeaderGroups()`/`getVisibleCells()` in `computed`s to flatten the template, purely cosmetic.
- Whether the row click should open the existing public `/listing/:id` or a new admin detail view on the unwired `GET /admin/properties/{id}`.

## Next steps
- Add `reload()` to `useAdminProperties` — the moderation endpoints return 204, and today only `load()` (which resets to page 1), `next()` and `prev()` exist.
- Fix `tsconfig.json` so `vue-tsc` runs, then the two type errors it was hiding.
- Wire the row actions; see the properties-service source of the same date for why they are not straightforward.
