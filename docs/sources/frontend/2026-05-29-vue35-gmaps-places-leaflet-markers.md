---
title: Vue 3.5 upgrade, Google Maps Places new API, Leaflet markers con Lucide
captured-from: conversation
captured-on: 2026-05-29
participants: [raul, claude]
---

## Context

Sesión de trabajo en el frontend: upgrade de Vue, integración del autocomplete de Google Maps Places (nueva API), markers en el mapa con iconos Lucide, y función de resolución de barrio por coordenadas.

## Key conclusions

- **Vue 3.5 upgrade**: solo cambiar `"vue": "^3.5.35"` en `package.json` + `npm install`. No hay breaking changes desde 3.2.
- **`defineModel` ESLint error**: `eslint-plugin-vue@8.x` no reconoce `defineModel`. Fix: subir a `^9.0.0` o agregar `defineModel` a globals en `.eslintrc.js`.
- **`useTemplateRef` (Vue 3.5)**: reemplaza `ref<HTMLElement>(null)`. Sintaxis: `useTemplateRef<HTMLDivElement>('refName')` — el template usa `ref="refName"` (string, no binding).
- **`@types/google.maps` no cargaba**: `tsconfig.json` tenía `"types": ["webpack-env"]` explícito → TypeScript ignora todos los demás `@types`. Fix: agregar `"google.maps"` al array.
- **PlaceAutocompleteElement — evento correcto**: el evento es `"gmp-select"` (no `"gmp-placeselect"`). El objeto evento tiene `e.placePrediction.toPlace()` — `toPlace()` está en `placePrediction`, no en el evento directamente.
- **fetchFields obligatorio**: `e.placePrediction.toPlace()` devuelve un `Place` sin datos. Hay que llamar `await place.fetchFields({ fields: ["location", "formattedAddress"] })` antes de acceder a `location`.
- **Tipado del evento**: `PlaceAutocompletePlaceSelectEvent` no está exportado en `@types/google.maps`. Workaround: `(e: any)` directamente en el parámetro del listener.
- **Lucide markers en vue-leaflet**: `<l-icon>` genera un div con estilos Leaflet visibles. Fix: `class-name="!bg-transparent !border-0 !shadow-none"` en `l-icon`. El anchor para iconos cuadrados es `[16, 16]`, no `[16, 32]` (que es para pins con punta).
- **markerIconMap**: `Record<MarkerImageType, Component>` en `@/constants/markerIcons.ts`. En template: `<component :is="markerIconMap[marker.imageType]" />`.
- **getNeighborhood**: dos requests en cadena — `GET /v1/geo-resolution/by-coordinates?lat&lon` → `neighborhood_id`, luego `GET /v1/neighborhoods/by-id?neighborhood_id` → nombre. `LocationByCoordinates` solo devuelve UUIDs, no el nombre.
- **Watch para barrio en tiempo real**: `watch(place, ...)` dentro de `useAvmForm` para llamar `getNeighborhood` cuando el usuario selecciona dirección y mostrar el barrio detectado antes del submit.

## Open questions

- `eslint-plugin-vue` — ¿subir a v9 o parche con globals? Pendiente de decidir.
- `getNeighborhood` — confirmar el campo exacto del nombre en `NeighborhoodListItem` (schema no verificado completamente).

## Next steps

- Implementar `watch(place)` en `useAvmForm` que llame `getNeighborhood` y exponga `neighborhood` ref.
- Conectar `neighborhood.value` al bloque "Barrio detectado" en `AvmForm.vue` step 3 (hoy hardcodeado como "EL NOGAL").
