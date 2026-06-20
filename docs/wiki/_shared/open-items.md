---
title: Open items — gaps y deuda técnica cross-service
status: draft
last-verified: 2026-06-16
owners: [_shared]
related:
  - "[[architecture]]"
  - "[[project-roadmap-2026]]"
  - "[[properties-service]]"
  - "[[properties-service-search]]"
  - "[[users-service]]"
  - "[[catalog-service]]"
  - "[[avm-training]]"
  - "[[adr-estimated-price-dual-signal]]"
  - "[[adr-gmaps-places-geocoding]]"
sources: [../../sources/properties-service/2026-05-28-foundational-exploration.md, ../../sources/users-service/2026-05-28-foundational-exploration.md, ../../sources/frontend/2026-06-04-feed-filters-contract.md, ../../sources/_shared/2026-06-09-mvp-audit-scores.md]
---

## TL;DR

Backlog vivo de gaps detectados al documentar la wiki (2026-05-28): cosas que el código aún no tiene pero la arquitectura asume, contradicciones, y bordes operativos. Marcá `[x]` a medida que se cierren. No es un reemplazo del issue tracker — es la vista cross-service para no perder contexto entre sesiones. Ver [[project-roadmap-2026]] para la visión de alto nivel por fases.

> Convención: cada ítem enlaza a la página/ADR que lo origina. Si cerrás uno, marcá `[x]` en su lugar y movelo a `## Cerrados` — nunca borres el texto. Si aplica, actualizá el claim de la página de origen.

---

## Fase 2 — Properties (front pendiente)

- [ ] **Vista detalle de propiedad (`/properties/:id`) — parcial.** Click en card del feed → página de detalle con galería completa, info del listing, precio estimado AVM, mapa con ubicación. **Update 2026-06-12 — la base ya existe**: `PropertyDetailView.vue` + `usePropertyDetail.ts` en `/listing/:id` y el endpoint `GET /v1/properties/{property_id}` ([properties.py:109](backend/properties-service/src/app/api/routes/properties.py#L109)). Falta: **popup/galería de fotos**. Las isócronas/POIs ya están implementadas (cerrado arriba). Ver [[properties-service-listing]], [[frontend-architecture]].
- [ ] **Form publicar propiedad + gestión de listings del dueño (`/properties`).** Formulario multi-step: datos básicos → ubicación → imágenes (presigned batch). Vista `/properties` lista los listings propios del usuario autenticado (`GET /v1/properties/mine`). Ver [[properties-service-listing]], [[adr-image-upload-presigned-batch]].
- [ ] **Panel de moderación admin.** Vista interna para aprobar/rechazar listings que infringen políticas — state machine `pending → active | rejected`. Solo accesible con rol admin (Keycloak). Ver [[properties-service-admin]].
---

## Fase 5 — Diferenciadores

### Crítico — flujo de valor

- [ ] **Worker de properties que consume `price-predicted`.** Cablear el consumer que escucha el topic de [[analytics-service]] y llama `SetEstimatedPriceUseCase` con `principal=None` para poblar `ml_estimated_price`. Hoy `workers/` de properties está vacío y el path ML no tiene caller — es el flujo async properties↔analytics que [[architecture]] marca "en definición". Sin esto, el precio del AVM nunca llega al listing. Ver [[adr-estimated-price-dual-signal]], [[properties-service-admin]].

### Impresiones, analytics de comportamiento y feed personalizado

- [ ] **Tracking de impresiones por listing.** Registrar cuántas veces fue visto cada listing (impression) y por quién (si está autenticado). Candidato a evento Kafka `listing.impressed` consumido por analytics-ms. Sin esto, el propietario no puede saber el alcance de su publicación. El enfoque (beacon de cliente → collector tonto → Kafka → consumer en analytics) está fijado en [[adr-impressions-beacon-pipeline]]. Ver [[properties-service]], [[analytics-service]].
- [ ] **Modelo de recomendación de promociones.** Con el historial de impresiones se puede entrenar un modelo que identifique qué listings promocionados tienen mayor probabilidad de conversión para cada perfil de usuario. Input: intereses del usuario + historial de views + features del listing. Ver [[analytics-service]], [[adr-estimated-price-dual-signal]].
- [ ] **Feed personalizado por comportamiento.** Hoy el feed filtra por preferencias declaradas (onboarding). Con tracking de comportamiento (qué vio, cuánto tiempo, si volvió) se puede alimentar un recomendador colaborativo o content-based que mejore el ranking. El bbox del mapa estilo Airbnb ya da señal de zona de interés implícita. Ver [[frontend-architecture]], [[analytics-service]].
- [ ] **Targeting de listings promocionados.** Cruzar perfil del usuario (barrios, tipo de propiedad) con historial de comportamiento para mostrar los promoted listings a las personas con mayor probabilidad de conversión — no al azar. Depende de los dos ítems anteriores.

### Producto — diferenciadores y gaps de mercado

- [ ] **Score de oportunidad de inversión inline en el feed.** Calcular `(precio_listado - precio_estimado) / precio_estimado` y exponerlo en `PropertyCardSchema` como campo numérico + badge visual en cada card. Diferenciador directo vs FincaRaíz/Metrocuadrado (sin AVM); supera a Cerouno (calculadora manual vs automático en cada card del feed). Depende del worker AVM → listing (`ml_estimated_price` poblado). Ver [[adr-estimated-price-dual-signal]], [[properties-service-search]].
- [ ] **Alertas de oportunidad de precio.** Notificación push/email cuando se lista una propiedad X% por debajo del precio estimado en la zona de interés del usuario. Alta conversión para perfiles de inversión — nadie en el mercado colombiano lo tiene automático. Requiere: AVM funcionando + sistema de notificaciones + preferencias de zona ya capturadas en onboarding. Ver [[adr-estimated-price-dual-signal]], [[users-service]].
- [x] **`POST /v1/geo-resolution/reachable-pois` en catalog-service (isócronas).** Implementado 2026-06-15. ORS → `polygon_to_cells(r9)` → `get_by_h3_cells` (1 query) → groupby en memoria → `list[ReachablePoisResult]`. Soporta múltiples perfiles en parallel gather. Ver [[catalog-service]], [[catalog-service-ors]], [[adr-isochrone-ors-h3]].
- [ ] **Cache-aside para `reachable-pois`.** Pendiente: key `geo:reachable:property:{property_id}` cuando viene desde property detail (invalidación obvia al actualizar la propiedad); key `geo:reachable:{hash(lat,lon,range,profiles)}` cuando viene del AVM sin `property_id`. TTL 1h — sin reverse index ni invalidación cruzada. Ver [[adr-poi-cache-aside]], [[catalog-service-ors]].
- [ ] **Búsqueda con lenguaje natural.** LLM con tool use que traduce una query en lenguaje natural a la estructura `preferences + filters` del endpoint `/v1/search/feed`. Cerouno ya la tiene → brecha competitiva activa. El endpoint de búsqueda ya soporta todos los parámetros necesarios; falta la capa de traducción. Ver [[properties-service-search]], [[frontend-architecture]].
- [ ] **Estrato socioeconómico en el modelo de propiedad.** Agregar campo `stratum` (1–6) a la tabla de propiedades. En Colombia el estrato predice precio, servicios públicos y entorno — feature de alto valor para el AVM y para filtros del feed. Habi lo expone en cada card; FincaRaíz y Metrocuadrado también lo tienen. Sin él, el AVM pierde una de las variables más predictivas del mercado colombiano. Ver [[properties-service-admin]], [[avm-training]].

---

## Deuda técnica cross-fase

### Cadena del frontend (Google Maps → predicción)

- [ ] **Endpoint de resolución por coordenadas en catalog para el front.** El ADR [[adr-gmaps-places-geocoding]] asume un `resolve-by-coords` (lat/lon → barrio, sin Mapbox). Verificar si el `/v1/geo-resolution/by-coordinates` existente ya lo cubre o si falta crear/ajustar el endpoint (path/método/shape) que describe el ADR.
- [ ] **Refactor `/geo-resolution` en catalog.** Deprecar `resolve-neighborhood` (forward Mapbox, duplica el SDK del front). `by-coordinates` ya tiene `BackgroundTasks` de POIs ✅ y `locality_id` ✅ — solo falta deprecar el otro endpoint. Ver [[catalog-service]], [[adr-mapbox-frontend-only]].
- [ ] **Restricción de HTTP referrer** en la API key de Google Maps antes de producción (en dev corre sin restricción de dominio). Ver [[adr-gmaps-places-geocoding]].

### Deuda geo / ML

- [ ] **Re-registrar AVM con `year_built` nullable.** `_make_raw_input_example()` en `trainer.py` usa `year_built: 2012` (int) → MLflow infiere `long required` → rechaza `null` en runtime antes del preprocessing. Fix: pasar `year_built: None` en el ejemplo y re-correr `final_train` + promover alias `production`. Workaround temporal: reemplazar `None` con `0` en `AVMModelAdapter` tras el `model_dump`. Ver [[analytics-service-mlflow]].
- [x] **Conciliar tag set de POIs.** `category_map.py` unifica 5 keys OSM, 15 categorías, 147 valores — idéntico al tag set del AVM. `extract_category()` reemplaza el mapper anterior. Cerrado 2026-06-11. Ver [[catalog-service-overpass]], [[adr-geospatial-feature-engineering]].
- [ ] **Resolución H3 al cablear feature store desde un MS (caveat, no bug).** Los servicios indexan en r9 (lookup espacial granular) y el AVM usa r6/r7/r8 (feature del vector; r9 mete ruido). Hoy NO rompe nada porque el modelo recomputa sus celdas desde `lat/lon` en inferencia y no consume las celdas de los MS. Cuando se conecte el feature store desde un MS al modelo, **recomputar la resolución del modelo, no reusar la celda r9 almacenada**. Decisión en [[adr-h3-resolution-per-use-case]]; documentado en [[glossary#h3]].
- [ ] **CI + promoción del training AVM.** Automatizar el run (orchestrator tipo Airflow) y formalizar la promoción del alias `production` (hoy manual). Ver [[avm-training]], [[adr-model-promotion-external-to-service]].

### Infra compartida entre servicios

- [ ] **Centralizar los clientes de Redis y MinIO en una librería interna compartida (single source of truth).** Hoy cada MS copia su propio stack: el de cache Redis (`integrations/cache/redis/cache.py` + `services/shared/adapters/redis_cache_adapter.py` + `services/shared/ports/cache.py` + `core/exceptions/cache.py`) existe por triplicado en catalog, properties y users; el de MinIO (`integrations/storage/minio/storage.py` + adapter + port + exceptions) por duplicado en properties y users. Las copias **ya divergieron** (verificado 2026-06-12, ningún hash coincide): el port de cache de users tiene los 7 métodos base, catalog agrega `set_nx`, properties agrega `mget`/`mget_json`/`mset`/`mset_json` y `delete` multi-key; en storage divergieron hasta funcionalmente — properties expone presigned PUT URLs y users hace `upload_file` server-side. Un bugfix o mejora en una copia no llega a las demás. Propuesta: paquete interno del monorepo (p. ej. `backend/_lib/`, instalable por path con uv) que centralice el cliente Redis (superset de métodos), el cliente MinIO y las excepciones base; cada servicio conserva su port de dominio — el hexagonal se respeta porque lo compartido es el adapter/cliente de infra, no el contrato del dominio. Trade-off: acoplamiento por shared lib (un cambio breaking obliga a actualizar N servicios en lockstep) vs el drift actual de 3+2 copias. **Decisión mapeada en [[adr-shared-infra-lib]] (2026-06-12)**: uv workspace, ports se quedan en cada servicio, scope infra-only; el coste principal es el ajuste de Dockerfiles/build context. Ver [[architecture]], [[adr-cache-optional-layer]].

### properties-service — seguridad del feed

- [ ] **Rate limiting en `/search/feed`.** Sin esto el corte de `FEED_MAX_RESULTS` es trivial — N sesiones paralelas cada una llega a 300 orgánicos. Implementar límite por IP y/o por usuario a nivel de API gateway (nginx, Traefik) o middleware FastAPI + Redis. Ver [[properties-service-search]], [[adr-feed-opaque-cursor]].
- [ ] **Cursor firmado (HMAC).** El cursor actual es opaco pero no autenticado: alguien puede decodear el base64, manipular `created_at` para saltar a cualquier punto del dataset, y re-encodear. Un HMAC con secret server-side previene la manipulación sin cambiar el contrato público. Fix de mayor impacto/menor coste si el catálogo tiene valor real. Ver [[adr-feed-opaque-cursor]].
- [ ] **TTL del cursor.** Un cursor válido hoy lo es para siempre. Embeber una expiración (ej. 24 h) en el payload del cursor y validarla en `decode_cursor` fuerza re-inicio del flujo de paginación y reduce la ventana de scraping sostenido. Ver [[adr-feed-opaque-cursor]].

### properties-service — deuda pequeña

- [ ] **Errores de bulk create sin identificador de row.** `BulkCreatePropertiesUseCase` captura excepciones de `_enrich_location` como `str(exception)` sin referencia al row original. Refactor pendiente: incluir lat/lon o índice del row en el mensaje de error para facilitar debugging del seed. Ver `bulk_create_properties.py`.

### frontend — deuda pequeña

- [ ] **Refactor sección POI de `PropertyDetailView`.** La view está sucia: `CATEGORY_TO_MARKER` se importa pero ya no se usa (los markers los maneja `MapUser` con `leaflet.markercluster` internamente), hay imports sin referencias, y la lógica de markers mezcla responsabilidades con el composable. Limpiar imports muertos, mover `CATEGORY_TO_MARKER` al composable si sigue siendo necesario, y revisar si `poiMarkers` computed tiene razón de ser en la view o en `useReachablePois`. Ver [[frontend-poi-reachable]], [[frontend-map-component]].
- [ ] **Error/loading states en FeedView y MapView.** Ambas vistas carecen de skeleton de carga y de manejo de errores visibles. Sin esto, cualquier fallo de red en demo es invisible para el usuario y difícil de diagnosticar. Ver [[frontend-architecture]].
- [ ] **`checkAuth` siempre loguea 401 en consola para usuarios no autenticados.** El catch no filtra el 401 esperado — aparece como error visual en devtools aunque el flujo es correcto. Fix: `if (axios.isAxiosError(error) && error.response?.status !== 401)` antes de loguear. Natural hacerlo junto con la centralización del axios instance. Ver `stores/auth.ts:87`. **Update 2026-06-12**: el catch de `checkAuth` ya es silencioso ([auth.ts:87-93](frontend/src/stores/auth.ts#L87-L93)) pero el 401 **sigue apareciendo** en consola — es el log nativo de red del navegador (request XHR fallido), no suprimible desde JS. Cerrarlo de verdad implica evitar el request especulativo (p. ej. solo llamar `checkAuth` si hay señal de sesión previa) o aceptar el log como ruido conocido.

### Observabilidad y telemetría

Los tres pilares están ausentes hoy. Sin los tres juntos es imposible diagnosticar degradación en producción: los logs dicen *qué* falló, las métricas dicen *cuándo* empezó, las trazas dicen *dónde exactamente*.

#### Pilar 1 — Logs
- [ ] **Logging estructurado uniforme.** Hoy cada MS configura su propio logger con distintos formatos. Unificar en JSON con campos fijos (`service`, `trace_id`, `level`, `message`) para poder agregar en una sola vista (Loki, CloudWatch Logs, etc.). El `correlation_id` middleware de properties-service es un buen punto de partida.

#### Pilar 2 — Métricas
- [ ] **Métricas de infraestructura por MS (Prometheus/Grafana).** Exponer métricas clave: requests/s, p95 latencia, errores por endpoint, hit rate del cache Redis. Sin esto no hay forma de detectar degradación antes de que el usuario la reporte.
- [ ] **Métricas del AVM.** Latencia de inferencia, tasa de errores `PREDICTION_FAILED`, distribución de precios predichos. Permite detectar drift del modelo sin auditoría manual. Ver [[analytics-service]], [[avm-training]].
- [ ] **Métricas de negocio.** Tamaño del feed devuelto, tasa de listings sin impresiones (supply invisible), CTR de promoted listings. Distintas de las métricas de infra — miden salud del producto, no del sistema.

#### Pilar 3 — Trazas
- [ ] **Trazas distribuidas (OpenTelemetry).** Un request del feed puede tocar gateway → properties-service → catalog-service sin forma de correlacionar latencias hoy. Stack: `opentelemetry-sdk` + exportador a Jaeger o Tempo. Expandir el `correlation_id` existente a W3C TraceContext para propagación automática entre MSs. Ver [[architecture]].

### analytics-service — gaps funcionales

- [ ] **Kafka worker no levantado en startup.** `runner.py` del consumer existe pero no se llama desde `main.py` — el pipeline batch (listings → predicciones) está off by default. Fix: levantar el worker en el evento de startup de FastAPI. Ver [[analytics-service-kafka-consumer]], [[analytics-service]].
- [ ] **Promotions domain sin cache invalidation efectiva.** Los UCs `create.py` y `delete.py` de promotions tienen `except Exception: pass` en las operaciones de cache — las invalidaciones no se ejecutan si Redis tiene un error transitorio. Fix: separar la lógica de invalidación del manejo de errores de cache. Ver [[properties-service-admin]].

### Bordes operativos

- [ ] **Service account de MinIO con scope restringido para MLflow.** Hoy MLflow usa las credenciales root de MinIO (`AWS_ACCESS_KEY_ID`/`AWS_SECRET_ACCESS_KEY`). Crear una service account con acceso solo al bucket `mlflow-artifacts` — limita el blast radius si las credenciales se filtran. Ver [[analytics-service-mlflow]], [[adr-mlflow-minio-stack]].
- [ ] **users-service — mismatch de env var de Brevo.** El cliente lee `BREVO_API_KEY` pero el `.env.example` declara `BREVO_SMTP_KEY`; rompe el envío de emails. Ver [[users-service-email-brevo]].
- [ ] **users-service — health router sin montar.** `routes/health.py` existe pero `api_router` no lo incluye; no hay `/v1/health`. Ver [[users-service]].
- [ ] **`.env.example` incompletos** en catalog y properties (solo declaran `DATABASE_URL` y `REDIS_URL`; faltan Keycloak, `CATALOG_URL`, MinIO, TTLs). Ver [[catalog-service-local-dev]], [[properties-service-local-dev]].
- [ ] **Seeds reproducibles.** catalog se siembra manual vía bulk endpoints; properties no tiene script de seed. Definir side-container o script de seed al startup. Ver [[catalog-service-local-dev]].

### Consistencia / wiki

- [ ] **Divergencia de patrones de worker** (proceso separado en analytics vs APScheduler in-process en users). Documentada en [[adr-apscheduler-in-process-worker]]; revisar al escalar (N réplicas → N schedulers).
- [ ] **Huérfanos del wiki.** Agregar *links* entrantes a [[catalog-service-mapbox]], [[adr-admin-division-single-level]], [[adr-geojson-upload-pattern]], [[analytics-service-testing]] (hoy solo alcanzables desde INDEX).

---

## Cerrados

- [x] **Contradicción PostGIS "único servicio"** — corregida en catalog (overview, runbook, ADR) y glossary; properties-ms-db también usa `postgis/postgis:17-master` (2026-05-28).
- [x] **Contradicción auth Bearer vs cookie** — corregida en [[analytics-service-architecture]] y [[architecture]]; todos los servicios leen el JWT de la cookie `access_token` (2026-05-28).
- [x] **Conectar `gmp-placeselect` al chain completo** en `DevPlaygroundView.vue` (place → coords → catalog by-coords → `/v1/predict`). Cableado 2026-05-29 — ver [[frontend-architecture]], [[adr-gmaps-places-geocoding]].
- [x] **Vista contenedora feed/mapa con toggle.** View que orquesta nested routes y alterna entre la subview de **feed** (cards) y la de **mapa** — la view padre mantiene `FeedFilters` y header compartidos alrededor del slot. Decisión tomada: nested route (URL bookmarkeable, no `v-if`). Ver [[frontend-architecture]], [[properties-service-search]]. Implementado 2026-06-08.
- [x] **MapView con Leaflet + bbox + paginación.** `/feed/map` con `GetFeedMapUseCase`: bbox del viewport → celdas H3 → markers en Leaflet, paginación local por flechas, hover state, URL state vía `router.replace`. Implementado 2026-06-09 — ver [[frontend-architecture]], [[frontend-map-component]].
- [x] **`BoundingBox.to_polygon()` instancia una clase abstracta de h3.** Fix: `h3.LatLngPoly(...)` y return type actualizado. Corregido 2026-06-09 — ver [[properties-service-search]].
- [x] **H3 pre-filter antes de `ST_Within` en `GetFeedMapUseCase`.** El repo ya filtra **solo por columna H3** (`h3_r7.in_(cells)` o `h3_r9.in_(cells)` según la resolución) — no hay `ST_Within` en este path. La precisión del bbox es la de las celdas (`contain="center"`). Verificado 2026-06-09 — ver [[properties-service-search]], [[adr-postgis-h3-hybrid]].

## Claims

- El directorio `workers/` de properties-service solo contiene `__init__.py` — no hay consumer Kafka al 2026-05-28 ([workers/](backend/properties-service/src/app/workers)).
- El path ML de `SetEstimatedPriceUseCase` (principal=None) no tiene caller al 2026-05-28 ([set_estimated_price.py:26-32](backend/properties-service/src/app/services/admin/use_cases/estimated_price/set_estimated_price.py#L26-L32)).
- El cliente Brevo lee `BREVO_API_KEY`, pero el `.env.example` de users-service declara `BREVO_SMTP_KEY` ([client.py:15](backend/users-service/src/app/integrations/email/brevo/client.py#L15), [backend/users-service/.env.example](backend/users-service/.env.example)).
- El `api_router` de users-service no incluye el health router ([api/main.py:3-8](backend/users-service/src/app/api/main.py#L3-L8)).
- Los `.env.example` de catalog y properties solo declaran `DATABASE_URL` y `REDIS_URL` ([backend/catalog-service/.env.example](backend/catalog-service/.env.example), [backend/properties-service/.env.example](backend/properties-service/.env.example)).
- El flujo async properties↔analytics figura como "en definición" en la arquitectura cross-service ([architecture.md](docs/wiki/_shared/architecture.md)).
- `BoundingBox.to_polygon()` fue corregido a `h3.LatLngPoly(...)` — corregido 2026-06-09 ([feed_schemas.py](backend/properties-service/src/app/services/search/schemas/feed_schemas.py)).
- `PropertyDetailView.vue` + `usePropertyDetail.ts` existen en la ruta `/listing/:id` — la base de la vista detalle ya está implementada al 2026-06-12 ([frontend/src/views/](frontend/src/views/)).
- El stack Redis (`integrations/cache/redis/` + adapter + port + exceptions) está triplicado en catalog, properties y users — ningún hash de archivo coincide entre copias (verificado 2026-06-12).
- El stack MinIO (`integrations/storage/minio/` + adapter + port + exceptions) está duplicado en properties y users con implementaciones funcionalmente divergentes: properties usa presigned PUT URLs, users usa `upload_file` server-side (verificado 2026-06-12).
