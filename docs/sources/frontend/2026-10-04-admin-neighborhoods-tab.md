---
title: Tab de barrios del panel admin — filtro en cascada, tabla con siluetas y mapa con vecinos
captured-from: conversation
captured-on: 2026-10-04
participants: [author, claude]
---

## Context
Con el read path admin de barrios ya en catalog-service, se armó la tab de barrios del panel. Hizo falta extender la barra de filtros compartida (cascada y búsqueda), reorganizar los tipos admin y destrabar las llamadas autenticadas a catalog.

## Key conclusions
- `types/admin.ts` se partió en `types/admin/{properties,moderation,promotions,bulk,filters,catalog}.ts`. Los consumidores importan del módulo directo, sin `index.ts` que reexporte; `BulkJobsFilters` salió del composable a `bulk.ts`.
- `AdminFilterDefinition` es una unión por `type`: `select` estático (`type` opcional, así los filtros existentes no cambian), `async-select` (`loadOptions(parents)` + `dependsOn`) y `search`.
- Las opciones dinámicas se cargan con una función que pasa la vista, no con una URL de endpoint: el componente no conoce el cliente HTTP ni la forma de cada respuesta.
- La cascada se resuelve en el `@change` (vacía y recarga hijos y nietos), no en un `watch`: sembrar desde la URL no debe vaciar nada. Un contador por key descarta respuestas viejas.
- `search` aplica con Enter, igual que el botón "Aplicar"; con eso no hace falta debounce.
- `sanitizeFilterQuery` solo valida contra el enum los selects estáticos; `async-select` y `search` los valida el backend.
- `AdminFilterBar` tiene la prop `filtersWidth`: `two-thirds` (default, filtros 2/3 y botón 1/3) o `full` (el botón ocupa solo su ancho). Las clases van literales en el template para que Tailwind no las purgue.
- En catálogo la barra va arriba de `AdminSplitView`, a todo el ancho, porque la cascada filtra la tabla y el mapa; en properties sigue en el slot `#filters`.
- La cascada usa País → Localidad con los `GET` públicos (solo activos). División se suma cuando exista su `GET` admin.
- `catalogApi` pasa a `withCredentials: true` + `applyAuthInterceptor`, como `propertiesApi`: los endpoints `/admin` leen la cookie.
- En dev el front llama a catalog directo (`VUE_APP_CATALOG_URL=http://localhost:8001`), así que con credenciales hizo falta CORS explícito en catalog: orígenes `localhost:8080`/`127.0.0.1:8080` y `allow_credentials=True`, igual que properties. Con credenciales CORS no admite `*`.
- Flujo de la tab: "Aplicar" → `router.push({ query })` → `urlFilters` (computed sobre `route.query`) → `watch(urlFilters, load)` → `GET /admin/neighborhoods`. La petición sale siempre de la URL, nunca del clic.
- `useAdminNeighborhoods` pide página por página usando `current_page`/`total_pages` del backend, sin el cache incremental de `useAdminProperties`. No manda `country_id`: solo acota el select de localidad.
- La silueta es `<svg viewBox="min_lon -max_lat ancho alto"><path d=svg_path/></svg>` con `vector-effect="non-scaling-stroke"`; la Y va negada porque `ST_AsSVG` la invierte.
- El panel usa un componente nuevo `NeighborhoodMap.vue` y no `MapUser.vue` (pensado para marcadores con cluster y sin `fitBounds`): vista fija sin zoom ni arrastre, `fitBounds` sobre la geometría con 24 px de padding, centroide con zoom 15 si no hay geometría, y emite `map.getBounds()` como bbox para pedir vecinos.
- El `watch` del mapa observa geometría, latitud y longitud por separado: con `:center="[lat, lon]"` inline se formaba un ciclo vecinos → re-render → reencuadre → vecinos.
- axios necesita `paramsSerializer: { indexes: null }` para mandar `bbox` repetido; por defecto arma `bbox[]=`, que FastAPI no entiende.
- Si el pedido de vecinos falla (p. ej. bbox mayor al tope de ~15 km), el mapa queda sin vecinos y el panel no se rompe.
- En macOS, Docker Desktop corre en una VM con tope fijo (aquí ~7,7 GB de 16 GB). Con ORS en `-Xmx6g`, MLflow, Keycloak, Kafka, el devcontainer y un build de webpack, el kernel de la VM mató ORS, Kafka, Keycloak y el build. El build del front pasa en el host o con `NODE_OPTIONS=--max-old-space-size=1536`.

## Open questions
- ¿Subir la memoria de Docker Desktop a 11–12 GB, bajar el heap de ORS a 2–3 GB (confirmar con una isócrona), o ambas?
- Los orígenes CORS de catalog y properties están fijos en código; para staging/prod tendrían que venir de configuración.
- Bajo `xl` el panel se oculta; si la ventana se agranda con el mapa montado, Leaflet puede necesitar `invalidateSize()`.

## Next steps
- Probar la tab en el navegador: cascada, URL, paginación, encuadre y vecinos al cambiar de fila.
- `GET` admin de países, divisiones y localidades para completar la cascada (y las otras tres tabs).
- Acciones del panel: editar, reemplazar geometría y desactivar.
- Commitear el trabajo del front en `feat/front-admin-panel`.
