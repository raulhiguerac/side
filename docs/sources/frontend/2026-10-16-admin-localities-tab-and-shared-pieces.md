---
title: Tab de localidades del panel admin y piezas compartidas de catálogo
captured-from: conversation
captured-on: 2026-10-16
participants: [raul, claude]
---

## Context
Con los GET admin de #28, se armó la tab Localidades del panel de catálogo copiando el molde de barrios. Al ver cuánto se repetía (y que Divisiones y Países lo multiplicarían), se sacaron piezas compartidas antes de seguir. Nada se probó en el navegador; lint, vue-tsc y build pasan.

## Key conclusions
- **Tab Localidades cableada.** Filtros País → División → Estado (`LOCALITY_FILTERS`), tabla `AdminLocalitiesTable` (nombre con ★ si es capital, código, tipo, estado), `AdminPaginationFooter` y panel `AdminLocalityPanel` sin GET de detalle: la vista le pasa la fila seleccionada de `rows`.
- El panel muestra un mapa fijo (`LocalityMap`, zoom 11) con un marcador en `point`, nombre local, coordenadas y zona horaria. La división no aparece: la fila solo trae `admin_division_id`.
- **Acciones:** Editar y Desactivar/Reactivar (`PATCH /v1/admin/localities/{id}`), Crear (`POST /v1/admin/localities`) con cascada País → División precargada del filtro, y **Barrios**, que no abre modal: `router.push({ name: "admin-catalog", query: { country_id, locality_id } })`. Manda `country_id` porque el select de localidad de barrios tiene `dependsOn: "country_id"`; el back no lo usa.
- Editar no permite cambiar código, país ni división (`UpdateLocalityRequest` no los acepta). `LocalityFormFields` tiene los campos compartidos por crear y editar.
- El cliente valida rango de lat/lng y zona horaria IANA (`Intl.DateTimeFormat` en `utils/timezone.ts`) porque el back no lo hace.
- Tipos de localidad: `city` → Ciudad, `town` → Municipio, `village` → Vereda (`constants/localityLabels.ts`).
- Desactivar una localidad no desactiva sus barrios (`UpdateLocalityUseCase` no cascadea).
- Opciones de División en filtros y modales: `GET /v1/admin/admin-divisions` con `page_size: 100` (el tope del back), así que incluye divisiones inactivas; País sigue con el GET público (solo activos).
- **Piezas compartidas:**
  - `COUNTRY_SELECT`, `DIVISION_SELECT`, `LOCALITY_SELECT`, `STATUS_FILTER` en `constants/catalogFilters.ts`; las barras y las cascadas de modales usan las mismas definiciones.
  - `useAdminPage` genérico sobre `AdminPage<T>` (`types/shared/pagination.ts`) + `pickFilters(source, keys)` sin casts; `useAdminNeighborhoods` = `useAdminPage` + `coverage`, `useAdminLocalities` = una llamada.
  - `AdminFormModal` (encabezado con icono, error, Cancelar/acción, modo `danger`, slot `#footer`) y `AdminStatusModal` encima; migrados los modales de barrios, de localidades y `RemovePromotionModal`. `BulkUploadPropertiesModal` no, por su flujo de 3 pasos.
  - `useCascadeOptions` (opciones de `async-select` con `dependsOn`, guarda contra respuestas viejas, `dependentsOf`) lo usan `AdminFilterBar` y `CascadeSelectFields`, la cascada obligatoria de los modales. Se borraron `useLocalityPicker`, `useDivisionPicker` y `LocalitySelectFields`.
  - `AdminStatusBadge` reemplaza las tres copias del badge Activo/Inactivo.
- Cambios visibles del refactor: placeholder genérico "Elige una opción" en las cascadas de modales; el error de opciones va bajo los selects; `AdminFilterBar` ahora loguea los fallos de opciones (antes silenciosos).
- **Cache del back:** los UCs admin de localidad hacen `set_json` de `db_model.model_dump()` en `cache_key_locality(id)`, que el by-id público no puede validar (`LocalityListItem` es `extra="forbid"` y exige `admin_division`); invalida de casualidad. Registrado en open-items.

## Open questions
- ¿El back agrega el nombre de la división al listado de localidades, o el panel la resuelve con la lista del país?
- ¿Se agregan al back los filtros de tipo y búsqueda por nombre para localidades?

## Next steps
- Probar en navegador: cascada de la barra de barrios, los seis modales de barrios, la tab Localidades completa y quitar promoción.
- Tabs Divisiones y Países sobre las piezas compartidas.
- Pendiente aparte: mensajes de error comunes y clases de inputs repetidas (punto 5 del análisis).
- Back (lo escribe el autor): cambiar el `set_json` por `delete` en `use_cases/locality/{update,create}.py`.
