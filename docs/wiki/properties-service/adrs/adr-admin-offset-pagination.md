---
title: "ADR-0009 — El listado admin pagina por offset, no con el cursor opaco del feed"
status: stable
last-verified: 2026-08-24
owners: [properties-service]
related:
  - "[[properties-service-admin]]"
  - "[[adr-feed-opaque-cursor]]"
  - "[[frontend-admin-panel]]"
sources: [../../../sources/properties-service/2026-07-28-bulk-import-smoke-test.md, ../../../sources/properties-service/2026-08-24-bulk-jobs-listing-endpoint.md]
decision-date: 2026-07-28
decision-status: accepted
---

# ADR-0009 — El listado admin pagina por offset, no con el cursor opaco del feed

## Contexto

El feed público usa un cursor opaco en base64url ([[adr-feed-opaque-cursor]]) y esa decisión está bien fundada para su caso. Al preparar `GET /admin/properties` para una tabla de moderación surgió la pregunta obvia: ¿por qué no reusar el mismo mecanismo, si ya está construido y probado?

## Decisión

El listado admin pagina por **offset/limit**, con `total` en la respuesta.

La razón no es simplicidad: es que el admin necesita algo que un cursor **estructuralmente no puede dar**.

- **Saltar a una página arbitraria.** Un cursor codifica "seguí desde acá"; no existe el concepto de página 40.
- **Saber cuántas hay.** "Mostrando 1-20 de 18.744" requiere un `COUNT`, que el cursor no aporta.
- **Ordenar por columna.** Cambiar el orden invalida cualquier cursor emitido, porque la clave de orden viaja adentro.

La evidencia de que esto duele está en el propio front: `useFeed.ts` mantiene un `cursorStack` **solo para poder ir hacia atrás** — y aun con esa maquinaria únicamente soporta anterior/siguiente.

## Alternativas consideradas

- **Reusar el cursor opaco del feed.** Descartado por lo de arriba. Habría obligado a meter la clave de orden en el cursor y aun así dejaría al admin sin total ni salto de página.
- **Cursor + un endpoint de conteo aparte.** Da el total pero no el salto a página N, y agrega un round-trip. Combina lo peor de los dos.

## Consecuencias

- ✅ La tabla puede mostrar total, saltar de página y ordenar por columna sin maquinaria extra en el cliente.
- ✅ `count_all` comparte los filtros con `get_all` vía `_apply_filters`, así que el total no puede divergir de las filas.
- ❌ Un `OFFSET` profundo escanea y descarta filas. Con ~19k propiedades es cuestión de milisegundos; dejaría de serlo en el orden de millones — punto en el que un panel admin necesita búsqueda, no paginación.
- ❌ Si se insertan filas mientras se pagina, el offset puede repetir o saltear elementos. Es el problema que el cursor resuelve, y se acepta: el admin trabaja sobre una tabla que no cambia sola, salvo durante un import bulk.
- ⚠️ Ahora hay **dos mecanismos de paginación en el mismo servicio**. Cuál usar depende del consumidor: scroll infinito sobre datos que se mueven → cursor; tabla operativa que necesita totales y salto de página → offset.

## Claims

- `GetPropertiesAdminRequest` acepta `page` (≥1) y `page_size` (1-100) como query params, y el UC calcula `offset = (page - 1) * page_size` ([admin_schemas.py](backend/properties-service/src/app/services/admin/schemas/admin_schemas.py), [get_properties.py](backend/properties-service/src/app/services/admin/use_cases/get_properties.py)).
- `AdminPropertiesPage` expone `total`, que sale de `count_all`; el feed no devuelve ningún total ([admin_schemas.py](backend/properties-service/src/app/services/admin/schemas/admin_schemas.py)).
- Los tres listados admin —`GET /admin/properties`, `GET /admin/promotions` y `GET /admin/properties/bulk`— aceptan `page`/`page_size` y devuelven `total` en su página ([admin_schemas.py](backend/properties-service/src/app/services/admin/schemas/admin_schemas.py)).
- `useFeed.ts` mantiene un `cursorStack` para soportar la navegación hacia atrás del feed ([useFeed.ts](frontend/src/composables/feed/useFeed.ts)).
