---
title: ADR-0004 — GeoJSON upload pattern para polígonos de barrios
status: stable
last-verified: 2026-05-21
owners: [catalog-service]
related: [[catalog-service-catalog-admin]], [[glossary]]
sources: [../../../sources/catalog-service/2026-05-21-foundational-qa.md]
decision-date: 2026-05-21
decision-status: accepted
---

# ADR-0004 — GeoJSON upload pattern para polígonos de barrios

## Contexto

Los polígonos de barrios vienen de fuentes externas (IDECA en Bogotá, equivalentes oficiales en otros distritos). El formato canónico es [[glossary#geojson]] FeatureCollection. Cada feature lleva una `geometry` (MultiPolygon) y `properties` con metadata (nombre, código).

Necesitamos cargar/actualizar 2 cosas distintas, posiblemente desde el mismo archivo:
1. **Crear barrios** (id, nombre, código) — sin geometría necesariamente.
2. **Enriquecer barrios existentes con sus polígonos** (`geom`).

¿Un solo upload o dos? ¿Cómo matchear features de GeoJSON con filas existentes?

## Decisión

**Dos endpoints distintos** con responsabilidades separadas:

| Endpoint | Input | Qué hace |
|---|---|---|
| `POST /admin/localities/{locality_id}/neighborhoods/bulk` | CSV o JSON con `name, code, latitude, longitude, ...` | Crea barrios; no toca `geom`. Si bulk falla, cae a row-by-row con savepoints. |
| `POST /admin/localities/{locality_id}/neighborhoods/bulk/geometry` | GeoJSON FeatureCollection + `name_field` (qué attribute usar) | Enriquece barrios **existentes** con su `geom`. Matchea por `search_name` (NFKD+lowercase+strip). Reporta `matched`/`unmatched`/`updated`. |
| `POST /admin/neighborhoods/{neighborhood_id}/geometry` | GeoJSON single feature | Enriquece un barrio puntual. |

Flujo operativo esperado:
1. Admin sube CSV de barrios (paso 1) → crea filas sin `geom`.
2. Admin sube GeoJSON FeatureCollection (paso 2) → matchea por nombre y popula `geom`.
3. (Reaplicable: subir un GeoJSON refrescado actualiza los polígonos sin tocar los IDs).

**Atado a `locality_id`** (en el path): un upload es siempre para una locality específica. Evita ambigüedad cross-locality y permite invalidación de cache focalizada.

**Matching por `search_name` normalizado** (NFKD + lowercase + strip de tildes): tolera diferencias de mayúsculas/tildes entre el CSV y el GeoJSON. Si no matchea, queda en `unmatched`.

## Alternativas consideradas

- **Upload único** (un GeoJSON que crea Y enriquece) — más simple para el admin pero acopla dos operaciones distintas; rollback parcial es ambiguo.
- **Matching por `code` en vez de `name`** — más robusto si el GeoJSON trae código, pero IDECA no siempre lo expone; nombre es el lowest common denominator.
- **Upload por API endpoint estructurado** (no archivo) — más control pero requiere un cliente custom; archivo es lo que el admin descarga de IDECA.
- **MinIO como staging** (subir archivo → procesar async) — overkill para volumen actual (~1.500 barrios por upload).

## Consecuencias

- ✅ Separación clara: crear datos ≠ enriquecer geometría.
- ✅ Re-upload del GeoJSON refresca polígonos sin re-crear barrios — workflow incremental.
- ✅ `unmatched` permite al admin ver qué nombres del CSV no aparecieron en el GeoJSON (o viceversa) y conciliar.
- ✅ Matching tolerante a tildes/case acomoda fuentes heterogéneas.
- ❌ Admin tiene que recordar el orden: primero CSV, después GeoJSON. Si lo invierte, el bulk_enrich reporta 100% unmatched.
- ❌ Matching por nombre puede generar **falsos positivos** si dos barrios tienen el mismo nombre normalizado en una locality. Hoy se dedup en el `neighborhood_lookup` ("primer match gana"), lo cual silenciosamente descarta colisiones.
- ❌ No hay validación del GeoJSON antes de aplicar `geom_from_geojson` — un `geometry` malformado puede romper el bulk_update entero. Mejor validar upstream.
- ❌ Sin UI admin frontend al 2026-05-21 — hoy los uploads se hacen vía curl/Postman.

## Claims

- Tres endpoints distintos para uploads ([api/routes/admin.py:161-201](backend/catalog-service/src/app/api/routes/admin.py#L161-L201)).
- `NeighborhoodFileParser` acepta `.csv`, `.json`, `.txt` ([file_parser.py](backend/catalog-service/src/app/services/catalog_admin/helpers/file_parser.py)).
- Matching usa `_normalize` (NFKD + lowercase + strip) tanto al crear como al enriquecer ([bulk_create_neighborhoods.py:19-21](backend/catalog-service/src/app/services/catalog_admin/use_cases/bulk_create_neighborhoods.py#L19-L21), [bulk_enrich_neighborhood_geometries.py:23-25](backend/catalog-service/src/app/services/catalog_admin/use_cases/bulk_enrich_neighborhood_geometries.py#L23-L25)).
- `BulkEnrichNeighborhoodGeometriesUseCase` retorna `matched`, `unmatched`, `updated` para diagnóstico ([bulk_enrich_neighborhood_geometries.py:95-99](backend/catalog-service/src/app/services/catalog_admin/use_cases/bulk_enrich_neighborhood_geometries.py#L95-L99)).
- Dedup en `neighborhood_lookup` por "primer match gana" — colisiones de nombre normalizado se descartan silenciosamente ([bulk_enrich_neighborhood_geometries.py:44-45](backend/catalog-service/src/app/services/catalog_admin/use_cases/bulk_enrich_neighborhood_geometries.py#L44-L45)).
- `geom_from_geojson` vive en `services/shared/helpers/geometry.py` ([bulk_enrich_neighborhood_geometries.py:17](backend/catalog-service/src/app/services/catalog_admin/use_cases/bulk_enrich_neighborhood_geometries.py#L17)).
