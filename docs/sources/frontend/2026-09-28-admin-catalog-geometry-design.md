---
title: Cierre de moderación y diseño de la sección admin de catálogo con geometrías
captured-from: conversation
captured-on: 2026-09-28
participants: [author, claude]
---

## Context
Antes de pasar del admin de propiedades al de catálogo se auditó qué quedaba pendiente en moderación y se bocetó la sección de catálogo, que necesita visualizar las geometrías de los barrios.

## Key conclusions
- Moderación usa 4 de los 5 endpoints admin que le corresponden; el único sin usar es `POST /admin/properties/{id}/estimated-price`.
- Cablear `estimated-price` no tiene sentido todavía: ningún schema admin expone `admin_estimated_price` ni `ml_estimated_price`, así que el admin escribiría a ciegas. Orden: exponer ambos en `AdminPropertyDetailSchema` → input en el panel de preview, junto con el fix de invalidación de cache de `SetEstimatedPriceUseCase`.
- `BulkUploadPropertiesModal` escribe a mano los paths `bulk/upload-url` y `bulk` en vez de usar `PROPERTIES_ENDPOINTS`.
- Lo que queda de propiedades está bloqueado por backend (precios, relanzar job, CSV de errores), así que es seguro pasar a catálogo.
- El trío de filtros en URL repetido en moderación e imports son ~10 líneas por vista; lo difícil ya vive en `sanitizeFilterQuery`. `useUrlFilters(definitions, onChange)` ahorra poco en líneas, pero deja las reglas (la URL manda, `push` y no `replace`, `immediate`) en un solo lugar. Conviene extraerlo al aparecer una tercera vista con filtros.
- Catálogo sería la quinta copia del esqueleto admin: el diseño de la sección tiene que decidirse antes de copiar.
- Los 11 endpoints admin de catalog-service son todos de escritura: no hay listado admin, y los `GET` públicos pasan por cache y probablemente ocultan las entidades inactivas (sin verificar).
- Ningún endpoint devuelve la geometría de un barrio: `NeighborhoodListItem` y `NeighborhoodAdminResponse` solo traen el centroide, y la geometría solo se escribe.
- Visualización: la silueta SVG por fila con **d3-geo** (`geoPath` + `fitSize`) y el polígono sobre el mapa base con los vecinos atenuados en el panel, con **Leaflet**. El objetivo es validar forma, ubicación, superposiciones y huecos, y eso pide 2D con mapa base.
- 3D descartado para el panel admin porque la perspectiva deforma los bordes. Queda para un dashboard analítico (extrusión por precio/m² o cantidad de listings) con MapLibre `fill-extrusion` o deck.gl, no d3.
- ADR-0003 dice "Leaflet+D3 para render", pero d3 no está en `package.json`: habría que agregar solo `d3-geo`.

## Boceto de la sección
- Tabs: Barrios · Localidades · Divisiones · Países, sobre `AdminSplitView`.
- Filtros en cascada: país → división → localidad, más estado, "tiene geometría" y búsqueda.
- Tabla de barrios: forma (silueta o placeholder "sin geometría"), nombre, código y estado. Encima, una barra de cobertura ("38 de 42 con geometría").
- Panel: mapa con vecinos, área, número de vértices, centroide, aviso de superposición y las acciones editar / reemplazar geometría / desactivar.
- Acciones bulk (CSV de barrios, GeoJSON de geometrías) visibles solo con una localidad elegida; eso resuelve la UX pendiente del bulk de catálogo.

## Open questions
- ¿Los `GET` públicos de catálogo excluyen las entidades inactivas? Si es así, el admin no puede ver ni reactivar lo que desactivó.
- ¿Navegar la jerarquía por filtros en cascada, o entrar desde un mapa de la ciudad?
- ¿El aviso de superposición entra en la primera iteración o en la segunda?

## Next steps
- Definir el contrato del `GET` admin de barrios de catalog-service: paginado, filtros de estado y geometría, y un FeatureCollection GeoJSON simplificado (`ST_SimplifyPreserveTopology`) con `ST_Area` y `ST_NPoints`.
- Agregar `d3-geo` al front para las siluetas; la misma pieza sirve para la miniatura pendiente de la tabla de propiedades.
