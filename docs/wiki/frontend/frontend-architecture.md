---
title: Arquitectura interna del frontend
status: draft
last-verified: 2026-05-21
owners: [frontend]
related: [[architecture]], [[frontend]], [[frontend-onboarding-flow]]
sources: [../../sources/frontend/2026-05-21-foundational-qa.md]
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
│   │   └── index.ts              # API.USERS_BASE_URL, CATALOG_BASE_URL, STORAGE_KEYS
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
└── .env / .env.example           # VUE_APP_USERS_URL, VUE_APP_CATALOG_URL, VUE_APP_IPAPI_URL
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

### `useOnboarding` ([composables/useOnboarding.ts](frontend/src/composables/useOnboarding.ts))

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

**Plan** (open item): un único `apiClient.ts` con axios instance configurada (`baseURL`, `withCredentials`, interceptor 401 → `authStore.logout()`). Eliminar las 3 variantes.

## Caching local

| Dato | Storage | TTL implícito |
|---|---|---|
| Countries | `localStorage` | Permanente hasta clear cache |
| Cities by country | `sessionStorage` | Por sesión del browser |
| Neighborhoods by locality | `sessionStorage` | Por sesión |
| User location (IP) | `localStorage` | Permanente hasta clear |
| `onboarding_dismissed` | `sessionStorage` | Por sesión |

Keys centralizadas en `STORAGE_KEYS` del `config/index.ts`. No hay invalidación explícita — depende del clear del browser.

## Components organization

| Carpeta | Propósito |
|---|---|
| `shared/` | NavBar, NavGuest (no-logged), NavUser (logged), BaseModal — reusables transversales. |
| `onboarding/` | 4 selectors (Intent, Locality, Neighborhood, PropertyType) — usados desde el modal. |
| `properties/` | PropertyCard, HouseCard — cards para feed/listing views (HouseCard probable duplicado o variante de PropertyCard). |
| `settings/` | SettingsSidebar — navegación lateral del SettingsLayout. |
| `map/` | MapUser — visualización con Leaflet + D3 (ver [[adr-mapbox-geocoding-leaflet-rendering]]). |

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
- **Forward geocoding** (address → lat/lon): Mapbox SDK directamente en el frontend, sin pasar por el backend. Alinea con [[adr-mapbox-frontend-only]] de catalog.
- **Reverse geocoding** (lat/lon → barrio): el frontend pasa el `(lat, lon)` al backend (catalog-service `/by-coordinates`).

Componente `MapUser.vue` (no leído en detalle) probablemente integra Leaflet + el JWT cookie para identificar al usuario.

## Build & deploy

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
- `leaflet` y `@vue-leaflet/vue-leaflet` están declarados en `devDependencies` del `package.json` — probablemente debería ser `dependencies` si se usa en runtime ([package.json:32-33](frontend/package.json#L32-L33), [package.json:43](frontend/package.json#L43)).
- Firebase NO se inicializa en `main.ts` — el `initializeApp(firebaseConfig)` está comentado ([main.ts:14](frontend/src/main.ts#L14)).
