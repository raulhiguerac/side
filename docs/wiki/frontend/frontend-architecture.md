---
title: Arquitectura interna del frontend
status: draft
last-verified: 2026-06-04
owners: [frontend]
related: [[architecture]], [[frontend]], [[frontend-onboarding-flow]], [[frontend-map-component]], [[properties-service-search]]
sources: [../../sources/frontend/2026-05-21-foundational-qa.md, ../../sources/frontend/2026-05-28-avm-form-split-and-dumb-map.md, ../../sources/frontend/2026-05-29-vue35-gmaps-places-leaflet-markers.md, ../../sources/frontend/2026-05-29-avm-form-wiring-predict.md, ../../sources/frontend/2026-06-03-feed-filters-neighborhood-lookup.md, ../../sources/frontend/2026-06-04-feed-filters-contract.md]
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
│   │   └── index.ts              # routes + beforeEach guard
│   ├── stores/                   # Pinia
│   │   ├── auth.ts
│   │   └── user.ts
│   ├── composables/
│   │   ├── useOnboarding.ts
│   │   └── Location.ts
│   ├── types/
│   │   ├── user.ts
│   │   └── properties.ts
│   ├── views/                    # páginas-ruta
│   │   ├── public/{HomeView, AboutView}
│   │   ├── auth/{LoginView, RegisterView, ResetPasswordView}
│   │   ├── settings/{SettingsLayout, SettingsProfile, SettingsSecurity, SettingsAccount}
│   │   ├── properties/MyPropertiesView
│   │   └── dev/DevPlaygroundView
│   └── components/
│       ├── shared/{NavBar, NavGuest, NavUser, BaseModal}
│       ├── onboarding/{IntentSelector, LocalitySelector, NeighborhoodSelector, PropertyTypeSelector}
│       ├── properties/{PropertyCard, HouseCard}
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

Gestiona el feed de propiedades:
- `data: ref<PropertyCard[]>` — resultados crudos del backend.
- `neighborhoodLookup: ref<Record<string, string>>` — mapa `neighborhood_id → name` construido tras cada fetch.
- `load(preferences?: FeedPreferences, filters?: FeedFilters)`: si llegan args los usa; si no, hace fallback a `userStore.userInterests` (resuelto con `preferences ?? (ternario del store)` — los paréntesis son obligatorios por la precedencia de `??` vs `?:`). Llama `fetchFeed`, extrae `city_id`s únicos de los resultados → `buildNeighborhoodMap` → popula `neighborhoodLookup`. Retorna `void` y muta `data.value` internamente — la view solo hace `await load(...)`, no asigna el resultado.
- `fetchFeed(preferences, filters?)`: `GET /v1/search/feed` con `params: { ...preferences, ...filters }` (spread de ambos) — así filtros parciales (solo `max_price`, etc.) viajan sin tocar el resto.
- **Bug histórico**: axios serializa arrays como `key[]=v` (bracket notation). FastAPI **no** parsea `key[]` como el parámetro `key` — lo trata como parámetro desconocido y usa el default vacío, haciendo que `parse_feed_preferences` retorne `None` y el feed ignore los filtros. Fix: `paramsSerializer: { indexes: null }` → serializa como `key=v1&key=v2`.

La view padre del feed orquesta: recibe el evento `submit` de `FeedFilters` y hace `await load(params.preferences, params.filters)` — el componente no llama al backend, solo emite hacia arriba.

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

**Hoy: axios directo, sin instance central.**

Tres patrones coexisten en código:

1. **Hardcoded URL string**: `auth.ts` (login, register, logout, checkAuth) — `"http://localhost:8000/v1/..."`.
2. **Template literal con config**: `user.ts`, `composables/Location.ts`, `useOnboarding.ts` — `` `${API.USERS_BASE_URL}/v1/...` ``.
3. **Constante directa**: `detectLocation` usa `API.IPAPI_URL` (third-party).

Todas las calls llevan `withCredentials: true` para que la cookie viaje.

> ⚠ **CORS + `withCredentials`**: `allow_origins=["*"]` en el backend es incompatible con `withCredentials: true` — el browser bloquea la respuesta (la spec prohíbe wildcard origin con credenciales). Cada backend debe usar `allow_origins=["http://localhost:8080"]` + `allow_credentials=True`. El analytics-service tiene este fix en `src/app/main.py`.

**Plan** (open item): un único `apiClient.ts` con axios instance configurada (`baseURL`, `withCredentials`, interceptor 401 → `authStore.logout()`). Eliminar las 3 variantes.

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
| `shared/` | NavBar, NavGuest (no-logged), NavUser (logged), BaseModal — reusables transversales. |
| `onboarding/` | 4 selectors (Intent, Locality, Neighborhood, PropertyType) — usados desde el modal. |
| `properties/` | `PropertyCard`, `HouseCard` — cards para feed. `FeedFilters` — sidebar de filtros con secciones Preferencias (ciudad, barrio, tipo) y Filtros (precio, área, habitaciones, baños); se pre-pobla con ciudades de `useCities`, barrios cargados dinámicamente al seleccionar ciudad vía `watch`. Mantiene estado local (`selected`, `selectedNeighborhoods`, `selectedTypes`, `filters: ref<FeedFilters>({})` con `v-model.number`); `property_types` se togglea con `toggleType(type)` (push/filter sobre el array). **Emite un solo `submit` con `{preferences, filters}` al click en "Aplicar"** — no reactivo con `watch`, decisión para evitar una petición por cada cambio de campo. El objeto `preferences` se arma en `onSubmit` leyendo los refs (`selected.value`, etc.), sin ref `preferences` duplicado. |
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

## Claims

- `main.ts` registra Pinia, vue-router, vue3-cookies y Vueform — sin axios instance global ([main.ts:15-20](frontend/src/main.ts#L15-L20)).
- `useAuthStore.checkAuth` envía `withCredentials: true` y usa `_authChecked` para no re-disparar en cada navegación protegida ([stores/auth.ts:73-94](frontend/src/stores/auth.ts#L73-L94)).
- `useUserStore.checkOnboardingStep` llama `authStore.logout()` si recibe 401 — acoplamiento entre stores para manejar expiración de sesión ([stores/user.ts:42-43](frontend/src/stores/user.ts#L42-L43)).
- `composables/Location.ts` cachea countries en `localStorage` y cities/neighborhoods en `sessionStorage` ([composables/Location.ts:7-9](frontend/src/composables/Location.ts#L7-L9), [composables/Location.ts:28-30](frontend/src/composables/Location.ts#L28-L30)).
- `detectLocation` usa el provider externo `ipapi.co` para inferir país por IP ([stores/user.ts:69](frontend/src/stores/user.ts#L69)).
- El guard del router llama `checkAuth()` solo si `_authChecked === false` ([router/index.ts:104-110](frontend/src/router/index.ts#L104-L110)).
- `useOnboarding` mantiene `activeComponent` como `shallowRef<Component | null>` — `shallowRef` porque los componentes Vue son reactivos por sí solos ([composables/useOnboarding.ts:19](frontend/src/composables/useOnboarding.ts#L19)).
- Las 3 variantes de cómo se arma la URL de axios coexisten en `auth.ts` (hardcoded), `user.ts` (template literal con config) y `Location.ts` (template literal con config).
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
- `FeedFilters` carga barrios dinámicamente via `watch(selected, ...)` sobre las ciudades seleccionadas — llama `useNeighborhoodMultiselect.load(localities)` y resetea `selectedNeighborhoods` al cambiar ciudades ([components/properties/FeedFilters.vue](frontend/src/components/properties/FeedFilters.vue)).
- `FeedFilters` emite un único evento `submit` con `{ preferences, filters }` desde `onSubmit` al click en "Aplicar" — no es reactivo con `watch`; el componente no llama al backend ([components/properties/FeedFilters.vue:269-278](frontend/src/components/properties/FeedFilters.vue#L269-L278)).
- `toggleType(type)` en `FeedFilters` quita el tipo con `filter` si ya está en `selectedTypes` o lo agrega con `push` si no ([components/properties/FeedFilters.vue:259-267](frontend/src/components/properties/FeedFilters.vue#L259-L267)).
- `useFeed.load(preferences?, filters?)` usa los args si llegan y cae a `userStore.userInterests` con `preferences ?? (ternario)` si no; `fetchFeed` hace spread `{ ...preferences, ...filters }` en los params ([composables/feed/useFeed.ts:33-51](frontend/src/composables/feed/useFeed.ts#L33-L51)).
- El interface `FeedFilters` (campos opcionales/nullable: `min/max_price`, `min/max_area_m2`, `min_bathrooms`, `bedrooms`) vive en `types/feed.ts` junto a `FeedPreferences` ([types/feed.ts:1](frontend/src/types/feed.ts#L1)).
