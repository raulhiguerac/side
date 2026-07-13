---
title: "ADR-0007 — Property es 1 fila = 1 listing_type (sin soporte para venta+arriendo simultáneo)"
status: stable
last-verified: 2026-07-13
owners: [properties-service]
related:
  - "[[properties-service-listing]]"
  - "[[adr-property-edit-fixed-fields]]"
sources: [../../../sources/properties-service/2026-07-13-single-listing-type-per-property-gap.md]
decision-date: 2026-07-13
decision-status: accepted
---

# ADR-0007 — Property es 1 fila = 1 listing_type (sin soporte para venta+arriendo simultáneo)

## Contexto

Al decidir si `listing_type` debería ser editable en el flujo de edición de propiedades (ver [[adr-property-edit-fixed-fields]]), se identificó que el modelo de datos actual no soporta que un mismo inmueble físico tenga simultáneamente una oferta de venta y una de arriendo.

## Decisión

`Property` se mantiene como está: **una fila = una oferta con un `listing_type` fijo**. No se introduce ninguna relación entre filas que representen el mismo inmueble físico bajo distintas modalidades — este ADR documenta el gap como conocido, no lo resuelve.

Consecuencia directa en el flujo de edición: `listing_type` queda **no editable** (ver [[adr-property-edit-fixed-fields]]) — cambiarlo transformaría la única oferta existente en vez de agregar una modalidad.

## Alternativas consideradas

- **Agregar `parent_property_id` o una tabla de agrupación** para vincular ofertas del mismo inmueble físico — no evaluado en profundidad, identificado como el camino más probable si el negocio pide esto. No implementado ahora: no hay demanda confirmada y agrega complejidad de modelo (migraciones, invalidación de cache por grupo, UI de gestión) sin caso de uso urgente.
- **Permitir `listing_type` como lista en una sola fila** (`["sale", "rent"]`) — no evaluado; cambiaría el shape de `PropertyCardSchema`/`PropertyDetailSchema` y probablemente de los filtros de búsqueda (`GetFeedUseCase` filtra por `listing_type` único hoy).

## Consecuencias

- ✅ Modelo simple: cada fila es autocontenida, sin necesidad de resolver relaciones al leer/escribir.
- ❌ Si un dueño quiere publicar el mismo inmueble en venta y arriendo, necesita crear **dos filas distintas** (dos `id`, con `location`/`area_m2`/etc. duplicados a mano) — sin ningún vínculo entre ellas.
- ❌ Si el dueño vende la propiedad y solo actualiza (o borra) la fila de venta, la fila de arriendo queda huérfana y sigue publicada — el sistema no sabe que están relacionadas.
- ❌ Deuda de producto/UX: hoy no hay forma de comunicarle al dueño que estas dos "propiedades" son en realidad una.

## Claims

- `Property` tiene `listing_type` como columna simple (no array, no relación) — una fila representa exactamente una oferta (backend/properties-service/src/app/models/property.py).
- No existe ningún campo tipo `parent_property_id` ni tabla de agrupación entre `Property` rows en el modelo actual (backend/properties-service/src/app/models/property.py).
- El frontend no permite editar `listing_type` desde `EditPropertyView.vue`, consistente con este gap (frontend/src/components/properties/edit/PropertyInfoCard.vue).
