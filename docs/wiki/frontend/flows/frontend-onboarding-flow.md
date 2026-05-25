---
title: Onboarding flow (frontend)
status: draft
last-verified: 2026-05-21
owners: [frontend, users-service]
related: [[frontend]], [[frontend-architecture]], [[catalog-service-geo-catalog]]
sources: [../../../sources/frontend/2026-05-21-foundational-qa.md]
---

## TL;DR

Modal-based wizard de 4 pasos que dispara automáticamente cuando el usuario autenticado entra a la app y no completó (ni dismisseó) el onboarding. Estado persistido en server-side (`users.onboarding_step`) y client-side (`sessionStorage` para el dismiss). El front está completo; el backend tiene parte implementada pero **necesita un refactor para acoplar el source-of-truth de localities/neighborhoods a `catalog-service`**.

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
                              │ user saves intent
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
                       │property_type │ ← tipo de inmueble preferido
                       └──────┬───────┘
                              │ user saves
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
| `userInterests` | Pinia `useUserStore` (memoria del tab) | Cache de localities/neighborhoods seleccionados — evita re-fetch durante la sesión |

`logoutReset()` borra el sessionStorage al cerrar sesión — siguiente login, si quedó incompleto, vuelve a aparecer.

## Endpoints backend involucrados

| Step | Endpoint | Estado backend |
|---|---|---|
| `intent` | (probable) `POST /v1/onboarding/intent` o `PATCH /v1/users/me` | per código del front, el componente emite `onSaved=closeFlow` pero el POST no se ve en `useOnboarding` — probablemente vive dentro del propio `IntentSelector` |
| `city` | `POST /v1/onboarding/city` body `{ locality_ids: string[] }` | ⚠ feature pausada (ver `[[project_current_priorities]]`) |
| `neighborhood` | `POST /v1/onboarding/neighborhood` body `{ localities: [{ locality_id, neighborhoods }] }` | ⚠ pausado |
| `property_type` | TBD | TBD |
| `GET /v1/users/me/` | retorna `{ ..., onboarding_step }` | ✅ |
| `GET /v1/users/me/interests` | retorna `{ localities, neighborhoods, properties }` | ⚠ TBD |

## El refactor pendiente — source-of-truth split

Hoy en `users-service` los datos de onboarding (localities elegidas, neighborhoods elegidos) se guardan sin validar contra `catalog-service`. Eso puede generar drift:
- Si un barrio se desactiva en catalog (`is_active=false`), users-service sigue refiriéndolo.
- Si un barrio cambia de id (caso edge), users queda con FK colgante.

**Cambio propuesto** (per autor): users-service debe llamar a catalog-service para **validar** los IDs antes de guardar, y/o solo persistir los IDs (no nombres) + obtener los nombres en read time desde catalog.

Decisión exacta del shape (validar en write vs join en read) — pendiente. Trackearlo cuando se retome la feature.

## Flow datos en `useOnboarding`

```
                 LocalitySelector (component)
                            │
                            │ user picks N localities
                            ▼
              saveCity(localities) [useOnboarding]
                            │
                            │ POST /v1/onboarding/city
                            ▼
            userStore.userInterests.localities = localities
            userStore.onboardingStep = "neighborhood"
            activeComponent.value = NeighborhoodSelector
```

Cada `save*` del composable:
1. Hace el POST al users-service.
2. Actualiza `userStore` en memoria.
3. Avanza `activeComponent` al siguiente del `STEP_MAP`.

El listado de localities/neighborhoods que el usuario VE en los selectors viene de **`composables/Location.ts`** que pega a `catalog-service` directo y cachea en `sessionStorage`.

## Failure modes

- **catalog-service down** al abrir el modal: `LocalitySelector` no carga opciones → user no puede avanzar. Sin retry visible al user hoy.
- **users-service down** al guardar: `saveCity` solo loggea `console.error` y deja el modal abierto. No hay toast/error UI hoy — gap.
- **401 en cualquier endpoint**: `userStore` llama `authStore.logout()` automáticamente. El modal queda huérfano hasta el próximo login.
- **Doble apertura del modal**: protegido por `hasCheckedOnboarding` (no se re-llama a `/users/me/` en cada navegación), pero si dos tabs se abren simultáneos, ambos disparan el flujo (sessionStorage es per-tab).

## Boundaries — lo que el flujo **NO** hace

- **No fuerza completion**: el user puede dismisseaer el modal (✗ esquina superior). El `dismissModal()` setea `userDismissedModal = true` y `onboardingStep = "done"`, ocultando el modal hasta logout/nueva sesión.
- **No valida los IDs** contra catalog antes del POST — eso vive (debería vivir) en users-service.
- **No re-popula** el feed después de guardar — los componentes de feed lo harán cuando se implementen.

## Open items

- **Refactor users-service ↔ catalog** (source-of-truth de localities/neighborhoods).
- **Error UX**: agregar toasts / retry visible en los selectors.
- **Endpoint definitivo de `intent`** y `property_type` — confirmar shape final con users-service.
- **Property type wizard**: hoy es un selector simple; quizás se expande a sub-pasos (cantidad de habitaciones, presupuesto, etc.).
- **A/B sobre si forzar completion** post-N visitas — decisión de producto, no técnica.

## Claims

- El `watch` sobre `isAuthenticated` con `immediate: true` dispara `startFlow()` automáticamente post-login ([App.vue:86-98](frontend/src/App.vue#L86-L98)).
- `STEP_MAP` define los 4 selectors y mapea exactamente a los strings del campo `onboarding_step` del backend ([composables/useOnboarding.ts:11-16](frontend/src/composables/useOnboarding.ts#L11-L16)).
- El step inicial por default es `"intent"` si el backend no devuelve uno ([stores/user.ts:37](frontend/src/stores/user.ts#L37)).
- `dismissModal()` setea `onboarding_dismissed = "true"` en `sessionStorage` (per-tab, no `localStorage`) ([stores/user.ts:78-82](frontend/src/stores/user.ts#L78-L82)).
- `saveCity` y `saveNeighborhoods` actualizan el step en `userStore` y avanzan `activeComponent` al siguiente del `STEP_MAP` ([composables/useOnboarding.ts:49-76](frontend/src/composables/useOnboarding.ts#L49-L76)).
- Las opciones (localities/neighborhoods) que el user ve vienen de `catalog-service` vía `composables/Location.ts` — cacheadas en `sessionStorage` por id.
- La feature backend está marcada como pausada en [[project_current_priorities]] al 2026-05-21.
