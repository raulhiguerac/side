---
title: Panel admin (frontend)
status: draft
last-verified: 2026-08-01
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
  - "[[adr-tanstack-table]]"
  - "[[adr-admin-tabs-nested-routes]]"
  - "[[open-items]]"
sources:
  - ../../../sources/frontend/2026-07-16-admin-panel-nav-and-hub.md
  - ../../../sources/properties-service/2026-07-16-bulk-create-sync-timeout-risk.md
  - ../../../sources/frontend/2026-07-28-admin-panel-groundwork.md
  - ../../../sources/frontend/2026-07-29-admin-table-tanstack-and-cleanup.md
  - ../../../sources/properties-service/2026-07-29-moderation-state-machines-block-imports.md
  - ../../../sources/frontend/2026-08-01-admin-panel-tabs-moderation-preview.md
---

## TL;DR

Panel admin embebido en la app existente (no un subdominio separado): un link condicional en el nav, rutas gateadas por rol, y una vista hub que orquesta hacia propiedades y catálogo. Desde el 2026-08-01 la sección de propiedades es un layout con tres tabs como rutas hijas (moderación, promociones, importaciones), y la de moderación combina tabla paginada + panel de vista previa de la propiedad seleccionada. Lo que sigue faltando son las **acciones** de moderación, los filtros, y toda la sección de catálogo.

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
| `/admin/properties` | — | `views/admin/properties/AdminPropertiesLayout.vue` (padre con tabs) |
| `/admin/properties` (`path: ""`) | `admin-properties` | `AdminPropertiesModerationView.vue` |
| `/admin/properties/promotions` | `admin-properties-promotions` | `AdminPropertiesPromotionsView.vue` |
| `/admin/properties/imports` | `admin-properties-imports` | `AdminPropertiesImportsView.vue` |
| `/admin/catalog` | `admin-catalog` | `views/admin/catalog/AdminCatalogView.vue` |

`home.ts`/`properties.ts`/`catalog.ts` se combinan en un barrel `index.ts` (`adminRoutes`) importado en `router/index.ts`.

Dos detalles del árbol de propiedades (2026-08-01):

- **El padre no lleva `name`.** Tiene un hijo con `path: ""`, y nombrar a los dos hace ambiguo un `push({ name: "admin-properties" })`. El nombre vive en el hijo, que es el destino real.
- **`meta` va solo en el padre.** El guard usa `to.matched.some(...)`, y `matched` incluye los registros padre, así que los tres hijos quedan protegidos sin repetirlo.

### Tabs como rutas hijas, no como switch de componentes

Ver [[adr-admin-tabs-nested-routes]] para la decisión completa. El resumen: el estado de los filtros de moderación pertenece a la URL, y con un switch de componentes habría que inventarle un store.

La barra de tabs vive en el layout y usa `RouterLink` con `custom` + `v-slot`, leyendo `isExactActive` para aplicar un ternario de clases. **No** se usan las props `active-class`/`exact-active-class`: con ellas las dos variantes conviven en el atributo (`border-transparent` y `border-brand-primary`) y quién gana lo decide el orden de emisión del CSS de Tailwind, no el atributo. Renderizar un `<a>` real además conserva el click del medio y "abrir en pestaña nueva".

Es `isExactActive` y no `isActive` porque `/admin/properties` es prefijo de las otras dos rutas: con activo por prefijo, "Moderación" quedaría encendida estando parado en promociones o importaciones.

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

Se revisó feedback genérico de dashboard (de un LLM externo) y se descartaron sugerencias que no corresponden a ninguna capacidad admin real en este dominio (ej. "crear usuario", "nueva propiedad" — no son acciones admin acá, la creación de propiedad es un flujo del dueño). Se mantuvo solo **"Importar CSV"** porque mapea a un endpoint real (`POST /admin/properties/bulk`), implementado como modal (`BulkUploadPropertiesModal.vue`). Desde el 2026-08-01 vive en la tab de importaciones, no en el header de la sección: es una acción de esa tab, y arriba aparecería también estando en promociones.

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

`emit("queued")` no lo escucha nadie — `AdminPropertiesImportsView.vue` monta el modal con `v-model` y sin `@queued` — y tampoco hay sistema de toasts en el proyecto. O sea que hoy el modal cierra en silencio y el admin no recibe confirmación de nada.

Peor: el `batch_id` se descarta al cerrar y **no existe ningún endpoint que liste los bulk jobs**, solo `GET /admin/properties/bulk/{job_id}/status`, que exige un id que ya haya que tener. El diseño de "revisar el resultado en otro lado" necesita primero un `GET /admin/properties/bulk`; `bulk_jobs` ya guarda todo lo que esa vista mostraría, y de paso le daría un punto de entrada al flujo de retry.

## Forma del panel: tabla, no el card grid del feed

El grid del feed optimiza para "cuál me gusta" — imagen, precio, ambientes. Moderar es "cuáles necesitan acción": más filas visibles a la vez, columnas alineadas para escanear, acciones por fila. Los filtros van **en la misma vista** que la tabla, porque el loop es filtrar → mirar → actuar → filtrar de nuevo, y separarlos obliga a ida y vuelta de navegación.

`GET /admin/properties` es el primero natural a cablear: moderación, verificación, pricing y promociones todas necesitan un `property_id` elegido de una lista. Pagina por offset con `total` — la decisión y por qué no reusa el cursor opaco del feed están en [[adr-admin-offset-pagination]].

## La tabla (2026-07-29)

Construida sobre `@tanstack/vue-table` ([[adr-tanstack-table]]), en dos componentes:

**`components/shared/BaseTable.vue`** — dumb y genérico (`<script setup generic="T">`), sin nada de dominio. Recibe `columns`/`data`/`loading` y reusa `EmptyState` y `BaseSpinner` para los bordes. Dos decisiones adentro:

- Registra **solo `getCoreRowModel`**. Sumar `getSortedRowModel` o `getPaginationRowModel` ordenaría o paginaría las 20 filas ya cargadas, con un resultado que parece global sin serlo.
- Cada celda es `<slot :name="cell.column.id">` con `<FlexRender>` de fallback: las columnas de texto plano no cuestan nada y los badges se escriben como template en el padre, no como `h()` dentro del `columnDef`. Se probó prefijar los slots con `cell:` y **se descartó** — un `:` en el nombre obliga a la sintaxis de argumento dinámico (``#[`cell:status`]``) en cada uso, y `BaseTable` no tiene otros slots con los que colisionar.

Desde el 2026-08-01 `BaseTable` acepta además **selección opcional**: props `rowKey` (función que extrae la clave de una fila) y `selectedKey`, más un emit `rowClick`. Sin `rowKey` no es seleccionable y el comportamiento es idéntico al anterior. La fila activa usa `bg-brand-primary-light`, y **hover y seleccionado son excluyentes a propósito**: Tailwind emite `.hover\:bg-brand-bg:hover` con más especificidad que `.bg-brand-primary-light`, así que llevando las dos clases el hover despintaría la fila activa justo al pasar por encima para clickear otra.

**`components/admin/properties/AdminPropertiesTable.vue`** — 6 columnas: verificación, tipo, operación, precio, creada y estado. Tipo y operación están **separadas** (antes eran una sola celda `Casa · Venta`): juntas se leen como una sola cosa y obligan a parsear la fila para distinguir venta de arriendo. La columna de acciones solo se renderiza si el padre pasa el slot, y el `id` sigue disponible ahí vía `row.original`.

Lo que la tabla **no** puede mostrar es qué propiedad es: el modelo `Property` no tiene título ni dirección, y `id`/`owner_id` son UUIDs. Peor, las columnas elegidas son justo las que salen constantes en datos importados por CSV — misma fecha, mismo estado, todas sin verificar — así que 20 filas se renderizan idénticas salvo el precio. Eso es lo que resuelve el panel de vista previa, no una columna más.

## El panel de vista previa (2026-08-01)

`components/admin/properties/AdminPropertyPreviewPanel.vue`, a la derecha de la tabla en la vista de moderación (60/40). Recibe `propertyId` y nada más; al cambiar, fetchea y renderiza **lo que ve un usuario en el detalle público**, que es el criterio real de moderación.

Reusa las piezas del detalle público sin tocarlas: `PropertyOverview` con los 12 props derivados de `usePropertyDetail`, y `PhotoGalleryPopup` para el visor. `usePropertyDetail` y `buildNeighborhoodMap` ya eran reutilizables; lo único no extraído es el bloque de fetch, que el panel no puede compartir igual (endpoint distinto, `watch` en vez de `onMounted`, y el guard de carrera).

- **Portada sola, no `PropertyPhotoGrid`.** Esa grilla reparte 5 fotos en 4 columnas con `grid-area` fijos; a 40% de ancho quedan miniaturas ilegibles. El click abre el mismo popup.
- **Pega a `/v1/admin/properties/{id}`, nunca al detalle público.** `GetPropertyUseCase` tira 404 cuando `status != active` y no sos el dueño — justo los borradores e inactivos que hay que moderar.
- **`NearbyPlaces` queda afuera a propósito.** Fetchea en su `onMounted` pidiendo 9 isócronas (3 rangos × 3 perfiles) contra ORS por propiedad. Moderar no usa walkability, y como se recorren propiedades *nuevas*, el cache por `property_id` es miss casi siempre. Si alguna vez se agrega tiene que ser detrás de un `v-if`: con `v-show` el componente se monta igual y el costo se paga.

**Guard de carrera.** Moderar es clickear filas rápido, así que las respuestas se pisan: elegir A, elegir B antes de que llegue, y la respuesta de A pinta A estando seleccionada B. Un contador `requestToken` se incrementa en cada selección y cada llamada guarda su copia; toda respuesta cuyo token ya no es el vigente se descarta. Hay tres puntos de descarte porque se encadenan dos `await` (detalle y después el nombre del barrio), y el `finally` también compara para que una respuesta tardía no apague el spinner de la actual.

**Layout.** 60/40 con `flex-[3]`/`flex-[2]`, no `w-3/5` + `w-2/5`: los porcentajes más el `gap-6` superan el 100% y fuerzan encogimiento desparejo. La primera fila se autoselecciona vía `watch` sobre `rows` —no solo en la carga inicial— porque paginar cambia la página entera y la selección previa quedaría marcada en una fila que ya no se ve. El panel está oculto por debajo de `xl`: moderar es desktop-only por decisión, sin fallback en móvil.

**`composables/admin/useAdminProperties.ts`** — reusa `usePagination` con `fetchMore`, siguiendo el precedente de `PublicProfileView` para endpoints paginados por offset; volver atrás nunca pega al servidor. El `total` del servidor se guarda **aparte**, porque `usePagination.total` es `allItems.length` — filas cargadas, no filas que existen.

La vista de moderación (`AdminPropertiesModerationView`) trae tabla, `PaginationArrows`, "Mostrando X-Y de Z", banner de error y el panel de vista previa.

## Lo que falta para que las acciones de moderación funcionen

Las dos acciones (aprobar/rechazar y publicar/despublicar) parecen un par de composables, pero el backend impone máquinas de estado — ver [[properties-service-admin]] para el detalle. Lo que eso implica acá:

- **Los botones dependen del estado de cada fila**, no son un set fijo. Y la tabla de transiciones vive solo en el backend, así que duplicarla en el front arriesga drift silencioso.
- **El primer salto de las importadas ya está resuelto**: desde el 2026-08-01 el import las crea en `pending` ([[properties-service-bulk-create-worker]]), así que aprobar o rechazar aplica directo. Las importadas *antes* de esa fecha siguen en `unverified` y necesitan backfill ([[open-items]]).
- **`verified` es terminal.** Aprobar es irreversible, así que no debería ser un click suelto en una fila.
- **Rechazar necesita motivo** (`rejection_reason`, máx. 500), o sea un modal con textarea.
- **Los tres endpoints devuelven 204 sin cuerpo**, y `useAdminProperties` no sabe recargar la página actual: solo tiene `load()` (que resetea a la 1), `next()` y `prev()`. Falta un `reload()`.
- **Sin sistema de toasts**, el resultado de la acción no tiene dónde mostrarse — el mismo gap que deja al modal de import cerrando en silencio.

## Estado del cableado: 4 de 23 endpoints admin con consumer

En properties-service hay 4 cableados —listado, detalle (el panel de preview) y los dos pasos del bulk upload— y quedan 8 sin consumer: verificación, status, precio estimado, los 4 de promociones y el status de un bulk job. En catalog-service son **11 de 11** sin cablear — `AdminCatalogView` está vacía.

De los tres que faltan para la tab de moderación, los tres son acciones sobre la propiedad seleccionada: `PATCH /verification`, `PATCH /status` y `POST /estimated-price`.

Tampoco hay módulo de API admin. Se evaluó crear `src/api/adminApi.ts` y **se descartó**: las instancias de axios del proyecto son una por servicio, y "admin" no es un servicio — los endpoints admin viven en properties y en catalog. En su lugar la ruta se agregó a `constants/propertiesEndpoints.ts` y el fetch vive en el composable, que es el patrón que ya usan `useFeed` y `useProfileListings`.

## Decisiones diferidas

- **Roles admin granulares** (super-admin / catalog-admin / properties-admin): descartado por prematuro — sin evidencia de necesitarlo, y el diseño de roles de Keycloak (lista de strings) lo hace barato de agregar después. Importante: no sería un cambio solo de `users-service` — `catalog-service` y `properties-service` cada uno valida su propio `require_admin` contra su propio JWT.
- **KPIs reales, gráficos**: bloqueado en tener endpoints de conteo reales. D3 (ya usado en el mapa) probablemente sea excesivo para indicadores simples de tendencia — se reservaría para analítica real con series/multi-dimensión.

## Claims

- El link "Admin" en `NavUser.vue` está gateado por `v-if="authStore.isAdmin"`, apunta a `/admin`, y es un link de primer nivel (no del dropdown) ([components/shared/NavUser.vue](frontend/src/components/shared/NavUser.vue)).
- `/admin/properties` es una ruta padre sin `name` con tres hijos (`""`, `promotions`, `imports`), y solo el padre declara `meta: { requiresAuth: true, requiresAdmin: true }` ([router/routes/admin/properties.ts](frontend/src/router/routes/admin/properties.ts)).
- El guard resuelve `requiresAdmin` con `to.matched.some(...)`, por lo que el `meta` del padre alcanza para proteger a los hijos ([router/index.ts](frontend/src/router/index.ts)).
- `AdminPropertiesLayout.vue` renderiza las tabs con `RouterLink` en modo `custom`, aplicando clases según `isExactActive` ([AdminPropertiesLayout.vue](frontend/src/views/admin/properties/AdminPropertiesLayout.vue)).
- El guard `requiresAdmin` llama `authStore.fillUserData()` si `!authStore.accountId` antes de chequear `isAdmin` — evita que un admin sea rebotado en un deep-link directo ([router/index.ts](frontend/src/router/index.ts)).
- `AdminHomeView.vue` muestra 4 KPI cards con valor placeholder `"—"` — sin wiring a ningún endpoint de conteo todavía ([views/admin/AdminHomeView.vue](frontend/src/views/admin/AdminHomeView.vue)).
- `BulkUploadPropertiesModal.upload()` encadena `POST /v1/admin/properties/bulk/upload-url` → `fetch(upload_url, { method: "PUT" })` → `POST /v1/admin/properties/bulk` con `{ storage_key }`, y emite `queued` con el `batch_id` antes de cerrar ([components/admin/properties/BulkUploadPropertiesModal.vue](frontend/src/components/admin/properties/BulkUploadPropertiesModal.vue)).
- El `PUT` a storage no usa `propertiesApi`: es `fetch` nativo sin credenciales, porque la firma va en el query string ([components/admin/properties/BulkUploadPropertiesModal.vue](frontend/src/components/admin/properties/BulkUploadPropertiesModal.vue)).
- La presigned URL se pide dentro de `upload()`, no en `onFileChange()` ([components/admin/properties/BulkUploadPropertiesModal.vue](frontend/src/components/admin/properties/BulkUploadPropertiesModal.vue)).
- El modal compara `file.size` contra `presigned.max_size_bytes` antes de subir; no hay validación de tamaño del lado del servidor en el flujo de presigned PUT ([components/admin/properties/BulkUploadPropertiesModal.vue](frontend/src/components/admin/properties/BulkUploadPropertiesModal.vue)).
- `AdminPropertiesImportsView.vue` monta `<BulkUploadPropertiesModal v-model="isBulkModalOpen" />` sin listener de `@queued` ([AdminPropertiesImportsView.vue](frontend/src/views/admin/properties/AdminPropertiesImportsView.vue)).
- `AdminPropertiesModerationView.vue` renderiza `AdminPropertiesTable` + `PaginationArrows` + `AdminPropertyPreviewPanel`, alimentados por `useAdminProperties`, con `onMounted(load)` ([AdminPropertiesModerationView.vue](frontend/src/views/admin/properties/AdminPropertiesModerationView.vue)).
- `AdminPropertiesModerationView.vue` autoselecciona la primera fila con un `watch` sobre `rows`, reasignando solo si la seleccionada no está en la página actual ([AdminPropertiesModerationView.vue](frontend/src/views/admin/properties/AdminPropertiesModerationView.vue)).
- `BaseTable.vue` declara `generic="T"` y expone un slot por columna nombrado `cell.column.id`, con `<FlexRender>` como contenido por defecto ([BaseTable.vue](frontend/src/components/shared/BaseTable.vue)).
- `AdminPropertiesTable.vue` define 6 columnas —`verification_status`, `property_type`, `listing_type`, `price`, `created_at`, `status`— y agrega la de acciones solo si el padre pasa el slot ([AdminPropertiesTable.vue](frontend/src/components/admin/properties/AdminPropertiesTable.vue)).
- `BaseTable.vue` acepta `rowKey` y `selectedKey` opcionales y emite `rowClick`; sin `rowKey` no marca ninguna fila como seleccionada ([BaseTable.vue](frontend/src/components/shared/BaseTable.vue)).
- La fila seleccionada de `BaseTable` recibe `bg-brand-primary-light` **en lugar de** `hover:bg-brand-bg`, no además ([BaseTable.vue](frontend/src/components/shared/BaseTable.vue)).
- `AdminPropertyPreviewPanel.vue` pide `PROPERTIES_ENDPOINTS.adminDetail(id)` (`/v1/admin/properties/{id}`), no el detalle público ([AdminPropertyPreviewPanel.vue](frontend/src/components/admin/properties/AdminPropertyPreviewPanel.vue), [propertiesEndpoints.ts](frontend/src/constants/propertiesEndpoints.ts)).
- `AdminPropertyPreviewPanel.vue` descarta respuestas cuyo `requestToken` ya no es el vigente, en los tres puntos donde puede llegar tarde ([AdminPropertyPreviewPanel.vue](frontend/src/components/admin/properties/AdminPropertyPreviewPanel.vue)).
- `AdminPropertyPreviewPanel.vue` monta `PropertyOverview` y `PhotoGalleryPopup`, y no monta `NearbyPlaces` ([AdminPropertyPreviewPanel.vue](frontend/src/components/admin/properties/AdminPropertyPreviewPanel.vue)).
- `useAdminProperties` mantiene `serverTotal` en un ref propio, separado del `total` de `usePagination` ([useAdminProperties.ts](frontend/src/composables/admin/useAdminProperties.ts)).
- La ruta del listado admin vive en `PROPERTIES_ENDPOINTS.adminList`, y el fetch está en el composable — no hay módulo de API admin ([propertiesEndpoints.ts](frontend/src/constants/propertiesEndpoints.ts), [useAdminProperties.ts](frontend/src/composables/admin/useAdminProperties.ts)).
- No existe `src/api/adminApi.ts` — el directorio `src/api/` tiene solo `avmApi`, `catalogApi`, `interceptors`, `propertiesApi` y `usersApi`, uno por servicio ([api/](frontend/src/api)).
- No existe ningún botón de bulk-import en `AdminCatalogView.vue` — el endpoint de catálogo requiere `locality_id`, no es una acción global ([views/admin/catalog/AdminCatalogView.vue](frontend/src/views/admin/catalog/AdminCatalogView.vue)).
- `propertiesApi` tiene `timeout: 8000`, suficiente ahora que los tres requests del modal son cortos ([api/propertiesApi.ts](frontend/src/api/propertiesApi.ts)).
