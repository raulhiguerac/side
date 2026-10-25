---
title: Arquitectura interna del frontend
status: draft
last-verified: 2026-10-24
owners: [frontend]
related:
  - "[[architecture]]"
  - "[[adr-no-component-library]]"
  - "[[adr-tanstack-table]]"
  - "[[adr-admin-tabs-nested-routes]]"
  - "[[adr-vue-cli-deferred-vite-migration]]"
  - "[[frontend]]"
  - "[[frontend-onboarding-flow]]"
  - "[[frontend-admin-panel]]"
  - "[[frontend-map-component]]"
  - "[[adr-api-layer-by-domain]]"
  - "[[adr-feed-map-whole-bbox-cluster]]"
  - "[[frontend-poi-reachable]]"
  - "[[frontend-property-create-form]]"
  - "[[frontend-property-edit-form]]"
  - "[[properties-service-search]]"
  - "[[open-items]]"
sources:
  - ../../sources/frontend/2026-10-24-reset-password-flow-wired.md
  - ../../sources/frontend/2026-10-24-assets-cleanup-lucide-and-mvp-status.md
  - ../../sources/frontend/2026-05-21-foundational-qa.md
  - ../../sources/frontend/2026-05-28-avm-form-split-and-dumb-map.md
  - ../../sources/frontend/2026-05-29-vue35-gmaps-places-leaflet-markers.md
  - ../../sources/frontend/2026-05-29-avm-form-wiring-predict.md
  - ../../sources/frontend/2026-06-03-feed-filters-neighborhood-lookup.md
  - ../../sources/frontend/2026-06-04-feed-filters-contract.md
  - ../../sources/frontend/2026-06-08-feed-pagination-map-view.md
  - ../../sources/frontend/2026-06-09-mapview-leaflet-implementation.md
  - ../../sources/frontend/2026-06-11-property-detail-router-refactor.md
  - ../../sources/frontend/2026-06-15-poi-detail-view-mapuser-cluster.md
  - ../../sources/frontend/2026-06-20-property-detail-view-refactor.md
  - ../../sources/frontend/2026-06-21-public-profile-view-and-properties-refactor.md
  - ../../sources/frontend/2026-06-25-property-create-form-and-nearby-fixes.md
  - ../../sources/frontend/2026-06-28-devcontainer-proxy-chrome-fix.md
  - ../../sources/frontend/2026-07-13-view-decoupling-composables-and-cards.md
  - ../../sources/frontend/2026-07-13-decimal-serialized-as-string.md
  - ../../sources/frontend/2026-07-15-property-edit-photos-upload-delete.md
  - ../../sources/frontend/2026-07-16-auth-user-store-consolidation.md
  - ../../sources/frontend/2026-07-16-admin-panel-nav-and-hub.md
  - ../../sources/frontend/2026-07-28-admin-panel-groundwork.md
  - ../../sources/frontend/2026-07-29-admin-table-tanstack-and-cleanup.md
  - ../../sources/frontend/2026-08-01-admin-panel-tabs-moderation-preview.md
  - ../../sources/frontend/2026-09-28-catalog-tabs-and-production-readiness.md
  - ../../sources/frontend/2026-10-04-admin-neighborhoods-tab.md
  - ../../sources/frontend/2026-10-05-admin-actions-and-front-smell-audit.md
  - ../../sources/frontend/2026-10-09-api-layer-map-cluster-and-typecheck.md
  - ../../sources/frontend/2026-10-16-shared-buttons.md
  - ../../sources/frontend/2026-10-16-shared-inputs-and-color-tokens.md
  - ../../sources/frontend/2026-10-18-reset-and-reactivation-front-gaps.md
---

## TL;DR

SPA Vue 3 + TypeScript organizada en `views/` (páginas-ruta), `components/` (presentación reusable), `stores/` (Pinia, estado global), `composables/` (lógica con estado), `api/` (HTTP), `types/<dominio>/` (shapes) y `config/` (env). Desde el 2026-10-09 todo el HTTP pasa por funciones tipadas de `api/` sobre clientes axios con interceptor ([[adr-api-layer-by-domain]]). Caching local manual en `localStorage`/`sessionStorage`. Auth cookie-based con `withCredentials: true`. Router con guard global de auth.

## Layout

```
frontend/
├── public/                       # index.html, favicon
├── src/
│   ├── App.vue                   # root: NavBar + router-view + onboarding modal
│   ├── main.ts                   # createApp + use(pinia, router, VueCookies, Vueform)
│   ├── shims-vue.d.ts            # types para imports .vue
│   ├── assets/                   # logo.svg, reset-password.svg, secure-account.svg, landing_cover.png
│   ├── config/
│   │   └── index.ts              # API.USERS_BASE_URL, CATALOG_BASE_URL, AVM_BASE_URL (port 8003), LOCALE, STORAGE_KEYS
│   ├── theme/
│   │   └── brandColors.json      # paleta brand-*: la lee tailwind.config.js y, vía constants/brandColors, el JS (Leaflet, SVG)
│   ├── router/
│   │   ├── index.ts              # instancia router + beforeEach guard; importa 6 módulos
│   │   └── routes/
│   │       ├── public.ts         # /, /about, /users/:userId
│   │       ├── auth.ts           # /login, /register, /forgot-password, /reset-password
│   │       ├── settings.ts       # /settings + children
│   │       ├── properties.ts     # /properties, /listing/:id, /feed + children
│   │       ├── analytics.ts      # /avm
│   │       └── admin/            # /admin, /admin/properties, /admin/catalog — ver [[frontend-admin-panel]]
│   │           ├── home.ts
│   │           ├── properties.ts
│   │           ├── catalog.ts
│   │           └── index.ts      # barrel: adminRoutes
│   ├── stores/                   # Pinia
│   │   ├── auth.ts
│   │   └── user.ts
│   ├── composables/               # lógica con estado; un subdirectorio por dominio
│   │   ├── admin/                 # listados, moderación, promociones, filtros en URL, barrios — ver [[frontend-admin-panel]]
│   │   ├── avm/useAvmForm.ts
│   │   ├── catalog/               # useCities, useLocalitiesWithNames, useLocation, useNeighborhoodLookup (funciones con caché, no composables)
│   │   ├── feed/{useFeed, useFeedMap}.ts
│   │   ├── map/useMarkerCluster.ts      # cluster maker genérico — ver [[frontend-map-component]]
│   │   ├── onboarding/useOnboarding.ts  # guarda pasos; el modal lo controla el padre — ver [[frontend-onboarding-flow]]
│   │   ├── pois/useReachablePois.ts
│   │   ├── properties/            # useCreatePropertyForm, useImageUpload, useMyProperties, usePropertyDetail, usePropertyMapper, usePropertyVisibility
│   │   ├── shared/                # usePagination, useMultiselect, useInfiniteScroll (centinela + IntersectionObserver)
│   │   └── users/                 # useProfileSettings, useAccountSettings, useProfileListings, useForgotPassword, useResetPassword
│   ├── api/                       # todo el HTTP — ver [[adr-api-layer-by-domain]]
│   │   ├── clients/{users, catalog, properties, avm, interceptors}.ts   # instancias axios + interceptor de refresh
│   │   ├── {users, catalog, properties, avm}.ts                         # una función tipada por endpoint, devuelve `data`
│   │   └── admin/{properties, catalog}.ts                              # endpoints admin + loaders de opciones de filtros
│   ├── utils/
│   │   ├── money.ts               # formatMoney/parseMoney (inputs) + formatCurrency (display)
│   │   ├── password.ts            # MIN_PASSWORD_LENGTH, isNewPasswordValid
│   │   ├── number.ts              # formatNumber, formatArea (m² / km²)
│   │   ├── date.ts                # formatShortDate, formatShortDateTime, formatLongDateTime — Intl construido una vez a nivel módulo
│   │   ├── pagination.ts          # pageRange(page, pageSize, shown) → { from, to }
│   │   ├── property.ts            # propertyTitle(type, listing), cityIdsOf(cards)
│   │   ├── feedMap.ts             # sortForMap: promocionadas, luego distancia al centro del bbox
│   │   ├── markerIcon.ts          # markerIcon / clusterIcon (lucide renderizado y cacheado)
│   │   ├── renderToElement.ts     # renderiza un componente Vue a HTMLElement para APIs fuera de Vue (Leaflet)
│   │   ├── placeAutocomplete.ts   # monta el autocompletado de Google Places (AVM y alta de propiedades)
│   │   ├── adminFilters.ts        # sanitizeFilterQuery, toFilterOptions
│   │   └── logger.ts              # punto único de logs de error
│   ├── constants/
│   │   ├── {users, catalog, properties, avm}Endpoints.ts   # todas las rutas `/v1/...` del front viven acá
│   │   ├── propertyStatus.ts      # LISTING_STATUS_* y VERIFICATION_STATUS_* (labels + badges)
│   │   ├── propertyLabels.ts      # PROPERTY_TYPE_LABELS, LISTING_TYPE_LABELS
│   │   ├── propertiesFilters.ts   # MODERATION_FILTERS, BULK_JOB_FILTERS
│   │   ├── catalogFilters.ts      # NEIGHBORHOOD_FILTERS (loaders en api/admin/catalog)
│   │   ├── poiCategories.ts       # CATEGORY_PRIORITY, CATEGORY_META
│   │   ├── markerIcons.ts, poiColors.ts, brandColors.ts, bulkJobStatus.ts
│   │   └── pagination.ts          # PAGE_SIZE por vista, incluido FEED_MAP_CHUNK (tanda del scroll infinito)
│   ├── types/                     # un directorio por dominio; `base.ts` cuando son 1-2 tipos
│   │   ├── users/{base, auth, profile, interests}.ts
│   │   ├── feed/{cards, filters, search}.ts
│   │   ├── properties/{base, detail, forms, images}.ts   # base: ListingStatus, PropertyType, ListingType, VerificationStatus
│   │   ├── catalog/{base, neighborhoods}.ts
│   │   ├── maps/{base, cluster}.ts
│   │   ├── pois/{base, reachable}.ts
│   │   ├── avm/{form, predict}.ts
│   │   ├── shared/{ui, pagination, table}.ts             # table: aumento de ColumnMeta de TanStack
│   │   └── admin/                # un módulo por tema: properties, moderation, promotions, bulk, filters, catalog, actions
│   ├── views/                    # páginas-ruta
│   │   ├── public/{HomeView, AboutView, PublicProfileView}  # /users/:userId
│   │   ├── auth/{LoginView, RegisterView, ForgotPasswordView, ResetPasswordView}
│   │   ├── settings/{SettingsLayout, SettingsProfile, SettingsSecurity, SettingsAccount}
│   │   ├── properties/
│   │   │   ├── PropertiesView.vue          # parent feed con toggle lista/mapa
│   │   │   ├── feed/{FeedView, MapView}
│   │   │   ├── dashboard/MyPropertiesView
│   │   │   ├── detail/PropertyDetailView   # /listing/:id
│   │   │   └── edit/EditPropertyView       # /properties/:id/edit — ver [[frontend-property-edit-form]]
│   │   ├── dev/{DevPlaygroundView, CreatePropertyDevView}  # sin auth, dev only
│   │   └── admin/{AdminHomeView, properties/{AdminPropertiesLayout, moderation/AdminModerationView, promotions/{AdminPromotionsLayout, AdminPromotionsActiveView, AdminPromotionsCreateView}, imports/AdminImportsView}, catalog/{AdminCatalogView, neighborhoods/AdminNeighborhoodsView, localities/AdminLocalitiesView, divisions/AdminDivisionsView, countries/AdminCountriesView}}  # requiresAdmin — ver [[frontend-admin-panel]]
│   └── components/
│       ├── shared/{NavBar, NavGuest, NavUser, BaseModal, BaseSpinner, PaginationArrows, FilterTabs, EmptyState, BaseButton, IconButton, ChoiceChip, OptionCard, BaseTable, FormMessage, AuthLayout, form/{BaseInput, BaseSelect, BaseTextarea, PasswordInput, NewPasswordFields, FormField}}
│       ├── onboarding/{OnboardingModal, IntentSelector, LocalitySelector, NeighborhoodSelector, PropertyTypeSelector}
│       ├── properties/
│       │   ├── cards/PropertyCard
│       │   ├── photos/{PropertyPhotoGrid, PhotoGalleryPopup}
│       │   ├── detail/{PropertyOverview, NearbyPlaces}
│       │   ├── dashboard/DeletePropertyModal        # envuelve BaseModal, autocontenido (DELETE + loading)
│       │   ├── edit/{PropertyHeaderCard, PropertyPhotosCard, PropertyInfoCard, PropertyEditForm, PropertyEditActions, UploadPropertyImagesModal, DeletePropertyImagesModal}
│       │   └── feed/FeedFilters
│       ├── settings/SettingsSidebar
│       ├── map/{MapUser, PoiPopup, MapLegend}
│       └── admin/                                  # ver [[frontend-admin-panel]]
│           ├── shared/{AdminSplitView, AdminTabsNav, AdminFilterBar, AdminActionBar, AdminPaginationFooter}    # piezas sin dominio
│           └── properties/
│               ├── {AdminPropertiesTable, AdminPropertyPreviewPanel}   # compartidos entre tabs
│               ├── moderation/AdminModerationForm
│               ├── promotions/{AdminPromotionsTable, AdminPromotionForm, RemovePromotionModal}
│               └── imports/BulkUploadPropertiesModal
├── package.json
├── vue.config.js                 # webpack tweaks (Vue CLI)
├── tailwind.config.js
├── vueform.config.ts
├── postcss.config.js
├── tsconfig.json
└── .env / .env.example           # VUE_APP_USERS_URL, VUE_APP_CATALOG_URL, VUE_APP_AVM_URL, VUE_APP_IPAPI_URL
```

## Bootstrap (`main.ts`)

```ts
createApp(App)
  .use(pinia)
  .use(router)
  .use(VueCookies)
  .use(Vueform, vueformConfig)
  .mount("#app");
```

Notas:
- **Firebase ya no está** — removido el 2026-07-28 ejecutando [[adr-firebase-removal]]. No se inicializaba en ningún lado, así que el login con Google nunca funcionó; los botones quedaron comentados en `LoginView`/`RegisterView` esperando el Identity Brokering de Keycloak.
- **Vueform** se registra global, pero **ningún template usa sus componentes** — corregido 2026-07-28, ver §Forms. Lo que sí se usa es `@vueform/multiselect`.
- Sin axios instance global: hay una instancia por servicio en `api/clients/` y nadie fuera de `api/` las importa.

## Stores Pinia

### `useAuthStore` ([stores/auth.ts](frontend/src/stores/auth.ts))

Única fuente de verdad de identidad/sesión/rol — desde 2026-07-16 absorbió los campos de cuenta que antes vivían en `useUserStore`.

State:
```ts
user: AuthUser | null
isAuthenticated: boolean
isLoading: boolean
_authChecked: boolean    // guard contra checkAuth duplicado en navegación
onboardingStep: OnboardingStep   // "intent" | "city" | "neighborhood" | "property_type" | "done" (types/users/base.ts)
isAdmin: boolean
accountId: string | null
```

Actions:
- `checkAuth(force=false)`: `usersApi.getAuthProfile()` (`GET /v1/users/me/profile`). **Desde el 2026-10-09 pasa por el interceptor**: recargar con el access token vencido y el refresh vigente ya no desloguea. Antes iba con `axios` puro para no redirigir anónimos; eso lo resuelve ahora `forceLogout`, que solo actúa si `isAuthenticated` (ver interceptor). Setea `_authChecked` para no re-llamar en cada navegación.
- `fillUserData()`: `usersApi.getAccount()` (`GET /v1/users/me`, sin la barra final que tenía antes) → setea `onboardingStep`, `isAdmin`, `accountId`. Se llama solo **después** de que `checkAuth` confirmó sesión.
- `login(email, password)` / `register(userData)`: vía `usersApi` (excluidos del retry-refresh del interceptor) → `checkAuth(force=true)`.
- `logout()`: `usersApi.logout()` (`/auth/logout` también está excluido del retry-refresh) → resetea `onboardingStep`/`isAdmin`/`accountId`/`user`/`isAuthenticated`, llama `userStore.resetInterests()`, `router.push("/")`.
- `setOnboardingStep(step)`: único camino para avanzar el paso del onboarding desde fuera del store.

Getters: `fullName`, `isOrganization`, `userAvatar` (default a `ui-avatars.com`).

### `useUserStore` ([stores/user.ts](frontend/src/stores/user.ts))

Reducido a **preferencias + estado de UI del onboarding** — ya no tiene nada de identidad/sesión.

State:
```ts
userInterests: { localities, neighborhoods, properties }
```

Actions clave:
- `checkInterests()`: GET `/v1/users/me/interests` vía `usersApi` → cachea en store.
- `detectLocation()`: usa **ipapi.co** (third-party) para inferir país por IP. Cachea en `localStorage`.
- `isOnboardingDismissed()`: lee `sessionStorage` con key `STORAGE_KEYS.ONBOARDING_DISMISSED(authStore.accountId)` — scoped por cuenta, no global al browser.
- `dismissModal()`: escribe esa misma key con `"true"`.
- `setLocalities(ids)`: escribe las localidades elegidas en el onboarding (antes se mutaba el state desde el composable).
- `resetInterests()`: limpia `userInterests` — llamado desde `authStore.logout()` para que una cuenta distinta en el mismo tab no herede intereses de la anterior.

> El dismissal del onboarding **ya no se borra en logout** (antes sí) — es intencional: "no me vuelvas a preguntar hoy" debe sobrevivir un logout/login en el mismo browser, y solo resetearse si el browser se cierra de verdad (`sessionStorage` nativo). Ver [[frontend-onboarding-flow]].

## Composables

### `useFeed` ([composables/feed/useFeed.ts](frontend/src/composables/feed/useFeed.ts))

Gestiona el feed de propiedades con paginación por cursor:

**Estado expuesto:**
- `data: ref<PropertyCard[]>` — items de la página actual.
- `nextCursor: ref<string | null>` — cursor opaco para la siguiente página (`null` = última página).
- `isFirstPage: computed` — `true` si `cursorStack` está vacío.
- `neighborhoodLookup: ref<Record<string, string>>` — mapa `neighborhood_id → name` construido tras cada fetch (sessionStorage cachea las llamadas al catalog-service).

**Funciones:**
- `load(preferences?, filters?)` — carga página 1: resetea cursor stack, pageCache y nextCursor; guarda `resolvedPreferences` y `filters` en refs internos para reusar en `loadNext`/`loadPrev`; cachea en `pageCache["first"]`.
- `loadNext(cursor)` — si el cursor ya está en `pageCache`, restaura de caché sin petición; si no, hace `GET /v1/search/feed?cursor=...`; push `currentPageKey` al `cursorStack` antes de avanzar.
- `loadPrev()` — pop del `cursorStack`, restaura `data` y `nextCursor` desde `pageCache`; siempre local, nunca toca el backend.
- `fetchFeed(preferences, filters?, cursor?)` — axios con `params: { ...preferences, ...filters, ...(cursor ? { cursor } : {}) }`.

**Caché local (en memoria por instancia):**
- `pageCache: ref<Record<string, { items, nextCursor }>>` — keyed por cursor; `"first"` para página 1.
- `cursorStack: ref<string[]>` — historial de keys para `loadPrev`.
- `currentPageKey: ref<string>` — key de la página actual (arranca en `"first"`).

**Respuesta del back:** `FeedPage { items: PropertyCard[], next_cursor: string | null }` — el composable desempaqueta `.items`.

**Bug histórico (resuelto):** axios serializa arrays como `key[]=v`; FastAPI no parsea `key[]` como `key`. Fix: `paramsSerializer: { indexes: null }`.

> ⚠ **Pendiente:** cursor debería vivir en `route.query.cursor` (URL) para que sea compartible y el browser history funcione. La implementación actual es in-memory.

`PropertiesView` es la vista padre en `/feed`: contiene el header ("Las escogimos pensando en ti" + subtítulo `v-if isAuthenticated`) y el toggle Lista/Mapa. El toggle usa `router-link` a `feed-list` / `feed-map` y deriva el estado activo de `route.name`. `FeedView` y `MapView` son vistas hijas renderizadas por `<router-view />`.

### `useFeedMap` ([composables/feed/useFeedMap.ts](frontend/src/composables/feed/useFeedMap.ts))

Gestiona el feed del mapa (rehecho el 2026-10-09, ver [[adr-feed-map-whole-bbox-cluster]]):

- `fetchByBbox(payload: BboxPayload)` — `propertiesApi.getFeedMap` con `{ min_lat, max_lat, min_lon, max_lon, resolution }`. `resolution`: zoom≥15 → H3 r9, zoom<15 → H3 r7. Ordena con `sortForMap` (promocionadas primero, luego distancia al centro del bbox, desempate por id) y descarta la respuesta si mientras tanto se pidió otro bbox (`latestRequest`).
- `allItems` — todo el bbox, para el mapa (el cluster agrupa).
- `items` — los primeros `visibleCount` (tandas de `PAGE_SIZE.FEED_MAP_CHUNK` = 20), para la lista; `loadMore()` suma una tanda y devuelve si cargó algo. Cada bbox nuevo vuelve a la primera tanda.

Diferencia clave con `useFeed`: no usa cursor ni hace requests extra al scrollear — el backend ya devuelve el bbox completo.

### `usePropertyMapper` ([composables/properties/usePropertyMapper.ts](frontend/src/composables/properties/usePropertyMapper.ts))

Composable compartido entre `FeedView` y `MapView` para resolver nombres de barrios:

```ts
export function usePropertyMapper(items: Ref<FeedCard[]>) {
  // watch(items) → deduplica city_ids → buildNeighborhoodMap → neighborhoodLookup
  // toCard(p): FeedCard → Property (title, price, location con nombre resuelto, etc.)
  const cards = computed(() => items.value.map(toCard));
  return { cards };
}
```

Extrae la lógica de `toCard` + lookup que antes vivía duplicada en cada vista.

### `useNeighborhoodLookup` ([composables/catalog/useNeighborhoodLookup.ts](frontend/src/composables/catalog/useNeighborhoodLookup.ts))

```ts
export async function buildNeighborhoodMap(
  localityIds: string[]
): Promise<Record<string, string>>
```

Llama `getNeighborhoodsByLocalities`, aplana con `Object.values(result).flat()`, reduce a `id → name`. Lookup O(1) para resolver nombres en `toCard`.

### `useCities` ([composables/catalog/useCities.ts](frontend/src/composables/catalog/useCities.ts))

Singleton de módulo (no instancia por componente):
- `export const cities: Ref<Map<string, string>>` — mapa `id → name` de localidades del país del usuario.
- `export async function load()` — detecta país por IP → `getCitiesByCountry` → popula `cities`.

Patrón singleton correcto aquí porque las ciudades son las mismas para todos los componentes que las consuman en la misma sesión.

### `useMultiselect` ([composables/shared/useMultiselect.ts](frontend/src/composables/shared/useMultiselect.ts))

Dos factory functions con estado por instancia (no singleton):

- **`useCityMultiselect()`** → `{ selected: Ref<string[]>, removeCity(id) }`.
- **`useNeighborhoodMultiselect()`** → `{ cities, selectedByCity, allSelected, allNeighborhoodOptions, removeNeighborhood, load(localities) }`.
  - `load(localities: {id, name}[])`: llama `getNeighborhoodsByLocalities`, popula `cities` con barrios, inicializa `selectedByCity`.
  - `allNeighborhoodOptions`: computed flat `{value, label}[]` para multiselect sin tabs.
  - `allSelected`: computed flat de todos los barrios seleccionados en todas las localidades.

Usado en `NeighborhoodSelector` (tabbed, por localidad) y `FeedFilters` (flat, todos los barrios de ciudades seleccionadas).

### `useOnboarding` ([composables/onboarding/useOnboarding.ts](frontend/src/composables/onboarding/useOnboarding.ts))

Guarda cada paso y avanza el flujo; **abrir y cerrar el modal es del padre** (desde el 2026-10-09):
- `shouldStart()`: no descartado en la sesión y `onboardingStep !== "done"`.
- `completeIntent()`, `saveCity(localities)`, `saveNeighborhoods(localities)`, `savePropertyTypes(selections)`: llaman a `usersApi` y avanzan con `authStore.setOnboardingStep`; devuelven `true`/`false`.
- Sin estado de módulo ni imports de componentes.

Detalle en [[frontend-onboarding-flow]].

### `useLocation.ts` ([composables/catalog/useLocation.ts](frontend/src/composables/catalog/useLocation.ts))

Funciones puras (no es composable Vue strictly hablando, son helpers que aceptan parámetros):
- `getCitiesByCountry(id)`: `catalogApi.getLocalitiesByCountry` → cachea por country en `sessionStorage`.
- `getNeighborhoodsByLocalities(localityIds)`: `catalogApi.getNeighborhoodsByLocalities` con dedup de cached vs missing. Cachea por locality en `sessionStorage`.
- `locations()`: combina `detectLocation` (ipapi) + `countries` (catalog) → devuelve `(countryDetected, countryUser)`.
- `getNeighborhood(lat, lon)`: dos requests en cadena — `catalogApi.resolveCoordinates` → `neighborhood_id`, luego `catalogApi.getNeighborhoodById` → nombre. Usado por `useAvmForm` para mostrar el barrio detectado al seleccionar dirección.

### `useForgotPassword` y `useResetPassword` ([composables/users/](frontend/src/composables/users))

El reset de password son dos vistas sobre `AuthLayout` (panel oscuro en el slot `#aside`, contenido en el default) (2026-10-24):

- **`/forgot-password` → `ForgotPasswordView` + `useForgotPassword`.** Devuelve `{ sending, sent, error, requestReset(email) }`. No muestra el `message` del back, que viene en inglés y en un 5xx puede traer detalles de infra: 422 → "Revisa el correo", el resto → mensaje genérico. Con `sent` la vista cambia el formulario por el aviso y "Ya puedes cerrar esta pestaña o ir a iniciar sesión": el flujo sigue en la pestaña que abre el link del correo.
- **`/reset-password` → `ResetPasswordView` + `useResetPassword`.** Lee `route.query.token` validando con `typeof === "string"` (puede llegar como array) y, si vino, lo quita con `router.replace({ query: {} })` para que no quede en el historial. Cambiar solo el query no vuelve a montar la vista, así que el token sigue en un `const`; recargar lo pierde. Devuelve `{ sending, confirmed, invalidLink, error, confirmReset(newPassword, confirmPassword) }`: sin token o con 401 → `invalidLink` y link a `/forgot-password`; 400 → contraseñas no coinciden; éxito → aviso con link a login, porque el confirm no setea cookies.
- La ruta no lleva `isLogged`: con ese flag el guard manda a home a un usuario logueado y el token del link se pierde.
- Los campos "nueva + confirmar" son `NewPasswordFields` (`v-model:password`, `v-model:confirmation`) y la regla vive en `utils/password.ts`; `SettingsSecurity` usa las mismas piezas.

## Router con guard global

`router.beforeEach`:
1. Si la ruta es `isLogged: true` (guest-only) y `isAuthenticated` → redirige a `/`.
2. Si `requiresAuth: true` y `!_authChecked` → `await authStore.checkAuth()`.
3. Si `requiresAuth && !isAuthenticated` → redirige a `/login`.
4. Si `requiresAdmin: true` → si `!authStore.accountId` (todavía no corrió `fillUserData`), `await authStore.fillUserData()` primero; si `!authStore.isAdmin` → redirige a `/`.

El paso 4 existe por una race real: `authStore.isAdmin` normalmente solo se llena vía el `watch` de `App.vue` **después** de que el guard ya resolvió la navegación — sin este paso, un admin real entrando por link directo a una ruta `requiresAdmin` sería rebotado a Home. Ver [[frontend-admin-panel]].

History mode (`createWebHistory`), URLs sin `#` — ver [[adr-history-mode-cloudflare-pages]], que reemplaza a [[adr-hash-history-static-hosting]].

## API consumption pattern

**Dos niveles** ([[adr-api-layer-by-domain]]):

1. **Clientes** en `src/api/clients/` — una instancia de axios por servicio:

| Archivo | baseURL (dev) | `withCredentials` | Auth interceptor |
|---|---|---|---|
| `clients/catalog.ts` | `/api/catalog` | Sí (desde 2026-10-04) | Sí — los endpoints `/admin` leen la cookie |
| `clients/avm.ts` | `/api/avm` | No | No — `/v1/predict` sin auth hoy |
| `clients/users.ts` | `/api/users` | Sí | Sí |
| `clients/properties.ts` | `/api/properties` | Sí | Sí |

2. **Funciones por dominio** en `src/api/{users,catalog,properties,avm}.ts` y `src/api/admin/{properties,catalog}.ts`: una por endpoint, con la ruta de `*_ENDPOINTS`, tipos de `types/` y `data` como retorno. Las conversiones de payload (camelCase → snake_case, campos opcionales omitidos) viven acá. Se importan como namespace: `import * as usersApi from "@/api/users"` → `usersApi.login(...)` (no choca con las acciones del store y se mockea el módulo entero).

Fuera de `api/` nadie importa un cliente. Composables, stores, componentes y vistas llaman a estas funciones; componentes y vistas solo para acciones puntuales sin estado (borrar, cargar un detalle). Las únicas llamadas HTTP fuera de los clientes son el refresh del interceptor, `ipapi.co` (`detectLocation`) y los `fetch` a URLs presignadas de storage.

Las baseURLs son rutas relativas (proxy en dev) — ver sección "Webpack devServer proxy".

### Silent refresh interceptor (`src/api/clients/interceptors.ts`)

`applyAuthInterceptor(instance)` se llama en los clientes de users, properties y catalog. Comportamiento:

```
response 401
  └─ !error.config → reject inmediato (error sin config = cancelado/red)
  └─ original._retry → reject (evita loop infinito en el retry)
  └─ url matchea AUTH_ENTRYPOINTS (login, register, logout, reset-password/confirm) → reject inmediato
  └─ isRefreshing === true → encolar en failedQueue; resolver/rechazar cuando termine el refresh en curso
  └─ isRefreshing === false →
       original._retry = true
       isRefreshing = true
       POST /v1/auth/refresh (timeout 3s, withCredentials, axios puro — no pasa por este mismo interceptor)
         ├─ éxito → processQueue(null) → retry instance(original)
         └─ fallo → processQueue(error) → forceLogout() → reject
       finally: isRefreshing = false
```

**`AUTH_ENTRYPOINTS`** excluye login y register del retry-refresh — un 401 ahí es "credenciales inválidas", no "sesión expirada". **Logout también está excluido (2026-10-09)**: si el refresh falla, `forceLogout → logout → 401` se encolaría en `failedQueue` esperando un refresh que ya terminó, y la promesa no resolvería nunca. Las rutas salen de `USERS_ENDPOINTS`.

**Un endpoint con token propio que responde 401 tiene que ir en `AUTH_ENTRYPOINTS` (2026-10-18).** Los confirm de reset y de reactivación mandan un action token en `Authorization: Bearer` y responden `401 TOKEN_INVALID_OR_EXPIRED` si venció o ya se usó. Fuera de la lista, el interceptor lo toma por sesión vencida: intenta el refresh y rechaza con el error del refresh, así que la vista no puede decir "el enlace venció". **Update 2026-10-24:** `reset-password/confirm` ya está en la lista; el de reactivación entra cuando se cablee ([[open-items]]).

**`forceLogout()`** solo llama a `logout()` si `authStore.isAuthenticated` (2026-10-09): un anónimo cuyo `checkAuth` da 401 y no tiene refresh simplemente queda anónimo, sin redirección a `/`. Reemplazó al viejo `redirectToLogin()` (`window.location.href` hardcodeado a `/#/login`, hard reload). Ahora hace `const { useAuthStore } = await import("@/stores/auth"); await useAuthStore().logout()` — invalida el refresh token en el back de verdad y limpia el estado de Pinia antes de redirigir, en vez de solo tirar un reload. El `import()` dinámico es deliberado: evita un ciclo de imports estático (`auth.ts → usersApi.ts → interceptors.ts → auth.ts`), ya que `auth.ts` importa `usersApi` para sus propias llamadas.

**`isRefreshing` y `failedQueue` son module-level** (declarados fuera de cualquier función o composable Vue), no instancia-por-componente. Esto es intencional: sobreviven al desmonte/remonte de componentes. Si fueran `ref` dentro de un composable, cada componente tendría su propio flag y podrían dispararse múltiples refresh concurrentes.

**`!error.config` guard**: `error.config` puede ser `undefined` cuando el error ocurre antes de que axios haya terminado de construir la request (red caída, request cancelada). Sin el guard, `original._retry` lanzaría un TypeError. El guard hace `return Promise.reject(error)` inmediatamente en ese caso.

**Timeout de 3s en refresh**: si users-service no responde, el refresh falla rápido en vez de colgar indefinidamente — la request original termina rechazada y el usuario es redirigido a login.

### Webpack devServer proxy

Las baseURLs usan rutas relativas (`/api/users`, `/api/catalog`, etc.) para desarrollo. `vue.config.js` configura el proxy:

> **Gap 2026-10-04:** la intención es usar el proxy, pero `frontend/.env.development` define `VUE_APP_*_URL=http://localhost:800x` y `config/index.ts` las prefiere sobre las rutas relativas. Hoy el front llama directo a cada backend, el proxy no se usa y CORS sí aplica. Ver [[open-items]].

```js
devServer: {
  proxy: {
    "/api/users":      { target: "http://localhost:8000", changeOrigin: true, pathRewrite: { "^/api/users": "" } },
    "/api/catalog":    { target: "http://localhost:8001", changeOrigin: true, pathRewrite: { "^/api/catalog": "" } },
    "/api/avm":        { target: "http://localhost:8003", changeOrigin: true, pathRewrite: { "^/api/avm": "" } },
    "/api/properties": { target: "http://localhost:8002", changeOrigin: true, pathRewrite: { "^/api/properties": "" } },
  }
}
```

**Por qué existe el proxy**: Chrome bloquea subresource requests (`fetch`/XHR) entre puertos distintos de `localhost` en un devcontainer — VS Code port forwarding agrega una capa Node.js que interactúa mal con el mecanismo de reutilización de conexiones keep-alive de Chrome (el request queda stalled indefinidamente sin error). Firefox no tiene este problema. El proxy hace que el browser siempre hable con `localhost:8080` (same-origin, sin CORS, sin problema de Chrome); webpack reenvía internamente dentro del container.

Para producción: setear `VUE_APP_USERS_URL`, `VUE_APP_CATALOG_URL`, `VUE_APP_AVM_URL`, `VUE_APP_PROPERTIES_URL` con las URLs reales — `config/index.ts` las prioriza sobre el default del proxy.

## Caching local

| Dato | Storage | TTL implícito |
|---|---|---|
| Countries | `localStorage` | Permanente hasta clear cache |
| Cities by country | `sessionStorage` | Por sesión del browser |
| Neighborhoods by locality | `sessionStorage` | Por sesión |
| Neighborhood lookup (`id → name`) | en memoria (`ref`) | Por instancia de `useFeed` — se reconstruye en cada `load()` |
| User location (IP) | `localStorage` | Permanente hasta clear |
| `onboarding_dismissed:{accountId}` | `sessionStorage` | Por sesión del browser, scoped por cuenta — **no se borra en logout** (a propósito, ver [[frontend-onboarding-flow]]) |

Keys centralizadas en `STORAGE_KEYS` del `config/index.ts`. `ONBOARDING_DISMISSED` es una función `(accountId) => key`, no un string fijo — mismo patrón que `CITIES_BY_COUNTRY`/`NEIGHBORHOODS_BY_LOCALITY`. No hay invalidación explícita — depende del clear del browser.

## Components organization

| Carpeta | Propósito |
|---|---|
| `shared/` | NavBar, NavGuest (no-logged), NavUser (logged), BaseModal, los cuatro botones compartidos — **BaseButton** (variantes `primary`/`secondary`/`ghost`/`danger`/`danger-soft`/`link`, tamaños `sm`–`xl`, `loading`, `block`, `to` para dibujarse como `RouterLink`), **IconButton** (solo icono, `label` obligatorio), **ChoiceChip** (opción chica elegible) y **OptionCard** (tarjeta elegible con el contenido en un slot) —, los campos de `form/` — **BaseInput**, **BaseSelect**, **BaseTextarea**, **PasswordInput** (input + mostrar contraseña) y **FormField** (label + campo + error o ayuda) —, PaginationArrows, EmptyState, BaseSpinner y **BaseTable** (tabla dumb genérica sobre TanStack, un slot por columna, con selección de fila opcional vía `rowKey`/`selectedKey` + emit `rowClick` — ver [[adr-tanstack-table]]) — reusables transversales. Gotcha de la selección: la clase de fila activa y el `hover:` se aplican de forma **excluyente**, porque Tailwind emite la variante `hover:` con más especificidad y si conviven despinta la fila seleccionada al pasarle el mouse. |
| `onboarding/` | `OnboardingModal` (controlado por `v-model` desde `App.vue`) + 4 selectors (Intent, Locality, Neighborhood, PropertyType) que emiten `submit` y reciben `saving`. Ver [[frontend-onboarding-flow]]. |
| `properties/` | Organizado en subcarpetas por dominio desde 2026-06-21. `cards/PropertyCard` — card del feed (`HouseCard` se borró el 2026-10-05: no lo usaba nadie). `photos/{PropertyPhotoGrid, PhotoGalleryPopup}`. `detail/{PropertyOverview, NearbyPlaces}`. `feed/FeedFilters` — sidebar de filtros con secciones Preferencias (ciudad, barrio, tipo) y Filtros (precio, área, habitaciones, baños); se pre-pobla con ciudades de `useCities`, barrios cargados dinámicamente al seleccionar ciudad vía `watch`. Mantiene estado local (`selected`, `selectedNeighborhoods`, `selectedTypes`, `filters: ref<FeedFilters>({})` con `v-model.number`); `property_types` se togglea con `toggleType(type)` (push/filter sobre el array). **Emite un solo `submit` con `{preferences, filters}` al click en "Aplicar"** — no reactivo con `watch`, decisión para evitar una petición por cada cambio de campo. El objeto `preferences` se arma en `onSubmit` leyendo los refs (`selected.value`, etc.), sin ref `preferences` duplicado. |
| `settings/` | SettingsSidebar — navegación lateral del SettingsLayout. |
| `admin/` | `properties/{BulkUploadPropertiesModal, AdminPropertiesTable, AdminPropertyPreviewPanel}` — el modal de import por presigned PUT, la tabla de moderación (columnas + badges sobre `BaseTable`) y el panel de vista previa, que reusa `PropertyOverview` y `PhotoGalleryPopup` del detalle público. Ver [[frontend-admin-panel]]. |
| `map/` | MapUser — mapa dumb/reusable: vue-leaflet para mapa, tiles y `subject`; el resto de marcadores en un cluster imperativo (`useMarkerCluster`). `PoiPopup` es el contenido del popup de POIs. Ver [[frontend-map-component]]. |
| `avm/` | AvmForm / AvmResult — form del avalúo multi-step. `AvmForm` consume `composables/avm/useAvmForm` (los tipos viven en `types/avm/{form,predict}.ts`; `SelectedPlace` en `types/maps/base.ts`). Emite `place-selected` (marker en tiempo real) y `submit` (`AvmSubmitEvent`: payload + place + neighborhood resuelto). `DevPlaygroundView` orquesta: recibe `place-selected` → actualiza `center` y `marker` reactivos → pasa al mapa. |

## Estilos: Tailwind + diseño tokens

- Tailwind 3 con clases utility directas en templates.
- Custom utilities/colors en `tailwind.config.js` — usa nombres tipo `brand-primary`, `brand-text`, `brand-bg`, `brand-muted`, `brand-divider`, `brand-placeholder`, `brand-border` (vistos en `LoginView`).
- **Paleta en un solo archivo (2026-10-05).** `src/theme/brandColors.json` es la fuente: `tailwind.config.js` la carga con `require`, y el JS que no acepta clases (estilos de Leaflet, `fill` de SVG) la lee como `BRAND_COLORS` desde `constants/brandColors.ts`. Por eso `tsconfig.json` activa `resolveJsonModule`. Se sumaron `primary-dark`, `navy` y `accent`. El tema del multiselect, que estaba duplicado en `LocalitySelector` y `NeighborhoodSelector`, vive en `main.css` como `.brand-multiselect`, con colores vía `theme()`.
- **Tokens semánticos y verde accesible (2026-10-16).** `brandColors.json` suma `primary-strong` (`#15803D`, ~5:1 con texto blanco) y su hover, más `danger`, `success` y `warning` con variantes `-light` y `-border` (y `danger-hover`). El fondo de los botones primarios, los links y el texto del chip elegido usan `primary-strong`; `brand-primary` (`#22C55E`, ~2,3:1 con blanco, no pasa AA) queda para acentos, bordes y fondos claros. Las clases `red/green/yellow/orange/amber` crudas se pasaron a tokens; quedan crudas a propósito las paletas categóricas (rangos de isócronas en `useReachablePois`, puntos de estado en `bulkJobStatus`/`propertyStatus`).
- `App.vue` ya no tiene CSS: el de la plantilla de Vue CLI se borró el 2026-10-16. Su `#app` nunca aplicó (un `<style scoped>` no alcanza al elemento de montaje); el `nav { padding: 30px }` sí, y ese padding ahora vive en `NavBar` como `p-[30px]`.
- Un solo CSS de entrada, `main.css`, con las tres directivas de Tailwind; `main.ts` lo importa después de `leaflet/dist/leaflet.css`, que viene del paquete y no de un CDN. `.leaflet-container { isolation: isolate }` va fuera de `@layer` porque Tailwind purgaría una clase que solo agrega Leaflet en runtime.
- **Botones por componente (2026-10-16).** Ningún botón lleva sus propias clases de estilo: van por `BaseButton`, `IconButton`, `ChoiceChip` u `OptionCard`. `BaseButton` es `type="button"` por defecto, así que un botón dentro de un `<form>` no lo envía sin pedirlo. Una clase que pasa el padre no pisa a una del componente del mismo grupo (`justify-start` contra `justify-center`): en Tailwind manda el orden del CSS generado, no el del atributo, así que la variación va por props. Quedan fuera las pestañas, los botones de la navbar, el switch de visibilidad, los "mostrar contraseña" y los CTAs del hero del home.
- **Campos por componente (2026-10-16).** Inputs, selects y textareas van por `components/shared/form/`: un solo look (borde 1px, `rounded-xl`, foco visible, borde rojo con `invalid`) en dos alturas, `md` (`h-10`) para admin, settings y formularios de propiedad y `lg` (`h-12`) para auth. `BaseInput` y `BaseTextarea` escriben el valor a mano, sin la directiva `v-model` adentro, así que sirven con `v-model` y con `:value` + `@input` (el formato de precio de los formularios de propiedad); con `type="number"` emiten con `looseToNumber`, la regla del `.number` de Vue. `BaseSelect` usa el `v-model` nativo, que reaplica el valor cuando las opciones llegan después. `FormField` solo está en el admin, donde los labels eran idénticos; auth, settings y propiedades conservan su estilo de label por área.
- Sin component library tipo Element Plus — todos los componentes son custom, por decisión: ver [[adr-no-component-library]].

## Forms

**Corregido 2026-07-28 tras auditar el código.** Esta sección afirmaba que convivían dos sistemas (Vueform + Vuelidate); una auditoría por grep mostró que **ninguno de los dos se usa**. Lo que hay es un solo sistema:

- **Campos compartidos y validación a mano.** Desde el 2026-10-16 los inputs son los componentes de `components/shared/form/` (ver "Estilos"); la validación sigue a mano en cada vista. Antes eran inputs nativos con cuatro estilos de clases distintos. `LoginView` y `RegisterView` no importan ninguna librería de forms.
- **`@vueform/multiselect`** es la única pieza de Vueform realmente en uso, en `FeedFilters`, `LocalitySelector`, `NeighborhoodSelector` y `main.ts` (ver el composable `useMultiselect` más arriba).

Consecuencias de la corrección:

- `vuelidate`, `@vuelidate/core`, `@vuelidate/validators` y `@types/vuelidate` se **removieron** el 2026-07-28 — cero imports. El paquete `vuelidate` era además el build de **Vue 2**, incapaz de correr en esta app.
- `@vueform/vueform` sigue registrado en `main.ts` pero ningún template usa sus componentes. La consideración de licencia que motivaba esta sección **no aplica** a lo que hay hoy.
- ⚠️ **Trampa antes de desinstalarlo**: `@vueform/multiselect` no está declarado en `package.json` — llega como dependencia transitiva de `@vueform/vueform`. Sacar Vueform rompe esos tres componentes sin ningún aviso del bundler. Ver [[open-items]].
- ⚠️ **Y el plugin de Tailwind de Vueform no es inocuo.** `tailwind.config.js` carga `@vueform/vueform/tailwind`, que inyecta una base de formularios: entre otras cosas pone `appearance: none` a los `[type="checkbox"]`, por eso los checkbox del admin llevan `appearance-auto` para verse. Quitar Vueform cambia el aspecto de todos los campos, no solo rompe el multiselect.

También se removieron `vue-class-component` (API de Vue 2, sin imports) y `vue-google-autocomplete` — el input de ubicación ya usa el web component `gmp-place-autocomplete` ([[adr-gmaps-places-geocoding]]).

## Formateo (`utils/`)

Consolidado el 2026-07-29. Antes el dinero tenía **cuatro** implementaciones compitiendo: `utils/money.ts` sin símbolo, dos `Intl.NumberFormat` idénticos en `usePropertyDetail`, `"$ " + Math.round(...)` en `AvmResult` y un `toLocaleString` pelado en `PropertyCard`.

- **`formatCurrency(value, currency = "COP")`** en `utils/money.ts` es el único camino hoy. Acepta `string` además de `number` porque los `Decimal` del backend se serializan como string.
- **`formatMoney`/`parseMoney` quedan aparte a propósito**: no son formateo de display, son el par que usan los inputs de `StepDetalles` y `PropertyEditForm` en `@blur`. Meterles símbolo rompería el `parseMoney` de vuelta.
- **Update 2026-10-05:** `utils/number.ts` suma `formatNumber` (reemplaza los `toLocaleString("es-CO")` sueltos del admin) y `formatArea`, `utils/date.ts` suma `formatLongDateTime`, y el locale vive en `LOCALE` de `config/index.ts`: `"es-CO"` no aparece en ningún otro archivo.
- **`utils/date.ts`** (`formatShortDate`) es nuevo — no existía **ningún** formateo de fechas en el proyecto. Su `Intl.DateTimeFormat` se construye una vez a nivel de módulo: instanciarlo por celda es de lo más caro que puede hacer una tabla.

Efecto colateral visible: `PropertyCard` tenía el `$` hardcodeado en el template, así que los precios pasaron de `$450.000.000` a `$ 450.000.000` — la salida real del locale `es-CO`, que `AvmResult` ya usaba.

Limitación conocida: `PropertyCardUI` no lleva `currency` (el mapper lo descarta), así que las tarjetas del feed asumen COP aunque el backend soporte cinco monedas. Ver [[open-items]].

## Mapas y geocoding

Ver [[adr-mapbox-geocoding-leaflet-rendering]] para el detalle. Resumen:

- **Render del mapa**: Leaflet + `@vue-leaflet/vue-leaflet` (wrapper Vue) + **D3.js** para overlays/data visualization.
- **Forward geocoding** (address → lat/lon): **Google Maps Places API (New)** — `PlaceAutocompleteElement` en el frontend, sin pasar por el backend. Reemplazó a Mapbox (calidad insuficiente en Colombia). Ver [[adr-gmaps-places-geocoding]].
- **Reverse geocoding** (lat/lon → barrio): el frontend pasa el `(lat, lon)` al backend (catalog-service `/by-coordinates`).

El render lo encapsula `MapUser.vue` — un componente **dumb/reusable**: props in (`center`, `markers` tipados, `zoom` vía `v-model`/`defineModel`) + un `<slot>` para capas extra; los iconos de marker son data-driven (`public/icons/<imageType>.svg`). No tiene lógica de negocio ni de auth. Detalle completo en [[frontend-map-component]].

## Build & tooling

- **Vue 3.5.35** (upgrade completado 2026-05-29) — habilita `defineModel` y `useTemplateRef`. Es **independiente** de la migración a Vite, que sigue diferida (ver [[adr-vue-cli-deferred-vite-migration]]).
- **`useTemplateRef`** (Vue 3.5): reemplaza `ref<HTMLElement>(null)` para refs de template. Sintaxis: `useTemplateRef<HTMLDivElement>('refName')` — el template usa `ref="refName"` (string, no binding dinámico).
- **Build**: `npm run build` (vue-cli-service) → `dist/` estático. **Verde desde el 2026-07-29**; venía fallando por 9 errores de lint pre-existentes, resueltos con `lint --fix` más dos bugs reales (ver abajo).
- **Deploy planeado**: bucket público (probable S3 / MinIO / GCS) sirviendo `index.html` + assets. Hash history evita necesidad de rewrites en el bucket.
- **Sin SSR** — pura SPA client-side.

### El typecheck nunca corrió (2026-07-29)

`vue-tsc --noEmit` **aborta** por un error de config pre-existente: `tsconfig.json` declara `baseUrl`, deprecado en TS 5.x, y eso emite `TS5101` antes de typecheckear nada. O sea que cualquier lectura de "el typecheck pasa" en este proyecto era una corrida que nunca arrancó.

Corriéndolo con `--ignoreDeprecations 6.0` aparecen **2 errores reales**, ambos pre-existentes:

- `HouseCard.vue:81` importa un default export que `types/properties.ts` no tiene.
- `ResetPasswordView.vue:51` usa un `loginUser` que no existe en ese componente.

Ninguno rompe el build porque **`vue-cli-service build` no corre `vue-tsc`, solo ESLint**. Arreglar el `tsconfig` es el prerequisito para que el typecheck vuelva a ser una red de seguridad. Ver [[open-items]].

**Update 2026-10-05.** El `TS5101` depende de la versión de TypeScript que baje `npx`: el proyecto fija TS 5.0 y `npx vue-tsc` a secas trae uno incompatible, que aborta. Con versiones fijadas corre sin tocar el `tsconfig`:

```bash
npx -p vue-tsc@2 -p typescript@5.6 vue-tsc --noEmit -p tsconfig.json
```

`HouseCard.vue` se borró. Quedan `ResetPasswordView.vue:51` y dos errores nuevos en `AdminModerationForm.vue:52` y `:81` (`null` como índice). Al tipar los `any` del proyecto apareció además un bug real: `useCities` hacía `.map` sobre el `undefined` que devuelve `getCitiesByCountry` cuando falla.

**Update 2026-10-09 — el build no typecheckea los `.vue`, y eso dejó pasar dos errores.** Se confirmó inyectando un error de tipos en `BaseTable.vue`: `vue-cli-service build` termina "Build complete" con solo un warning de ESLint. `tsc --noEmit` tampoco sirve: no lee `.vue`. La única verificación real es el comando de arriba. Sin correrlo se mergearon #22 (`AvmForm.vue` sin el import de `SelectedPlace`) y #23 (`MapUser.vue` pasando un `DivIcon` a `<l-marker>`), ambos arreglados en #24. Quedan 3 errores: `AdminModerationForm.vue:52` y `:81` (`null` como índice, inocuos) y `ResetPasswordView.vue:51`, que **es un bug real**: el `<form>` llama a `loginUser`, que no existe (es `resetPasswordUser`). Además, `eslint src` sin `--ext .ts,.vue` no revisa los `.vue`; el comando correcto es el de `scripts/audit.sh`. Ver [[open-items]]. **Update (harness, 2026-10-09):** los 3 se arreglaron y `vue-tsc` quedó en 0. `ResetPasswordView` envía por el `<form>` (`resetPasswordUser`) y el botón ya no tiene `@click`, que con `type="submit"` mandaba dos veces. Ahora corre solo: `npm run typecheck`, el hook `Stop` de Claude Code y `make audit` ([[dev-workflow]], "Harness").

### Reglas de ESLint desactivadas

`no-undef` está apagado a nivel proyecto desde el 2026-07-29. `eslint-plugin-vue` está en v8 (2022) y no entiende `<script setup generic="T">` ni `defineSlots`, así que marcaba los parámetros de tipo como identificadores no definidos. La regla además es redundante con `vue-tsc` —que sí ve el type-space de TS— y es lo que recomienda typescript-eslint para proyectos TS. Sin esto, cada componente genérico nuevo daría falsos positivos.

### Bugs encontrados al dejar el build verde

- **`StepImagenes.vue`**: un `computed` leía y escribía el mismo ref (`objectUrls`), así que se auto-invalidaba y podía revocar object URLs que las miniaturas seguían usando. Reemplazado por un `watch` sobre `files`, colapsando los dos refs en uno.
- **`CreatePropertyView.vue`**: el `catch` vacío **no** era el bug que parecía. Que el `finally` avance al paso 3 pase lo que pase es deliberado — el paso 3 es una pantalla de doble uso que renderiza el estado de error *o* el uploader, y el botón de publicar está gateado por `!error`, así que el "estado roto" era inalcanzable. Solo se arregló el bloque vacío.

### Costo medido de migrar a Vite (2026-07-28)

La migración sigue diferida ([[adr-vue-cli-deferred-vite-migration]]), pero al evaluar Nuxt UI se midió el costo en vez de estimarlo: **116 archivos**, solo **5** usos de `process.env` (todos en `config/index.ts`), **una** API específica de webpack (`require("leaflet.markercluster")` en `MapUser.vue`), ningún `require.context`, y un proxy de 4 entradas que traduce directo. Es más barato de lo que suponía el ADR.

**Tailwind v4 es el lado riesgoso y no depende de nosotros**: `tailwind.config.js` carga `@vueform/vueform/tailwind` y Vueform 1.13 apunta a v3. Además dos hojas cargan directivas `@tailwind` (`main.css` y `assets/tailwind.css`), la segunda con ~40 líneas de `@layer` que tematizan el web component de autocomplete de Google, cuya semántica cambió en v4.

## Convenciones de código (2026-10-05)

Acordadas al auditar los smells del front:

- **Comentarios de una línea**, preferiblemente inline al final de la línea que explican. Nada de bloques `/** */` multilínea; la razón larga va a la wiki o al commit.
- **Tipos en `types/<dominio>/`** como `interface` exportada (o unión con `type`); `base.ts` cuando el dominio tiene 1-2 tipos, archivos temáticos cuando crece, `shared/` para lo transversal. No se declaran tipos dentro de componentes, vistas o composables. Las claves de acciones van como uniones tipadas (`NeighborhoodAction`), no como `string`.
- **Constantes en `constants/`, separadas por dominio** (`propertiesFilters.ts`, `catalogFilters.ts`), como ya lo están los `*Endpoints.ts`.
- **HTTP solo en `api/`** (2026-10-09), nunca en composables, componentes, constantes ni definiciones de filtro: `NEIGHBORHOOD_FILTERS` solo referencia `loadCountryOptions` / `loadLocalityOptions` de `api/admin/catalog`. Ver [[adr-api-layer-by-domain]].
- **Errores de formulario con `FormMessage`** (`variant="error" | "success"`, `role="alert"`), no con `alert()`.
- **Logs con `logger.error`** de `utils/logger.ts`, no con `console`.
- **Textos de la interfaz en tuteo**: la app es es-CO.
- **Iconos como componentes de `@lucide/vue`** (2026-10-24), renderizados con `<component :is>` y tipados con `ChoiceOption` cuando son opciones; no como SVG copiados en `assets/`, porque un `<img>` no hereda `currentColor` y el icono no puede cambiar de color con el estado.
- **Los assets del bundle no van a un CDN aparte** (2026-10-24): Cloudflare Pages sirve `dist/` y el build les pone hash (`img/<nombre>.<hash>.svg`), así que se cachean sin vencimiento. R2 es para lo que no viaja con el código, como las fotos de usuarios y de propiedades.

Lo que la auditoría dejó abierto está en [[open-items]]. HTTP en vistas, rutas `/v1` a mano y tipos fuera de `types/` se cerraron el 2026-10-09; siguen abiertos los errores tragados, el último `alert()` y `useLocation`.

## Tipos — separación UI vs API

`types/feed/cards.ts` tiene dos shapes distintas:
- `PropertyCard` — response shape de la API de properties-service.
- `PropertyCardUI` — shape para render del card en feed (UI). Antes vivía como `Property` en `PropertyCard.vue` — causaba TS2614 al importar desde `.ts` files.

`types/properties/`:
- `images.ts`: `PropertyImageCard` — imagen de una propiedad, compartida por card y detalle.
- `detail.ts`: `PropertyDetail` (response de `GET /v1/properties/{id}`) y `PropertyLocationDetail` (usa `city_id`, el campo de properties-service, distinto al `locality_id` de catalog-service).

Regla: nunca exportar interfaces de tipos desde archivos `.vue` — rompe TypeScript en consumers `.ts`.

## PropertyDetailView

Vista de detalle del listing en `/listing/:id` (`views/properties/detail/PropertyDetailView.vue`). Refactorizada (2026-06-20) para que la view **solo orqueste**: un `property = ref<PropertyDetail | null>`, el composable `usePropertyDetail`, y 3 componentes hijos que reciben los datos ya resueltos.

- **`PropertyPhotoGrid.vue`** (`components/properties/photos/`) — grid de fotos (`grid grid-cols-4 grid-rows-[200px_200px]`, `grid-area` en `<style scoped>` porque Tailwind arbitrary values no funciona con clases dinámicas en `v-for`). Es padre de **`PhotoGalleryPopup.vue`** (carrusel `vue3-carousel` dentro de `BaseModal` con `size="3xl"`) — patrón props-down/events-up: el popup nunca muta el prop `isOpen`, solo emite `close`.
- **`PropertyOverview.vue`** — header + precio + stats chips + descripción + detalles secundarios. Cero lógica propia, todo via props que mapean 1:1 a lo que devuelve `usePropertyDetail` (incluye `hasAdminFee`/`description` como `computed`, y `locationLabel` resuelto en la view con el mismo patrón de `buildNeighborhoodMap` que usan las cards del feed).
- **`NearbyPlaces.vue`** — sección "Cerca del lugar" (perfiles, acordeón POI, mapa, isocronas, leyenda). Ver [[frontend-poi-reachable]] — a diferencia de los otros dos, es dueño de su propio `useReachablePois` (recibe `lat`/`lon`/`propertyId`, resuelve interno).
- **Padding de la view**: `px-[8%] sm:px-[12%] lg:px-[18%]` — más estrecho que navbar para dar respiro visual.
- **Lógica de detalle**: `composables/properties/usePropertyDetail.ts` — la view solo destructura el composable.
- **Location label**: `buildNeighborhoodMap` (`composables/catalog/useNeighborhoodLookup.ts`) resuelto en `onMounted` de la view tras cargar la propiedad — resuelve barrio, no ciudad.
- **Fetch real**: `propertiesApi.getProperty(props.id)`. La ruta `/listing/:id` declara `props: true`, así que la vista recibe `id` como prop tipada en vez de leer `route.params.id as string` (igual `/properties/:id/edit` y `/users/:userId`).

## PublicProfileView

Vista pública del perfil de un publicante en `/users/:userId` (`views/public/PublicProfileView.vue`). El header (foto, nombre, badge verificado, rating, stats, CTAs) sigue siendo mock — no hay endpoint público de perfil en `users-service` todavía. El listado de propiedades ya está cableado al backend real via `fetchUserListings` + `usePropertyMapper` + `usePagination`.

### Paginación: `useProfileListings` (fetch puro) + `usePagination` (estado, compartido)

`useProfileListings.ts` se redujo a una sola función pura sin estado — `fetchUserListings(account_id, offset): Promise<{ items, hasMore }>` (`GET /v1/properties/users/{id}?offset=...`). El estado de paginación (qué página se ve, si hay anterior/siguiente, cuántos items van cargados) se movió al composable genérico `composables/shared/usePagination.ts`.

`usePagination<T>(pageSize)` expone `{ pagedItems, page, hasPrev, hasNext, hasMore, total, setItems, next, prev, reset }`:
- `setItems(items, hasMore?)` — carga (o recarga) el array completo; resetea a página 1.
- `next(fetchMore?)` — si la página siguiente ya está en memoria, solo avanza el índice (slice puro, sin red). Si está en la última página cargada y `hasMore` es `true`, espera el callback `fetchMore` (que el consumidor define — ej. un fetch por offset), acumula el resultado y recién ahí avanza. `prev()` siempre es local.
- Con esto, un mismo composable cubre tanto paginación **client-side pura** (`MyPropertiesView`, que carga todo de una vez, `fetchMore` nunca se dispara) como paginación **por red bajo demanda** (`PublicProfileView`, que sí pasa `fetchMore` porque el backend pagina por offset).

En `PublicProfileView`: `next(() => fetchUserListings(userId, total.value))` — usa `total.value` (cantidad ya cargada) como offset del siguiente fetch, más robusto que llevar un contador de páginas aparte.

**`usePagination` solo lo consumen `MyPropertiesView` y `PublicProfileView`** — `FeedView` sigue con el estado propio de `useFeed` (cursor) y `MapView` ya no pagina: es scroll infinito sobre `useFeedMap` (desde el 2026-10-09). `MyPropertiesView`, `FeedView` y `PublicProfileView` comparten el componente visual `PaginationArrows.vue` (`components/shared/`) — botones con estilo relleno/atenuado + íconos, cada view le pasa su propio `hasPrev`/`hasNext`/`@prev`/`@next` sin importar el mecanismo de paginación de fondo.

## Claims

- `src/assets/` contiene solo `logo.svg`, `reset-password.svg`, `secure-account.svg` y `landing_cover.png` ([src/assets/](frontend/src/assets)).
- `AUTH_ENTRYPOINTS` contiene `login`, `register`, `logout` y `resetPasswordConfirm` ([interceptors.ts:29-34](frontend/src/api/clients/interceptors.ts#L29-L34)).
- `main.ts` registra Pinia, vue-router, vue3-cookies y Vueform — sin axios instance global ([main.ts:15-20](frontend/src/main.ts#L15-L20)).
- `useAuthStore.checkAuth` obtiene el perfil con `usersApi.getAuthProfile()` y usa `_authChecked` para no re-disparar en cada navegación protegida ([stores/auth.ts:42-48](frontend/src/stores/auth.ts#L42-L48)).
- `useAuthStore.fillUserData()` no tiene try/catch propio — un 401 (con refresh fallido) lo maneja el interceptor de `usersApi` centralizadamente; el error que llegue a propagarse lo atrapa el `watch` de `App.vue` ([stores/auth.ts](frontend/src/stores/auth.ts), [App.vue](frontend/src/App.vue)).
- `composables/catalog/useLocation.ts` cachea countries en `localStorage` y cities/neighborhoods en `sessionStorage` ([composables/catalog/useLocation.ts](frontend/src/composables/catalog/useLocation.ts)).
- `detectLocation` usa el provider externo `ipapi.co` para inferir país por IP ([stores/user.ts:69](frontend/src/stores/user.ts#L69)).
- El guard del router llama `checkAuth()` solo si `_authChecked === false` ([router/index.ts:104-110](frontend/src/router/index.ts#L104-L110)).
- `useOnboarding` no declara estado a nivel de módulo ni importa componentes; avanza el paso con `authStore.setOnboardingStep` ([composables/onboarding/useOnboarding.ts](frontend/src/composables/onboarding/useOnboarding.ts), [stores/auth.ts:116](frontend/src/stores/auth.ts#L116)).
- Hay 4 instancias de axios dedicadas por servicio en `api/clients/`: `avm` sin `withCredentials` ni interceptor; `users`, `properties` y `catalog` con `withCredentials: true` y `applyAuthInterceptor` ([api/clients/](frontend/src/api/clients)).
- `config/index.ts` usa `VUE_APP_CATALOG_URL` si está definida y si no `/api/catalog`; `frontend/.env.development` la define como `http://localhost:8001` ([config/index.ts:3](frontend/src/config/index.ts#L3), [.env.development](frontend/.env.development)).
- `applyAuthInterceptor` intercepta 401, refresca token con POST `/v1/auth/refresh` (timeout 3s), reintenta la request original; si el refresh falla, llama `forceLogout()` ([api/clients/interceptors.ts](frontend/src/api/clients/interceptors.ts)).
- `AUTH_ENTRYPOINTS` (login, register, logout y el confirm del reset, tomados de `USERS_ENDPOINTS`) están excluidos del retry-refresh del interceptor ([api/clients/interceptors.ts:29-34](frontend/src/api/clients/interceptors.ts#L29-L34)).
- `forceLogout()` solo llama a `authStore.logout()` si `authStore.isAuthenticated` es `true` ([api/clients/interceptors.ts:35-39](frontend/src/api/clients/interceptors.ts#L35-L39)).
- `isRefreshing` y `failedQueue` en `interceptors.ts` son variables de módulo (no Vue ref ni composable) — garantizan que solo se dispare un refresh concurrente aunque múltiples requests fallen con 401 simultáneamente ([api/clients/interceptors.ts](frontend/src/api/clients/interceptors.ts)).
- El guard `!error.config` en el interceptor evita TypeError cuando `error.config` es `undefined` (request cancelada o error de red antes de que axios termine de construirla) ([api/clients/interceptors.ts](frontend/src/api/clients/interceptors.ts)).
- Las baseURLs usan rutas relativas (`/api/*`) en dev — el proxy de `vue.config.js` las reenvía a cada backend dentro del container; en prod se sobreescriben con `VUE_APP_*_URL` ([config/index.ts](frontend/src/config/index.ts), [vue.config.js](frontend/vue.config.js)).
- El proxy de webpack es necesario porque Chrome bloquea subresource requests entre puertos `localhost` distintos en un devcontainer (VS Code port forwarding + keep-alive reuse); Firefox no tiene este problema ([vue.config.js](frontend/vue.config.js)).
- `leaflet` (^1.9.4) y `@vue-leaflet/vue-leaflet` (^0.10.1) están en `devDependencies`, pero **se usan en runtime** en `MapUser.vue` — deberían moverse a `dependencies` ([package.json:35](frontend/package.json#L35), [package.json:46](frontend/package.json#L46), [components/map/MapUser.vue](frontend/src/components/map/MapUser.vue)).
- `main.ts` no contiene ninguna referencia a firebase ([main.ts](frontend/src/main.ts)).
- `MapUser.vue` es un componente de mapa dumb: vue-leaflet para mapa, tiles y el marcador `subject`, y `useMarkerCluster` para el resto de marcadores — ver [[frontend-map-component]] ([components/map/MapUser.vue](frontend/src/components/map/MapUser.vue)).
- El form del avalúo está partido en `components/avm/` (`AvmForm`, `AvmResult`) con la lógica en `composables/avm/useAvmForm.ts` ([components/avm/](frontend/src/components/avm), [composables/avm/useAvmForm.ts](frontend/src/composables/avm/useAvmForm.ts)).
- Vue está en `^3.5.35`; upgrade completado 2026-05-29 ([package.json:23](frontend/package.json#L23)).
- `useTemplateRef<T>('refName')` es el patrón Vue 3.5 para refs de template — requiere `ref="refName"` (string) en el template, no binding dinámico ([components/avm/AvmForm.vue](frontend/src/components/avm/AvmForm.vue)).
- `getNeighborhood(lat, lon)` en `useLocation.ts` hace dos requests en cadena: `catalogApi.resolveCoordinates` → `neighborhood_id`, luego `catalogApi.getNeighborhoodById` → nombre del barrio ([composables/catalog/useLocation.ts](frontend/src/composables/catalog/useLocation.ts)).
- `AvmPredictRequest` extiende `AvmFormPayload` con `lat`, `lon`, `barrio_ideca` — vive en `types/avm/predict.ts` y es el body de `POST /v1/predict` ([types/avm/predict.ts](frontend/src/types/avm/predict.ts)).
- `fetchPredict` es una función local en `AvmView` que llama `avmApi.predict(payload)` y devuelve `predicted_price` ([views/avm/AvmView.vue:124-125](frontend/src/views/avm/AvmView.vue#L124-L125)).
- `allow_origins=["*"]` es incompatible con `withCredentials: true` — el analytics-service usa `allow_origins=["http://localhost:8080"]` + `allow_credentials=True` ([analytics-service/src/app/main.py](backend/analytics-service/src/app/main.py)).
- `useFeed.load()` lee `userStore.userInterests` dentro del cuerpo de `load()`, no al inicializar el composable — garantiza que los datos del store estén frescos tras login ([composables/feed/useFeed.ts](frontend/src/composables/feed/useFeed.ts)).
- axios serializa arrays como `key[]=v` (bracket notation) por defecto; FastAPI no parsea `key[]` como el parámetro `key` — fix: `paramsSerializer: { indexes: null }` en el request de `useFeed` ([composables/feed/useFeed.ts](frontend/src/composables/feed/useFeed.ts)).
- `buildNeighborhoodMap` aplana `Object.values(getNeighborhoodsByLocalities(ids)).flat()` y arma `Record<neighborhoodId, name>` con `Object.fromEntries` ([composables/catalog/useNeighborhoodLookup.ts](frontend/src/composables/catalog/useNeighborhoodLookup.ts)).
- `useCities` es un singleton de módulo (`export const cities`) — estado compartido entre todos los componentes que lo importen en la misma sesión ([composables/catalog/useCities.ts](frontend/src/composables/catalog/useCities.ts)).
- `FeedFilters` carga barrios dinámicamente via `watch(selected, ...)` sobre las ciudades seleccionadas — llama `useNeighborhoodMultiselect.load(localities)` y resetea `selectedNeighborhoods` al cambiar ciudades ([components/properties/feed/FeedFilters.vue](frontend/src/components/properties/feed/FeedFilters.vue)).
- `FeedFilters` emite un único evento `submit` con `{ preferences, filters }` desde `onSubmit` al click en "Aplicar" — no es reactivo con `watch`; el componente no llama al backend ([components/properties/feed/FeedFilters.vue:269-278](frontend/src/components/properties/feed/FeedFilters.vue#L269-L278)).
- `toggleType(type)` en `FeedFilters` quita el tipo con `filter` si ya está en `selectedTypes` o lo agrega con `push` si no ([components/properties/feed/FeedFilters.vue:259-267](frontend/src/components/properties/feed/FeedFilters.vue#L259-L267)).
- `useFeed.load(preferences?, filters?)` usa los args si llegan y cae a `userStore.userInterests` con `preferences ?? (ternario)` si no; `fetchFeed` hace spread `{ ...preferences, ...filters, cursor? }` en los params ([composables/feed/useFeed.ts](frontend/src/composables/feed/useFeed.ts)).
- `useFeed` expone `nextCursor`, `isFirstPage`, `loadNext(cursor)` y `loadPrev()` para paginación — `loadPrev` es siempre local (sin petición al back) ([composables/feed/useFeed.ts](frontend/src/composables/feed/useFeed.ts)).
- `useProfileListings.ts` exporta solo `fetchUserListings(account_id, offset)` — función async pura, sin `ref` ni estado propio ([composables/users/useProfileListings.ts](frontend/src/composables/users/useProfileListings.ts)).
- `usePagination<T>(pageSize)` cubre paginación client-side pura y paginación por red con un mismo composable: `next(fetchMore?)` solo dispara `fetchMore` si la página pedida excede lo ya cargado y `hasMore` es `true`; si no, es un slice local ([composables/shared/usePagination.ts](frontend/src/composables/shared/usePagination.ts)).
- Solo `MyPropertiesView` y `PublicProfileView` usan `usePagination` como fuente de estado; `FeedView` usa el cursor de `useFeed` y `MapView` el scroll infinito de `useFeedMap` ([composables/shared/usePagination.ts](frontend/src/composables/shared/usePagination.ts)).
- `MyPropertiesView`, `FeedView` y `PublicProfileView` usan `PaginationArrows.vue`; `MapView` no ([components/shared/PaginationArrows.vue](frontend/src/components/shared/PaginationArrows.vue), [views/properties/feed/MapView.vue](frontend/src/views/properties/feed/MapView.vue)).
- `FeedView`, `MapView`, `MyPropertiesView` y `PublicProfileView` tienen `@click="router.push('/listing/${card.id}')"` en el `v-for` de cards ([views/properties/feed/FeedView.vue](frontend/src/views/properties/feed/FeedView.vue), [views/public/PublicProfileView.vue](frontend/src/views/public/PublicProfileView.vue)).
- `types/properties/forms.ts` contiene `CreatePropertyForm` — shape del body `POST /v1/properties/create`, incluye `location: { neighborhood_id, city_id, country_id, latitude, longitude }` ([types/properties/forms.ts](frontend/src/types/properties/forms.ts)).
- `BaseButton.vue` tiene `type` `"button"` por defecto, variante `primary` con hover `brand-primary-dark` y tamaño `xl` = `h-12 px-6 text-base`; `loading` muestra un `BaseSpinner` y deshabilita ([BaseButton.vue:39](frontend/src/components/shared/BaseButton.vue#L39), [:48](frontend/src/components/shared/BaseButton.vue#L48), [:61](frontend/src/components/shared/BaseButton.vue#L61)).
- `IconButton.vue` declara `label` como prop obligatoria y la usa como `aria-label` ([IconButton.vue:4](frontend/src/components/shared/IconButton.vue#L4), [:27](frontend/src/components/shared/IconButton.vue#L27)).
- `ChoiceChip.vue` y `OptionCard.vue` reflejan `selected` en `aria-pressed` ([ChoiceChip.vue:4](frontend/src/components/shared/ChoiceChip.vue#L4), [OptionCard.vue:4](frontend/src/components/shared/OptionCard.vue#L4)).
- No existe `components/shared/PrimaryButton.vue` ([components/shared/](frontend/src/components/shared)).
- `main.ts` importa `leaflet/dist/leaflet.css` y `main.css`, y no existe `assets/tailwind.css` ([main.ts](frontend/src/main.ts)).
- `tailwind.config.js` toma la paleta `brand` de `src/theme/brandColors.json`, que `constants/brandColors.ts` reexporta como `BRAND_COLORS` ([tailwind.config.js](frontend/tailwind.config.js), [constants/brandColors.ts](frontend/src/constants/brandColors.ts)).
- Ningún archivo de `src/` llama a `console` salvo `utils/logger.ts` ([utils/logger.ts](frontend/src/utils/logger.ts)).
- `LOCALE` de `config/index.ts` es el único lugar donde aparece `"es-CO"` ([config/index.ts](frontend/src/config/index.ts)).
- `PROPERTIES_ENDPOINTS` incluye `images(id)`, `imagesPresignedUrls` e `imagesConfirm(id)`; ninguna ruta `/v1/...` aparece fuera de `constants/*Endpoints.ts` ([constants/propertiesEndpoints.ts](frontend/src/constants/propertiesEndpoints.ts)).
- `GET /v1/search/feed` retorna `FeedPage { items: PropertyCard[], next_cursor: string | null }` ([types/feed/search.ts](frontend/src/types/feed/search.ts)).
- `PropertiesView` es la vista padre en `/feed` con el header y toggle Lista/Mapa; el estado activo del toggle se deriva de `route.name` (computed), no de un ref local ([views/properties/feed/PropertiesView.vue](frontend/src/views/properties/feed/PropertiesView.vue)).
- El `<router-view />` de `PropertiesView` está fuera del div con padding del header para evitar doble padding en las vistas hijas ([views/properties/feed/PropertiesView.vue](frontend/src/views/properties/feed/PropertiesView.vue)).
- `MapView.vue` implementa el feed-mapa: lista con scroll infinito a la izquierda y mapa con todo el bbox a la derecha, `useFeedMap` + `useInfiniteScroll` + `usePropertyMapper`, hover en ambos sentidos y bbox en la URL vía `router.replace` ([views/properties/feed/MapView.vue](frontend/src/views/properties/feed/MapView.vue)).
- `MapView` persiste el bbox en `route.query` con `router.replace` en cada `moveend` — el handler `onBbox` llama primero `router.replace({ query: bbox })` y luego `fetchByBbox`; no hay `watch` sobre `route.query` porque el mapa es el único que escribe la URL ([views/properties/feed/MapView.vue](frontend/src/views/properties/feed/MapView.vue)).
- `MapView` inicializa `center` síncronamente desde `localStorage` (clave `STORAGE_KEYS.USER_LOCATION`) para evitar la race condition de vue-leaflet; el `onMounted` solo llama `fetchByBbox` alrededor de `loc ± 0.05°` ([views/properties/feed/MapView.vue](frontend/src/views/properties/feed/MapView.vue)).
- `FeedFilters` y `FeedPreferences` viven en `types/feed/filters.ts`; `FeedPage`, `PageCache`, `FeedQuery` y `BboxPayload` en `types/feed/search.ts` ([types/feed/](frontend/src/types/feed)).
- No hay ningún import de `vuelidate` ni de `@vuelidate/*` en `src/`; `LoginView` y `RegisterView` validan con inputs nativos y `ref`, sin librería de forms ([views/auth/LoginView.vue](frontend/src/views/auth/LoginView.vue), [views/auth/RegisterView.vue](frontend/src/views/auth/RegisterView.vue)).
- Ningún template usa componentes de `@vueform/vueform` pese a estar registrado en `main.ts`; `@vueform/multiselect` sí se importa en `main.ts`, `FeedFilters.vue`, `LocalitySelector.vue` y `NeighborhoodSelector.vue` ([main.ts](frontend/src/main.ts), [components/properties/feed/FeedFilters.vue](frontend/src/components/properties/feed/FeedFilters.vue)).
- `@vueform/multiselect` no figura en `package.json` — llega como dependencia transitiva de `@vueform/vueform` ([package.json](frontend/package.json)).
- `firebase` no está en `package.json` ni hay imports de `firebase/*` en `src/` — removido el 2026-07-28 ([package.json](frontend/package.json)).
- `process.env` aparece 5 veces en `src/`, todas en `config/index.ts`; el único uso de una API específica de webpack es `require("leaflet.markercluster")` en `useMarkerCluster.ts` ([config/index.ts](frontend/src/config/index.ts), [composables/map/useMarkerCluster.ts](frontend/src/composables/map/useMarkerCluster.ts)).
- `tailwind.config.js` carga `require("@vueform/vueform/tailwind")` como plugin y escanea los temas de Vueform en `content`, lo que ata la versión de Tailwind a la que soporte Vueform ([tailwind.config.js:6-8,30](frontend/tailwind.config.js#L30)).
- `tsconfig.json` declara `baseUrl` y `resolveJsonModule` ([tsconfig.json](frontend/tsconfig.json)).
- `vue.config.js` no invoca `vue-tsc`; el `build` de `vue-cli-service` valida con ESLint, no con el compilador de tipos ([vue.config.js](frontend/vue.config.js), [package.json](frontend/package.json)).
- `.eslintrc.js` desactiva `no-undef` en `rules` ([.eslintrc.js](frontend/.eslintrc.js)).
- `formatCurrency` es la única función de formateo de moneda con símbolo, y no queda ningún `Intl.NumberFormat` ni `toLocaleString` fuera de `utils/` ([utils/money.ts](frontend/src/utils/money.ts), [utils/number.ts](frontend/src/utils/number.ts)).
- `utils/date.ts` construye su `Intl.DateTimeFormat` a nivel de módulo, no por llamada ([utils/date.ts](frontend/src/utils/date.ts)).
- `StepImagenes.vue` genera las previews con un `watch` sobre `files` (no un `computed`) y las revoca en `onUnmounted` ([StepImagenes.vue](frontend/src/components/properties/create/StepImagenes.vue)).
- Ningún archivo fuera de `src/api/` importa un cliente de `api/clients/`; composables, stores, componentes y vistas usan las funciones de `api/{users,catalog,properties,avm}.ts` y `api/admin/` ([api/](frontend/src/api)).
- `useFeedMap` solo aplica la respuesta del último bbox pedido (`latestRequest`) y la ordena con `sortForMap` ([composables/feed/useFeedMap.ts:19-31](frontend/src/composables/feed/useFeedMap.ts#L19-L31)).
- `authStore.onboardingStep` está tipado como `OnboardingStep` (`"intent" | "city" | "neighborhood" | "property_type" | "done"`) ([types/users/base.ts](frontend/src/types/users/base.ts)).
- Las rutas `/listing/:id`, `/properties/:id/edit` y `/users/:userId` declaran `props: true` ([router/routes/properties.ts:21](frontend/src/router/routes/properties.ts#L21), [router/routes/public.ts:20](frontend/src/router/routes/public.ts#L20)).
- `useResetPassword` acepta el token solo si `route.query.token` es string y lo quita de la URL con `router.replace({ query: {} })` ([useResetPassword.ts:13-15](frontend/src/composables/users/useResetPassword.ts#L13-L15)).
- `confirmPasswordReset` manda el action token en `Authorization: Bearer` solo en esa request ([api/users.ts:48](frontend/src/api/users.ts#L48)).
- La ruta `/reset-password` declara solo `hideNavbar`, sin `isLogged` ([routes/auth.ts:22-27](frontend/src/router/routes/auth.ts#L22-L27)).
- `useForgotPassword` traduce el 422 a un mensaje propio y no usa el `message` del back ([useForgotPassword.ts:19-22](frontend/src/composables/users/useForgotPassword.ts#L19-L22)).
- `BaseInput.vue` enlaza `:value="model"` y escribe el modelo en su propio `@input`, sin la directiva `v-model`; `BaseSelect.vue` usa `v-model="model"` ([BaseInput.vue:4](frontend/src/components/shared/form/BaseInput.vue#L4), [BaseSelect.vue:3](frontend/src/components/shared/form/BaseSelect.vue#L3)).
- `PasswordInput.vue` declara `inheritAttrs: false` y reenvía los attrs al `BaseInput` interno ([PasswordInput.vue:30](frontend/src/components/shared/form/PasswordInput.vue#L30)).
- `brandColors.json` define `primary-strong` como `#15803D`, y la variante `primary` de `BaseButton` usa `bg-brand-primary-strong` ([brandColors.json:14](frontend/src/theme/brandColors.json#L14), [BaseButton.vue:48](frontend/src/components/shared/BaseButton.vue#L48)).
- `tailwind.config.js` carga `@vueform/vueform/tailwind`, cuyo `tailwind.js` incluye la regla de base de formularios con `[type='datetime-local']` ([tailwind.config.js:23](frontend/tailwind.config.js#L23)).
- Los checkbox de `LocalityFormFields` y `CountryFormFields` llevan `appearance-auto` ([LocalityFormFields.vue:104](frontend/src/components/admin/catalog/localities/widgets/LocalityFormFields.vue#L104), [CountryFormFields.vue:104](frontend/src/components/admin/catalog/countries/widgets/CountryFormFields.vue#L104)).
