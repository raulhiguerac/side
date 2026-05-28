---
title: ADR-0005 — Google Maps Places API (New) para geocoding
status: stable
last-verified: 2026-05-27
owners: [frontend]
related: [[frontend]], [[frontend-architecture]], [[adr-mapbox-geocoding-leaflet-rendering]], [[adr-mapbox-frontend-only]]
sources: [../../sources/frontend/2026-05-27-gmaps-places-avm-form.md]
decision-date: 2026-05-27
decision-status: accepted
supersedes: ADR-0003 (mitad de geocoding)
---

# ADR-0005 — Google Maps Places API (New) para geocoding

## Contexto

Para el form AVM del frontend se necesita autocomplete de dirección que resuelva `address → lat/lon`. Se evaluaron tres proveedores:

| Provider | Colombia | Notas |
|---|---|---|
| Mapbox | ❌ insuficiente | Calidad de geocoding en Colombia no apta para producción |
| HERE | ❌ "Entry" | Nivel oficial de cobertura Colombia = Entry — no apto para autocomplete específico |
| Google Maps Places API (New) | ✅ | Excelente cobertura, $200 USD crédito/mes (~66k requests por $1) |

## Decisión

**Google Maps Places API (New)** reemplaza a Mapbox para el geocoding en el frontend.

- Se usa `PlaceAutocompleteElement` (web component nativo de la nueva API).
- El script se carga en `public/index.html` con la key desde `process.env.VUE_APP_GMAPS_KEY` — nunca hardcodeada.
- La key vive en `.env.local` (no va al repo).
- En GCP: habilitar **Places API (New)** (no la clásica) y restringir la key a esa API.

## Setup técnico

```html
<!-- public/index.html -->
<script async src="https://maps.googleapis.com/maps/api/js?key=<%= process.env.VUE_APP_GMAPS_KEY %>&libraries=places&loading=async"></script>
```

El `PlaceAutocompleteElement` se monta via `watch(step === 3)` + `nextTick` + 260ms de espera para que la transición de Vue termine antes de que el div esté disponible en el DOM.

## Flujo acordado (AVM form → predict)

```
PlaceAutocompleteElement
  → gmp-placeselect → place.location.lat()/lng()
    → POST /geo/resolve-by-coords (catalog-service) → barrio_ideca
      → POST /v1/predict (analytics-service)
```

El backend **no necesita un adapter de geocoding nuevo** — catalog-service ya tiene PostGIS ST_Contains para resolver por coordenadas. Solo falta exponer ese endpoint por coordenadas (hoy solo existe resolución por dirección que llama Mapbox internamente).

## Consecuencias

- ✅ Calidad de autocomplete en Colombia notablemente superior a Mapbox y HERE.
- ✅ $200 USD crédito/mes cubre ampliamente el tráfico MVP.
- ✅ `PlaceAutocompleteElement` es un web component — cero código de UI para el autocomplete.
- ❌ Requiere cuenta GCP con tarjeta de crédito (aunque no cobra dentro del crédito).
- ❌ HTTP referrer restriction pendiente para producción — en dev corre sin restricción de dominio.
- ❌ `POST /geo/resolve-by-coords` en catalog-service aún no existe — pendiente crear UC + route que reciba `{lat, lon}` sin pasar por Mapbox.

## Open items

- Agregar restricción de HTTP referrer a la API key antes de ir a producción.
- Crear `ResolveNeighborhoodByCoordsUseCase` en catalog-service (recibe lat/lon → ST_Contains → neighborhood, sin Mapbox).
- Conectar el handler `gmp-placeselect` al chain completo en `DevPlaygroundView.vue`.

## Claims

- El script de GMaps se carga en `public/index.html` con `<%= process.env.VUE_APP_GMAPS_KEY %>` ([public/index.html:15](frontend/public/index.html#L15)).
- `VUE_APP_GMAPS_KEY` se define en `.env.local` — no existe en el repo.
- `PlaceAutocompleteElement` se monta en `DevPlaygroundView.vue` via `watch(step)` con 260ms de delay post-`nextTick` ([views/dev/DevPlaygroundView.vue](frontend/src/views/dev/DevPlaygroundView.vue)).
- `@googlemaps/js-api-loader` está en `dependencies` del `package.json` ([package.json](frontend/package.json)).
