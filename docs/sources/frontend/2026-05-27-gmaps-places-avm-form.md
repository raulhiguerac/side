---
title: GMaps Places API — integración AVM form y decisión de proveedor geocoding
captured-from: conversation
captured-on: 2026-05-27
participants: [raul, claude]
---

## Context
Se necesitaba un autocomplete de dirección para el paso 3 del form AVM. Se evaluaron Mapbox, HERE y Google Maps Places API (New).

## Key conclusions
- **Mapbox descartado**: calidad de geocoding en Colombia insuficiente para producción.
- **HERE descartado**: nivel de cobertura Colombia = "Entry" en su ranking oficial — no apto para autocomplete de direcciones específicas.
- **Google Maps Places API (New) elegida**: free tier real ($200 USD/mes de crédito, ~66k requests por $1). Requiere GCP con tarjeta de crédito pero no cobra mientras no se supere el crédito.
- **No se necesita adapter de geocoding en el back**: el front resuelve lat/lon directamente con `PlaceAutocompleteElement`. El back solo necesita el endpoint de resolución por coordenadas (ya existe en catalog-service con PostGIS ST_Contains).
- **Flujo acordado**: `PlaceAutocompleteElement` → evento `gmp-placeselect` → `place.location.lat()/lng()` → `POST /geo/resolve-by-coords` en catalog → barrio_ideca → `POST /v1/predict`.

## Setup técnico
- Script de GMaps en `public/index.html` con `<%= process.env.VUE_APP_GMAPS_KEY %>` (NO hardcodeado).
- Key en `.env.local` como `VUE_APP_GMAPS_KEY=...` — no va al repo.
- `libraries=places&loading=async` en la URL del script.
- En GCP: habilitar **Places API (New)** (no la clásica) + restricción de key a esa API.
- `PlaceAutocompleteElement` se appenda vía `watch(step === 3)` + `nextTick` + 260ms para esperar la transición de Vue antes de que el div esté en el DOM.

## Open questions
- Restricción de HTTP referrer en la API key (pendiente para producción — usar dominio real, no localhost).
- Endpoint `POST /geo/resolve-by-coords` en catalog-service no existe aún — solo existe resolución por dirección (que llama Mapbox internamente).

## Next steps
- Crear endpoint en catalog-service que reciba `{lat, lon}` y retorne neighborhood via PostGIS (sin llamar Mapbox).
- Conectar el `gmp-placeselect` handler al chain completo: lat/lon → catalog → predict.
