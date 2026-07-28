---
title: Bulk import modal rewired, admin table shape, and dependency cleanup
captured-from: conversation
captured-on: 2026-07-28
participants: [raul, claude]
---

## Context
The bulk import endpoint moved to a presigned-upload contract, which left the admin modal sending multipart to an endpoint that now expects JSON — broken on merge. Rewiring it opened the wider question of how the admin panel should be built, and an audit of what the frontend actually depends on.

## Key conclusions

### The modal
- Rewired to the three-step flow: ask for a presigned PUT → upload the CSV straight to storage → hand the key back to the API, which returns `202` and queues the job. The modal then closes; **no polling, no result panel**. Reviewing the outcome belongs elsewhere.
- The presigned URL is requested **on submit, not on file pick**. Asking early would let it go stale (`expires_in`, 5 min today) while the admin is still choosing a file, and the failure would surface as an opaque 403 from MinIO.
- The `PUT` uses plain `fetch`, not `propertiesApi`: it goes straight to MinIO, the signature travels in the query string, and the API client's cookies do not belong on it. This is the step most likely to be got wrong when reimplementing.
- File size is checked client-side against `max_size_bytes` from the response. A plain presigned PUT cannot enforce a limit, so **this is the only check that exists** — the server would accept an oversized file. A hard limit would require presigned POST with `content-length-range`.
- The modal emits `queued` with the `batch_id`. Nothing listens yet and there is no toast system in the project, so today the modal just closes silently and the admin gets no confirmation.

### The blocking gap
- There is **no endpoint that lists bulk jobs** — only `GET /properties/bulk/{job_id}/status`, which needs an id you must already have. Since the modal discards the `batch_id` on close, an import currently becomes unreviewable. The "review elsewhere" design needs `GET /admin/properties/bulk` first; `bulk_jobs` already holds everything such a view would show, and it would also give the retry flow an entry point.

### Admin panel shape
- **Table, not the feed's card grid.** The grid optimises for "which one do I like" — image, price, rooms. Moderation is "which ones need action": more rows visible, columns aligned for scanning, per-row actions.
- **Filters in the same view as the table.** The loop is filter → look → act → filter again; splitting them forces navigation round-trips.
- The admin panel is currently a scaffold: `AdminPropertiesView` says "En construcción", and **10 of the 12 admin endpoints have no frontend consumer**. The two wired are the bulk ones. `GET /admin/properties` is the natural first, since moderation, verification, pricing and promotions all need a `property_id` picked from a list.
- There is no admin API module; the modal's URLs are inline strings. With 10 endpoints coming, a `src/api/adminApi.ts` or composable is worth introducing before they spread.

### Nuxt UI, Vite and Tailwind
- **Nuxt UI does not fit this stack.** `@nuxt/ui` v3 runs in plain Vue but installs as a **Vite** plugin, and requires **Tailwind v4**. This project is Vue CLI (webpack) on Tailwind v3, so adopting it means migrating the build *and* a Tailwind major — infrastructure work, not "adding a component library".
- **Migrating to Vite is cheap here**, measured rather than guessed: 116 files, only **5** `process.env` usages (all in `config/index.ts`), **one** webpack-specific API (`require("leaflet.markercluster")` in `MapUser.vue`), no `require.context`, and a 4-entry proxy that translates directly. Worth doing on its own merits — Vue CLI is in maintenance mode, as a comment in `vue.config.js` already notes.
- **Tailwind v4 is riskier and gated on something outside our control**: `tailwind.config.js` loads `@vueform/vueform/tailwind`, and Vueform 1.13 targets v3. Also two stylesheets carry `@tailwind` directives (`main.css` and `assets/tailwind.css`), the second holding ~40 lines of `@layer` theming for the Google Maps autocomplete web component, whose semantics changed in v4.
- Recommendation taken: build the admin table by hand with the existing `brand-*` tokens. `@tanstack/vue-table` (headless, bundler-agnostic) is the option if it later needs multi-sort, selection or virtualisation.

### Dependency audit
- Removed with zero imports: `vuelidate` (the **Vue 2** build, which cannot run on this app at all), `@vuelidate/core`, `@vuelidate/validators`, `@types/vuelidate`, `vue-class-component`, `vue-google-autocomplete` (location input already uses the `gmp-place-autocomplete` web component).
- **`@vueform/vueform` is registered in `main.ts` but no template uses its components.** What is actually used is `@vueform/multiselect`, in `FeedFilters`, `LocalitySelector` and `NeighborhoodSelector` — and it is **not declared in `package.json`**, arriving as a transitive dependency. Dropping Vueform would break those three with no warning.
- **`npm run build` was already failing before any of this**, on 9 pre-existing lint errors in files untouched by this work (7 auto-fixable formatting, plus a real `vue/no-side-effects-in-computed-properties` in `StepImagenes.vue` and an empty block). `vue-cli-service build` runs ESLint and aborts. Same shape as the backend test suite having been red since the model reorg.

## Open questions
- Whether to declare `@vueform/multiselect` directly and drop `@vueform/vueform` (which also pulls `country-phones`, `slider` and `toggle`, none used).
- What the admin sees after queueing an import, given there is no toast system and nothing handles `queued`.
- How the jobs view should present errors — the last run produced 1.256, too many for a list; grouping by cause plus a CSV download was sketched but not decided.
- `firebase` is a heavy dependency with a single import and `initializeApp` commented out in `main.ts`.

## Next steps
- Add `GET /admin/properties/bulk` so imports stop being unreviewable.
- Build the admin properties table by hand against the new `AdminPropertiesPage` contract.
