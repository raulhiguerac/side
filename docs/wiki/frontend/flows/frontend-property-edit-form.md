---
title: Flujo de edición de propiedad — tarjetas presentacionales
status: stable
last-verified: 2026-07-15
owners: [frontend]
related:
  - "[[frontend-architecture]]"
  - "[[frontend-property-create-form]]"
  - "[[properties-service-listing]]"
  - "[[adr-property-edit-fixed-fields]]"
  - "[[adr-single-listing-type-per-property]]"
sources:
  - ../../../sources/frontend/2026-07-13-view-decoupling-composables-and-cards.md
  - ../../../sources/frontend/2026-07-13-decimal-serialized-as-string.md
  - ../../../sources/properties-service/2026-07-13-property-edit-fixed-vs-editable-fields.md
  - ../../../sources/frontend/2026-07-15-property-edit-photos-upload-delete.md
---

## TL;DR

Vista de edición en `/properties/:id/edit` (`EditPropertyView.vue`), accesible desde `MyPropertiesView`. A diferencia del form de creación (wizard de 4 pasos), es una sola pantalla en 2 columnas: fotos + info fija a la izquierda, estadísticas + form editable a la derecha. La view solo orquesta (fetch + `form` ref + save + estado de 2 modales de fotos); todo el markup vive en 5 componentes-tarjeta + 2 modales bajo `components/properties/edit/`. Reutiliza la convención `:form`/`@update:form` del create flow (ver [[frontend-property-create-form]]) y el componente `PropertyPhotoGrid` que ya usaba `PropertyDetailView`.

## Por qué solo un subconjunto de campos es editable

Ver [[adr-property-edit-fixed-fields]] para la decisión completa. Resumen: `property_type`, `listing_type`, `location`, `area_m2`, `bathrooms`, `bedrooms`, `floor_number`/`total_floors`, `year_built`, `parking_spots` y `stratum` se muestran como información de solo lectura — cambiar cualquiera de estos, aunque el backend lo permita, convierte la publicación en "otra propiedad" en la práctica. Solo `condition`, `currency`, `price`, `admin_fee` y `description` son editables.

## Componentes (`components/properties/edit/`)

| Componente | Responsabilidad | Props / Emits |
|---|---|---|
| `PropertyHeaderCard.vue` | Tipo + negocio + badge de estado + ubicación + fila de estadísticas (área/habitaciones/baños/parqueaderos) | `property: PropertyDetail \| null`, `locationLabel: string` |
| `PropertyPhotosCard.vue` | Envuelve `PropertyPhotoGrid.vue` + header "Fotos N/20" + botones Agregar/Eliminar. Presentacional puro: calcula `imagesAllowed` localmente pero no llama a la red ni sabe de modales | `property: PropertyDetail \| null`, emits `add-photos`, `delete-photos` |
| `PropertyInfoCard.vue` | Chips de los campos fijos (tipo, negocio, piso(s), año, estrato) | `property: PropertyDetail \| null` |
| `PropertyEditForm.vue` | Los 5 campos editables — precio/admin con formateo de dinero, condición/moneda con toggles, descripción | `form: PropertyEditForm`, emit `update:form` |
| `PropertyEditActions.vue` | Botones Volver/Guardar | emits `back`, `save` |
| `UploadPropertyImagesModal.vue` | Modal que reusa `StepImagenes.vue` + `useImageUpload()` del create flow para agregar fotos a una propiedad ya publicada | `modelValue`, `propertyId`, `imagesAllowed`, `hasExistingPhotos`, emits `update:modelValue`, `success` |
| `DeletePropertyImagesModal.vue` | Modal con grid 5 columnas de fotos existentes; selección múltiple + borrado batch en un solo request | `modelValue`, `propertyId`, `images: PropertyImageCard[]`, emits `update:modelValue`, `success` |

`EditPropertyView.vue`: `route`/`router`, `isLoading`/`property`/`locationLabel`/`form` refs, `showUploadModal`/`showDeleteModal` refs, una función `fetchProperty()` (usada tanto en `onMounted` como de refetch tras subir/borrar fotos), y `handleSave` cableado a `PATCH /v1/properties/{id}`.

### Patrón de form reutilizado del create flow

```vue
<PropertyEditForm :form="form" @update:form="form = $event" />
```

Mismo contrato que `StepTipo.vue`/`StepDetalles.vue` (ver [[frontend-property-create-form]]) — reemplazo del objeto completo, no v-model por campo. `PropertyEditForm.vue` es dueño de todo el estado de UI de los inputs de dinero (`displayPrice`/`displayAdminFee`, focus/blur/input) — el padre solo ve `form.price`/`form.admin_fee` como números.

### `PropertyPhotoGrid.vue` — prop `expand` para reuso sin romper el consumidor original

`PropertyPhotoGrid.vue` (usado también por `PropertyDetailView`) tenía alto fijo por CSS (`grid-rows-[200px_200px]`). Para que `PropertyPhotosCard.vue` pudiera estirarlo y empatar la altura de las dos columnas del edit form, se agregó un prop opcional `expand?: boolean` (default `false`) que cambia a `flex-1 grid-rows-2` solo cuando se pasa explícito. `PropertyDetailView` no lo pasa — cero cambio de comportamiento ahí.

## Gotcha: campos `Decimal` del backend llegan como string

`price`, `admin_fee`, `area_m2` y `bathrooms` vienen serializados como **string JSON** desde `PropertyDetailSchema` (Pydantic serializa `Decimal` así), pese a que el tipo TS (`PropertyDetail`) los declara `number`. Hay que envolverlos en `Number(...)` al leerlos de la respuesta — si no, el formateo (`toLocaleString`) pasa de largo sin error visible porque `Object.prototype.toLocaleString` en un string simplemente devuelve el string sin tocar. `EditPropertyView.vue` lo hace al popular `form`; `usePropertyMapper.ts` ya lo hacía antes para `price`/`bathrooms` en las cards del feed.

## Flujo de fotos: agregar y borrar sobre una propiedad existente

`PropertyPhotosCard.vue` ya no es de solo lectura — expone dos acciones que `EditPropertyView.vue` resuelve con dos modales nuevos, ambos montados como hermanos del card (no dentro de él).

### Reuso del create flow para subir

`UploadPropertyImagesModal.vue` monta `<StepImagenes v-model="selectedFiles" :max="imagesAllowed" :has-existing-photos="hasExistingPhotos" />` y usa el mismo composable `useImageUpload()` que `CreatePropertyView` (ver [[frontend-property-create-form]]) — reusable tal cual porque ya no navega internamente. `imagesAllowed = LIMITS.MAX_IMAGES_PER_PROPERTY - property.images.length` se calcula en `PropertyPhotosCard.vue` como UI derivada (sin red) y se pasa como `max`; `hasExistingPhotos = property.images.length > 0` controla si `StepImagenes` muestra el badge "Portada" en el primer archivo — no tiene sentido marcarlo si la propiedad ya tiene fotos (y posible cover) previas.

### Por qué borrar es selección múltiple + un solo request

El backend expone `DELETE /v1/properties/{id}/images` como endpoint **batch-only** (`{ image_ids: uuid[] }`) — no hay endpoint de borrado por-imagen. `DeletePropertyImagesModal.vue` refleja eso: grid de 5 columnas, cada foto con un ícono de basurero que togglea su `id` dentro de un array local `selectedIds`, y un solo botón "Eliminar (N)" que manda el array completo en un request.

### `fetchProperty()` como refetch, no como reset

`EditPropertyView.vue` extrajo el fetch inicial a una función `fetchProperty()`, reusada como callback de `@success` en ambos modales de fotos. Intencionalmente **no** resetea `form` — evita perder ediciones en curso en los otros campos cuando el usuario cierra un modal de fotos.

### Endurecimiento del delete modal

`DeletePropertyImagesModal.vue` tiene un ref `loading` como guard (evita doble submit concurrente si el usuario clickea "Eliminar" dos veces rápido), `try/catch/finally` con mensaje de error visible, y un `watch` sobre `modelValue` que limpia `selectedIds`/`error` al cerrarse (el componente no se desmonta entre aperturas porque `BaseModal` solo togglea un `v-if` interno).

## Pendientes

Ninguno pendiente al 2026-07-15: `handleSave()` está cableado a `PATCH /v1/properties/{id}` y el flujo de fotos (agregar/borrar) quedó completo end-to-end.

## Claims

- `EditPropertyView.vue` no contiene markup de tarjetas — solo layout de 2 columnas y wiring de los 5 componentes hijos (frontend/src/views/properties/edit/EditPropertyView.vue).
- `PropertyEditForm.vue` recibe `form: PropertyEditForm` y emite `update:form` con el objeto completo modificado, igual que `StepTipo.vue`/`StepDetalles.vue` (frontend/src/components/properties/edit/PropertyEditForm.vue).
- `PropertyEditForm.vue` es dueño exclusivo de `displayPrice`/`displayAdminFee` y su lógica de focus/blur/input — el padre no los conoce (frontend/src/components/properties/edit/PropertyEditForm.vue).
- `PropertyPhotoGrid.vue` acepta un prop opcional `expand` (default `false`) que cambia `grid-rows-[200px_200px]` fijo por `flex-1 grid-rows-2` (frontend/src/components/properties/photos/PropertyPhotoGrid.vue).
- `PropertyPhotosCard.vue` es el único consumidor que pasa `expand` a `PropertyPhotoGrid` (frontend/src/components/properties/edit/PropertyPhotosCard.vue).
- El tipo `PropertyEditForm` reusa `PropertyDetail["condition"]` y `PropertyDetail["currency"]` en vez de redeclarar los union literals (frontend/src/types/properties.ts).
- `EditPropertyView.vue` coacciona `price`/`admin_fee`/`area_m2`/`bathrooms` con `Number(...)` al leerlos de `GET /v1/properties/{id}` (frontend/src/views/properties/edit/EditPropertyView.vue).
- `PropertyPhotosCard.vue` calcula `imagesAllowed` localmente y emite `add-photos`/`delete-photos` sin llamar a la red — el estado de los modales (`showUploadModal`/`showDeleteModal`) vive en `EditPropertyView.vue` (frontend/src/components/properties/edit/PropertyPhotosCard.vue).
- `UploadPropertyImagesModal.vue` reusa `StepImagenes.vue` y `useImageUpload()` del create flow, pasándoles `max=imagesAllowed` y `has-existing-photos` dinámicos en vez de los valores fijos que usa `CreatePropertyView` (frontend/src/components/properties/edit/UploadPropertyImagesModal.vue).
- `DELETE /v1/properties/{id}/images` es batch-only (`image_ids: uuid[]`) — no existe endpoint de borrado por imagen individual ([properties.py](backend/properties-service/src/app/api/routes/properties.py)).
- `DeletePropertyImagesModal.vue` usa un ref `loading` como guard para evitar que un doble click dispare dos `DELETE` concurrentes (frontend/src/components/properties/edit/DeletePropertyImagesModal.vue).
- `fetchProperty()` en `EditPropertyView.vue` se reutiliza como refetch tras `@success` de ambos modales de fotos y no resetea `form` (frontend/src/views/properties/edit/EditPropertyView.vue).
