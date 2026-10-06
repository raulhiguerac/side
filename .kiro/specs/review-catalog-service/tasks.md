# Revisión de catalog-service — tareas

- [ ] 1. Leer `audit-report.txt` (sección catalog-service) y los pendientes de catalog en `open-items.md`.
- [ ] 2. Bulk create de barrios (`POST /admin/localities/{id}/neighborhoods/bulk`): parser de archivos, fallback fila por fila con savepoints, normalización de `search_name`, invalidación de cache.
- [ ] 3. Bulk enrich de geometrías (`POST /admin/localities/{id}/neighborhoods/bulk/geometry`): matching por `search_name`, duplicados, GeoJSON inválido, `h3_cells`, invalidación por barrio y por localidad.
- [ ] 4. Escrituras unitarias por entidad (create/update de country, admin_division, locality, neighborhood y enrich_geometry): `rollback`, `translate_db_error`, qué claves de cache refresca o borra cada una.
- [ ] 5. Lecturas admin de barrios (listado, detalle, vecinos): filtros compartidos, coverage, paginación, validación del bbox, consumo desde el front.
- [ ] 6. `geo_resolution` por coordenadas (uno y en lote): prefiltro H3, segunda pasada, puntos fuera de todo barrio, tareas en background de POIs.
- [ ] 7. POIs e isócronas (`reachable-pois`): cache-aside, locks y `FetchZone`, fallos de ORS y Overpass, timeouts.
- [ ] 8. `geo_catalog` público: cache-aside, activos solamente, claves de cache y su invalidación desde las escrituras admin.
- [ ] 9. Transversal: `require_admin` en todo `/admin`, CORS, settings con valores fijos, handlers de excepciones.
- [ ] 10. Tests: casos de uso sin test, tests que no verifican lo que dicen, y la causa de los tests rojos.
- [ ] 11. Escribir el reporte con el formato de #review.
