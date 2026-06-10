---
title: frontend
status: draft
last-verified: 2026-06-08
owners: [frontend]
related:
  - "[[architecture]]"
  - "[[frontend-architecture]]"
  - "[[frontend-onboarding-flow]]"
  - "[[frontend-local-dev]]"
sources: [../../sources/frontend/2026-05-21-foundational-qa.md, ../../sources/frontend/2026-05-27-gmaps-places-avm-form.md, ../../sources/frontend/2026-06-03-feed-filters-neighborhood-lookup.md, ../../sources/frontend/2026-06-08-feed-pagination-map-view.md]
---

## TL;DR

SPA en Vue 3 + TypeScript que consume los microservicios del backend (users-service, catalog-service, properties-service, analytics-service). Stack hoy: **Vue CLI 5 (webpack)**, Pinia, vue-router en **hash mode**, Tailwind, Axios. Deployment planificado en **bucket estático público**. Estado actual: las **2 features funcionales end-to-end son Login y Register**; el resto es scaffolding visual o features que requieren UCs backend pendientes. Varias decisiones puestas como deuda técnica reconocida (ver Roadmap).

## Por qué existe

Capa de presentación del producto inmobiliario. Tres jobs claros:
1. **Autenticar al usuario** (signup, login, password reset, sesión persistente vía cookie).
2. **Consumir el catálogo geográfico** para autocomplete (countries/localities/neighborhoods).
3. **Onboarding** del usuario tras autenticación: capturar intent + ubicación de interés + tipo de propiedad → personalizar el feed.

Lo que NO hace (todavía): publicar listings, navegar el feed, comunicar con propietarios. Esos viewports están en scaffolding o no existen.

## Estado funcional al 2026-05-21

| Surface | Estado | Backend asociado |
|---|---|---|
| `/login` | ✅ funcional end-to-end | users-service `POST /v1/auth/login` |
| `/register` | ✅ funcional end-to-end | users-service `POST /v1/auth/register` |
| `/forgot-password` | ⚠ scaffolded | desconocido |
| `/settings/{profile,security,account}` | ✅ con UCs en users-service | users-service (wiki pendiente) |
| `/about`, `/` (home) | ⚠ scaffolded — sin data dinámica | n/a |
| `/feed/list` (feed lista) | ✅ feed funcional — sidebar filtros + neighborhood lookup + paginación por cursor | properties-service `GET /v1/search/feed` |
| `/feed/map` (feed mapa) | ⚠ stub placeholder — pendiente implementación con Leaflet | properties-service `GET /v1/search/feed/map` |
| `/dev` (DevPlayground) | sandbox interno | n/a — no es producto |
| Onboarding modal (4 pasos) | ⚠ front completo, backend pausado | users-service `/v1/onboarding/{city,neighborhood}` — pausado |

## Stack

- **Vue 3.2** + **TypeScript 5**
- **Vue CLI 5** + webpack (deuda técnica — migra a Vite post-backend, ver [[adr-vue-cli-deferred-vite-migration]])
- **vue-router 4** en `createWebHashHistory` (`/#/`) — ver [[adr-hash-history-static-hosting]]
- **Pinia 3** — stores: `auth` (autenticación), `user` (onboarding + intereses)
- **Tailwind 3** + **Vueform** (forms complejos) + **Vuelidate** (validación)
- **Axios** (sin instance central hoy — ver [[frontend-architecture]])
- **Mapa**: `leaflet` + `@vue-leaflet/vue-leaflet` + **D3.js** para overlays — ver [[adr-mapbox-geocoding-leaflet-rendering]]
- **Forward geocoding**: Google Maps Places API (New) — `PlaceAutocompleteElement` web component, key en `.env.local`. Ver [[adr-gmaps-places-geocoding]].

### A remover (tracked)
- **Firebase 10** + Google sign-in: spike-out, no funcionó. Ver [[adr-firebase-removal]].
- `vue-class-component`: alpha de Vue 2 era — sospecha de zombie, no se importa en el código revisado.

## Routes (10)

| Path | Auth | Componente |
|---|---|---|
| `/` | público | `HomeView` |
| `/about` | público | `AboutView` |
| `/login` | guest-only (redirige si logged) | `LoginView` |
| `/register` | guest-only | `RegisterView` |
| `/forgot-password` | sin auth meta | `ResetPasswordView` |
| `/settings` → `/settings/profile` | auth required | `SettingsLayout` + 3 children |
| `/dev` | público | `DevPlaygroundView` |
| `/properties` | auth required | `MyPropertiesView` |
| `/feed` → `/feed/list` | público | `PropertiesView` (parent con toggle) + `FeedView` |
| `/feed/map` | público | `PropertiesView` (parent) + `MapView` (stub) |

Guard global en `router.beforeEach`: si la ruta `requiresAuth` y `_authChecked === false`, llama `authStore.checkAuth()`. Si tras eso `!isAuthenticated`, redirige a `/login`.

## Consumers de servicios backend

- **users-service** (`API.USERS_BASE_URL` default `localhost:8000`): auth, profile, settings, onboarding endpoints.
- **catalog-service** (`API.CATALOG_BASE_URL` default `localhost:8001`): countries, localities by-country, neighborhoods by-locality.
- **properties-service** (`API.PROPERTIES_BASE_URL` default `localhost:8003`): `GET /v1/search/feed` (cursor pagination, `FeedPage { items, next_cursor }`) y `GET /v1/search/feed/map` — consumidos desde `composables/feed/useFeed.ts`.
- **analytics-service**: form AVM en `DevPlaygroundView` — `PlaceAutocompleteElement` + `POST /v1/predict` cableado end-to-end.

## Patrones — resumen alto nivel

### Auth — cookie based
Backend (users-service) setea cookie `access_token` en login/register. Todas las requests llevan `withCredentials: true`. Mismo patrón que [[catalog-service-architecture]] (cookie vs Bearer header). Auth state vive en `useAuthStore` (Pinia).

### Caching local
- `localStorage` para countries (semi-permanente, list raramente cambia).
- `sessionStorage` para cities y neighborhoods por id (refresh cada sesión).
- Las llamadas vía composables (`composables/Location.ts`) van **directo a catalog-service** — no hay BFF intermedio.

### State management — split por dominio
- `useAuthStore`: usuario autenticado, `isAuthenticated`, `_authChecked` (guard contra checkAuth duplicado).
- `useUserStore`: onboarding step, intereses (localities/neighborhoods/properties), `userDismissedModal`.

Detalle de cada patrón en [[frontend-architecture]].

## Roadmap inmediato (deuda técnica tracked)

- [ ] **Remover Firebase** — imports en `LoginView.vue`, dep `firebase` del `package.json`, eventual cleanup del endpoint backend (`/v1/auth/login/google` si solo lo usaba esta integración).
- [ ] **Centralizar axios** — instance única con `baseURL` y `withCredentials`, interceptor 401 → logout. Eliminar URLs hardcoded en `auth.ts`.
- [ ] **Vite migration** — post-cierre de todos los microservicios backend.
- [ ] **Cerrar CORS** en backends pre-producción — hoy `allow_origins=["*"]` en catalog.
- [ ] **Implementar `/v1/properties/mine`** en properties-service para activar `/properties` end-to-end.
- [ ] **Error handling robusto** en `LoginView` / `RegisterView` (hoy mensaje genérico).

## Boundaries — lo que el frontend **NO** hace

- **No autentica directamente** — Keycloak vía users-service, frontend solo recibe cookie.
- **No persiste datos críticos en el cliente** — solo cachea catálogos read-only (countries/cities/neighborhoods). Estado de usuario y onboarding vive en backend.
- **No resuelve barrio_ideca por sí solo** — usa Google Maps Places API para `address → lat/lon`, después pasa el `(lat, lon)` a catalog-service para el reverse por coordenadas. Ver [[adr-gmaps-places-geocoding]].
- **No hostea POIs ni geometrías** — los consume vía catalog-service.

## Related

- [[architecture]] — monorepo, patrones cross-cutting
- [[frontend-architecture]] — layout interno, stores, composables, routing, axios
- [[frontend-onboarding-flow]] — modal-based wizard, 4 pasos
- [[frontend-local-dev]] — runbook
- [[adr-vue-cli-deferred-vite-migration]], [[adr-hash-history-static-hosting]], [[adr-mapbox-geocoding-leaflet-rendering]], [[adr-gmaps-places-geocoding]], [[adr-firebase-removal]]
- [[adr-mapbox-frontend-only]] (cross-service, vive en catalog-service)

## Claims

- 12 rutas definidas en `src/router/index.ts` — incluyendo `/feed` (parent `PropertiesView`) con dos hijas: `feed-list` (`FeedView`) y `feed-map` (`MapView`) ([router/index.ts](frontend/src/router/index.ts)).
- `vue-router` corre en `createWebHashHistory` (URL pattern `/#/...`) ([router/index.ts:89](frontend/src/router/index.ts#L89)).
- `auth.ts` store hardcodea `http://localhost:8000/v1/...` en login/register/logout/checkAuth ([stores/auth.ts:80-83](frontend/src/stores/auth.ts#L80-L83), [stores/auth.ts:98-101](frontend/src/stores/auth.ts#L98-L101)).
- `config/index.ts` define `API.USERS_BASE_URL` y `API.CATALOG_BASE_URL` pero solo `user.ts` y los composables lo usan; `auth.ts` ignora la config ([config/index.ts:1-5](frontend/src/config/index.ts#L1-L5)).
- Firebase 10 está en `package.json` y se usa solo en `LoginView.loginWithGoogle()` ([package.json:17](frontend/package.json#L17), [LoginView.vue:253-326](frontend/src/views/auth/LoginView.vue#L253-L326)).
- `leaflet` + `@vue-leaflet/vue-leaflet` están en **devDependencies** del package.json (probablemente debería ser dependencies si se usa en runtime) ([package.json:32-33](frontend/package.json#L32-L33), [package.json:43](frontend/package.json#L43)).
- `vue.config.js` reconoce que Vue CLI está en maintenance ("Vue CLI is in maintenance mode") ([vue.config.js:13](frontend/vue.config.js#L13)).
- Onboarding tiene 4 pasos definidos en `useOnboarding.ts` (`STEP_MAP`): intent, city, neighborhood, property_type ([composables/useOnboarding.ts:11-16](frontend/src/composables/useOnboarding.ts#L11-L16)).
- CORS del backend hoy está `allow_origins=["*"]` (catalog-service), temporal pre-producción ([backend/catalog-service/src/app/main.py:18-23](backend/catalog-service/src/app/main.py#L18-L23)).
- El feed de propiedades en `/properties` consume `GET /v1/search/feed` (properties-service puerto 8003) con `paramsSerializer: { indexes: null }` para evitar bracket notation que FastAPI no parsea ([composables/feed/useFeed.ts](frontend/src/composables/feed/useFeed.ts)).
