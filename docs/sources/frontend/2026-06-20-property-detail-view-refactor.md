---
title: Refactor de PropertyDetailView en componentes — view como orquestador
captured-from: conversation
captured-on: 2026-06-20
participants: [raul, claude]
---

## Context

`PropertyDetailView.vue` era un monolito (grid de fotos, header/precio/stats/detalles, y la sección "Cerca del lugar" con perfiles + acordeón de POIs + mapa + isócronas, todo inline). Se refactorizó para que la view solo orqueste: un `property` ref + composables + 3 componentes hijos.

## Key conclusions

- **`PropertyPhotoGrid.vue`** (padre) + **`PhotoGalleryPopup.vue`** (hijo, carrusel con `vue3-carousel` + `BaseModal`): patrón "props down, events up" — el hijo nunca muta el prop `isOpen`, solo emite `close`; el padre decide qué hacer. `BaseModal` ganó un prop `size` opcional (`lg`/`xl`/`3xl`) para no romper su otro uso en `App.vue`.
- **`PropertyOverview.vue`**: cero lógica propia, recibe todo ya resuelto del composable `usePropertyDetail` (incluye `hasAdminFee`, `description` nuevos, agregados como `computed` — el error típico ahí fue olvidarse del `computed()` y evaluar una sola vez antes de que `property.value` exista).
- **`NearbyPlaces.vue`**: a diferencia de los otros dos, es dueño de su propio composable (`useReachablePois`) — recibe `lat`/`lon`/`propertyId` como props y resuelve internamente, porque el timing (fetch async dependiente de que la propiedad ya cargó) lo hace más autocontenido así que si la view sigue orquestando ese estado.
- **Location label**: se resuelve con el mismo patrón que usan las cards del feed (`usePropertyMapper` → `buildNeighborhoodMap` en `composables/catalog/useNeighborhoodLookup.ts`) — no hay lógica nueva, solo reutilización.
- **Fetch real**: se reemplazó el mock hardcodeado en `onMounted` por `propertiesApi.get<PropertyDetail>('/v1/properties/${route.params.id}')`, usando el `id` de la ruta (`/listing/:id`) y la instancia de axios ya existente en `api/propertiesApi.ts`.
- **Single source of truth para categoría→color**: `CATEGORY_TO_MARKER` (duplicaba las 18 keys de `CATEGORY_META`) se eliminó; `CategoryMeta` ahora tiene un campo `bucket: MarkerImageType` y todo el código lee de ahí.
- **`POI_COLORS`** se sacó de `MapUser.vue` a `constants/poiColors.ts` (junto con `POI_BUCKET_LABELS` nuevos) para poder reusarlo en un componente `MapLegend.vue` reusable — pensado también para conectarlo después en `AvmView`.
- **Popups en markers del cluster**: el cluster de Leaflet (`buildCluster()` en `MapUser.vue`) solo pintaba un punto de color por performance (1000+ POIs con íconos SVG individuales degrada). Se agregó `bindPopup` con nombre/categoría/dirección/teléfono/website del POI (campos nuevos en `MarkerData`), escapando cada campo (`escapeHtml` vía `textContent`/`innerHTML`) porque el dato viene de OSM/Overpass.
- **Responsive**: la fila de perfiles+leyenda y la fila de POIs+mapa pasan a `flex-col` en mobile (`md:flex-row` desde tablet); en mobile el mapa va arriba y los POIs abajo vía `order-1 md:order-2` / `order-2 md:order-1`.

## Open questions

- Ninguna abierta — el alcance de este refactor se considera cerrado.

## Next steps

- Conectar `MapLegend.vue` en `AvmView.vue` cuando se trabaje esa vista (mencionado pero no implementado en esta sesión).
- El `location-label` solo resuelve barrio, no ciudad — si se quiere mostrar "Barrio, Ciudad" completo falta un segundo lookup.
