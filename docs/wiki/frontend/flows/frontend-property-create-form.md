---
title: Flujo de creación de propiedad — form multi-step
status: draft
last-verified: 2026-06-28
owners: [frontend]
related:
  - "[[frontend-architecture]]"
  - "[[frontend-poi-reachable]]"
  - "[[properties-service-listing]]"
  - "[[adr-gmaps-places-geocoding]]"
  - "[[adr-image-upload-presigned-batch]]"
sources:
  - ../../sources/frontend/2026-06-25-property-create-form-and-nearby-fixes.md
  - ../../sources/frontend/2026-06-28-endpoint-coverage-and-stepimages.md
---

## TL;DR

Form de 4 pasos para crear una propiedad, accesible en `/properties/create` (auth requerida). El estado vive en un `ref<CreatePropertyForm>` en el orquestador `CreatePropertyView.vue`; cada step recibe `form` como prop y emite `update:form` al cambiar — patrón `v-model` manual. El step de ubicación incluye Google Places + `NearbyPlaces`. Al terminar paso 2, la propiedad se crea en backend (POST); paso 3 sube las imágenes y navega a `/properties`.

## Pasos

| # | Componente | Campos |
|---|---|---|
| 0 | `StepTipo.vue` | `property_type`, `listing_type`, `condition`, `currency`, `area_m2`, `bedrooms`, `bathrooms` |
| 1 | `StepDetalles.vue` | `price`, `admin_fee`, `parking_spots`, `floor_number`/`total_floors`, `stratum`, `year_built`, `description` |
| 2 | `StepUbicacion.vue` | `location.latitude`, `location.longitude` (vía Google Places); barrio detectado visual; `NearbyPlaces` full width |
| 3 | `StepImagenes.vue` | selección de archivos local; lógica de upload la cablea el padre |

## Orquestador `CreatePropertyView.vue`

- Único `ref<CreatePropertyForm>` — la fuente de verdad del form.
- `StepIndicator` en la cabecera con 4 pasos.
- Layout: paso 0/1 → `flex-1 p-8` izquierda + `CreateSummary` derecha. Pasos 2 y 3 → `w-full`.
- Botones Anterior/Siguiente en el footer con validación por paso (`isStepValid`).
- Al hacer click en "Publicar →" desde paso 2 → `submitAndContinue()` → `POST /v1/properties/create` → si ok: `propertyId` se guarda, `currentStep = 3`; si falla: `currentStep = 3` con error state.
- Paso 3 muestra `StepImagenes` (sin error) o el bloque de error con "Reintentar →".
- `selectedFiles = ref<File[]>([])` vive en el orquestador y se pasa al paso 3 vía `v-model`.

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

## `StepImagenes.vue`

Componente visual puro — selección y preview de imágenes. La lógica de upload la cablea el padre.

- `defineModel<File[]>({ default: () => [] })` — el padre accede al array de `File` para las API calls.
- Drop zone con drag-and-drop + click to select; preview grid con badge "Portada" en la primera imagen.
- `URL.createObjectURL` para previews locales; `onUnmounted` revoca los object URLs.
- Botón "Publicar" en el footer deshabilitado si `selectedFiles.length === 0`.
- Ruta dev: `/#/dev/imagenes` → `StepImagenesDevView.vue` para ver el componente sin pasar por el form completo.

### Flujo de upload (a cablear por el padre)

```
POST /v1/properties/images/presigned-urls  { property_id, create_count }
  → { batch_id, items[{ upload_url, public_url, key }] }

PUT <upload_url>  (binary, directo a MinIO — uno por imagen)

POST /v1/properties/{id}/images/confirm  { batch_id, confirmed_keys: [keys de PUTs exitosos] }
  → 204

router.push('/properties')
```

`confirmed_keys` incluye solo los keys de los PUTs que salieron bien. Si alguno falla, ese key se omite.

## Pendientes

- Cablear flujo upload en `CreatePropertyView`: presigned-urls → PUT → confirm → `router.push('/properties')`.
- Resolver y cablear `neighborhood_id` / `city_id` / `country_id` en `StepUbicacion` (hoy solo se guardan `lat`/`lon`).

## Claims

- `CreatePropertyView` es el único dueño del `ref<CreatePropertyForm>` y `ref<File[]>`; los steps no tienen estado local de form ([views/properties/create/CreatePropertyView.vue](frontend/src/views/properties/create/CreatePropertyView.vue)).
- El step 2 (`StepUbicacion`) y step 3 (`StepImagenes`) ocupan `w-full` y ocultan `CreateSummary` ([views/properties/create/CreatePropertyView.vue](frontend/src/views/properties/create/CreatePropertyView.vue)).
- `submitAndContinue()` hace `POST /v1/properties/create`; en éxito guarda `propertyId` y avanza a step 3; en fallo avanza igual pero con `error` seteado ([views/properties/create/CreatePropertyView.vue](frontend/src/views/properties/create/CreatePropertyView.vue)).
- `StepImagenes` expone `files` vía `defineModel<File[]>({ default: () => [] })` — sin API calls internas ([components/properties/create/StepImagenes.vue](frontend/src/components/properties/create/StepImagenes.vue)).
- `StepUbicacion` monta `PlaceAutocompleteElement` en `onMounted` con `google.maps.importLibrary("places")` ([components/properties/create/StepUbicacion.vue](frontend/src/components/properties/create/StepUbicacion.vue)).
- `previewId = crypto.randomUUID()` se genera una vez en el `setup` del componente y se reutiliza mientras el step esté montado ([components/properties/create/StepUbicacion.vue](frontend/src/components/properties/create/StepUbicacion.vue)).
- Ruta dev `/#/dev/imagenes` → `StepImagenesDevView.vue` para preview del componente sin auth ni form ([router/routes/dev.ts](frontend/src/router/routes/dev.ts), [views/dev/StepImagenesDevView.vue](frontend/src/views/dev/StepImagenesDevView.vue)).
