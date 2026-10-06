# Revisión de catalog-service — diseño

## Alcance

`backend/catalog-service/src/app` y `backend/catalog-service/tests`, más el consumidor del front cuando exista (`frontend/src/composables/admin/*Neighborhood*`, `frontend/src/api/catalogApi.ts`).

Tres dominios:
- `catalog_admin`: escrituras por entidad, bulk de barrios (CSV y GeoJSON) y lecturas admin de barrios.
- `geo_catalog`: lecturas públicas cacheadas (solo activos).
- `geo_resolution`: `(lat, lon) → barrio` (uno y en lote), POIs con Overpass, isócronas con ORS.

## Contexto que conviene leer

- Página del dominio admin: #[[file:docs/wiki/catalog-service/domain/catalog-service-catalog-admin.md]]
- Ciclo de vida de POIs: #[[file:docs/wiki/catalog-service/domain/catalog-service-poi-lifecycle.md]]

## Por qué este orden

Primero lo que escribe o lo que cambia el estado compartido (bulk, cache, locks de POIs), porque un bug ahí corrompe datos; después las lecturas, donde un bug se ve y se corrige rápido.

## Salida

El reporte completo como respuesta final. El script `scripts/review.sh` (CLI) o quien dispare el hook (IDE) lo guarda en `docs/sources/catalog-service/<fecha>-review-catalog-service.md`.
