---
title: Admin panel front implementation — nav gating, router guard, hub view
captured-from: conversation
captured-on: 2026-07-16
participants: [raul, claude]
---

## Context
With `is_admin` wired into `authStore` (see the paired `users-service` capture on JWT roles), this session built the actual admin panel front scaffolding: nav visibility, route protection, and an orchestrator/hub view linking to the properties and catalog admin sections.

## Key conclusions
- Admin link lives in `NavUser.vue` (never `NavGuest`) as a top-level link next to `Dashboard`/`Mis propiedades`, gated by `v-if="authStore.isAdmin"` — chosen over hiding it in the account dropdown because moderation is expected to be an active, frequent workflow, not an occasional settings tweak.
- Router: new `router/routes/admin/` folder (`home.ts`, `properties.ts`, `catalog.ts` + an `index.ts` barrel), mirroring the existing per-domain file convention (`properties.ts`, `settings.ts`). Routes: `/admin` (hub), `/admin/properties`, `/admin/catalog`, each with `meta: { requiresAuth: true, requiresAdmin: true }`.
- Router guard (`beforeEach`) extended with a `requiresAdmin` check. Found and fixed a real race: `authStore.isAdmin` is only populated by `fillUserData()`, which normally only runs via `App.vue`'s reactive watch **after** the guard already resolved the navigation — so a direct deep-link to an admin route would have bounced a real admin to home, since `isAdmin` would still read its default `false` at guard-check time. Fixed by having the guard itself call `fillUserData()` (gated on `authStore.accountId` being unset, mirroring the existing `_authChecked` gate used for `checkAuth`) before checking `isAdmin`.
- No admin views existed at all, so minimal placeholder views were created (`views/admin/properties/AdminPropertiesView.vue`, `views/admin/catalog/AdminCatalogView.vue`, reusing `PageContainer`) purely so the routes resolve and the build doesn't break.
- Built an orchestrator/hub view (`views/admin/AdminHomeView.vue`) at `/admin`: hero + a 4-metric KPI card row (Usuarios/Propiedades/Localidades/Barrios, currently placeholder `—` values) + a "Gestión" section with two cards (Propiedades, Catálogo) linking to their respective admin views.
- Reviewed generic dashboard UX feedback (from an external LLM) and deliberately rejected the parts that don't map to real backend capabilities in this domain — e.g. "crear usuario" or "nueva propiedad" aren't admin actions here (property creation is an owner flow; there's no admin-create-user endpoint). Kept only "Importar CSV" as a quick action since it maps to a real existing endpoint (`POST /admin/properties/bulk`), implemented as a modal over the properties-admin parent view (`BulkUploadPropertiesModal.vue`), not a new route. Catalog's equivalent bulk-neighborhoods endpoint needs a `locality_id` first, so no bulk button was added there yet — flagged as unresolved UX (needs a locality picker).
- Icons switched from emoji to `@lucide/vue` components (`Home`, `Globe`, `Upload`) after emoji rendering broke — matches the icon convention already used elsewhere in the front (e.g. `PropertyHeaderCard.vue`).
- Discussed and explicitly deferred: fine-grained admin roles (super-admin / catalog-admin / properties-admin split). Rejected as premature — no evidence yet that scoped admins are needed, and Keycloak's role-list design makes this cheap to add later. Important note for when it does happen: it wouldn't be a `users-service`-only change, since `catalog-service` and `properties-service` each enforce their own `require_admin` independently against their own JWT `roles` claim.
- Discussed and explicitly deferred: real KPI numbers and charts. Simple trend indicators don't need D3 (already used in this codebase for the map); D3 would only be justified for genuine multi-series/interactive analytics, and only once real backend data exists.

## Open questions
- Where the 4 KPI counts will actually be served from (cached count endpoints per owning service vs. a future `analytics-service` reporting domain) — not decided.
- Catalog's bulk-import UX (needs a locality-selection step first) — not designed yet.

## Next steps
- Plan and build cached count endpoints (`users-service`/`properties-service`/`catalog-service`) to replace the placeholder KPI values.
- Design the catalog bulk-import flow (locality picker + modal).
- See the paired `properties-service` capture from this same session for a reliability finding on `POST /admin/properties/bulk` that surfaced while building the CSV-import modal.
