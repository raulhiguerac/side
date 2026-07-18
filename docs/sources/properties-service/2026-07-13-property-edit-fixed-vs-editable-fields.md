---
title: Campos fijos vs. editables al editar una propiedad
captured-from: conversation
captured-on: 2026-07-13
participants: [raul, claude]
---

## Context

Al diseñar el frontend de edición de propiedades (`EditPropertyView.vue`), se revisó que `UpdatePropertyRequest` (backend) técnicamente acepta cambiar cualquier campo de la propiedad, incluida la ubicación completa (`LocationField`). Se discutió qué debería permitir editar el **producto**, no el backend — la razón de fondo: cambiar ciertos atributos hace que, en la práctica, sea "otra propiedad" aunque el `id` se mantenga (analogía usada: barco de Teseo).

## Key conclusions

- **Campos fijos tras publicar** (no editables desde el frontend, aunque el backend los acepte): `property_type`, `listing_type`, `location` (completa: neighborhood/city/country/lat/lon), `area_m2`, `bathrooms`, `bedrooms`, `floor_number`/`total_floors`, `year_built`, `parking_spots`, `stratum`.
- **Campos editables**: `condition` (nuevo/usado/remodelado — sí cambia con el tiempo, ej. remodelaciones), `currency`, `price`, `admin_fee`, `description`.
- **`property_type` y `listing_type` fijos por la misma razón**: cambiar "casa" a "apto", o "venta" a "arriendo", transforma la publicación en otra distinta. Ver `[[single-listing-type-per-property-gap]]` para el gap de modelo relacionado (no se puede tener venta+arriendo del mismo inmueble).
- **`stratum` se agrupó con los fijos** porque es una clasificación de la zona (depende de `location`, no del dueño).
- Esta es una regla de **producto**, no una restricción de `UpdatePropertyRequest` — el backend (`app/services/listing/schemas/listing_schemas.py`) no impone ninguna de estas restricciones; se aplican solo en el frontend (campos renderizados como `disabled` en `PropertyInfoCard.vue`/`PropertyHeaderCard.vue`).

## Open questions

- Si en el futuro se permite editar `location`, falta decidir si eso dispara un re-cálculo de H3 (`compute_h3`) igual que en `UpdatePropertyUseCase` — el backend ya lo soporta, solo falta exponerlo en el front.

## Next steps

- Ninguno inmediato: el frontend de edición (`EditPropertyView.vue` + componentes en `components/properties/edit/`) ya refleja esta regla vía campos disabled/hidden.
