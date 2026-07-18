---
title: Onboarding flow (frontend)
status: stable
last-verified: 2026-07-16
owners: [frontend, users-service]
related:
  - "[[frontend]]"
  - "[[frontend-architecture]]"
  - "[[catalog-service-geo-catalog]]"
sources:
  - docs/sources/frontend/2026-05-21-foundational-qa.md
  - docs/sources/frontend/2026-05-26-onboarding-wiring.md
  - docs/sources/frontend/2026-07-16-auth-user-store-consolidation.md
---

## TL;DR

Modal-based wizard de 4 pasos que dispara automáticamente cuando el usuario autenticado entra a la app y no completó (ni dismisseó) el onboarding. Estado persistido server-side (`accounts.onboarding_step`, expuesto en `CurrentUserOut`) y client-side (`sessionStorage`, scoped por cuenta, para el dismiss). Los 4 pasos están completamente conectados end-to-end: frontend ↔ users-service ↔ catalog-service.

## Trigger

Vive en [`App.vue`](frontend/src/App.vue) con un `watch` sobre `authStore.isAuthenticated`:

```ts
onMounted(async () => {
  await authStore.checkAuth();
});

watch(
  () => authStore.isAuthenticated,
  async (isLogged) => {
    if (!isLogged) return;
    try {
      await authStore.fillUserData();
      await userStore.checkInterests();
      startFlow();
    } catch (e) {
      console.error("Error al inicializar la sesión", e);
    }
  },
  { immediate: true }
);
```

`onMounted` solo dispara `checkAuth()` — todo lo que depende de estar autenticado (`fillUserData`, `checkInterests`, `startFlow`) vive únicamente en el `watch`, que reacciona a cualquier cambio de `isAuthenticated` sin importar qué código lo disparó (boot inicial vía `immediate: true`, o un `login()`/`register()` posterior sin recargar la página). Antes había una llamada duplicada a `checkInterests()` en ambos lados — se eliminó (2026-07-16).

- `fillUserData()` (en `authStore`) es la que trae `onboarding_step` desde el back — sin ella, `startFlow()` no tiene de dónde leer el step.
- `startFlow()` viene del composable [`useOnboarding`](frontend/src/composables/onboarding/useOnboarding.ts) y ya no es async ni hace fetch propio — solo lee `authStore.onboardingStep`, ya poblado por `fillUserData()`.

## State machine — 4 pasos

```
                       ┌──────────────┐
                       │   intent     │ ← step inicial, "qué buscas"
                       └──────┬───────┘
                              │ POST /v1/onboarding/intent
                              ▼
                       ┌──────────────┐
                       │     city     │ ← seleccionar 1-N localities de interés
                       └──────┬───────┘
                              │ POST /v1/onboarding/city
                              ▼
                       ┌──────────────┐
                       │ neighborhood │ ← seleccionar barrios dentro de las cities
                       └──────┬───────┘
                              │ POST /v1/onboarding/neighborhood
                              ▼
                       ┌──────────────┐
                       │property_type │ ← tipo de inmueble preferido (por city)
                       └──────┬───────┘
                              │ POST /v1/onboarding/property-type (per city)
                              ▼
                       ┌──────────────┐
                       │     done     │ ← modal cerrado, onboarding completado
                       └──────────────┘
```

El step actual se determina así:
- Si `userStore.isOnboardingDismissed()` (lee `sessionStorage` scoped por `accountId`) → no se abre el modal.
- Si no, usa `authStore.onboardingStep` — ya poblado por `fillUserData()` (`GET /v1/users/me/` → `data.onboarding_step ?? "intent"`) antes de que `startFlow()` corra.

## Componentes (4 selectors)

| Step | Componente | Vive en |
|---|---|---|
| `intent` | `IntentSelector` | `components/onboarding/IntentSelector.vue` |
| `city` | `LocalitySelector` | `components/onboarding/LocalitySelector.vue` |
| `neighborhood` | `NeighborhoodSelector` | `components/onboarding/NeighborhoodSelector.vue` |
| `property_type` | `PropertyTypeSelector` | `components/onboarding/PropertyTypeSelector.vue` |

`STEP_MAP` en `useOnboarding.ts` mapea el string del step al componente. `activeComponent: shallowRef<Component>` se renderiza dinámicamente dentro de `BaseModal` en `App.vue`:

```html
<BaseModal v-model="isModalOpen" @update:modelValue="(val) => !val && closeFlow()">
  <transition name="scale" mode="out-in">
    <component :is="activeComponent" v-bind="dynamicProps" @complete="closeFlow" />
  </transition>
</BaseModal>
```

## Persistencia — dual: server + client

| Estado | Dónde vive | Para qué |
|---|---|---|
| `onboarding_step` | server-side, `accounts.onboarding_step` en users-service | Source-of-truth del progreso; sobrevive logout/relog |
| dismissal del modal | `sessionStorage["onboarding_dismissed:{accountId}"]` | Si el usuario dismisseó el modal sin terminarlo, no re-aparece **mientras el browser siga abierto** — sobrevive logout/login en el mismo tab/ventana |
| `userInterests.localities` | Pinia `useUserStore` (memoria del tab) | Cache de locality UUIDs — evita re-fetch durante la sesión |

**Cambio de comportamiento (2026-07-16):** el dismissal **ya no se borra en logout** — antes sí, lo cual causaba que un usuario que cerraba el modal, hacía logout y volvía a entrar al rato en el mismo browser viera el modal de nuevo, aunque hubiese dicho que no. La semántica correcta es "no me vuelvas a preguntar hoy, pero si cerrás el browser te vuelvo a preguntar por si cambiaste de opinión" — eso es exactamente lo que da `sessionStorage` sin borrarlo nosotros. La key está parametrizada por `accountId` (`STORAGE_KEYS.ONBOARDING_DISMISSED(accountId)`) para que dos cuentas distintas en el mismo browser no hereden el dismissal una de la otra. Si la cuenta **sí completó** el onboarding (`onboarding_step === "done"` en el back), el modal no se muestra sin importar el dismissal — la finalización real es la única fuente de verdad que persiste entre logins, no el dismiss del cliente.

## Endpoints backend involucrados

| Step | Endpoint | Body / Params | Estado |
|---|---|---|---|
| `intent` | `POST /v1/onboarding/intent` | `{ intent: "buyer" \| "seller" \| "renter" \| "explorer" }` | ✅ |
| `city` | `POST /v1/onboarding/city` | `{ locality_ids: string[] }` | ✅ |
| `neighborhood` | `POST /v1/onboarding/neighborhood` | `{ localities: [{ locality_id, neighborhoods: { 1: uuid, ... } }] }` | ✅ |
| `property_type` | `POST /v1/onboarding/property-type` | `{ locality_id, property_type: string[] }` — llamado por ciudad en paralelo | ✅ |
| GET user | `GET /v1/users/me/` | — | ✅ |
| GET interests | `GET /v1/users/me/interests` | — | ✅ |

## Lookup pattern — UUIDs en users-ms, nombres desde catalog-ms

`users-service` almacena y devuelve **solo UUIDs** para localities y neighborhoods de interés. Los componentes obtienen los nombres legibles desde `catalog-service` en render time. Esto es intencional — evita acoplamiento entre servicios.

Flujo concreto:
1. `useLocalitiesWithNames.load()` lee `userStore.userInterests.localities` (UUIDs) — o llama `checkInterests()` si el store está vacío.
2. Llama `locations()` para obtener el `countryUser` (UUID del país detectado por IP).
3. Llama `getCitiesByCountry(countryUser)` → `catalog-service GET /v1/localities/by-country` — resultado cacheado en `sessionStorage`.
4. Construye un `Map<uuid, name>` y lo aplica a los IDs del usuario.

`NeighborhoodSelector` y `PropertyTypeSelector` usan este composable para obtener `[{ id, name }]` sin duplicar lógica.

## Flow datos en `useOnboarding`

```
IntentSelector (componente propio)
       │ POST /v1/onboarding/intent
       │ onSaved → advanceToCity()
       ▼
LocalitySelector → saveCity(localities)
       │ POST /v1/onboarding/city { locality_ids }
       │ userStore.userInterests.localities = [uuid, ...]
       │ authStore.onboardingStep = "neighborhood"
       │ activeComponent = NeighborhoodSelector
       ▼
NeighborhoodSelector → saveNeighborhoods(payload)
       │ POST /v1/onboarding/neighborhood
       │ authStore.onboardingStep = "property_type"
       │ activeComponent = PropertyTypeSelector
       ▼
PropertyTypeSelector → savePropertyTypes(selections)
       │ Promise.all(POST /v1/onboarding/property-type per city)
       │ closeFlow()
       ▼
     done
```

`IntentSelector` es el único selector que maneja su propio POST — emite `onSaved` y App.vue llama `advanceToCity()`. Los pasos 2-4 usan funciones de `useOnboarding`.

## Caching en catalog-service calls

| Recurso | Clave sessionStorage | Cuándo se cachea |
|---|---|---|
| Lista de países | `countries` | Primera llamada a `locations()` en la sesión |
| Localities por país | `cities:{country_id}` | Primera llamada a `getCitiesByCountry(id)` |
| Neighborhoods por locality | `neighborhoods:{locality_id}` | Primera llamada a `getNeighborhoodsByLocalities([ids])` |

`getNeighborhoodsByLocalities` implementa cache parcial: solo llama al endpoint para los IDs que faltan en sessionStorage y fusiona con los cacheados.

**Nota sobre Axios + FastAPI:** FastAPI espera `?locality_ids=val1&locality_ids=val2`; Axios serializa arrays como `locality_ids[]=val`. Se usa `new URLSearchParams(ids.map(id => ['locality_ids', id]))` explícitamente.

## Failure modes

- **catalog-service down** al abrir el modal: `LocalitySelector` no carga opciones → user no puede avanzar. Sin retry visible al user hoy.
- **users-service down** al guardar: las funciones `save*` solo loggean `console.error` y dejan el modal abierto. No hay toast/error UI hoy — gap.
- **401 en cualquier endpoint**: ya no lo maneja cada store manualmente — el interceptor centralizado de `usersApi` (ver [[frontend-architecture]]) intenta un refresh silencioso y, si falla, hace logout real + redirect. El modal queda huérfano hasta el próximo login.
- **Doble apertura del modal**: si dos tabs se abren simultáneos, ambos disparan el flujo — `sessionStorage` es per-tab (una pestaña nueva, no duplicada, arranca sin el dismissal aunque el browser siga abierto).

## Boundaries — lo que el flujo **NO** hace

- **No fuerza completion**: el user puede dismissear el modal (✗ esquina superior). `dismissModal()` escribe la key de `sessionStorage` scoped por cuenta, ocultando el modal mientras el browser siga abierto (no hasta logout — ver sección Persistencia).
- **No valida los IDs** contra catalog antes del POST — eso vive en users-service.
- **No re-popula** el feed después de guardar — los componentes de feed lo harán cuando se implementen.

## Open items

- **Error UX**: agregar toasts / retry visible en los selectors cuando `save*` falla.
- **Property type wizard**: hoy es selector simple; quizás se expande a sub-pasos (habitaciones, presupuesto).
- **A/B sobre si forzar completion** post-N visitas — decisión de producto.

## Claims

- El `watch` sobre `isAuthenticated` con `immediate: true` dispara `startFlow()` automáticamente post-login; el mismo handler llama `authStore.fillUserData()` y `userStore.checkInterests()` antes, envuelto en un try/catch ([App.vue](frontend/src/App.vue)).
- `isModalOpen` y `activeComponent` son **estado a nivel de módulo** (`ref`/`shallowRef` declarados fuera de la función `useOnboarding()`, no dentro) — singleton entre todos los componentes que llamen al composable, mismo patrón que `useCities` ([composables/onboarding/useOnboarding.ts](frontend/src/composables/onboarding/useOnboarding.ts)).
- `STEP_MAP` define los 4 selectors y mapea exactamente a los strings del campo `onboarding_step` del backend ([composables/onboarding/useOnboarding.ts](frontend/src/composables/onboarding/useOnboarding.ts)).
- El step inicial por default es `"intent"` si el backend no devuelve uno ([stores/auth.ts](frontend/src/stores/auth.ts)).
- `dismissModal()` setea `STORAGE_KEYS.ONBOARDING_DISMISSED(accountId) = "true"` en `sessionStorage` (per-tab y per-cuenta, no `localStorage`) — ya no toca `onboardingStep` ([stores/user.ts](frontend/src/stores/user.ts)).
- `IntentSelector` llama `POST /v1/onboarding/intent` directamente y emite el evento `saved`; `App.vue` lo escucha via el prop dinámico `onSaved: advanceToCity` que solo se pasa cuando `activeComponent === IntentSelector` ([components/onboarding/IntentSelector.vue](frontend/src/components/onboarding/IntentSelector.vue), [App.vue](frontend/src/App.vue)).
- `saveCity` envía `{ locality_ids: string[] }` y guarda solo UUIDs en `userStore.userInterests.localities` ([composables/onboarding/useOnboarding.ts](frontend/src/composables/onboarding/useOnboarding.ts)).
- `savePropertyTypes` llama `POST /v1/onboarding/property-type` en paralelo, una vez por ciudad, via `Promise.all` ([composables/onboarding/useOnboarding.ts](frontend/src/composables/onboarding/useOnboarding.ts)).
- `useLocalitiesWithNames.load()` resuelve UUIDs a nombres usando `catalog-service` cacheado en `sessionStorage` — compartido por `NeighborhoodSelector` y `PropertyTypeSelector` ([composables/catalog/useLocalitiesWithNames.ts](frontend/src/composables/catalog/useLocalitiesWithNames.ts)).
- `getNeighborhoodsByLocalities` usa `new URLSearchParams` para serializar el array (workaround para FastAPI query params vs comportamiento default de Axios) ([composables/catalog/useLocation.ts](frontend/src/composables/catalog/useLocation.ts)).
- Las opciones visibles al user (nombres de localities/neighborhoods) vienen siempre de `catalog-service` — `users-service` solo almacena UUIDs.
