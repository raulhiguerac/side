---
title: ADR-0006 — Campos fijos vs. editables al editar una propiedad
status: stable
last-verified: 2026-07-13
owners: [frontend]
related:
  - "[[frontend-property-edit-form]]"
  - "[[properties-service-listing]]"
  - "[[adr-single-listing-type-per-property]]"
sources: [../../../sources/properties-service/2026-07-13-property-edit-fixed-vs-editable-fields.md]
decision-date: 2026-07-13
decision-status: accepted
---

# ADR-0006 — Campos fijos vs. editables al editar una propiedad

## Contexto

`UpdatePropertyRequest` (backend) acepta técnicamente cambiar cualquier campo de una propiedad, incluida la ubicación completa (`LocationField`) — no hay restricción a nivel de schema ni de use case. Al diseñar el frontend de edición (`EditPropertyView.vue`) había que decidir qué debía permitir editar el **producto**, independientemente de lo que el backend tolere.

La razón de fondo: cambiar ciertos atributos hace que, en la práctica, sea "otra propiedad" aunque el `id` se mantenga — el mismo problema que el barco de Teseo.

## Decisión

El frontend restringe la edición a un subconjunto de campos, aunque el backend acepte más:

- **Fijos** (renderizados `disabled`, visibles pero no editables): `property_type`, `listing_type`, `location` (completa), `area_m2`, `bathrooms`, `bedrooms`, `floor_number`/`total_floors`, `year_built`, `parking_spots`, `stratum`.
- **Editables**: `condition`, `currency`, `price`, `admin_fee`, `description`.

## Alternativas consideradas

- **Dejar editable todo lo que el backend acepta** (incluida `location`) — descartada: cambiar la ubicación o los m² de una propiedad ya publicada la convierte en un inmueble distinto sin que cambie de `id`, rompiendo la trazabilidad (histórico de precio, verificación, etc. quedarían atados a un inmueble que ya no es el mismo).
- **Dejar `listing_type` editable** (pasar de venta a arriendo sobre la misma fila) — descartada con más fuerza que el resto: el modelo de datos no soporta que un inmueble tenga ambas modalidades a la vez (ver [[adr-single-listing-type-per-property]]), así que editar `listing_type` no "agrega" una modalidad, transforma la única oferta existente — más confuso que útil.
- **`stratum` editable** — descartada: es una clasificación de la zona (depende de `location`), no un dato que el dueño controle.
- **`condition` fijo junto con el resto** — descartada: a diferencia de los atributos físicos, sí cambia legítimamente con el tiempo (remodelaciones).

## Consecuencias

- ✅ El `id` de una propiedad sigue identificando de forma estable el mismo inmueble físico durante toda su vida en la plataforma.
- ✅ Regla simple de comunicar en UI: los campos fijos se muestran como información (chips/tarjetas), no como inputs.
- ❌ Es una restricción **solo de producto**, no de backend — cualquier cliente que hable directo con `PATCH /v1/properties/{id}` puede saltarla. No hay enforcement server-side.
- ❌ Si en el futuro se decide permitir editar `location`, falta decidir si eso dispara re-cómputo de H3 (`compute_h3`) igual que en `UpdatePropertyUseCase` — el backend ya lo soporta, solo faltaría exponerlo en el front.

## Claims

- El frontend renderiza `property_type`, `listing_type`, `location`, `area_m2`, `bathrooms`, `bedrooms`, `floor_number`/`total_floors`, `year_built`, `parking_spots` y `stratum` como campos no editables en `PropertyHeaderCard.vue` e `PropertyInfoCard.vue` (frontend/src/components/properties/edit/PropertyHeaderCard.vue, frontend/src/components/properties/edit/PropertyInfoCard.vue).
- `PropertyEditForm.vue` solo captura `condition`, `currency`, `price`, `admin_fee` y `description` (frontend/src/components/properties/edit/PropertyEditForm.vue).
- `UpdatePropertyRequest` en el backend no impone ninguna de estas restricciones — todos los campos son `Optional` y aceptados si se envían (backend/properties-service/src/app/services/listing/schemas/listing_schemas.py).
