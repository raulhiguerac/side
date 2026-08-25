---
title: Panel admin (frontend)
status: draft
last-verified: 2026-08-24
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
  - "[[adr-moderation-panel-staged-form]]"
  - "[[adr-verification-reversible-lifecycle]]"
  - "[[adr-transitions-served-by-backend]]"
  - "[[adr-promotions-own-subtab]]"
  - "[[adr-admin-filters-in-query-params]]"
  - "[[open-items]]"
sources:
  - ../../../sources/frontend/2026-07-16-admin-panel-nav-and-hub.md
  - ../../../sources/properties-service/2026-07-16-bulk-create-sync-timeout-risk.md
  - ../../../sources/frontend/2026-07-28-admin-panel-groundwork.md
  - ../../../sources/frontend/2026-07-29-admin-table-tanstack-and-cleanup.md
  - ../../../sources/properties-service/2026-07-29-moderation-state-machines-block-imports.md
  - ../../../sources/frontend/2026-08-01-admin-panel-tabs-moderation-preview.md
  - ../../../sources/frontend/2026-08-02-moderation-panel-form-over-buttons.md
  - ../../../sources/frontend/2026-08-09-moderation-wiring-and-promotions-shell.md
  - ../../../sources/frontend/2026-08-09-promotions-tab-wired.md
  - ../../../sources/frontend/2026-08-24-admin-url-filters-and-imports-tab.md
---

## TL;DR

Panel admin embebido en la app existente (no un subdominio separado): un link condicional en el nav, rutas gateadas por rol, y una vista hub que orquesta hacia propiedades y catálogo. Desde el 2026-08-01 la sección de propiedades es un layout con tres tabs como rutas hijas (moderación, promociones, importaciones), y la de moderación combina tabla paginada + panel de vista previa. Desde el 2026-08-02 el panel lleva además el **formulario de moderación**, y desde el 2026-08-09 ese guardado **llega a la API**: moderar funciona punta a punta. Promociones quedó cableada el mismo día en dos sub-tabs: activas (listar y quitar) y promocionar (elegir y crear). Desde el 2026-08-24 los filtros de la cola viven en la URL y la tab de importaciones lista las corridas contra su endpoint nuevo. Lo que sigue faltando es el relanzar de un import y toda la sección de catálogo.

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
| `/admin/properties` (`path: ""`) | `admin-properties` | `moderation/AdminModerationView.vue` |
| `/admin/properties/promotions` | — | `promotions/AdminPromotionsLayout.vue` (padre con sub-tabs) |
| `/admin/properties/promotions` (`path: ""`) | `admin-properties-promotions` | `promotions/AdminPromotionsActiveView.vue` |
| `/admin/properties/promotions/new` | `admin-properties-promotions-new` | `promotions/AdminPromotionsCreateView.vue` |
| `/admin/properties/imports` | `admin-properties-imports` | `imports/AdminImportsView.vue` |
| `/admin/catalog` | `admin-catalog` | `views/admin/catalog/AdminCatalogView.vue` |

`home.ts`/`properties.ts`/`catalog.ts` se combinan en un barrel `index.ts` (`adminRoutes`) importado en `router/index.ts`.

Dos detalles del árbol de propiedades (2026-08-01):

- **El padre no lleva `name`.** Tiene un hijo con `path: ""`, y nombrar a los dos hace ambiguo un `push({ name: "admin-properties" })`. El nombre vive en el hijo, que es el destino real.
- **`meta` va solo en el padre.** El guard usa `to.matched.some(...)`, y `matched` incluye los registros padre, así que los tres hijos quedan protegidos sin repetirlo.

### Tabs como rutas hijas, no como switch de componentes

Ver [[adr-admin-tabs-nested-routes]] para la decisión completa. El resumen: el estado de los filtros de moderación pertenece a la URL, y con un switch de componentes habría que inventarle un store.

La barra de tabs vive en `components/admin/shared/AdminTabsNav.vue` (extraída el 2026-08-09, cuando promociones necesitó la suya) y usa `RouterLink` con `custom` + `v-slot` para aplicar un ternario de clases. **No** se usan las props `active-class`/`exact-active-class`: con ellas las dos variantes conviven en el atributo (`border-transparent` y `border-brand-primary`) y quién gana lo decide el orden de emisión del CSS de Tailwind, no el atributo. Renderizar un `<a>` real además conserva el click del medio y "abrir en pestaña nueva".

**Cada tab elige su propio matching**: si su ruta es prefijo de la de otra tab, matchea exacto; si no, por prefijo. Antes el nav entero era `isExactActive` porque `/admin/properties` es prefijo de las otras dos, y con activo por prefijo "Moderación" quedaría encendida estando en promociones. Esa regla global dejó de servir al aparecer las sub-rutas: `/admin/properties/promotions/new` apagaba la tab "Promociones". Derivarlo de la lista de tabs cubre los dos casos sin que nadie tenga que acordarse.

`stretch` reparte el ancho entre las tabs — lo usa el nav de primer nivel, no el de promociones.

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

> **Cerrado el 2026-08-24.** El endpoint existe ([[properties-service-admin]]) y la tab lo consume: `useBulkJobs` lista las corridas y el panel de la derecha pide los errores por id. Sigue abierto lo otro que decía este párrafo — el toast de confirmación al encolar (el `emit("queued")` sigue sin escucha) y el flujo de retry, que necesita un endpoint propio.

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

**Layout.** 60/40 con `flex-[3]`/`flex-[2]`, no `w-3/5` + `w-2/5`: los porcentajes más el `gap-6` superan el 100% y fuerzan encogimiento desparejo. El panel está oculto por debajo de `xl`: moderar es desktop-only por decisión, sin fallback en móvil.

Desde el 2026-08-09 ese layout es `components/admin/shared/AdminSplitView.vue` (slots `#table`, `#footer`, `#panel`), y la selección de fila es `composables/admin/useRowSelection.ts`. Las dos salieron de esta vista cuando promociones necesitó lo mismo. La regla de la selección: autoselecciona la primera fila, y al cambiar la lista —paginar, refetchear— la reasigna **solo si la seleccionada ya no está**; si sigue visible no se toca, y con lista vacía queda en `null`.

**`composables/admin/useAdminProperties.ts`** — reusa `usePagination` con `fetchMore`, siguiendo el precedente de `PublicProfileView` para endpoints paginados por offset; volver atrás nunca pega al servidor. El `total` del servidor se guarda **aparte**, porque `usePagination.total` es `allItems.length` — filas cargadas, no filas que existen.

La vista de moderación (`AdminModerationView`) trae tabla, `PaginationArrows`, "Mostrando X-Y de Z", banner de error y el panel de vista previa.

## Moderar se hace en el panel, no en la tabla (2026-08-02)

La decisión completa y las alternativas descartadas están en [[adr-moderation-panel-staged-form]]. El resumen: **moderar exige mirar**, y aprobar desde una fila de la tabla es aprobar sin ver las fotos. Las columnas disponibles —tipo, precio, fecha— no alcanzan para decidir nada.

Consecuencia práctica: la tabla no cambió ni una línea. Como ninguna vista pasa el slot `#actions`, `AdminPropertiesTable` no agrega la columna (el chequeo `slots.actions`), y el click en fila sigue siendo solo selección.

### Formulario con borrador, no botones instantáneos

Se construyó primero una barra de botones (`AdminModerationActionBar.vue`) y se borró. El problema decisivo no era estético: con la tabla filtrada por `verification_status=pending`, cambiar la verificación **saca la fila de la lista antes** de poder tocar el status. Moderar los dos ejes no era lento, era imposible.

`AdminModerationForm.vue` lo reemplaza — dos selects, cambios en borrador, un "Guardar". La fila sale del filtro una sola vez, cuando el trabajo terminó.

Cuatro cosas que resuelve de paso:

- **Los selects ofrecen el estado actual más los destinos legales, y nada más.** Llegar a `verified` desde `unverified` son dos guardados por construcción, porque `verified` no está en la lista. La regla de los dos saltos se comunica en vez de aparecer como un 409.
- **El motivo del rechazo es inline**, bajo el select, solo al elegir "Rechazada", con contador de 500 y "Guardar" deshabilitado mientras esté vacío. Coincide con el `model_validator` que el backend agregó el mismo día ([[properties-service-admin]]): el motivo es obligatorio al rechazar y prohibido en el resto.
- **Aprobar dejó de ser irreversible.** `verified` ya no es terminal ([[adr-verification-reversible-lifecycle]]), así que desde ahí el select ofrece "Reencolar" y "Revocar".
- **El formulario va detrás de `v-if="property"`**, así que ni se dibuja mientras la foto carga — no se puede moderar a ciegas.

### El formulario es tonto; el composable irá en la vista

Props: `status`, `verificationStatus`, `saving`, `successMessage`, `errorMessage`. Emite `save` con **solo lo que cambió**. El panel lo alimenta desde el detalle que ya trajo —`PropertyDetailSchema` incluye ambos campos— y reenvía el evento hacia arriba con el `propertyId`.

El composable de ejecución pertenece a `AdminModerationView`, la única que tiene la lista, la selección y el refetch (cableado el 2026-08-09, ver más abajo). Dejar la llamada fuera del formulario y fuera del panel evita atar a cualquiera de los dos a esta pantalla.

**Los destinos legales ya no se duplican acá.** `constants/moderationTransitions.ts` espejaba las dos tablas del backend y se **borró** el 2026-08-09: el detalle admin las publica por property (`allowed_verification_targets`, `allowed_status_targets`) y el formulario las recibe como prop, así que solo les pone etiqueta. Ver [[adr-transitions-served-by-backend]].

Las dos props llevan default `[]`. Front y backend se despliegan por separado, y contra un backend viejo esos campos llegan `undefined`: sin default el `.map` reventaba el panel entero. Con default, el select muestra solo el estado actual —no se puede mover nada— y el panel sigue en pie.

`ModerationPayload` vive en `types/admin.ts` y no exportado del SFC: el shim de `*.vue` solo declara el default export, así que un import de tipo con nombre desde un componente rompería bajo `vue-tsc`.

## El guardado, cableado punta a punta (2026-08-09)

`composables/admin/useModerateProperty.ts` traduce el payload del formulario a **uno o dos PATCH**, y la vista es quien lo llama: es la única que tiene la lista, la selección y el refetch.

- **La verificación va primero.** Si solo entra uno de los dos requests, conviene que sea el que decide si la property sigue en la cola: aprobada sin publicar es un estado revisable, publicada sin resolver es una property que se escapó de la cola.
- **`moderate()` devuelve "algo quedó escrito", no "salió todo bien".** Un fallo parcial deja igual de viejo lo que se está mostrando, así que obliga a refetchear; el mensaje distingue el caso ("se guardó la verificación, pero el estado no cambió") para que el reintento no choque contra la mitad ya aplicada.
- **El 409 no puede explicar qué pasó.** `base_error_handler` descarta el `context`, así que `{current, target}` no viaja: el mensaje dice qué hacer —recargar— en vez de qué falló ([[properties-service-admin]]).

Refrescar después son dos cosas distintas:

- **La lista.** `useAdminProperties.reload()` refetchea la página actual con los filtros vigentes; `load()` no sirve porque resetea a la 1 y devolvería al principio a quien modera en la página 5. Por debajo usa `usePagination.replaceCurrentPage`, que **descarta las páginas siguientes**: al salir una fila del filtro todas se corren un lugar, y conservarlas mostraría filas duplicadas al avanzar. Si la página queda vacía, retrocede a la anterior.
- **El panel.** Expone `refresh()` vía `defineExpose`, porque su `watch` mira `propertyId` y tras moderar cambia el estado, no el id. La vista se lo pide **solo si la fila sobrevivió al refetch**: si la selección se movió, el watcher del panel ya está cargando la nueva y pedirlo sería fetchear dos veces.

La división queda: `load()` para aplicar o cambiar filtros, `reload()` para refrescar después de moderar.

## Lo que falta para cerrar la moderación

- ~~**El filtro por `verification_status`.**~~ **Hecho el 2026-08-24**: la tab filtra por `verification_status` y `status` desde la URL (ver abajo y [[adr-admin-filters-in-query-params]]). Sigue pendiente el matiz que traía este ítem: `useRowSelection` salta a la primera fila en vez de conservar el índice, así que moderar la fila 7 deja al panel parado en la 1.
- **Las importadas antes del 2026-08-01 siguen en `unverified`** y necesitan backfill ([[open-items]]).
- **El precio estimado quedó fuera del panel**, y no solo por alcance: `admin_estimated_price` y `ml_estimated_price` no están en ningún schema de respuesta, así que el input sería write-only — escribir un precio sin ver el guardado ni el del modelo. Además no es moderación: es una señal de pricing para el AVM.

## Promociones: dos sub-tabs, armazón montado (2026-08-09)

La decisión de por qué promocionar no vive en el panel de moderación está en [[adr-promotions-own-subtab]]. La forma elegida fue **tabla + preview**, la misma que moderación, y no un grid de cards: el grid se ve mejor pero no tiene dónde poner la prioridad ni comparar vencimientos, que es lo único que la promoción decide.

- **Activas** (`AdminPromotionsActiveView`) — lista `GET /admin/promotions`, que desde el 2026-08-09 devuelve promociones y no cards ([[properties-service-admin]]), así que la tabla muestra **prioridad** y **vencimiento**, este último con los días restantes calculados ("en 5 días", "vence hoy", "vencida"): la fecha sola obliga a hacer la cuenta mentalmente. Se selecciona por `property_id` y no por el id de la fila, porque lo que el panel muestra es la property — para eso `useRowSelection` acepta un extractor de clave.
- **Promocionar** (`AdminPromotionsCreateView`) — reusa `useAdminProperties` y `AdminPropertiesTable` con `{ status: "active", is_promoted: false }`, las dos condiciones que valida `CreatePromotionUseCase`. El filtro `is_promoted` se agregó al backend el mismo día en vez de cruzar las promociones en memoria.

### El pie del panel es un slot

`AdminPropertyPreviewPanel` expone `#footer` con la property ya cargada como slot prop, y perdió las props de guardado y el emit `save`. Antes traía el `AdminModerationForm` fijo adentro, así que las vistas de promociones habrían mostrado el formulario de moderación con un "Guardar" que no escuchaba nadie. De paso, moderación se ahorró el reenvío de dos saltos que tenía (formulario → panel → vista).

Cada tab pone el suyo:

- **Promocionar** — `AdminPromotionForm`: chips 7/15/30 más campo libre acotado a 1–60, prioridad como dropdown 1–5, y la fecha de vencimiento calculada en el cliente debajo de la duración, porque `promoted_days` es un número abstracto y la fecha es lo que se quiere saber. Emite `{ promotedDays, priority }`; el `property_id` lo pone la vista desde el slot prop.
- **Activas** — un botón "Quitar" que solo abre `RemovePromotionModal`. El botón que dispara el DELETE está en el modal, y el modal es **presentacional**: emite `confirm`/`close` y no hace el request, a diferencia de `DeletePropertyModal`, que se autogestiona y reporta con un `alert()`. Se cierra pase lo que pase y el error queda en el pie del panel, que es donde el admin sigue mirando.

Dos diferencias con el guardado de moderación:

- **`usePromoteProperty` puede decir qué falló.** Los dos 409 —`DUPLICATE_ACTIVE_PROMOTION` y `PROPERTY_NOT_READY_FOR_PROMOTION`— llegan distinguidos por `code`, que el handler del backend sí conserva; el 409 de transiciones no tiene esa suerte.
- **Tras promocionar no se refresca el panel, solo la lista.** `PropertyDetailSchema` no lleva `is_promoted`, así que nada de lo que se está mirando cambió, y la fila sale sola del listado por dejar de cumplir `is_promoted: false`.

`remove()` vive dentro de `useActivePromotions` y no en un composable aparte: acá el dueño de la lista y el de la acción son el mismo, y tras el DELETE hay que releerla igual. Ese composable **pagina contra el servidor sin acumular páginas en memoria**, a diferencia de `useAdminProperties`: quitar una promoción corre a todas las siguientes, así que una copia local quedaría desalineada al primer borrado.

## Organización de `admin/` (2026-08-09)

```
components/admin/
  shared/        AdminSplitView.vue · AdminTabsNav.vue
  properties/    AdminPropertiesTable.vue · AdminPropertyPreviewPanel.vue
    moderation/  AdminModerationForm.vue
    promotions/  AdminPromotionsTable.vue
    imports/     BulkUploadPropertiesModal.vue
```

`AdminPropertiesTable` y `AdminPropertyPreviewPanel` quedan en la raíz de `properties/` a propósito: la tabla la usan moderación y promocionar, y el panel las tres vistas. Meterlas bajo `moderation/` mentiría sobre quién las consume. Las vistas siguen el mismo corte (`views/admin/properties/{moderation,promotions,imports}/`), y ahí las que ya vivían en su carpeta perdieron el `Properties` redundante del nombre.

## Los filtros viven en la URL (2026-08-24)

`AdminFilterBar` es un componente tonto: recibe las definiciones de filtro —`key`, `label` y el `{ value: label }` de las constantes de estado—, mantiene un borrador local y solo lo emite al hacer click. Quien manda es la vista, que empuja los valores a la query y recarga desde ahí. El detalle de por qué, y las alternativas descartadas, están en [[adr-admin-filters-in-query-params]].

Lo que hay que saber al usarlo:

- **La barra entra por un slot `filters` de `AdminSplitView`**, en la columna izquierda y sobre la tabla, que es lo que filtra. El slot es opcional y no deja margen si nadie lo llena.
- **Aplicar sin filtros emite `{}`**, no `status=""`. La ausencia de param significa "sin filtrar"; el string vacío sería un valor inválido contra el enum del backend.
- **El borrador se siembra con todas las keys, incluso vacías.** Sobre una key ausente el `<option value="">` no tiene qué marcar como seleccionada, y el select aparecería en blanco tras un reload con filtro puesto.
- **`has_errors` viaja como `"true"`/`"false"`** y lo parsea Pydantic del lado del backend; los filtros de fecha no se exponen porque el componente todavía no tiene inputs de fecha.

## La tab de importaciones, cableada (2026-08-24)

Antes de cablearla se montó como **mock estático** —datos ficticios, banner de aviso, botones inertes— para revisar el layout mientras el endpoint no existía. Eso permitió discutir columnas y panel sin backend, y el reemplazo por datos reales fue un cambio acotado.

La forma final reusa el patrón de las otras tabs con una diferencia que importa: **el panel recibe la fila entera, no solo el id**. `GET /admin/properties/bulk/{job_id}/status` devuelve el estado y los errores, pero no `expires_at` ni `retry_of_job_id`, que son los que deciden si el CSV todavía se puede relanzar — y esos ya vinieron en el listado. El fetch de errores ni siquiera se dispara si la fila trae `error_count: 0`.

`useBulkJobs` se calcó de `useActivePromotions` (pide siempre la página al servidor) y **no** de `useAdminProperties` (que acumula páginas en memoria vía `usePagination`): relanzar un job agrega una corrida arriba y correría todas las demás, así que una copia local se desalinearía sola.

Quedan dos botones puestos y sin acción, a la espera de backend: relanzar el job y descargar el CSV de errores. Y dos límites del diseño que solo se ven con datos reales: un job `failed` global muestra `0/0` sin explicar por qué —`bulk_jobs` guarda errores por fila, no un mensaje de job— y una cadena de varios reintentos del mismo archivo es difícil de seguir en una lista plana.

## Estado del cableado: 11 de 23 endpoints admin con consumer (2026-08-24)

El total volvió a 23 con el `GET /admin/properties/bulk` nuevo ([[properties-service-admin]]). En properties-service hay **11 de 12** cableados: listado, detalle, los dos pasos del bulk upload, los dos PATCH de moderación, los tres de promociones, y desde el 2026-08-24 el historial de imports y el status por `job_id` —que hasta entonces no tenía consumer y ahora alimenta los errores del panel—. Queda **uno** sin cablear: `POST /admin/properties/{id}/estimated-price`, write-only porque ningún schema de respuesta devuelve esos campos, y que además no invalida cache ([[open-items]]). En catalog-service siguen **11 de 11** sin cablear — `AdminCatalogView` está vacía.

Tampoco hay módulo de API admin. Se evaluó crear `src/api/adminApi.ts` y **se descartó**: las instancias de axios del proyecto son una por servicio, y "admin" no es un servicio — los endpoints admin viven en properties y en catalog. En su lugar la ruta se agregó a `constants/propertiesEndpoints.ts` y el fetch vive en el composable, que es el patrón que ya usan `useFeed` y `useProfileListings`.

## Decisiones diferidas

- **Roles admin granulares** (super-admin / catalog-admin / properties-admin): descartado por prematuro — sin evidencia de necesitarlo, y el diseño de roles de Keycloak (lista de strings) lo hace barato de agregar después. Importante: no sería un cambio solo de `users-service` — `catalog-service` y `properties-service` cada uno valida su propio `require_admin` contra su propio JWT.
- **KPIs reales, gráficos**: bloqueado en tener endpoints de conteo reales. D3 (ya usado en el mapa) probablemente sea excesivo para indicadores simples de tendencia — se reservaría para analítica real con series/multi-dimensión.

## Claims

- El link "Admin" en `NavUser.vue` está gateado por `v-if="authStore.isAdmin"`, apunta a `/admin`, y es un link de primer nivel (no del dropdown) ([components/shared/NavUser.vue](frontend/src/components/shared/NavUser.vue)).
- `/admin/properties` es una ruta padre sin `name` con tres hijos (`""`, `promotions`, `imports`), donde `promotions` es a su vez padre de `""` y `new`, y solo el padre de todo declara `meta: { requiresAuth: true, requiresAdmin: true }` ([router/routes/admin/properties.ts](frontend/src/router/routes/admin/properties.ts)).
- El guard resuelve `requiresAdmin` con `to.matched.some(...)`, por lo que el `meta` del padre alcanza para proteger a los hijos ([router/index.ts](frontend/src/router/index.ts)).
- `AdminTabsNav.vue` renderiza las tabs con `RouterLink` en modo `custom` y elige entre `isExactActive` e `isActive` según si la ruta de la tab es prefijo de la de otra ([AdminTabsNav.vue](frontend/src/components/admin/shared/AdminTabsNav.vue)).
- `AdminPropertiesLayout.vue` y `AdminPromotionsLayout.vue` usan el mismo `AdminTabsNav`, y solo el primero pasa `stretch` ([AdminPropertiesLayout.vue](frontend/src/views/admin/properties/AdminPropertiesLayout.vue), [AdminPromotionsLayout.vue](frontend/src/views/admin/properties/promotions/AdminPromotionsLayout.vue)).
- El guard `requiresAdmin` llama `authStore.fillUserData()` si `!authStore.accountId` antes de chequear `isAdmin` — evita que un admin sea rebotado en un deep-link directo ([router/index.ts](frontend/src/router/index.ts)).
- `AdminHomeView.vue` muestra 4 KPI cards con valor placeholder `"—"` — sin wiring a ningún endpoint de conteo todavía ([views/admin/AdminHomeView.vue](frontend/src/views/admin/AdminHomeView.vue)).
- `BulkUploadPropertiesModal.upload()` encadena `POST /v1/admin/properties/bulk/upload-url` → `fetch(upload_url, { method: "PUT" })` → `POST /v1/admin/properties/bulk` con `{ storage_key }`, y emite `queued` con el `batch_id` antes de cerrar ([BulkUploadPropertiesModal.vue](frontend/src/components/admin/properties/imports/BulkUploadPropertiesModal.vue)).
- El `PUT` a storage no usa `propertiesApi`: es `fetch` nativo sin credenciales, porque la firma va en el query string ([BulkUploadPropertiesModal.vue](frontend/src/components/admin/properties/imports/BulkUploadPropertiesModal.vue)).
- La presigned URL se pide dentro de `upload()`, no en `onFileChange()` ([BulkUploadPropertiesModal.vue](frontend/src/components/admin/properties/imports/BulkUploadPropertiesModal.vue)).
- El modal compara `file.size` contra `presigned.max_size_bytes` antes de subir; no hay validación de tamaño del lado del servidor en el flujo de presigned PUT ([BulkUploadPropertiesModal.vue](frontend/src/components/admin/properties/imports/BulkUploadPropertiesModal.vue)).
- `AdminImportsView.vue` monta `<BulkUploadPropertiesModal v-model="isBulkModalOpen" />` sin listener de `@queued` ([AdminImportsView.vue](frontend/src/views/admin/properties/imports/AdminImportsView.vue)).
- `AdminModerationView.vue` compone `AdminSplitView` con `AdminPropertiesTable`, `PaginationArrows` y `AdminPropertyPreviewPanel`, alimentados por `useAdminProperties`, con `onMounted(load)` ([AdminModerationView.vue](frontend/src/views/admin/properties/moderation/AdminModerationView.vue)).
- `useRowSelection` autoselecciona la primera fila y reasigna solo si la seleccionada no está en la lista actual; con lista vacía deja `selectedId` en `null` ([useRowSelection.ts](frontend/src/composables/admin/useRowSelection.ts)).
- `AdminSplitView.vue` expone los slots `table`, `footer` y `panel`, y no conoce el dominio de lo que se lista ([AdminSplitView.vue](frontend/src/components/admin/shared/AdminSplitView.vue)).
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
- Ninguna vista declara `<template #actions>`, así que `AdminPropertiesTable` no agrega la columna de acciones ([AdminModerationView.vue](frontend/src/views/admin/properties/moderation/AdminModerationView.vue), [AdminPropertiesTable.vue](frontend/src/components/admin/properties/AdminPropertiesTable.vue)).
- `AdminModerationForm.vue` construye las opciones de sus dos selects desde las props `allowedVerificationTargets` y `allowedStatusTargets`, que por default son `[]` ([AdminModerationForm.vue](frontend/src/components/admin/properties/moderation/AdminModerationForm.vue)).
- No existe ninguna tabla de transiciones en el frontend: `constants/moderationTransitions.ts` fue eliminado ([constants/](frontend/src/constants)).
- `AdminModerationForm.vue` no importa `propertiesApi`: emite `save` con los campos que cambiaron y nada más ([AdminModerationForm.vue](frontend/src/components/admin/properties/moderation/AdminModerationForm.vue)).
- El textarea del motivo solo se renderiza cuando el target de verificación elegido es `rejected`, y bloquea "Guardar" si está vacío ([AdminModerationForm.vue](frontend/src/components/admin/properties/moderation/AdminModerationForm.vue)).
- `AdminPropertyPreviewPanel.vue` tipa la respuesta como `AdminPropertyDetail` y le pasa al formulario los `allowed_*` que trae el detalle ([AdminPropertyPreviewPanel.vue](frontend/src/components/admin/properties/AdminPropertyPreviewPanel.vue), [types/admin.ts](frontend/src/types/admin.ts)).
- `AdminPropertyPreviewPanel.vue` monta el formulario detrás de `v-if="property"` y reenvía su `save` con el `propertyId` ([AdminPropertyPreviewPanel.vue](frontend/src/components/admin/properties/AdminPropertyPreviewPanel.vue)).
- `useAdminProperties` expone `load`, `reload`, `next` y `prev`; `reload` refetchea la página actual con los filtros vigentes y `load` resetea a la 1 ([useAdminProperties.ts](frontend/src/composables/admin/useAdminProperties.ts)).
- `usePagination.replaceCurrentPage` reemplaza la página visible y trunca las siguientes, y retrocede una página si la nueva viene vacía ([usePagination.ts](frontend/src/composables/shared/usePagination.ts)).
- `useModerateProperty.moderate()` manda el PATCH de verificación antes que el de status y devuelve `true` si al menos uno se aplicó ([useModerateProperty.ts](frontend/src/composables/admin/useModerateProperty.ts)).
- `AdminPropertyPreviewPanel.vue` expone `refresh()` con `defineExpose`, y `AdminModerationView` solo lo invoca si la fila seleccionada sobrevivió al `reload()` ([AdminPropertyPreviewPanel.vue](frontend/src/components/admin/properties/AdminPropertyPreviewPanel.vue), [AdminModerationView.vue](frontend/src/views/admin/properties/moderation/AdminModerationView.vue)).
- `PROPERTIES_ENDPOINTS` declara `adminVerification` y `adminStatus`, y `useModerateProperty` es su único consumidor ([propertiesEndpoints.ts](frontend/src/constants/propertiesEndpoints.ts), [useModerateProperty.ts](frontend/src/composables/admin/useModerateProperty.ts)).
- `AdminPromotionsCreateView.vue` pide el listado admin con `{ status: "active", is_promoted: false }` ([AdminPromotionsCreateView.vue](frontend/src/views/admin/properties/promotions/AdminPromotionsCreateView.vue)).
- `AdminPromotionsActiveView.vue` lista `GET /v1/admin/promotions` vía `useActivePromotions` y selecciona por `property_id` ([AdminPromotionsActiveView.vue](frontend/src/views/admin/properties/promotions/AdminPromotionsActiveView.vue), [useActivePromotions.ts](frontend/src/composables/admin/useActivePromotions.ts)).
- `AdminPropertyPreviewPanel.vue` no importa ningún formulario: expone un slot `footer` con la property cargada como slot prop ([AdminPropertyPreviewPanel.vue](frontend/src/components/admin/properties/AdminPropertyPreviewPanel.vue)).
- `AdminPromotionForm.vue` acota la duración a 1–60 días y la prioridad a un select de 1 a 5, y no llama a la API ([AdminPromotionForm.vue](frontend/src/components/admin/properties/promotions/AdminPromotionForm.vue)).
- `RemovePromotionModal.vue` no hace el DELETE: emite `confirm` y `close` ([RemovePromotionModal.vue](frontend/src/components/admin/properties/promotions/RemovePromotionModal.vue)).
- `useActivePromotions` expone `load`, `reload`, `remove`, `next` y `prev`, y pide cada página al servidor sin acumular las anteriores ([useActivePromotions.ts](frontend/src/composables/admin/useActivePromotions.ts)).
- `usePromoteProperty` distingue `DUPLICATE_ACTIVE_PROMOTION` de `PROPERTY_NOT_READY_FOR_PROMOTION` leyendo `code` de la respuesta ([usePromoteProperty.ts](frontend/src/composables/admin/usePromoteProperty.ts)).
- `useRowSelection` acepta un extractor de clave y por defecto usa `row.id` ([useRowSelection.ts](frontend/src/composables/admin/useRowSelection.ts)).
- `AdminPromotionsTable.vue` usa `row.property_id` como `rowKey` y muestra columnas de prioridad y vencimiento ([AdminPromotionsTable.vue](frontend/src/components/admin/properties/promotions/AdminPromotionsTable.vue)).
- `AdminFilterBar` emite `apply` solo desde el click y omite los valores vacíos ([AdminFilterBar.vue](frontend/src/components/admin/shared/AdminFilterBar.vue)).
- `AdminModerationView` filtra por `verification_status` y `status`, y `AdminImportsView` por `status` y `has_errors`, en ambos casos desde `route.query` ([AdminModerationView.vue](frontend/src/views/admin/properties/moderation/AdminModerationView.vue), [AdminImportsView.vue](frontend/src/views/admin/properties/imports/AdminImportsView.vue)).
- `useBulkJobs` pide siempre la página al servidor y no usa `usePagination` ([useBulkJobs.ts](frontend/src/composables/admin/useBulkJobs.ts)).
- `AdminBulkJobPanel` recibe la fila como prop y solo llama a `adminBulkJobStatus` cuando `error_count` es distinto de cero ([AdminBulkJobPanel.vue](frontend/src/components/admin/properties/imports/AdminBulkJobPanel.vue)).
- `BulkJobRow` declara `error_count` y no un array de errores ([types/admin.ts](frontend/src/types/admin.ts)).
- El botón de relanzar de `AdminBulkJobPanel` no tiene handler: se deshabilita si el job está `pending` o si `expires_at` ya pasó ([AdminBulkJobPanel.vue](frontend/src/components/admin/properties/imports/AdminBulkJobPanel.vue)).
- `AdminImportsView` ya no monta el empty state fijo: renderiza `AdminSplitView` con la tabla de corridas ([AdminImportsView.vue](frontend/src/views/admin/properties/imports/AdminImportsView.vue)).
