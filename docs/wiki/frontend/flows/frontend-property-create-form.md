---
title: Flujo de creación de propiedad — form multi-step
status: draft
last-verified: 2026-06-25
owners: [frontend]
related:
  - "[[frontend-architecture]]"
  - "[[frontend-poi-reachable]]"
  - "[[properties-service-listing]]"
  - "[[adr-gmaps-places-geocoding]]"
sources:
  - ../../sources/frontend/2026-06-25-property-create-form-and-nearby-fixes.md
---

## TL;DR

Form de 4 pasos para crear una propiedad, accesible en `/dev/create-property` (sin auth, para desarrollo). El estado vive en un `ref<CreatePropertyForm>` en el orquestador; cada step recibe `form` como prop y emite `update:form` al cambiar — patrón `v-model` manual. El step de ubicación incluye Google Places + `NearbyPlaces` con isocronas para que el creador vea el entorno antes de publicar.

## Pasos

| # | Componente | Campos |
|---|---|---|
| 0 | `StepTipo.vue` | `property_type`, `listing_type`, `condition`, `currency`, `area_m2`, `bedrooms`, `bathrooms` |
| 1 | `StepDetalles.vue` | `price`, `admin_fee`, `parking_spots`, `floor_number`/`total_floors`, `stratum`, `year_built`, `description` |
| 2 | `StepUbicacion.vue` | `location.latitude`, `location.longitude` (vía Google Places); barrio detectado visual; `NearbyPlaces` full width |
| 3 | _(pendiente)_ `StepImagenes.vue` | presigned URL upload flow |

## Orquestador `CreatePropertyDevView.vue`

- Único `ref<CreatePropertyForm>` — la fuente de verdad del form.
- `StepIndicator` en la cabecera con 4 pasos.
- Layout: paso 0/1/3 → `flex-1 p-8` izquierda + `CreateSummary` derecha. Paso 2 → `w-full` (sin summary, `NearbyPlaces` necesita el ancho).
- Botones Anterior/Siguiente en el footer; sin validación de paso por ahora.

## Patrón de comunicación entre pasos

```vue
<StepTipo :form="form" @update:form="form = $event" />
```

Cada step recibe todo el form como prop (sin desestructurar) y emite el form completo modificado. El emisor nunca muta la prop — siempre hace spread:

```ts
emit('update:form', { ...form, price: newValue })
```

Para inputs numéricos el patrón es:
```ts
@input="emit('update:form', { ...form, [field]: +($event.target as HTMLInputElement).value || null })"
```

## `StepUbicacion.vue`

### Layout
Una sola fila: `PlaceAutocompleteElement` (3/4 del ancho) + card "Barrio detectado" (1/4). Debajo: `NearbyPlaces` full width si hay `selectedPlace`, o placeholder con copy explicando el valor del mapa.

### Google Places
Mismo patrón que `useAvmForm.ts` — monta `PlaceAutocompleteElement` en `onMounted` dentro de un `ref` de contenedor. Al seleccionar una dirección (`gmp-select`), extrae `lat`/`lon` de `p.location` y los emite al form.

### Barrio detectado
Llama `getNeighborhood(lat, lon)` de `useLocation.ts` → `GET /v1/geo-resolution/by-coordinates` → `GET /v1/neighborhoods/by-id` → nombre del barrio. Se muestra en la card 1/4 con fondo verde.

### `previewId`
`NearbyPlaces` requiere un `propertyId` válido (UUID). Como la propiedad no existe aún, `StepUbicacion` genera `crypto.randomUUID()` en el `setup` y lo pasa como `property-id`. El backend trata el UUID desconocido como una propiedad sin cache — hace el fetch normal de ORS.

## `CreateSummary.vue`

Sidebar de 72px de ancho con resumen vivo: icono de tipo de propiedad, tipo de negocio (venta/arriendo) y filas de campos (condición, moneda, área, habitaciones, baños). Se actualiza reactivamente con cada cambio del form.

## Pendientes

- `StepImagenes`: flujo presigned URL (igual que `RequestPresignedUrlsUseCase` / `ConfirmImageUploadsUseCase`).
- Envío del form: `POST /v1/properties` con `CreatePropertyForm` completo.
- Resolver y cablear `neighborhood_id` / `city_id` / `country_id` en `StepUbicacion` (hoy solo se guardan `lat`/`lon`).
- Ruta productiva `/properties/new` con auth (el `/dev/create-property` actual es sin auth).

## Claims

- `CreatePropertyDevView` es el único dueño del `ref<CreatePropertyForm>`; los steps no tienen estado local de form ([views/dev/CreatePropertyDevView.vue](frontend/src/views/dev/CreatePropertyDevView.vue)).
- El step 2 (`StepUbicacion`) ocupa `w-full` y oculta `CreateSummary` para dar espacio a `NearbyPlaces` ([views/dev/CreatePropertyDevView.vue](frontend/src/views/dev/CreatePropertyDevView.vue)).
- `StepUbicacion` monta `PlaceAutocompleteElement` en `onMounted` con `google.maps.importLibrary("places")` ([components/properties/create/StepUbicacion.vue](frontend/src/components/properties/create/StepUbicacion.vue)).
- `previewId = crypto.randomUUID()` se genera una vez en el `setup` del componente y se reutiliza mientras el step esté montado ([components/properties/create/StepUbicacion.vue](frontend/src/components/properties/create/StepUbicacion.vue)).
- La ruta `/dev/create-property` tiene `requiresAuth: false` — accesible sin login ([router/routes/dev.ts](frontend/src/router/routes/dev.ts)).
