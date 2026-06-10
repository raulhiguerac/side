---
title: ADR-0005 — Google Maps Places API (New) para geocoding
status: stable
last-verified: 2026-05-29
owners: [frontend]
related:
  - "[[frontend]]"
  - "[[frontend-architecture]]"
  - "[[adr-mapbox-geocoding-leaflet-rendering]]"
  - "[[adr-mapbox-frontend-only]]"
sources: [../../sources/frontend/2026-05-27-gmaps-places-avm-form.md, ../../sources/frontend/2026-05-29-vue35-gmaps-places-leaflet-markers.md]
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

El `PlaceAutocompleteElement` se monta en `composables/useAvmForm.ts` via `watch(step === 3)` + `nextTick` + 260ms de espera para que la transición de Vue termine antes de que el div esté disponible en el DOM.

### Detalles de integración (validados 2026-05-29)

- **Evento correcto**: `"gmp-select"` — no `"gmp-placeselect"` (que no dispara).
- **Chain para obtener coordenadas**: `e.placePrediction.toPlace()` → `await place.fetchFields({ fields: ["location", "formattedAddress"] })` → `place.location.lat()/lng()`. `fetchFields` es **obligatorio** — sin él `location` es `undefined`.
- **Tipado**: `PlaceAutocompletePlaceSelectEvent` no está exportado en `@types/google.maps` (versión actual). Workaround: `(e: any)` en el parámetro del listener.
- **`@types/google.maps` en tsconfig**: el array `"types"` de `tsconfig.json` debe incluir `"google.maps"` explícitamente — si solo lista `["webpack-env"]`, TypeScript ignora el paquete.

## Flujo acordado (AVM form → predict)

```
PlaceAutocompleteElement (gmp-select)
  → e.placePrediction.toPlace() + fetchFields → lat/lng
    → GET /v1/geo-resolution/by-coordinates (catalog-service) → neighborhood_id
      → GET /v1/neighborhoods/by-id → neighborhood_name
        → POST /v1/predict (analytics-service)
```

El backend **no necesita un adapter de geocoding nuevo** — catalog-service ya tiene PostGIS ST_Contains para resolver por coordenadas (`/geo-resolution/by-coordinates` existe y es público).

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
- `PlaceAutocompleteElement` se monta en `composables/useAvmForm.ts` via `watch(step)` con 260ms de delay post-`nextTick` ([composables/useAvmForm.ts](frontend/src/composables/useAvmForm.ts)).
- El evento de selección es `"gmp-select"` — el objeto tiene `e.placePrediction.toPlace()` y requiere `fetchFields` antes de acceder a `location` ([composables/useAvmForm.ts](frontend/src/composables/useAvmForm.ts)).
- `tsconfig.json` debe incluir `"google.maps"` en el array `"types"` para que `@types/google.maps` sea reconocido ([tsconfig.json](frontend/tsconfig.json)).
- `@googlemaps/js-api-loader` está en `dependencies` del `package.json` ([package.json](frontend/package.json)).
