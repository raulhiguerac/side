---
title: Panel admin (frontend)
status: draft
last-verified: 2026-07-16
owners: [frontend]
related:
  - "[[frontend]]"
  - "[[frontend-architecture]]"
  - "[[frontend-onboarding-flow]]"
  - "[[users-service-user]]"
  - "[[properties-service-admin]]"
sources:
  - ../../../sources/frontend/2026-07-16-admin-panel-nav-and-hub.md
  - ../../../sources/properties-service/2026-07-16-bulk-create-sync-timeout-risk.md
---

## TL;DR

Scaffolding del panel admin embebido en la app existente (no un subdominio separado): un link condicional en el nav, tres rutas gateadas por rol, y una vista hub que orquesta hacia las secciones de propiedades y catálogo. Hoy es mayormente placeholder — las vistas de moderación reales todavía no existen.

## Por qué embebido, no subdominio

Decisión de alcance: dado que no hay evidencia de necesitar aislamiento fuerte (mismo equipo chico administrando todo), embeber el panel en la SPA existente reusando el stack de auth/router/store es mucho más barato que un subdominio con su propio login. Si en el futuro se necesita separar, las vistas se pueden mover reusando el mismo código.

## Nav gating

El link "Admin" vive en `NavUser.vue` (nunca en `NavGuest` — implica estar logueado), como link de primer nivel junto a `Dashboard`/`Mis propiedades` (no en el dropdown de cuenta):

```html
<router-link v-if="authStore.isAdmin" to="/admin" ...>Admin</router-link>
```

Se eligió primer nivel sobre el dropdown porque la moderación se espera que sea un flujo de trabajo activo/frecuente, no un ajuste ocasional. `authStore.isAdmin` se lee directo del store en el template — no necesita `computed()` porque es un booleano simple, ya reactivo por ser parte del state de Pinia (a diferencia de `user`, que sí es un `computed` porque combina 3 campos).

## Rutas

`router/routes/admin/` (nuevo módulo, mismo patrón de archivo-por-dominio que `properties.ts`/`settings.ts`):

| Ruta | Nombre | Vista |
|---|---|---|
| `/admin` | `admin-home` | `views/admin/AdminHomeView.vue` (hub) |
| `/admin/properties` | `admin-properties` | `views/admin/properties/AdminPropertiesView.vue` |
| `/admin/catalog` | `admin-catalog` | `views/admin/catalog/AdminCatalogView.vue` |

Las tres llevan `meta: { requiresAuth: true, requiresAdmin: true }`. `home.ts`/`properties.ts`/`catalog.ts` se combinan en un barrel `index.ts` (`adminRoutes`) importado en `router/index.ts`.

## Guard `requiresAdmin` — el fix de la race

El guard global (ver [[frontend-architecture]]) chequea `requiresAdmin` después de `requiresAuth`. El punto no obvio: `authStore.isAdmin` normalmente solo se llena vía `fillUserData()`, que corre desde el `watch` de `App.vue` **después** de que el guard ya resolvió la navegación (`App.vue` monta después de que el router resuelve la primera ruta). Sin ajuste, un admin real entrando por link directo a `/admin/properties` sería rebotado a Home porque `isAdmin` todavía tendría su default `false`.

Fix: el guard mismo llama `fillUserData()` si `!authStore.accountId` (mismo gate que ya usa `_authChecked` para no repetir `checkAuth()`), antes de chequear `isAdmin`:

```ts
if (requiresAdmin) {
  if (!authStore.accountId) {
    await authStore.fillUserData();
  }
  if (!authStore.isAdmin) return { name: "home" };
}
```

## Vista hub (`AdminHomeView.vue`)

En `/admin`: hero + fila de 4 KPI cards (Usuarios/Propiedades/Localidades/Barrios, valores `—` placeholder) + sección "Gestión" con 2 cards (Propiedades, Catálogo) que linkean a sus vistas respectivas. Íconos vía `@lucide/vue` (`Home`, `Globe`) — no emoji, mismo paquete que ya usa `PropertyHeaderCard.vue`.

Las 4 KPIs son intencionalmente placeholder — requieren endpoints de conteo cacheado en cada servicio dueño del dato (users-service, properties-service, catalog-service), no construidos todavía. Se descartó ruteear esto por `analytics-service`: un `COUNT(*)` cacheado no es carga OLAP, no amerita esa capa para 4 contadores simples.

## Acciones rápidas — solo lo que mapea a una capacidad real

Se revisó feedback genérico de dashboard (de un LLM externo) y se descartaron sugerencias que no corresponden a ninguna capacidad admin real en este dominio (ej. "crear usuario", "nueva propiedad" — no son acciones admin acá, la creación de propiedad es un flujo del dueño). Se mantuvo solo **"Importar CSV"** porque mapea a un endpoint real (`POST /admin/properties/bulk`), implementado como modal (`BulkUploadPropertiesModal.vue`) sobre la vista padre `AdminPropertiesView.vue` — no una ruta nueva.

El equivalente en catálogo (`POST /admin/localities/{locality_id}/neighborhoods/bulk`) no tiene botón todavía porque necesita elegir una localidad primero — no es una acción global de un click. UX pendiente de diseñar.

## Riesgo encontrado: el bulk endpoint es síncrono

Al construir el modal de importación se encontró que `POST /admin/properties/bulk` corre síncrono end-to-end en el back — incluye una llamada de red a `catalog-service` por cada fila del CSV antes de comitear. El timeout de `propertiesApi` (8s) puede ser insuficiente para CSVs de más de un puñado de filas. Refactor a patrón `202 + batch_id` + polling propuesto pero no implementado — ver el source de `properties-service` para el detalle, y `wiki/_shared/open-items.md` (marcado IMPORTANTE).

## Decisiones diferidas

- **Roles admin granulares** (super-admin / catalog-admin / properties-admin): descartado por prematuro — sin evidencia de necesitarlo, y el diseño de roles de Keycloak (lista de strings) lo hace barato de agregar después. Importante: no sería un cambio solo de `users-service` — `catalog-service` y `properties-service` cada uno valida su propio `require_admin` contra su propio JWT.
- **KPIs reales, gráficos**: bloqueado en tener endpoints de conteo reales. D3 (ya usado en el mapa) probablemente sea excesivo para indicadores simples de tendencia — se reservaría para analítica real con series/multi-dimensión.

## Claims

- El link "Admin" en `NavUser.vue` está gateado por `v-if="authStore.isAdmin"`, apunta a `/admin`, y es un link de primer nivel (no del dropdown) ([components/shared/NavUser.vue](frontend/src/components/shared/NavUser.vue)).
- Las 3 rutas admin (`/admin`, `/admin/properties`, `/admin/catalog`) llevan `meta: { requiresAuth: true, requiresAdmin: true }` ([router/routes/admin/](frontend/src/router/routes/admin)).
- El guard `requiresAdmin` llama `authStore.fillUserData()` si `!authStore.accountId` antes de chequear `isAdmin` — evita que un admin sea rebotado en un deep-link directo ([router/index.ts](frontend/src/router/index.ts)).
- `AdminHomeView.vue` muestra 4 KPI cards con valor placeholder `"—"` — sin wiring a ningún endpoint de conteo todavía ([views/admin/AdminHomeView.vue](frontend/src/views/admin/AdminHomeView.vue)).
- `BulkUploadPropertiesModal.vue` llama `POST /v1/admin/properties/bulk` vía `propertiesApi` y muestra `{ inserted, errors }` de la respuesta ([components/admin/properties/BulkUploadPropertiesModal.vue](frontend/src/components/admin/properties/BulkUploadPropertiesModal.vue)).
- No existe ningún botón de bulk-import en `AdminCatalogView.vue` — el endpoint de catálogo requiere `locality_id`, no es una acción global ([views/admin/catalog/AdminCatalogView.vue](frontend/src/views/admin/catalog/AdminCatalogView.vue)).
- `BulkCreatePropertiesUseCase.execute()` en properties-service llama a `catalog-service` por cada fila del CSV (semáforo de 50 concurrentes) antes de `bulk_insert`+`commit`, todo dentro del ciclo del request HTTP ([bulk_create_properties.py](backend/properties-service/src/app/services/admin/use_cases/bulk_create_properties.py)).
- `propertiesApi` tiene `timeout: 8000` — insuficiente para CSVs grandes dado el patrón síncrono anterior ([api/propertiesApi.ts](frontend/src/api/propertiesApi.ts)).
