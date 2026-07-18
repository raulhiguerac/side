---
title: Feed filters — frontend props/emits contract & backend filter behavior
captured-from: conversation
captured-on: 2026-06-04
participants: [raul, claude]
---

## Context
Sesión de construcción del panel de filtros del feed (`FeedFilters.vue`) y su conexión con la view padre vía props/emits, más cómo el backend de properties-service aplica los filtros de búsqueda.

## Key conclusions

### Contrato de búsqueda (backend, properties-service)
- Dos DTOs separados en `search/schemas/feed_schemas.py`:
  - `FeedPreferences`: `city_ids`, `neighborhood_ids`, `property_types` (enum `PropertyType` = `"house"` | `"apartment"`). El dep `parse_feed_preferences` devuelve `None` si no llega ninguno → sin filtro geográfico.
  - `FeedFilters`: `min_price`, `max_price`, `min_area_m2`, `max_area_m2`, `min_bathrooms`, `bedrooms` (>=1). Todos opcionales.
- `SqlPropertySearchRepository.get_properties` aplica cada filtro con un `if x is not None` independiente → **filtros parciales funcionan** (p.ej. mandar solo `max_price` agrega solo `WHERE price <= max_price`).
- Preferencias y filtros son ambos opcionales; sin nada, el feed muestra todo.

### Patrón frontend (props/emits)
- `FeedFilters.vue` mantiene estado local: `selected` (ciudades) y `selectedNeighborhoods` desde composables `useCityMultiselect`/`useNeighborhoodMultiselect`, `selectedTypes` (`ref<string[]>`), y `filters` (`ref<FeedFilters>({})` con `v-model.number` en cada input).
- `property_types` se maneja con botones + `toggleType(type)`: si el array incluye el valor lo quita (`filter`), si no lo agrega (`push`); estilo activo Tailwind `bg-brand-primary text-white`.
- Emite un solo evento `submit` con `{ preferences, filters }` **al hacer click en "Aplicar"** — NO reactivo con watch. Decisión: evitar una petición por cada cambio de campo (sobrecarga del backend).
- El objeto `preferences` se arma en el `onSubmit` leyendo los refs directamente (`selected.value`, etc.), sin un ref `preferences` duplicado.
- Type `FeedFilters` agregado a `frontend/src/types/feed.ts` (todos los campos opcionales/nullable, espeja el backend). `FeedPreferences` ya existía ahí.

### Composable `useFeed`
- `load(preferences?: FeedPreferences, filters?: FeedFilters)`: si llegan args los usa; si no, hace fallback al `userStore.userInterests`. Resuelto con `preferences ?? (ternario del store)` — paréntesis obligatorios por precedencia `??` vs `?:`.
- `fetchFeed(preferences, filters?)` hace spread de ambos en `params`: `{ ...preferences, ...filters }`, con `paramsSerializer: { indexes: null }`.
- `load` actualiza `data.value` internamente (retorna `void`) → la view solo hace `await load(...)`, no asigna el resultado.
- La view padre desestructura el emit como `onSubmit(params)` y referencia `params.preferences` / `params.filters`.

## Open questions
- Toggle/feed reactivo descartado por ahora; revisitar si UX lo pide.

## Next steps
- **Bug pendiente** en `feed_schemas.py`: `BoundingBox.to_polygon()` instancia `h3.H3Shape(...)`, que es clase abstracta no instanciable → cambiar a `h3.LatLngPoly(...)` y actualizar el return type. Necesario para el map view (bbox del front → celdas H3 → query indexada vía `get_by_bbox`, resoluciones 7/9).
- Patrón map/feed inspirado en Airbnb: bbox del mapa → query → markers con precio; contenido estático en CDN, queries vía GraphQL persisted query.
