---
title: Arquitectura interna del frontend
status: draft
last-verified: 2026-07-15
owners: [frontend]
related:
  - "[[architecture]]"
  - "[[frontend]]"
  - "[[frontend-onboarding-flow]]"
  - "[[frontend-map-component]]"
  - "[[frontend-poi-reachable]]"
  - "[[frontend-property-create-form]]"
  - "[[frontend-property-edit-form]]"
  - "[[properties-service-search]]"
  - "[[open-items]]"
sources:
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
---

## TL;DR

SPA Vue 3 + TypeScript organizada en `views/` (páginas-ruta), `components/` (presentación reusable), `stores/` (Pinia, estado global), `composables/` (lógica reusable async), `types/` (DTOs) y `config/` (env). Sin "service layer" formal — los stores y composables hacen HTTP directo con axios. Caching local manual en `localStorage`/`sessionStorage`. Auth cookie-based con `withCredentials: true`. Router con guard global de auth.

## Layout

```
frontend/
├── public/                       # index.html, favicon
├── src/
│   ├── App.vue                   # root: NavBar + router-view + onboarding modal
│   ├── main.ts                   # createApp + use(pinia, router, VueCookies, Vueform)
│   ├── shims-vue.d.ts            # types para imports .vue
│   ├── assets/                   # tailwind.css, logo, etc.
│   ├── config/
│   │   └── index.ts              # API.USERS_BASE_URL, CATALOG_BASE_URL, AVM_BASE_URL (port 8002), STORAGE_KEYS
│   ├── router/
│   │   ├── index.ts              # instancia router + beforeEach guard; importa 5 módulos
│   │   └── routes/
│   │       ├── public.ts         # /, /about, /users/:userId
│   │       ├── auth.ts           # /login, /register, /forgot-password
│   │       ├── settings.ts       # /settings + children
│   │       ├── properties.ts     # /properties, /listing/:id, /feed + children
│   │       └── analytics.ts      # /avm
│   ├── stores/                   # Pinia
│   │   ├── auth.ts
│   │   └── user.ts
│   ├── composables/
│   │   ├── useOnboarding.ts
│   │   ├── Location.ts
│   │   ├── pois/
│   │   │   └── useReachablePois.ts    # POIs alcanzables desde una propiedad (3 perfiles × 3 rangos)
│   │   ├── shared/
│   │   │   └── usePagination.ts       # slice client-side genérico; opcionalmente pagina por red vía fetchMore
│   │   ├── properties/
│   │   │   ├── usePropertyDetail.ts   # computed logic de PropertyDetailView
│   │   │   ├── usePropertyMapper.ts   # PropertyCard → PropertyCardUI con lookup de barrio
│   │   │   ├── usePropertyVisibility.ts  # toggleVisibility(id): Promise<boolean>, sin estado
│   │   │   └── useMyProperties.ts     # { properties, isLoading, fetchProperties } — mismo molde que useFeed
│   │   └── users/
│   │       └── useProfileListings.ts  # fetchUserListings(id, offset) — función pura, sin estado (la paginación vive en usePagination)
│   ├── utils/
│   │   └── money.ts               # formatMoney / parseMoney — compartido entre create y edit form
│   ├── constants/
│   │   ├── propertyStatus.ts      # LISTING_STATUS_LABELS / LISTING_STATUS_BADGE_CLASSES
│   │   ├── pagination.ts          # PAGE_SIZE por vista (MY_PROPERTIES, PUBLIC_PROFILE)
│   │   └── propertiesEndpoints.ts # paths de properties-service (me, byId, byUser, visibility, images)
│   ├── types/
│   │   ├── user.ts
│   │   ├── feed.ts               # PropertyCard (API shape), PropertyCardUI (UI shape), PropertyImageCard, ListingStatus
│   │   ├── properties.ts         # PropertyDetail, PropertyLocationDetail, CreatePropertyForm, PropertyEditForm
│   │   └── pois.ts               # OrsProfile, GeoJsonPolygon, ReachablePoiItem, RangeGroup, CATEGORY_META, CATEGORY_PRIORITY
│   ├── views/                    # páginas-ruta
│   │   ├── public/{HomeView, AboutView, PublicProfileView}  # /users/:userId
│   │   ├── auth/{LoginView, RegisterView, ResetPasswordView}
│   │   ├── settings/{SettingsLayout, SettingsProfile, SettingsSecurity, SettingsAccount}
│   │   ├── properties/
│   │   │   ├── PropertiesView.vue          # parent feed con toggle lista/mapa
│   │   │   ├── feed/{FeedView, MapView}
│   │   │   ├── dashboard/MyPropertiesView
│   │   │   ├── detail/PropertyDetailView   # /listing/:id
│   │   │   └── edit/EditPropertyView       # /properties/:id/edit — ver [[frontend-property-edit-form]]
│   │   └── dev/{DevPlaygroundView, CreatePropertyDevView}  # sin auth, dev only
│   └── components/
│       ├── shared/{NavBar, NavGuest, NavUser, BaseModal, BaseSpinner, PaginationArrows, FilterTabs, EmptyState, PrimaryButton}
│       ├── onboarding/{IntentSelector, LocalitySelector, NeighborhoodSelector, PropertyTypeSelector}
│       ├── properties/
│       │   ├── cards/{PropertyCard, HouseCard}      # HouseCard sin uso actual
│       │   ├── photos/{PropertyPhotoGrid, PhotoGalleryPopup}
│       │   ├── detail/{PropertyOverview, NearbyPlaces}
│       │   ├── dashboard/DeletePropertyModal        # envuelve BaseModal, autocontenido (DELETE + loading)
│       │   ├── edit/{PropertyHeaderCard, PropertyPhotosCard, PropertyInfoCard, PropertyEditForm, PropertyEditActions, UploadPropertyImagesModal, DeletePropertyImagesModal}
│       │   └── feed/FeedFilters
│       ├── settings/SettingsSidebar
│       └── map/MapUser
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
- **Firebase NO se inicializa acá** — la initialización está comentada (`initializeApp(firebaseConfig)`). Se llama on-demand desde `LoginView.loginWithGoogle()`.
- **Vueform** se registra global; sus formularios se usan en views como `RegisterView`.
- Sin axios instance global — cada store/composable crea/usa el axios default.

## Stores Pinia

### `useAuthStore` ([stores/auth.ts](frontend/src/stores/auth.ts))

State:
```ts
user: User | null
isAuthenticated: boolean
isLoading: boolean
_authChecked: boolean    // guard contra checkAuth duplicado en navegación
```

Actions:
- `checkAuth(force=false)`: GET `/v1/users/me/profile` con `withCredentials`. Setea `_authChecked` para no re-llamar en cada navegación.
- `login(email, password)`: POST `/v1/auth/login` → cookie llega del backend → `checkAuth(force=true)`.
- `register(userData)`: POST `/v1/auth/register` → idem login post-success.
- `logout()`: POST `/v1/auth/logout` → resetea ambos stores → `router.push("/")`. Marca `_authChecked=true` post-logout para evitar que el guard re-dispare durante la transición.

Getters: `fullName`, `isOrganization`, `userAvatar` (default a `ui-avatars.com`).

> ⚠ URLs hardcoded en `localhost:8000` — no usa el `API.USERS_BASE_URL` del config. Pendiente de centralizar.

### `useUserStore` ([stores/user.ts](frontend/src/stores/user.ts))

State del onboarding y datos derivados:
```ts
onboardingStep: "intent" | "city" | "neighborhood" | "property_type" | "done"
hasCheckedOnboarding: boolean
userDismissedModal: boolean    // hidratado de sessionStorage
userInterests: { localities, neighborhoods, properties }
```

Actions clave:
- `checkOnboardingStep()`: GET `/v1/users/me/` → setea `onboardingStep` desde `data.onboarding_step`. Si 401 → llama `authStore.logout()`.
- `checkInterests()`: GET `/v1/users/me/interests` → cachea en store.
- `detectLocation()`: usa **ipapi.co** (third-party) para inferir país por IP. Cachea en `localStorage`.
- `dismissModal()`: marca onboarding como dismiss en sessionStorage.
- `logoutReset()`: limpia todo (usado desde `useAuthStore.logout`).

> Patrón de manejo de 401: en cada action, si 401 → `authStore.logout()`. Acoplamiento entre stores.

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

Gestiona el feed del mapa con fetch por bbox y paginación local:

- `fetchByBbox(payload: BboxPayload)` — `GET /v1/search/feed/map` con `{ min_lat, max_lat, min_lon, max_lon, resolution }`. `resolution`: zoom≥15 → H3 r9 (~300m), zoom<15 → H3 r7 (~5km). Guarda todos los resultados en `_allItems` con Fisher-Yates shuffle (desegrega agrupamiento por celda H3).
- `PAGE_SIZE` — `computed` (no constante): zoom≥15 → 20, zoom<14 → 40. Reactivo a cambios de zoom.
- `items` — `computed` que slice `_allItems` según `page.value` y `PAGE_SIZE`.
- `next()` / `prev()` — paginación local (sin petición al back).
- `page` se resetea a 0 en cada nuevo `fetchByBbox`.

Diferencia clave con `useFeed`: no usa cursor — la paginación es client-side sobre la respuesta completa del bbox.

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

Orquesta el modal de onboarding:
- `STEP_MAP`: `{ intent, city, neighborhood, property_type }` → componente Vue.
- `activeComponent: shallowRef<Component | null>` — qué selector renderizar.
- `isModalOpen: ref<boolean>`.
- `startFlow()`: chequea `userDismissedModal` + `checkOnboardingStep()`; si step != "done" y matchea STEP_MAP, abre modal.
- `closeFlow()`: cierra modal + `userStore.dismissModal()`.
- `saveCity(localities)`: POST `/v1/onboarding/city` → avanza a "neighborhood".
- `saveNeighborhoods(localities)`: POST `/v1/onboarding/neighborhood` → avanza a "property_type".

Detalle en [[frontend-onboarding-flow]].

### `Location.ts` ([composables/Location.ts](frontend/src/composables/Location.ts))

Funciones puras (no es composable Vue strictly hablando, son helpers que aceptan parámetros):
- `getCitiesByCountry(id)`: GET `/v1/localities/by-country` → cachea por country en `sessionStorage`.
- `getNeighborhoodsByLocalities(localityIds)`: GET `/v1/neighborhoods/by-localities` con dedup de cached vs missing. Cachea por locality en `sessionStorage`.
- `locations()`: combina `detectLocation` (ipapi) + `countries` (catalog) → devuelve `(countryDetected, countryUser)`.
- `getNeighborhood(lat, lon)`: dos requests en cadena — GET `/v1/geo-resolution/by-coordinates` → `neighborhood_id`, luego GET `/v1/neighborhoods/by-id` → retorna `name` (string). Usado por `useAvmForm` para mostrar el barrio detectado al seleccionar dirección.

## Router con guard global

`router.beforeEach`:
1. Si la ruta es `isLogged: true` (guest-only) y `isAuthenticated` → redirige a `/`.
2. Si `requiresAuth: true` y `!_authChecked` → `await authStore.checkAuth()`.
3. Si `requiresAuth && !isAuthenticated` → redirige a `/login`.

Hash history (`createWebHashHistory`) — ver [[adr-hash-history-static-hosting]].

## API consumption pattern

**Instancias dedicadas por servicio** — cada servicio tiene su propia instancia de axios en `src/api/`:

| Archivo | baseURL (dev) | `withCredentials` | Auth interceptor |
|---|---|---|---|
| `catalogApi.ts` | `/api/catalog` | No | No — catálogo es público |
| `avmApi.ts` | `/api/avm` | No | No — sin auth hoy |
| `usersApi.ts` | `/api/users` | Sí | Sí |
| `propertiesApi.ts` | `/api/properties` | Sí | Sí |

`auth.ts` (store Pinia) sigue usando `usersApi` directamente para login/register/logout/checkAuth.

Las baseURLs son rutas relativas (proxy en dev) — ver sección "Webpack devServer proxy".

### Silent refresh interceptor (`src/api/interceptors.ts`)

`applyAuthInterceptor(instance)` se llama en `usersApi` y `propertiesApi`. Comportamiento:

```
response 401
  └─ !error.config → reject inmediato (error sin config = cancelado/red)
  └─ original._retry → reject (evita loop infinito en el retry)
  └─ isRefreshing === true → encolar en failedQueue; resolver/rechazar cuando termine el refresh en curso
  └─ isRefreshing === false →
       original._retry = true
       isRefreshing = true
       POST /v1/auth/refresh (timeout 3s, withCredentials)
         ├─ éxito → processQueue(null) → retry instance(original)
         └─ fallo → processQueue(error) → redirectToLogin() → reject
       finally: isRefreshing = false
```

**`isRefreshing` y `failedQueue` son module-level** (declarados fuera de cualquier función o composable Vue), no instancia-por-componente. Esto es intencional: sobreviven al desmonte/remonte de componentes. Si fueran `ref` dentro de un composable, cada componente tendría su propio flag y podrían dispararse múltiples refresh concurrentes.

**`!error.config` guard**: `error.config` puede ser `undefined` cuando el error ocurre antes de que axios haya terminado de construir la request (red caída, request cancelada). Sin el guard, `original._retry` lanzaría un TypeError. El guard hace `return Promise.reject(error)` inmediatamente en ese caso.

**Timeout de 3s en refresh**: si users-service no responde, el refresh falla rápido en vez de colgar indefinidamente — la request original termina rechazada y el usuario es redirigido a login.

### Webpack devServer proxy

Las baseURLs usan rutas relativas (`/api/users`, `/api/catalog`, etc.) para desarrollo. `vue.config.js` configura el proxy:

```js
devServer: {
  proxy: {
    "/api/users":      { target: "http://localhost:8000", changeOrigin: true, pathRewrite: { "^/api/users": "" } },
    "/api/catalog":    { target: "http://localhost:8001", changeOrigin: true, pathRewrite: { "^/api/catalog": "" } },
    "/api/avm":        { target: "http://localhost:8002", changeOrigin: true, pathRewrite: { "^/api/avm": "" } },
    "/api/properties": { target: "http://localhost:8003", changeOrigin: true, pathRewrite: { "^/api/properties": "" } },
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
| `onboarding_dismissed` | `sessionStorage` | Por sesión |

Keys centralizadas en `STORAGE_KEYS` del `config/index.ts`. No hay invalidación explícita — depende del clear del browser.

## Components organization

| Carpeta | Propósito |
|---|---|
| `shared/` | NavBar, NavGuest (no-logged), NavUser (logged), BaseModal, PrimaryButton (botón gradiente verde reusable, presentacional puro) — reusables transversales. |
| `onboarding/` | 4 selectors (Intent, Locality, Neighborhood, PropertyType) — usados desde el modal. |
| `properties/` | Organizado en subcarpetas por dominio desde 2026-06-21. `cards/{PropertyCard, HouseCard}` — cards para feed (`HouseCard` sin uso actual). `photos/{PropertyPhotoGrid, PhotoGalleryPopup}`. `detail/{PropertyOverview, NearbyPlaces}`. `feed/FeedFilters` — sidebar de filtros con secciones Preferencias (ciudad, barrio, tipo) y Filtros (precio, área, habitaciones, baños); se pre-pobla con ciudades de `useCities`, barrios cargados dinámicamente al seleccionar ciudad vía `watch`. Mantiene estado local (`selected`, `selectedNeighborhoods`, `selectedTypes`, `filters: ref<FeedFilters>({})` con `v-model.number`); `property_types` se togglea con `toggleType(type)` (push/filter sobre el array). **Emite un solo `submit` con `{preferences, filters}` al click en "Aplicar"** — no reactivo con `watch`, decisión para evitar una petición por cada cambio de campo. El objeto `preferences` se arma en `onSubmit` leyendo los refs (`selected.value`, etc.), sin ref `preferences` duplicado. |
| `settings/` | SettingsSidebar — navegación lateral del SettingsLayout. |
| `map/` | MapUser — componente de mapa dumb/reusable (vue-leaflet declarativo, markers-prop + slot). Ver [[frontend-map-component]]. |
| `avm/` | AvmForm / AvmResult — form del avalúo multi-step. `AvmForm` consume `composables/useAvmForm` (expone `AvmFormPayload`, `AvmPredictRequest`, `SelectedPlace`). Emite `place-selected` (marker en tiempo real) y `submit` (payload + place + neighborhood resuelto). `DevPlaygroundView` orquesta: recibe `place-selected` → actualiza `center` y `marker` reactivos → pasa al mapa. |

## Estilos: Tailwind + diseño tokens

- Tailwind 3 con clases utility directas en templates.
- Custom utilities/colors en `tailwind.config.js` — usa nombres tipo `brand-primary`, `brand-text`, `brand-bg`, `brand-muted`, `brand-divider`, `brand-placeholder`, `brand-border` (vistos en `LoginView`).
- `assets/tailwind.css` y `main.css` cargados en `main.ts`.
- Sin component library tipo Element Plus — todos los componentes son custom.

## Forms

Dos sistemas conviven hoy:

1. **Vueform**: registrado global, se usa en views complejas (probable: register, settings forms). Es una librería con **plan free limitado** — uso comercial avanzado requiere licencia.
2. **Custom inputs + Vuelidate**: vistos en `LoginView` (inputs nativos con clases Tailwind, validación con `@vuelidate/core` + `@vuelidate/validators`).

Coexistencia es deuda — pendiente decidir si todo va a Vueform (con consideración de licencia) o todo a custom.

## Mapas y geocoding

Ver [[adr-mapbox-geocoding-leaflet-rendering]] para el detalle. Resumen:

- **Render del mapa**: Leaflet + `@vue-leaflet/vue-leaflet` (wrapper Vue) + **D3.js** para overlays/data visualization.
- **Forward geocoding** (address → lat/lon): **Google Maps Places API (New)** — `PlaceAutocompleteElement` en el frontend, sin pasar por el backend. Reemplazó a Mapbox (calidad insuficiente en Colombia). Ver [[adr-gmaps-places-geocoding]].
- **Reverse geocoding** (lat/lon → barrio): el frontend pasa el `(lat, lon)` al backend (catalog-service `/by-coordinates`).

El render lo encapsula `MapUser.vue` — un componente **dumb/reusable**: props in (`center`, `markers` tipados, `zoom` vía `v-model`/`defineModel`) + un `<slot>` para capas extra; los iconos de marker son data-driven (`public/icons/<imageType>.svg`). No tiene lógica de negocio ni de auth. Detalle completo en [[frontend-map-component]].

## Build & tooling

- **Vue 3.5.35** (upgrade completado 2026-05-29) — habilita `defineModel` y `useTemplateRef`. Es **independiente** de la migración a Vite, que sigue diferida (ver [[adr-vue-cli-deferred-vite-migration]]).
- **`useTemplateRef`** (Vue 3.5): reemplaza `ref<HTMLElement>(null)` para refs de template. Sintaxis: `useTemplateRef<HTMLDivElement>('refName')` — el template usa `ref="refName"` (string, no binding dinámico).
- **Build**: `npm run build` (vue-cli-service) → `dist/` estático.
- **Deploy planeado**: bucket público (probable S3 / MinIO / GCS) sirviendo `index.html` + assets. Hash history evita necesidad de rewrites en el bucket.
- **Sin SSR** — pura SPA client-side.

## Tipos — separación UI vs API

`types/feed.ts` tiene dos shapes distintas:
- `PropertyCard` — response shape de la API de properties-service.
- `PropertyCardUI` — shape para render del card en feed (UI). Antes vivía como `Property` en `PropertyCard.vue` — causaba TS2614 al importar desde `.ts` files.
- `PropertyImageCard` — imagen de una propiedad, compartida por feed y detail.

`types/properties.ts`:
- `PropertyDetail` — shape completa del response `GET /v1/properties/{id}`.
- `PropertyLocationDetail` — ubicación (neighborhood_id, city_id, country_id, lat, lon). Usa `city_id` — es el campo de properties-service, distinto al rename `locality_id` de catalog-service.

Regla: nunca exportar interfaces de tipos desde archivos `.vue` — rompe TypeScript en consumers `.ts`.

## PropertyDetailView

Vista de detalle del listing en `/listing/:id` (`views/properties/detail/PropertyDetailView.vue`). Refactorizada (2026-06-20) para que la view **solo orqueste**: un `property = ref<PropertyDetail | null>`, el composable `usePropertyDetail`, y 3 componentes hijos que reciben los datos ya resueltos.

- **`PropertyPhotoGrid.vue`** (`components/properties/photos/`) — grid de fotos (`grid grid-cols-4 grid-rows-[200px_200px]`, `grid-area` en `<style scoped>` porque Tailwind arbitrary values no funciona con clases dinámicas en `v-for`). Es padre de **`PhotoGalleryPopup.vue`** (carrusel `vue3-carousel` dentro de `BaseModal` con `size="3xl"`) — patrón props-down/events-up: el popup nunca muta el prop `isOpen`, solo emite `close`.
- **`PropertyOverview.vue`** — header + precio + stats chips + descripción + detalles secundarios. Cero lógica propia, todo via props que mapean 1:1 a lo que devuelve `usePropertyDetail` (incluye `hasAdminFee`/`description` como `computed`, y `locationLabel` resuelto en la view con el mismo patrón de `buildNeighborhoodMap` que usan las cards del feed).
- **`NearbyPlaces.vue`** — sección "Cerca del lugar" (perfiles, acordeón POI, mapa, isocronas, leyenda). Ver [[frontend-poi-reachable]] — a diferencia de los otros dos, es dueño de su propio `useReachablePois` (recibe `lat`/`lon`/`propertyId`, resuelve interno).
- **Padding de la view**: `px-[8%] sm:px-[12%] lg:px-[18%]` — más estrecho que navbar para dar respiro visual.
- **Lógica de detalle**: `composables/properties/usePropertyDetail.ts` — la view solo destructura el composable.
- **Location label**: `buildNeighborhoodMap` (`composables/catalog/useNeighborhoodLookup.ts`) resuelto en `onMounted` de la view tras cargar la propiedad — resuelve barrio, no ciudad.
- **Fetch real**: `propertiesApi.get<PropertyDetail>('/v1/properties/${route.params.id}')` usando el `id` de la ruta (`/listing/:id`) — reemplaza el mock hardcodeado que tenía antes.

## PublicProfileView

Vista pública del perfil de un publicante en `/users/:userId` (`views/public/PublicProfileView.vue`). El header (foto, nombre, badge verificado, rating, stats, CTAs) sigue siendo mock — no hay endpoint público de perfil en `users-service` todavía. El listado de propiedades ya está cableado al backend real via `fetchUserListings` + `usePropertyMapper` + `usePagination`.

### Paginación: `useProfileListings` (fetch puro) + `usePagination` (estado, compartido)

`useProfileListings.ts` se redujo a una sola función pura sin estado — `fetchUserListings(account_id, offset): Promise<{ items, hasMore }>` (`GET /v1/properties/users/{id}?offset=...`). El estado de paginación (qué página se ve, si hay anterior/siguiente, cuántos items van cargados) se movió al composable genérico `composables/shared/usePagination.ts`.

`usePagination<T>(pageSize)` expone `{ pagedItems, page, hasPrev, hasNext, hasMore, total, setItems, next, prev, reset }`:
- `setItems(items, hasMore?)` — carga (o recarga) el array completo; resetea a página 1.
- `next(fetchMore?)` — si la página siguiente ya está en memoria, solo avanza el índice (slice puro, sin red). Si está en la última página cargada y `hasMore` es `true`, espera el callback `fetchMore` (que el consumidor define — ej. un fetch por offset), acumula el resultado y recién ahí avanza. `prev()` siempre es local.
- Con esto, un mismo composable cubre tanto paginación **client-side pura** (`MyPropertiesView`, que carga todo de una vez, `fetchMore` nunca se dispara) como paginación **por red bajo demanda** (`PublicProfileView`, que sí pasa `fetchMore` porque el backend pagina por offset).

En `PublicProfileView`: `next(() => fetchUserListings(userId, total.value))` — usa `total.value` (cantidad ya cargada) como offset del siguiente fetch, más robusto que llevar un contador de páginas aparte.

**`usePagination` solo lo consumen `MyPropertiesView` y `PublicProfileView`** — `FeedView` sigue con el estado propio de `useFeed` (cursor) y `MapView` con el de `useFeedMap` (bbox + slice local), cada uno con su propia noción de "página". Lo que **sí** comparten los cuatro es el componente visual `PaginationArrows.vue` (`components/shared/`) — botones con estilo relleno/atenuado + íconos, cada view le pasa su propio `hasPrev`/`hasNext`/`@prev`/`@next` sin importar el mecanismo de paginación de fondo.

## Claims

- `main.ts` registra Pinia, vue-router, vue3-cookies y Vueform — sin axios instance global ([main.ts:15-20](frontend/src/main.ts#L15-L20)).
- `useAuthStore.checkAuth` envía `withCredentials: true` y usa `_authChecked` para no re-disparar en cada navegación protegida ([stores/auth.ts:73-94](frontend/src/stores/auth.ts#L73-L94)).
- `useUserStore.checkOnboardingStep` llama `authStore.logout()` si recibe 401 — acoplamiento entre stores para manejar expiración de sesión ([stores/user.ts:42-43](frontend/src/stores/user.ts#L42-L43)).
- `composables/Location.ts` cachea countries en `localStorage` y cities/neighborhoods en `sessionStorage` ([composables/Location.ts:7-9](frontend/src/composables/Location.ts#L7-L9), [composables/Location.ts:28-30](frontend/src/composables/Location.ts#L28-L30)).
- `detectLocation` usa el provider externo `ipapi.co` para inferir país por IP ([stores/user.ts:69](frontend/src/stores/user.ts#L69)).
- El guard del router llama `checkAuth()` solo si `_authChecked === false` ([router/index.ts:104-110](frontend/src/router/index.ts#L104-L110)).
- `useOnboarding` mantiene `activeComponent` como `shallowRef<Component | null>` — `shallowRef` porque los componentes Vue son reactivos por sí solos ([composables/useOnboarding.ts:19](frontend/src/composables/useOnboarding.ts#L19)).
- Hay 4 instancias de axios dedicadas por servicio: `catalogApi` y `avmApi` (sin `withCredentials`, sin interceptor — son APIs públicas); `usersApi` y `propertiesApi` (con `withCredentials: true` y `applyAuthInterceptor`) ([api/](frontend/src/api/)).
- `applyAuthInterceptor` intercepta 401, refresca token con POST `/v1/auth/refresh` (timeout 3s), reintenta la request original; si el refresh falla, redirige a login ([api/interceptors.ts](frontend/src/api/interceptors.ts)).
- `isRefreshing` y `failedQueue` en `interceptors.ts` son variables de módulo (no Vue ref ni composable) — sobreviven al ciclo de vida de los componentes y garantizan que solo se dispare un refresh concurrente aunque múltiples requests fallen con 401 simultáneamente ([api/interceptors.ts:6-11](frontend/src/api/interceptors.ts#L6-L11)).
- El guard `!error.config` en el interceptor evita TypeError cuando `error.config` es `undefined` (request cancelada o error de red antes de que axios termine de construirla) ([api/interceptors.ts:39](frontend/src/api/interceptors.ts#L39)).
- Las baseURLs usan rutas relativas (`/api/*`) en dev — el proxy de `vue.config.js` las reenvía a cada backend dentro del container; en prod se sobreescriben con `VUE_APP_*_URL` ([config/index.ts](frontend/src/config/index.ts), [vue.config.js](frontend/vue.config.js)).
- El proxy de webpack es necesario porque Chrome bloquea subresource requests entre puertos `localhost` distintos en un devcontainer (VS Code port forwarding + keep-alive reuse); Firefox no tiene este problema ([vue.config.js](frontend/vue.config.js)).
- `leaflet` (^1.9.4) y `@vue-leaflet/vue-leaflet` (^0.10.1) están en `devDependencies`, pero **se usan en runtime** en `MapUser.vue` — deberían moverse a `dependencies` ([package.json:35](frontend/package.json#L35), [package.json:46](frontend/package.json#L46), [components/map/MapUser.vue](frontend/src/components/map/MapUser.vue)).
- Firebase NO se inicializa en `main.ts` — el `initializeApp(firebaseConfig)` está comentado ([main.ts:14](frontend/src/main.ts#L14)).
- `MapUser.vue` es un componente de mapa dumb (vue-leaflet declarativo, props + `<slot>`, `defineModel` para zoom) — ver [[frontend-map-component]] ([components/map/MapUser.vue](frontend/src/components/map/MapUser.vue)).
- El form del avalúo está partido en `components/avm/` (`AvmForm`, `AvmResult`, `AvmMap`) con la lógica en `composables/useAvmForm.ts` ([components/avm/](frontend/src/components/avm), [composables/useAvmForm.ts](frontend/src/composables/useAvmForm.ts)).
- Vue está en `^3.5.35`; upgrade completado 2026-05-29 ([package.json:23](frontend/package.json#L23)).
- `useTemplateRef<T>('refName')` es el patrón Vue 3.5 para refs de template — requiere `ref="refName"` (string) en el template, no binding dinámico ([components/avm/AvmForm.vue](frontend/src/components/avm/AvmForm.vue)).
- `getNeighborhood(lat, lon)` en `Location.ts` hace dos requests en cadena: `/geo-resolution/by-coordinates` → `neighborhood_id`, luego `/neighborhoods/by-id` → nombre del barrio ([composables/Location.ts](frontend/src/composables/Location.ts)).
- `AvmPredictRequest` extiende `AvmFormPayload` con `lat`, `lon`, `barrio_ideca` — vive en `composables/useAvmForm.ts` y es el shape del body de `POST /v1/predict` ([composables/useAvmForm.ts](frontend/src/composables/useAvmForm.ts)).
- `fetchPredict` es una función local en `DevPlaygroundView` (no composable) porque es una sola call sin estado compartido — patrón: `axios.post(AVM_BASE_URL/v1/predict, payload, { withCredentials: true })` → retorna `res.data.predicted_price` ([views/dev/DevPlaygroundView.vue](frontend/src/views/dev/DevPlaygroundView.vue)).
- `allow_origins=["*"]` es incompatible con `withCredentials: true` — el analytics-service usa `allow_origins=["http://localhost:8080"]` + `allow_credentials=True` ([analytics-service/src/app/main.py](backend/analytics-service/src/app/main.py)).
- `useFeed.load()` lee `userStore.userInterests` dentro del cuerpo de `load()`, no al inicializar el composable — garantiza que los datos del store estén frescos tras login ([composables/feed/useFeed.ts](frontend/src/composables/feed/useFeed.ts)).
- axios serializa arrays como `key[]=v` (bracket notation) por defecto; FastAPI no parsea `key[]` como el parámetro `key` — fix: `paramsSerializer: { indexes: null }` en el request de `useFeed` ([composables/feed/useFeed.ts](frontend/src/composables/feed/useFeed.ts)).
- `buildNeighborhoodMap` aplana `Object.values(getNeighborhoodsByLocalities(ids)).flat()` y reduce a `Record<neighborhoodId, name>` — lookup O(1) usado en `toCard` de `FeedView` ([composables/catalog/useNeighborhoodLookup.ts](frontend/src/composables/catalog/useNeighborhoodLookup.ts)).
- `useCities` es un singleton de módulo (`export const cities`) — estado compartido entre todos los componentes que lo importen en la misma sesión ([composables/catalog/useCities.ts](frontend/src/composables/catalog/useCities.ts)).
- `FeedFilters` carga barrios dinámicamente via `watch(selected, ...)` sobre las ciudades seleccionadas — llama `useNeighborhoodMultiselect.load(localities)` y resetea `selectedNeighborhoods` al cambiar ciudades ([components/properties/feed/FeedFilters.vue](frontend/src/components/properties/feed/FeedFilters.vue)).
- `FeedFilters` emite un único evento `submit` con `{ preferences, filters }` desde `onSubmit` al click en "Aplicar" — no es reactivo con `watch`; el componente no llama al backend ([components/properties/feed/FeedFilters.vue:269-278](frontend/src/components/properties/feed/FeedFilters.vue#L269-L278)).
- `toggleType(type)` en `FeedFilters` quita el tipo con `filter` si ya está en `selectedTypes` o lo agrega con `push` si no ([components/properties/feed/FeedFilters.vue:259-267](frontend/src/components/properties/feed/FeedFilters.vue#L259-L267)).
- `useFeed.load(preferences?, filters?)` usa los args si llegan y cae a `userStore.userInterests` con `preferences ?? (ternario)` si no; `fetchFeed` hace spread `{ ...preferences, ...filters, cursor? }` en los params ([composables/feed/useFeed.ts](frontend/src/composables/feed/useFeed.ts)).
- `useFeed` expone `nextCursor`, `isFirstPage`, `loadNext(cursor)` y `loadPrev()` para paginación — `loadPrev` es siempre local (sin petición al back) ([composables/feed/useFeed.ts](frontend/src/composables/feed/useFeed.ts)).
- `useProfileListings.ts` exporta solo `fetchUserListings(account_id, offset)` — función async pura, sin `ref` ni estado propio ([composables/users/useProfileListings.ts](frontend/src/composables/users/useProfileListings.ts)).
- `usePagination<T>(pageSize)` cubre paginación client-side pura y paginación por red con un mismo composable: `next(fetchMore?)` solo dispara `fetchMore` si la página pedida excede lo ya cargado y `hasMore` es `true`; si no, es un slice local ([composables/shared/usePagination.ts](frontend/src/composables/shared/usePagination.ts)).
- Solo `MyPropertiesView` y `PublicProfileView` usan `usePagination` como fuente de estado — `MyPropertiesView` nunca pasa `fetchMore` (ya tiene todo cargado), `PublicProfileView` sí, porque el backend pagina por offset. `FeedView` (cursor, `useFeed`) y `MapView` (bbox + slice, `useFeedMap`) mantienen su propio estado de paginación ([composables/shared/usePagination.ts](frontend/src/composables/shared/usePagination.ts)).
- Las 4 views (`MyPropertiesView`, `FeedView`, `MapView`, `PublicProfileView`) comparten el componente visual `PaginationArrows.vue`, independiente del composable de estado que use cada una ([components/shared/PaginationArrows.vue](frontend/src/components/shared/PaginationArrows.vue)).
- `FeedView`, `MapView`, `MyPropertiesView` y `PublicProfileView` tienen `@click="router.push('/listing/${card.id}')"` en el `v-for` de cards ([views/properties/feed/FeedView.vue](frontend/src/views/properties/feed/FeedView.vue), [views/public/PublicProfileView.vue](frontend/src/views/public/PublicProfileView.vue)).
- `types/properties.ts` contiene `CreatePropertyForm` — shape del body `POST /v1/properties`, incluye `location: { neighborhood_id, city_id, country_id, latitude, longitude }` ([types/properties.ts](frontend/src/types/properties.ts)).
- `PrimaryButton.vue` (`components/shared/`) encapsula el gradiente verde reusado en botones de acción principal (Guardar cambios, Subir fotos, Agregar fotos) — recibe `disabled` + slot; `class` y `@click` se reenvían al `<button>` interno vía attrs fallthrough de Vue, sin declararlos como props explícitos ([components/shared/PrimaryButton.vue](frontend/src/components/shared/PrimaryButton.vue)).
- `PROPERTIES_ENDPOINTS` incluye `images(id)` para el batch delete de fotos — los endpoints de presigned-urls/confirm siguen inline como string literals en `useImageUpload.ts`, no centralizados en este archivo de constants ([constants/propertiesEndpoints.ts](frontend/src/constants/propertiesEndpoints.ts)).
- `GET /v1/search/feed` retorna `FeedPage { items: PropertyCard[], next_cursor: string | null }` — el composable desempaqueta `.items` ([types/feed.ts](frontend/src/types/feed.ts)).
- `PropertiesView` es la vista padre en `/feed` con el header y toggle Lista/Mapa; el estado activo del toggle se deriva de `route.name` (computed), no de un ref local ([views/properties/PropertiesView.vue](frontend/src/views/properties/PropertiesView.vue)).
- El `<router-view />` de `PropertiesView` está fuera del div con padding del header para evitar doble padding en las vistas hijas ([views/properties/PropertiesView.vue](frontend/src/views/properties/PropertiesView.vue)).
- `MapView.vue` implementa el feed-mapa: layout split (lista izquierda, mapa derecho), `useFeedMap` + `usePropertyMapper`, marcadores hover, paginación local, URL state vía `router.replace` ([views/properties/MapView.vue](frontend/src/views/properties/MapView.vue)).
- `MapView` persiste el bbox en `route.query` con `router.replace` en cada `moveend` — el handler `onBbox` llama primero `router.replace({ query: bbox })` y luego `fetchByBbox`; no hay `watch` sobre `route.query` porque el mapa es el único que escribe la URL ([views/properties/MapView.vue](frontend/src/views/properties/MapView.vue)).
- `MapView` inicializa `center` síncronamente desde `localStorage` (clave `STORAGE_KEYS.USER_LOCATION`) para evitar la race condition de vue-leaflet; el `onMounted` solo llama `fetchByBbox` alrededor de `loc ± 0.05°` ([views/properties/MapView.vue](frontend/src/views/properties/MapView.vue)).
- El interface `FeedFilters`, `FeedPreferences`, `FeedPage` y `PageCache` viven en `types/feed.ts` ([types/feed.ts](frontend/src/types/feed.ts)).
