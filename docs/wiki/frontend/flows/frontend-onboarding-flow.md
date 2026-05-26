---
title: Onboarding flow (frontend)
status: stable
last-verified: 2026-05-26
owners: [frontend, users-service]
related: [[frontend]], [[frontend-architecture]], [[catalog-service-geo-catalog]]
sources:
  - docs/sources/frontend/2026-05-21-foundational-qa.md
  - docs/sources/frontend/2026-05-26-onboarding-wiring.md
---

## TL;DR

Modal-based wizard de 4 pasos que dispara automáticamente cuando el usuario autenticado entra a la app y no completó (ni dismisseó) el onboarding. Estado persistido server-side (`users.onboarding_step`) y client-side (`sessionStorage` para el dismiss). Los 4 pasos están completamente conectados end-to-end: frontend ↔ users-service ↔ catalog-service.

## Trigger

Vive en [`App.vue`](frontend/src/App.vue) con un `watch` sobre `authStore.isAuthenticated`:

```ts
watch(
  () => authStore.isAuthenticated,
  (isLogged) => {
    if (!isLogged) return;
    const manualCheck = sessionStorage.getItem("onboarding_dismissed") === "true";
    if (!manualCheck) startFlow();
  },
  { immediate: true }
);
```

- Dispara `startFlow()` **una vez** post-login si el usuario no dismisseó el modal en esta sesión.
- `startFlow()` viene del composable [`useOnboarding`](frontend/src/composables/useOnboarding.ts).

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
- Si `userDismissedModal === true` → `done` (no se abre modal en esta sesión).
- Si `hasCheckedOnboarding === true` → usa el step en memoria.
- Si no, GET `/v1/users/me/` → `data.onboarding_step ?? "intent"`.

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
| `onboarding_step` | server-side, `users.users` table en users-service | Source-of-truth del progreso; sobrevive logout/relog |
| `userDismissedModal` | `sessionStorage["onboarding_dismissed"]` | Si el usuario dismisseó el modal en esta sesión, no re-aparece hasta logout o nueva ventana |
| `userInterests.localities` | Pinia `useUserStore` (memoria del tab) | Cache de locality UUIDs — evita re-fetch durante la sesión |

`logoutReset()` borra el sessionStorage al cerrar sesión — siguiente login, si quedó incompleto, vuelve a aparecer.

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
       │ activeComponent = NeighborhoodSelector
       ▼
NeighborhoodSelector → saveNeighborhoods(payload)
       │ POST /v1/onboarding/neighborhood
       │ userStore.onboardingStep = "property_type"
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
- **401 en cualquier endpoint**: `userStore` llama `authStore.logout()` automáticamente. El modal queda huérfano hasta el próximo login.
- **Doble apertura del modal**: protegido por `hasCheckedOnboarding` (no se re-llama a `/users/me/` en cada navegación), pero si dos tabs se abren simultáneos, ambos disparan el flujo (sessionStorage es per-tab).

## Boundaries — lo que el flujo **NO** hace

- **No fuerza completion**: el user puede dismissear el modal (✗ esquina superior). `dismissModal()` setea `userDismissedModal = true`, ocultando el modal hasta logout/nueva sesión.
- **No valida los IDs** contra catalog antes del POST — eso vive en users-service.
- **No re-popula** el feed después de guardar — los componentes de feed lo harán cuando se implementen.

## Open items

- **Error UX**: agregar toasts / retry visible en los selectors cuando `save*` falla.
- **Property type wizard**: hoy es selector simple; quizás se expande a sub-pasos (habitaciones, presupuesto).
- **A/B sobre si forzar completion** post-N visitas — decisión de producto.

## Claims

- El `watch` sobre `isAuthenticated` con `immediate: true` dispara `startFlow()` automáticamente post-login ([App.vue](frontend/src/App.vue)).
- `STEP_MAP` define los 4 selectors y mapea exactamente a los strings del campo `onboarding_step` del backend ([composables/useOnboarding.ts:11-16](frontend/src/composables/useOnboarding.ts#L11-L16)).
- El step inicial por default es `"intent"` si el backend no devuelve uno ([stores/user.ts](frontend/src/stores/user.ts)).
- `dismissModal()` setea `onboarding_dismissed = "true"` en `sessionStorage` (per-tab, no `localStorage`) ([stores/user.ts](frontend/src/stores/user.ts)).
- `IntentSelector` llama `POST /v1/onboarding/intent` directamente; al éxito emite `onSaved` que App.vue mapea a `advanceToCity()` ([composables/useOnboarding.ts:49-52](frontend/src/composables/useOnboarding.ts#L49-L52)).
- `saveCity` envía `{ locality_ids: string[] }` y guarda solo UUIDs en `userStore.userInterests.localities` ([composables/useOnboarding.ts:54-67](frontend/src/composables/useOnboarding.ts#L54-L67)).
- `savePropertyTypes` llama `POST /v1/onboarding/property-type` en paralelo, una vez por ciudad, via `Promise.all` ([composables/useOnboarding.ts:85-100](frontend/src/composables/useOnboarding.ts#L85-L100)).
- `useLocalitiesWithNames.load()` resuelve UUIDs a nombres usando `catalog-service` cacheado en `sessionStorage` — compartido por `NeighborhoodSelector` y `PropertyTypeSelector` ([composables/useLocalitiesWithNames.ts](frontend/src/composables/useLocalitiesWithNames.ts)).
- `getNeighborhoodsByLocalities` usa `new URLSearchParams` para serializar el array (workaround para FastAPI query params vs comportamiento default de Axios) ([composables/Location.ts:43](frontend/src/composables/Location.ts#L43)).
- Las opciones visibles al user (nombres de localities/neighborhoods) vienen siempre de `catalog-service` — `users-service` solo almacena UUIDs.
