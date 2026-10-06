# Revisión de properties-service — tareas

- [ ] 1. Leer `audit-report.txt` (properties-service) y los pendientes de properties en `open-items.md`.
- [ ] 2. Import bulk (`POST /admin/properties/bulk*` + `workers/bulk_create_properties_worker.py`): CSV en streaming, chunks, idempotencia por `external_id`, reintentos, errores por fila, resolución de dueños y de ubicación en lote.
- [ ] 3. Crear y editar propiedad (`/properties/create`, `PATCH /properties/{id}`): campos fijos frente a editables, dueño verificado, geo al escribir, H3 r7/r9, invalidación de cache.
- [ ] 4. Imágenes (URLs prefirmadas, `confirm`, `DELETE`): que el objeto exista antes de confirmar, límite de imágenes, degradar la verificación al cambiar fotos, limpieza en storage.
- [ ] 5. Visibilidad y borrado: transiciones de `ListingStatus`, qué pasa con promociones y cache.
- [ ] 6. Moderación (`PATCH .../status`, `.../verification`): transiciones legales del backend, motivo de rechazo, invalidación del cache del feed y de los ads.
- [ ] 7. Promociones y precio estimado: solapamientos, vigencia, columnas admin frente a ML.
- [ ] 8. Feed y mapa (`/search/feed`, `/search/feed/map`): cursor opaco (manipulable), composición orgánico + ads, filtros, bbox → celdas H3, claves de cache por página.
- [ ] 9. Lecturas admin (listado, detalle, jobs): paginación por offset, filtros, `total`.
- [ ] 10. Transversal: `require_admin`, dueño frente a otros usuarios en cada endpoint de `/properties`, cache opcional, CORS.
- [ ] 11. Tests y reporte con el formato de #review.
