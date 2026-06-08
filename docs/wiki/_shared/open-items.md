---
title: Open items — gaps y deuda técnica cross-service
status: draft
last-verified: 2026-06-05
owners: [_shared]
related: [[architecture]], [[properties-service]], [[properties-service-search]], [[users-service]], [[catalog-service]], [[avm-training]], [[adr-estimated-price-dual-signal]], [[adr-gmaps-places-geocoding]]
sources: [../../sources/properties-service/2026-05-28-foundational-exploration.md, ../../sources/users-service/2026-05-28-foundational-exploration.md, ../../sources/frontend/2026-06-04-feed-filters-contract.md]
---

## TL;DR

Backlog vivo de gaps detectados al documentar la wiki (2026-05-28): cosas que el código aún no tiene pero la arquitectura asume, contradicciones, y bordes operativos. Marcá `[x]` a medida que se cierren. No es un reemplazo del issue tracker — es la vista cross-service para no perder contexto entre sesiones.

> Convención: cada ítem enlaza a la página/ADR que lo origina. Si cerrás uno, marcá `[x]` y, si aplica, actualizá el claim de la página de origen.

## Crítico — flujo de valor

- [ ] **Worker de properties que consume `price-predicted`.** Cablear el consumer que escucha el topic de [[analytics-service]] y llama `SetEstimatedPriceUseCase` con `principal=None` para poblar `ml_estimated_price`. Hoy `workers/` de properties está vacío y el path ML no tiene caller — es el flujo async properties↔analytics que [[architecture]] marca "en definición". Sin esto, el precio del AVM nunca llega al listing. Ver [[adr-estimated-price-dual-signal]], [[properties-service-admin]].

## Cadena del frontend (Google Maps → predicción)

- [ ] **Endpoint de resolución por coordenadas en catalog para el front.** El ADR [[adr-gmaps-places-geocoding]] asume un `resolve-by-coords` (lat/lon → barrio, sin Mapbox). Verificar si el `/v1/geo-resolution/by-coordinates` existente ya lo cubre o si falta crear/ajustar el endpoint (path/método/shape) que describe el ADR.
- [ ] **Refactor `/geo-resolution` en catalog.** Deprecar `resolve-neighborhood` (forward Mapbox, duplica el SDK del front) y dejar solo `by-coordinates`, agregándole el `BackgroundTasks` de POIs. Ver [[catalog-service]], [[adr-mapbox-frontend-only]].
- [x] **Conectar `gmp-placeselect` al chain completo** en `DevPlaygroundView.vue` (place → coords → catalog by-coords → `/v1/predict`). Cableado 2026-05-29 — ver [[frontend-architecture]], [[adr-gmaps-places-geocoding]].
- [ ] **Restricción de HTTP referrer** en la API key de Google Maps antes de producción (en dev corre sin restricción de dominio). Ver [[adr-gmaps-places-geocoding]].

## Deuda geo / ML

- [ ] **Re-registrar AVM con `year_built` nullable.** `_make_raw_input_example()` en `trainer.py` usa `year_built: 2012` (int) → MLflow infiere `long required` → rechaza `null` en runtime antes del preprocessing. Fix: pasar `year_built: None` en el ejemplo y re-correr `final_train` + promover alias `production`. Workaround temporal: reemplazar `None` con `0` en `AVMModelAdapter` tras el `model_dump`. Ver [[analytics-service-mlflow]].

- [ ] **Conciliar tag set de POIs.** El del training del AVM (~15 categorías) diverge del que extrae catalog vía Overpass; el feature store de catalog aún NO alimenta el modelo. Ver [[adr-geospatial-feature-engineering]], [[catalog-service-overpass]].
- [ ] **Resolución H3 al cablear feature store desde un MS (caveat, no bug).** Los servicios indexan en r9 (lookup espacial granular) y el AVM usa r6/r7/r8 (feature del vector; r9 mete ruido). Hoy NO rompe nada porque el modelo recomputa sus celdas desde `lat/lon` en inferencia y no consume las celdas de los MS. Cuando se conecte el feature store desde un MS al modelo, **recomputar la resolución del modelo, no reusar la celda r9 almacenada**. Decisión en [[adr-h3-resolution-per-use-case]]; documentado en [[glossary#h3]].
- [ ] **`GET /v1/geo-resolution/reachable-pois` en catalog-service.** Nuevo UC en el dominio `geo_resolution`: dado lat/lon + minutes + mode, llama ORS para obtener el polígono de isocrona → `h3shape_to_cells(polygon, r9)` → cache lookup por celdas (key = hash del sorted set de H3 cells) → miss: `SELECT * FROM poi WHERE h3_index IN (cells)` → cachea + devuelve. Edge case de borde: usar `contain="center"` (centroide de la celda dentro del polígono) en lugar de intersección parcial. Responsabilidad completa en catalog-service — el caller (properties-service, front) solo ve `list[PoiSchema]`. No mezcla con analytics-service. Motor de routing recomendado: ORS (self-hosted o tier gratis), descarta Mapbox por cobertura en Colombia. Ver [[catalog-service]], [[catalog-service-poi-lifecycle]], [[adr-impressions-beacon-pipeline]].
- [ ] **CI + promoción del training AVM.** Automatizar el run (orchestrator tipo Airflow) y formalizar la promoción del alias `production` (hoy manual). Ver [[avm-training]], [[adr-model-promotion-external-to-service]].

## Impresiones, analytics de comportamiento y feed personalizado

- [ ] **Tracking de impresiones por listing.** Registrar cuántas veces fue visto cada listing (impression) y por quién (si está autenticado). Candidato a evento Kafka `listing.impressed` consumido por analytics-ms. Sin esto, el propietario no puede saber el alcance de su publicación. El enfoque (beacon de cliente → collector tonto → Kafka → consumer en analytics) está fijado en [[adr-impressions-beacon-pipeline]]. Ver [[properties-service]], [[analytics-service]].
- [ ] **Modelo de recomendación de promociones.** Con el historial de impresiones se puede entrenar un modelo que identifique qué listings promocionados tienen mayor probabilidad de conversión para cada perfil de usuario. Input: intereses del usuario + historial de views + features del listing. Ver [[analytics-service]], [[adr-estimated-price-dual-signal]].
- [ ] **Feed personalizado por comportamiento.** Hoy el feed filtra por preferencias declaradas (onboarding). Con tracking de comportamiento (qué vio, cuánto tiempo, si volvió) se puede alimentar un recomendador colaborativo o content-based que mejore el ranking. El bbox del mapa estilo Airbnb ya da señal de zona de interés implícita. Ver [[frontend-architecture]], [[analytics-service]].
- [ ] **Targeting de listings promocionados.** Cruzar perfil del usuario (barrios, tipo de propiedad) con historial de comportamiento para mostrar los promoted listings a las personas con mayor probabilidad de conversión — no al azar. Depende de los dos ítems anteriores.

## Producto — diferenciadores y gaps de mercado

- [ ] **Score de oportunidad de inversión inline en el feed.** Calcular `(precio_listado - precio_estimado) / precio_estimado` y exponerlo en `PropertyCardSchema` como campo numérico + badge visual en cada card. Diferenciador directo vs FincaRaíz/Metrocuadrado (sin AVM); supera a Cerouno (calculadora manual vs automático en cada card del feed). Depende del worker AVM → listing (`ml_estimated_price` poblado). Ver [[adr-estimated-price-dual-signal]], [[properties-service-search]].
- [ ] **Alertas de oportunidad de precio.** Notificación push/email cuando se lista una propiedad X% por debajo del precio estimado en la zona de interés del usuario. Alta conversión para perfiles de inversión — nadie en el mercado colombiano lo tiene automático. Requiere: AVM funcionando + sistema de notificaciones + preferencias de zona ya capturadas en onboarding. Fase 3. Ver [[adr-estimated-price-dual-signal]], [[users-service]].
- [ ] **Búsqueda con lenguaje natural.** LLM con tool use que traduce una query en lenguaje natural a la estructura `preferences + filters` del endpoint `/v1/search/feed`. Cerouno ya la tiene → brecha competitiva activa. El endpoint de búsqueda ya soporta todos los parámetros necesarios; falta la capa de traducción. Ver [[properties-service-search]], [[frontend-architecture]].
- [ ] **Estrato socioeconómico en el modelo de propiedad.** Agregar campo `stratum` (1–6) a la tabla de propiedades. En Colombia el estrato predice precio, servicios públicos y entorno — feature de alto valor para el AVM y para filtros del feed. Habi lo expone en cada card; FincaRaíz y Metrocuadrado también lo tienen. Sin él, el AVM pierde una de las variables más predictivas del mercado colombiano. Ver [[properties-service-admin]], [[avm-training]].

## frontend — deuda pequeña

- [ ] **Vista contenedora feed/mapa con toggle.** Crear una view que orqueste y, vía `v-if` (estado local) o nested route (URL bookmarkeable), alterne entre la subview/componente de **feed** (cards) y la de **mapa** — para que el usuario cambie de modo fácilmente desde un solo lugar. La view padre mantiene la UI compartida (`FeedFilters`, header) alrededor del slot que monta feed o mapa. Decisión `v-if` vs nested route pendiente: router si el modo debe reflejarse/compartirse en la URL, `v-if` si es solo preferencia de sesión. Conecta con el bug de `to_polygon()` (el modo mapa depende de `GetFeedMapUseCase`). Ver [[frontend-architecture]], [[properties-service-search]].
- [ ] **`checkAuth` siempre loguea 401 en consola para usuarios no autenticados.** El catch no filtra el 401 esperado — aparece como error visual en devtools aunque el flujo es correcto. Fix: `if (axios.isAxiosError(error) && error.response?.status !== 401)` antes de loguear. Natural hacerlo junto con la centralización del axios instance. Ver `stores/auth.ts:87`.

## properties-service — seguridad del feed

- [ ] **Rate limiting en `/search/feed`.** Sin esto el corte de `FEED_MAX_RESULTS` es trivial — N sesiones paralelas cada una llega a 300 orgánicos. Implementar límite por IP y/o por usuario a nivel de API gateway (nginx, Traefik) o middleware FastAPI + Redis. Ver [[properties-service-search]], [[adr-feed-opaque-cursor]].
- [ ] **Cursor firmado (HMAC).** El cursor actual es opaco pero no autenticado: alguien puede decodear el base64, manipular `created_at` para saltar a cualquier punto del dataset, y re-encodear. Un HMAC con secret server-side previene la manipulación sin cambiar el contrato público. Fix de mayor impacto/menor coste si el catálogo tiene valor real. Ver [[adr-feed-opaque-cursor]].
- [ ] **TTL del cursor.** Un cursor válido hoy lo es para siempre. Embeber una expiración (ej. 24 h) en el payload del cursor y validarla en `decode_cursor` fuerza re-inicio del flujo de paginación y reduce la ventana de scraping sostenido. Ver [[adr-feed-opaque-cursor]].

## properties-service — deuda pequeña

- [ ] **Errores de bulk create sin identificador de row.** `BulkCreatePropertiesUseCase` captura excepciones de `_enrich_location` como `str(exception)` sin referencia al row original. Refactor pendiente: incluir lat/lon o índice del row en el mensaje de error para facilitar debugging del seed. Ver `bulk_create_properties.py`.
- [ ] **`BoundingBox.to_polygon()` instancia una clase abstracta de h3.** `feed_schemas.py` hace `h3.H3Shape(outer=[...])`, pero `H3Shape` es la clase abstracta padre de `LatLngPoly`/`LatLngMultiPoly` y no es instanciable → `GetFeedMapUseCase` crashea en runtime al construir el polígono. Fix: `h3.LatLngPoly(...)` y actualizar el return type. Bloquea el map view (bbox del front → celdas H3 → `get_by_bbox`). Ver [[properties-service-search]].

## Observabilidad y telemetría

Los tres pilares están ausentes hoy. Sin los tres juntos es imposible diagnosticar degradación en producción: los logs dicen *qué* falló, las métricas dicen *cuándo* empezó, las trazas dicen *dónde exactamente*.

### Pilar 1 — Logs
- [ ] **Logging estructurado uniforme.** Hoy cada MS configura su propio logger con distintos formatos. Unificar en JSON con campos fijos (`service`, `trace_id`, `level`, `message`) para poder agregar en una sola vista (Loki, CloudWatch Logs, etc.). El `correlation_id` middleware de properties-service es un buen punto de partida.

### Pilar 2 — Métricas
- [ ] **Métricas de infraestructura por MS (Prometheus/Grafana).** Exponer métricas clave: requests/s, p95 latencia, errores por endpoint, hit rate del cache Redis. Sin esto no hay forma de detectar degradación antes de que el usuario la reporte.
- [ ] **Métricas del AVM.** Latencia de inferencia, tasa de errores `PREDICTION_FAILED`, distribución de precios predichos. Permite detectar drift del modelo sin auditoría manual. Ver [[analytics-service]], [[avm-training]].
- [ ] **Métricas de negocio.** Tamaño del feed devuelto, tasa de listings sin impresiones (supply invisible), CTR de promoted listings. Distintas de las métricas de infra — miden salud del producto, no del sistema.

### Pilar 3 — Trazas
- [ ] **Trazas distribuidas (OpenTelemetry).** Un request del feed puede tocar gateway → properties-service → catalog-service sin forma de correlacionar latencias hoy. Stack: `opentelemetry-sdk` + exportador a Jaeger o Tempo. Expandir el `correlation_id` existente a W3C TraceContext para propagación automática entre MSs. Ver [[architecture]].

## Bordes operativos

- [ ] **Service account de MinIO con scope restringido para MLflow.** Hoy MLflow usa las credenciales root de MinIO (`AWS_ACCESS_KEY_ID`/`AWS_SECRET_ACCESS_KEY`). Crear una service account con acceso solo al bucket `mlflow-artifacts` — limita el blast radius si las credenciales se filtran. Ver [[analytics-service-mlflow]], [[adr-mlflow-minio-stack]].

- [ ] **users-service — mismatch de env var de Brevo.** El cliente lee `BREVO_API_KEY` pero el `.env.example` declara `BREVO_SMTP_KEY`; rompe el envío de emails. Ver [[users-service-email-brevo]].
- [ ] **users-service — health router sin montar.** `routes/health.py` existe pero `api_router` no lo incluye; no hay `/v1/health`. Ver [[users-service]].
- [ ] **`.env.example` incompletos** en catalog y properties (solo declaran `DATABASE_URL` y `REDIS_URL`; faltan Keycloak, `CATALOG_URL`, MinIO, TTLs). Ver [[catalog-service-local-dev]], [[properties-service-local-dev]].
- [ ] **Seeds reproducibles.** catalog se siembra manual vía bulk endpoints; properties no tiene script de seed. Definir side-container o script de seed al startup. Ver [[catalog-service-local-dev]].

## Consistencia / wiki

- [ ] **Divergencia de patrones de worker** (proceso separado en analytics vs APScheduler in-process en users). Documentada en [[adr-apscheduler-in-process-worker]]; revisar al escalar (N réplicas → N schedulers).
- [ ] **Huérfanos del wiki.** Agregar *links* entrantes a [[catalog-service-mapbox]], [[adr-admin-division-single-level]], [[adr-geojson-upload-pattern]], [[analytics-service-testing]] (hoy solo alcanzables desde INDEX).

## Cerrados

- [x] **Contradicción PostGIS "único servicio"** — corregida en catalog (overview, runbook, ADR) y glossary; properties-ms-db también usa `postgis/postgis:17-master` (2026-05-28).
- [x] **Contradicción auth Bearer vs cookie** — corregida en [[analytics-service-architecture]] y [[architecture]]; todos los servicios leen el JWT de la cookie `access_token` (2026-05-28).

## Claims

- El directorio `workers/` de properties-service solo contiene `__init__.py` — no hay consumer Kafka al 2026-05-28 ([workers/](backend/properties-service/src/app/workers)).
- El path ML de `SetEstimatedPriceUseCase` (principal=None) no tiene caller al 2026-05-28 ([set_estimated_price.py:26-32](backend/properties-service/src/app/services/admin/use_cases/estimated_price/set_estimated_price.py#L26-L32)).
- El cliente Brevo lee `BREVO_API_KEY`, pero el `.env.example` de users-service declara `BREVO_SMTP_KEY` ([client.py:15](backend/users-service/src/app/integrations/email/brevo/client.py#L15), [backend/users-service/.env.example](backend/users-service/.env.example)).
- El `api_router` de users-service no incluye el health router ([api/main.py:3-8](backend/users-service/src/app/api/main.py#L3-L8)).
- Los `.env.example` de catalog y properties solo declaran `DATABASE_URL` y `REDIS_URL` ([backend/catalog-service/.env.example](backend/catalog-service/.env.example), [backend/properties-service/.env.example](backend/properties-service/.env.example)).
- El flujo async properties↔analytics figura como "en definición" en la arquitectura cross-service ([architecture.md](docs/wiki/_shared/architecture.md)).
- `BoundingBox.to_polygon()` instancia `h3.H3Shape(...)`, clase abstracta no instanciable — el feed-mapa no puede construir el polígono ([feed_schemas.py:31-32](backend/properties-service/src/app/services/search/schemas/feed_schemas.py#L31-L32)).
