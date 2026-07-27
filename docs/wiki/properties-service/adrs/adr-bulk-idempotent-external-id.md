---
title: "ADR-0008 — Idempotencia del bulk create vía external_id determinístico (reemplaza la decisión de no deduplicar)"
status: stable
last-verified: 2026-07-27
owners: [properties-service]
related:
  - "[[properties-service-bulk-create-worker]]"
  - "[[properties-service-admin]]"
  - "[[adr-image-upload-presigned-batch]]"
  - "[[open-items]]"
sources: [../../../sources/properties-service/2026-07-27-bulk-async-import-worker.md, ../../../sources/properties-service/2026-07-17-bulk-async-redesign-presigned-retry.md]
decision-date: 2026-07-27
decision-status: accepted
supersedes: decisión de dedup del 2026-07-17 (registrada en [[open-items]], fuente `2026-07-17-bulk-async-redesign-presigned-retry.md`)
---

# ADR-0008 — Idempotencia del bulk create vía external_id determinístico

## Contexto

El 2026-07-17 se decidió **no** implementar deduplicación automática en el bulk create: se evaluó y descartó (a) hash de la fila completa como key sintética —rompe ante cualquier edición legítima, en particular el precio— y (b) hash excluyendo precio con detección de abuso a nivel batch, juzgado sobre-ingeniería. Se aceptó que reintentar con el mismo archivo duplicara, documentándolo como comportamiento esperado, con `Property.bulk_job_id` + una acción de "redo" (soft-delete por batch + reproceso) como mitigación.

Al conectar el worker end-to-end (2026-07-27) se encontró que esa aceptación era más cara de lo previsto:

- `build_models` generaba `uuid.uuid4()` por fila, mientras `bulk_insert` hace upsert con `index_elements=["id"]`. El conflict target **nunca podía dispararse**, así que el `ON CONFLICT DO UPDATE` era decorativo para `Property`.
- `Property` no tiene ningún `UniqueConstraint` de negocio que atrapara el duplicado por otra vía.
- La persistencia pasó a ser **por chunk** (commit cada 2500 filas), así que "el import falló a mitad de camino con parte ya persistida" dejó de ser el caso raro y pasó a ser el normal. Un retry sobre ese estado duplicaba todo lo ya insertado.
- La mitigación en la que se apoyaba la decisión vieja no existe: `Property.bulk_job_id` está declarada ([listing.py:90](backend/properties-service/src/app/models/listing.py#L90)) pero **ningún código la escribe**, y la acción de redo nunca se implementó.

## Decisión

El CSV pasa a llevar una columna **`external_id` obligatoria y no vacía**, y el `property_id` se deriva de ella:

```python
uuid.uuid5(settings.BULK_PROPERTY_ID_NAMESPACE, external_id)
```

El mismo `external_id` produce siempre el mismo `property_id`, lo que hace que el upsert por `id` que ya existía empiece a funcionar y que el reintento sea idempotente por construcción.

**Por qué esto no reincide en lo descartado en julio:** lo que se rechazó fue el *hash de la fila completa*, cuya falla concreta era romperse ante una edición legítima del precio. `external_id` es una clave de negocio estable provista por el autor del archivo, no un derivado del contenido — editar el precio y reimportar **actualiza** la misma property en vez de duplicarla, que es justo el comportamiento que la objeción de julio quería preservar.

`BULK_PROPERTY_ID_NAMESPACE` vive en `settings` y se trata como **congelado**: cambiarlo re-keya todas las properties y los imports pasados vuelven a entrar como registros nuevos.

## Alternativas consideradas

- **`UniqueConstraint` de negocio en `properties`** (p. ej. owner + lat/lon + precio) y conflictuar por ahí — descartado: define "propiedad duplicada" a nivel de schema y es probablemente falso (un edificio tiene N apartamentos en la misma coordenada).
- **Que el retry borre lo insertado por el job original** antes de arrancar — es el camino de la decisión de julio (`bulk_job_id` + redo). Requiere poblar `bulk_job_id` (hoy muerta) y construir la acción de redo. No descartado en el fondo: sigue siendo la respuesta correcta para "deshacer un import", que es un problema distinto de "reintentar sin duplicar".
- **Dejarlo como estaba** — descartado: con commits por chunk el duplicado deja de ser hipotético.

## Consecuencias

- ✅ El reintento es idempotente sin ninguna maquinaria extra: el upsert que ya estaba escrito empieza a hacer lo que decía hacer.
- ✅ La cadena entera deduplica: `Property` por `id`, `PropertyLocation` por `property_id` (deriva del anterior), `PropertyImage` por `url`.
- ✅ `_PROPERTY_UPSERT_FIELDS` excluye `created_at`/`created_by`, así que un re-import actualiza datos pero preserva la auditoría de creación original.
- ❌ **Los CSV existentes dejan de servir**: `seed_bogota_500.csv` y `seed_bogota_5k.csv` no tienen la columna, y con `StrictBase(extra="forbid")` + campo requerido, fallan el 100% de las filas.
- ❌ Un `external_id` reusado entre archivos distintos **sobreescribe** la property anterior en vez de crear una nueva. Si la numeración se reinicia por archivo, se pisan datos.
- ❌ Al vivir en `settings`, el namespace quedó override-able por env var — un valor distinto entre entornos rompe la idempotencia en silencio. Costo aceptado a cambio de no hardcodearlo.
- ⚠️ Esto resuelve "reintentar sin duplicar", **no** "deshacer un import". `bulk_job_id` sigue muerta y la acción de redo sigue sin existir.

## Claims

- `derive_property_id(external_id)` devuelve `uuid.uuid5(settings.BULK_PROPERTY_ID_NAMESPACE, external_id)`; el mismo `external_id` produce siempre el mismo `property_id` ([seed_mapper.py](backend/properties-service/src/app/workers/helpers/mapping/seed_mapper.py)).
- `build_models` deriva `property_id` de `item.external_id` en vez de generar `uuid.uuid4()` ([seed_mapper.py](backend/properties-service/src/app/workers/helpers/mapping/seed_mapper.py)).
- `BulkPropertyCsvRow.external_id` y `BulkCreatePropertyItem.external_id` son `Field(min_length=1)` — un valor vacío haría colisionar todas las filas en un mismo id ([bulk_schemas.py](backend/properties-service/src/app/workers/schemas/bulk_schemas.py)).
- `row_to_item` devuelve `None` si `external_id` viene vacío o solo espacios, convirtiendo la fila en un `BulkRowError` en vez de abortar el chunk ([seed_mapper.py](backend/properties-service/src/app/workers/helpers/mapping/seed_mapper.py)).
- `settings.BULK_PROPERTY_ID_NAMESPACE` es un `uuid.UUID` con default `d1bbd361-a2e7-44b9-b6e3-2a9d699dcdb5` ([settings.py](backend/properties-service/src/app/core/config/settings.py)).
- `_PROPERTY_UPSERT_FIELDS` no incluye `created_at` ni `created_by`, solo `updated_at`/`updated_by` ([sql_property_repository.py:11-17](backend/properties-service/src/app/services/admin/adapters/sql_property_repository.py#L11-L17)).
- `Property.bulk_job_id` está declarada como FK nullable indexada pero ningún código del servicio la escribe ([listing.py:90](backend/properties-service/src/app/models/listing.py#L90)).
