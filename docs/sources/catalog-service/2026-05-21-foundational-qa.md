---
title: Foundational Q&A — catalog-service
captured-from: conversation
captured-on: 2026-05-21
participants: [author, claude]
---

## Context

Primera sesión de captura para catalog-service. Servicio mucho más maduro en código que analytics (routes wired, 3 dominios, auth implementada, bulk uploads). Cubrió scope, decisiones de modelo geográfico, lifecycle de POIs, divergencias con analytics-service, y un refactor decidido en `/geo-resolution`.

## Key conclusions

### Scope & boundaries
- catalog es **el único servicio que toca providers geo** en todo el sistema.
- Frontend usa **Mapbox SDK directo** solo para el UX de "type address → see point on map" (autocomplete + preview); no produce datos geo del lado server.
- 3 dominios en `services/`: `catalog_admin` (writes), `geo_catalog` (reads), `geo_resolution` (providers + endpoint).

### Consumers
- Frontend: GETs de countries / localities / neighborhoods con debounce para autocomplete; futura UI admin para uploads de catálogo.
- properties-service: `/geo-resolution` al crear listing (geo-enrichment at write time, ver ADR cross-service).
- Sin server-to-server async hoy.

### Modelo geográfico — simplificación deliberada
- `AdminDivision` **1-nivel sin recursión** (Colombia: País → Departamento → Municipio → Barrio).
- Granularidad fina (provincia, mesorregión, microrregión) sacrificada por simplicidad del feed/UX.
- Vale hasta que el producto escale a países con jerarquías más profundas; ahí toca revisar.

### `h3_cells` lazy-fill en neighborhoods
- Optimización para evitar el point-in-polygon costoso contra `geom MULTIPOLYGON` en cada request.
- Mecánica: primer hit a un barrio cuyos `h3_cells` están `NULL` → polyfill H3 res 9 del polígono → persiste el array. Próximas requests usan el índice GIN sobre el array para reducir a 1-3 candidatos antes del `ST_Contains` exacto.
- Trade-off: cold start lento, hot path barato. Pre-fill batch como mitigación futura si P99 sufre.

### POI lifecycle — cache-aside, side-effect only
- POIs **nunca on-demand**. Solo se fetchea Overpass como side-effect de un `/geo-resolution`.
- Flujo: Request → Redis → Postgres → Overpass (si la zona H3 no fue fetcheada).
- `FetchZone` tabla registra qué celdas H3 res 9 fueron consultadas; evita refetch.
- **Batch de refresh de zonas stale: planificado, no implementado.**

### `/geo-resolution` refactor decidido
- **Estado actual:** recibe `address`, hace forward geocoding vía Mapbox (duplica lo que el frontend ya hace).
- **Estado deseado:** recibe `lat/lon` (ya resuelto por frontend), hace solo reverse (point-in-polygon → barrio). Ahorra latencia + costo Mapbox + remueve duplicación.
- Documentar el deseado como canónico; flag refactor pendiente en código + open item.

### Tag set Overpass — divergencia con analytics
- catalog: ~15 tags (subset de amenity/leisure/shop).
- analytics ML training: ~150 tags categorizados (amenity/shop/public_transport/leisure/healthcare).
- **Necesita conciliación** para que el side-effect de POIs sirva al modelo ML eventualmente.

### Auth admin
- JWT carry claim de rol con valor `admin` (configurable vía env `ADMIN_ROLE`).
- Asignación manual en Keycloak por super-user del realm.
- Dep `require_admin` ya implementada y aplicada a todo `/admin/*`.

### Seed
- Hoy: manual vía bulk endpoints (admin sube CSVs y GeoJSON).
- Futuro deseado: side-container que corre script de seed al startup con CSVs IDECA (los mismos barrios que usa el ML).

## Open questions

- Mecanismo concreto y trigger del batch de refresh de FetchZones (cron k8s, worker permanente, evento manual).
- Quién es source-of-truth del tag set Overpass — catalog cura o analytics define y catalog adopta.
- Implementar el side-container de seed con los CSVs IDECA.
- Cuándo y por quién se hace el refactor real de `/geo-resolution` (Mapbox out del backend, reverse only).

## Next steps

- Batches del wiki para catalog-service:
  - Batch 2: `catalog-service.md` overview + `catalog-service-architecture.md`
  - Batch 3: 3 páginas de dominio (`catalog-admin`, `geo-catalog`, `poi-lifecycle`)
  - Batch 4: 5 ADRs (PostGIS+h3 híbrido, AdminDivision 1-nivel, POI cache-aside, GeoJSON upload, Mapbox solo en frontend)
  - Batch 5: `integrations/{mapbox, overpass}.md` + `runbook/catalog-service-local-dev.md`
- Glossary `_shared` gana 7 términos cross-cutting: cache-aside, forward geocoding, GeoJSON, h3, point-in-polygon, PostGIS, reverse geocoding.
- Abrir issues por los 3 open items operativos (FetchZone batch, tag set conciliation, seed script).
