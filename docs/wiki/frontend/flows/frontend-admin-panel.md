---
title: Panel admin (frontend)
status: draft
last-verified: 2026-07-28
owners: [frontend]
related:
  - "[[frontend]]"
  - "[[frontend-architecture]]"
  - "[[frontend-onboarding-flow]]"
  - "[[users-service-user]]"
  - "[[properties-service-admin]]"
  - "[[properties-service-bulk-create-worker]]"
  - "[[adr-admin-offset-pagination]]"
  - "[[adr-no-component-library]]"
  - "[[open-items]]"
sources:
  - ../../../sources/frontend/2026-07-16-admin-panel-nav-and-hub.md
  - ../../../sources/properties-service/2026-07-16-bulk-create-sync-timeout-risk.md
  - ../../../sources/frontend/2026-07-28-admin-panel-groundwork.md
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

## El modal de importación — flujo de 3 pasos (2026-07-28)

El backend pasó a un contrato de presigned upload (ver [[properties-service-bulk-create-worker]]), lo que dejó al modal mandando `multipart` a un endpoint que ahora espera JSON — roto al mergear. Reescrito, `upload()` hace tres pasos:

1. `POST /v1/admin/properties/bulk/upload-url` → `{ storage_key, upload_url, max_size_bytes, expires_in }`.
2. `PUT` del CSV directo a MinIO.
3. `POST /v1/admin/properties/bulk` con `{ storage_key }` → `202 { batch_id }`.

Tres detalles que no son obvios al reimplementarlo:

- **La URL se pide en el submit, no al elegir el archivo.** Pedirla antes la deja vencer (`expires_in`, hoy 5 min) mientras el admin todavía está eligiendo, y el fallo aparecería como un 403 opaco de MinIO.
- **El `PUT` usa `fetch` pelado, no `propertiesApi`.** Va directo a MinIO, la firma viaja en el query string y las cookies del cliente API no tienen por qué ir ahí. Es el paso que más fácil se hace mal.
- **El tamaño se chequea del lado del cliente contra `max_size_bytes`, y es el único chequeo que existe.** Un presigned PUT plano no puede imponer un límite: el server aceptaría un archivo más grande. Un límite duro requeriría presigned POST con `content-length-range` (ver [[open-items]]).

No hay polling ni panel de resultado: el modal emite `queued` con el `batch_id` y cierra. Revisar el resultado es problema de otra vista, deliberadamente.

## El riesgo del bulk síncrono — cerrado

La versión anterior de esta página documentaba que `POST /admin/properties/bulk` corría síncrono end-to-end y podía superar el `timeout: 8000` de `propertiesApi`. **Ya no aplica**: el endpoint responde `202` apenas encola y el trabajo pesado corre en un `BackgroundTask` ([[properties-service-bulk-create-worker]]). Los tres requests que hace el modal son cortos por construcción.

## El hueco que bloquea: un import no se puede revisar

`emit("queued")` no lo escucha nadie — `AdminPropertiesView.vue` monta el modal con `v-model` y sin `@queued` — y tampoco hay sistema de toasts en el proyecto. O sea que hoy el modal cierra en silencio y el admin no recibe confirmación de nada.

Peor: el `batch_id` se descarta al cerrar y **no existe ningún endpoint que liste los bulk jobs**, solo `GET /admin/properties/bulk/{job_id}/status`, que exige un id que ya haya que tener. El diseño de "revisar el resultado en otro lado" necesita primero un `GET /admin/properties/bulk`; `bulk_jobs` ya guarda todo lo que esa vista mostraría, y de paso le daría un punto de entrada al flujo de retry.

## Forma del panel: tabla, no el card grid del feed

El grid del feed optimiza para "cuál me gusta" — imagen, precio, ambientes. Moderar es "cuáles necesitan acción": más filas visibles a la vez, columnas alineadas para escanear, acciones por fila. Los filtros van **en la misma vista** que la tabla, porque el loop es filtrar → mirar → actuar → filtrar de nuevo, y separarlos obliga a ida y vuelta de navegación.

`GET /admin/properties` es el primero natural a cablear: moderación, verificación, pricing y promociones todas necesitan un `property_id` elegido de una lista. Pagina por offset con `total` — la decisión y por qué no reusa el cursor opaco del feed están en [[adr-admin-offset-pagination]]. La tabla se construye a mano, sin librería de componentes ([[adr-no-component-library]]).

## Estado del cableado: 10 de 12 endpoints admin sin consumer

`AdminPropertiesView` sigue diciendo "En construcción". Los únicos dos endpoints admin con consumer en el front son los dos del bulk; los otros diez no tienen ninguno.

Tampoco hay módulo de API admin: las URLs del modal son strings inline. Con diez endpoints por venir, conviene introducir un `src/api/adminApi.ts` (o un composable) **antes** de que se dispersen.

## Decisiones diferidas

- **Roles admin granulares** (super-admin / catalog-admin / properties-admin): descartado por prematuro — sin evidencia de necesitarlo, y el diseño de roles de Keycloak (lista de strings) lo hace barato de agregar después. Importante: no sería un cambio solo de `users-service` — `catalog-service` y `properties-service` cada uno valida su propio `require_admin` contra su propio JWT.
- **KPIs reales, gráficos**: bloqueado en tener endpoints de conteo reales. D3 (ya usado en el mapa) probablemente sea excesivo para indicadores simples de tendencia — se reservaría para analítica real con series/multi-dimensión.

## Claims

- El link "Admin" en `NavUser.vue` está gateado por `v-if="authStore.isAdmin"`, apunta a `/admin`, y es un link de primer nivel (no del dropdown) ([components/shared/NavUser.vue](frontend/src/components/shared/NavUser.vue)).
- Las 3 rutas admin (`/admin`, `/admin/properties`, `/admin/catalog`) llevan `meta: { requiresAuth: true, requiresAdmin: true }` ([router/routes/admin/](frontend/src/router/routes/admin)).
- El guard `requiresAdmin` llama `authStore.fillUserData()` si `!authStore.accountId` antes de chequear `isAdmin` — evita que un admin sea rebotado en un deep-link directo ([router/index.ts](frontend/src/router/index.ts)).
- `AdminHomeView.vue` muestra 4 KPI cards con valor placeholder `"—"` — sin wiring a ningún endpoint de conteo todavía ([views/admin/AdminHomeView.vue](frontend/src/views/admin/AdminHomeView.vue)).
- `BulkUploadPropertiesModal.upload()` encadena `POST /v1/admin/properties/bulk/upload-url` → `fetch(upload_url, { method: "PUT" })` → `POST /v1/admin/properties/bulk` con `{ storage_key }`, y emite `queued` con el `batch_id` antes de cerrar ([components/admin/properties/BulkUploadPropertiesModal.vue](frontend/src/components/admin/properties/BulkUploadPropertiesModal.vue)).
- El `PUT` a storage no usa `propertiesApi`: es `fetch` nativo sin credenciales, porque la firma va en el query string ([components/admin/properties/BulkUploadPropertiesModal.vue](frontend/src/components/admin/properties/BulkUploadPropertiesModal.vue)).
- La presigned URL se pide dentro de `upload()`, no en `onFileChange()` ([components/admin/properties/BulkUploadPropertiesModal.vue](frontend/src/components/admin/properties/BulkUploadPropertiesModal.vue)).
- El modal compara `file.size` contra `presigned.max_size_bytes` antes de subir; no hay validación de tamaño del lado del servidor en el flujo de presigned PUT ([components/admin/properties/BulkUploadPropertiesModal.vue](frontend/src/components/admin/properties/BulkUploadPropertiesModal.vue)).
- `AdminPropertiesView.vue` monta `<BulkUploadPropertiesModal v-model="isBulkModalOpen" />` sin listener de `@queued`, y su cuerpo dice "En construcción" ([views/admin/properties/AdminPropertiesView.vue](frontend/src/views/admin/properties/AdminPropertiesView.vue)).
- No existe `src/api/adminApi.ts` — el directorio `src/api/` tiene solo `avmApi`, `catalogApi`, `interceptors`, `propertiesApi` y `usersApi` ([api/](frontend/src/api)).
- No existe ningún botón de bulk-import en `AdminCatalogView.vue` — el endpoint de catálogo requiere `locality_id`, no es una acción global ([views/admin/catalog/AdminCatalogView.vue](frontend/src/views/admin/catalog/AdminCatalogView.vue)).
- `propertiesApi` tiene `timeout: 8000`, suficiente ahora que los tres requests del modal son cortos ([api/propertiesApi.ts](frontend/src/api/propertiesApi.ts)).
