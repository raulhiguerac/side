---
title: Bulk-create worker — streaming CSV desde MinIO (properties-service)
status: draft
last-verified: 2026-07-22
owners: [properties-service]
related:
  - "[[properties-service]]"
  - "[[properties-service-admin]]"
  - "[[properties-service-catalog]]"
  - "[[properties-service-users]]"
  - "[[open-items]]"
sources:
  - ../../../sources/properties-service/2026-07-19-bulk-create-worker-streaming-csv.md
  - ../../../sources/properties-service/2026-07-22-bulk-create-properties-refactor.md
---

## TL;DR

`BulkCreatePropertiesUseCase` (`workers/bulk_create_properties.py`) está en reconstrucción: en vez de cargar el CSV entero en memoria, lo lee en streaming desde MinIO en chunks de bytes, los reensambla en filas de CSV correctamente (incluyendo campos multilínea entre comillas), las agrupa en batches de 2500, y resuelve `lat/lon` contra catalog-service **una vez por batch** en vez de una vez por fila. El hallazgo central de esta reconstrucción: `csv.reader` no tira error si le cortás el buffer a mitad de un campo entre comillas — trunca en silencio — así que el streaming necesita garantizar que nunca le llegue un buffer así.

## `MinioStorageAdapter.chunk_file` — streaming de bytes desde MinIO

`services/shared/adapters/minio_storage_adapter.py`. Envuelve `boto3` (sync) para leer un objeto de MinIO en chunks, sin cargar el archivo completo en memoria.

Bugs del primer borrador, corregidos:
1. **Sin loop** — el método hacía un solo `body.read(chunk_size)` y `yield`, terminando ahí; cualquier archivo más grande que `chunk_size` quedaba truncado en silencio. Fix: `while True: ... if chunk == b"": break`.
2. **Llamadas sync de boto3 sin `run_in_threadpool`** — `get_object`/`body.read()` bloqueaban el event loop en cada iteración, a diferencia de los otros métodos del mismo archivo (`generate_presigned_put_url(s)`), que sí wrappean `self._client.*` con `run_in_threadpool`.

`chunk_size` es `settings.STORAGE_CHUNK_SIZE_BYTES` (10 MB, subido desde 1 MB) — decisión separada del batch size de filas enviadas a catalog/users (ver abajo); no están relacionados.

## `chunk_file` (helper) — bytes → texto alineado a `\n`

`workers/helpers/chunking.py::chunk_file`. Envuelve al adapter de arriba para garantizar que cada bloque de texto que yieldea termina exactamente en un byte `\n` real — nunca corta una línea a la mitad entre un chunk y el siguiente. Guarda el resto sin `\n` (`partial_chunk`) para pegarlo con el próximo chunk. Al agotarse el stream, flushea lo que haya quedado pendiente (si el archivo no termina en `\n`, esa última línea se pierde sin este flush).

Esto resuelve el problema de **bytes cortados a mitad de línea**, pero no sabe nada de CSV — no le importa si una "línea" cortada por `\n` está en realidad dentro de un campo entre comillas de una fila de CSV. Ese problema lo resuelve la siguiente capa.

## `iter_csv_rows` — reensamblado CSV-aware, el hallazgo real

`workers/helpers/chunking.py::iter_csv_rows`. Consume `chunk_file` y yieldea un `dict` resuelto por fila (header ya aplicado), en vez de líneas crudas.

**El problema descubierto**: el CSV de seed real (`data/ml/AVM/data/seed_bogota_500.csv`) tiene campos `descripcion` con saltos de línea literales dentro de las comillas — verificado: 500 filas reales vía `csv.reader`, pero 1597 líneas físicas (`wc -l`). O sea, en promedio cada fila ocupa ~3.2 líneas de texto. Un split ingenuo por `\n` (lo que hace `chunk_file`) corta esos campos a la mitad de forma rutinaria, no como edge case raro.

**Por qué no alcanza con reintentar**: se probó empíricamente que `csv.reader`, si su iterador subyacente se queda sin líneas a mitad de un campo entre comillas, **no lanza excepción** — cierra el campo en el EOF que le tocó y devuelve la fila truncada, sin ningún error capturable. Ejemplo real del test:

```python
# buffer cortado a mitad de comillas
lines = ['a,b,c\n', '1,"hello\n']
# csv.reader(lines) devuelve:  ['1', 'hello\n']   ← truncado, sin avisar
```

Esto descarta cualquier estrategia de "parseá y si falla reintentá con más datos" — para cuando notás que algo salió mal, el dato ya está corrompido, no hay excepción que atrapar.

**La solución — paridad de comillas**: se acumula texto decodificado y se cuenta cuántos caracteres `"` aparecen en total. Mientras ese conteo sea impar, hay una comilla abierta sin cerrar (un campo multilínea a medio venir) y **no se intenta parsear** — se sigue acumulando más chunks. Recién cuando el conteo es par (todas las comillas cerradas) se le pasa el buffer completo a `csv.reader`, garantizando que nunca ve un campo truncado.

**Segundo bug encontrado en la misma pasada**: `pending.splitlines()` (sin `keepends`) **elimina los saltos de línea** al partir el texto — así que aunque la paridad de comillas esté bien y el buffer esté completo, `csv.reader` reconstruye el campo multilínea **sin el separador** (`"Dorado.Este bellísimo..."` en vez de `"Dorado.\n\nEste bellísimo..."`). Se reprodujo incluso pasándole el archivo entero en un solo chunk — no era un problema de streaming, era el uso de `splitlines()` en sí. Fix: `pending.splitlines(keepends=True)`.

**Validación**: comparado byte a byte contra `csv.DictReader` leyendo el archivo completo en memoria, con 5 tamaños de chunk distintos (37 bytes hasta el archivo entero de una vez) — las 500 filas matchean exacto en los 5 casos.

## `BulkPropertyCsvRow` — schema de la fila cruda

`services/admin/schemas/admin_schemas.py`. Mirror del header real del CSV de seed más un campo `email` nuevo (columna que todavía no existe en el CSV actual — necesaria para resolver `owner_id`, ver [[properties-service-users]]).

Decisión deliberada: los campos con valores no numéricos en el dataset real (`parqueaderos`, `piso`, `estrato`, `antiguedad`, etc. — "Sin especificar", "16 a 30 años") se quedan como `str` en este schema, **a propósito** — no se tipan como `int`/`Decimal` acá porque eso rompería el reuso de los parsers tolerantes que ya existen en `seed_mapper.py` (`parse_parking`, `parse_bathrooms`, `parse_stratum`, `parse_condition`, `parse_floor_number`). Este schema valida *shape* (columnas presentes, nombres correctos vía `extra="forbid"` de `StrictBase`), no *tipo de negocio* — esa conversión sigue pasando en `seed_mapper.py`, sin duplicarla acá.

`lat`/`lon` sí son `float` (nunca traen valores no numéricos, y hacen falta como float para `PointToResolve` de catalog de todos modos).

**Validación en el borde, no en el generador** (2026-07-22): `iter_csv_rows` se queda "tonto" (CSV genérico → `dict`), y `execute()` valida cada `dict` con `BulkPropertyCsvRow(**row)`. `StrictBase` es `extra="forbid"` + `str_strip_whitespace` pero **no** `strict=True`, así que la coerción sigue viva — `lat`/`lon` string del CSV se convierten a `float` sin fricción. Una fila que falla lanza `ValidationError`, se convierte en un `BulkRowError` y se saltea (`continue`); una fila mala no aborta el batch de 2500.

## `BulkRowError` — traza de error estructurada

`services/admin/schemas/admin_schemas.py`. Reemplaza el `list[str]` anterior de `BulkCreatePropertiesResult.errors`. Shape: `line: int`, `ref: str`, `issues: list[str]`.

- `line` es un **contador monotónico** sobre las filas que emite el generador — **no** el índice dentro del batch, que es windowed (0–2499) y reportaría el número equivocado (la fila 5000 saldría como "2500" en el segundo batch).
- `ref` = identificador humano de la fila cruda (`email @ lat,lon`), armado por el helper `row_ref(row: dict) -> str` (`workers/helpers/row_ref.py`), que lee con `.get(..., "?")` porque el campo que falló puede ser justo uno de esos.
- `issues` deriva de `e.errors()` como `f"{err['loc'][-1]}: {err['msg']}"` por cada error de pydantic.

`BulkCreatePropertiesResult.errors: list[BulkRowError]` queda alineado con `BulkJob.errors`, que es `ARRAY(JSONB)` (`jsonb[]`) — se serializa con `[e.model_dump() for e in result.errors]` en el borde de persistencia; el modelo ORM guarda `list[dict]`, sin importar el schema de servicio (evita invertir la dependencia dominio→aplicación).

## `BulkCreatePropertiesUseCase.execute()` y `process_location_batch`

`execute()`:
1. Itera `iter_csv_rows(...)`, valida cada fila (arriba) y acumula un **wrapper** por fila: `{"line": lines, "id": str(uuid.uuid4()), "value": BulkPropertyCsvRow}`. El `id` es un UUID real generado al leer — sirve de clave de correlación con catalog y de futuro `property_id`. Es `str(uuid.uuid4())` (no la clase `uuid.UUID`, no un `UUID` crudo) porque `PointToResolve.id` es `str` y `result.id` vuelve `str`; si la key de `rows_by_id` fuera `UUID`, el lookup daría `KeyError`.
2. Al llegar a 2500 filas: `to_process, batch = batch[:2500], batch[2500:]`, procesa `to_process`, sigue acumulando el resto.
3. Al agotarse el stream, flush del remanente (`if batch: ...`) — mismo patrón que el flush de `chunk_file`.

`process_location_batch(batch, *, catalog)` — extraído a `workers/helpers/location_batch.py` (función libre, desacoplada de la clase; recibe `catalog: CatalogGateway` por parámetro en vez de `self.catalog`):
1. Por cada wrapper del batch, arma `PointToResolve(id=row['id'], lat=row["value"].lat, lon=row["value"].lon)` (lat/lon son atributos del modelo en `row["value"]`) y lo registra en `rows_by_id[row['id']] = row`. Filas con `lat`/`lon` inválido caen a `errors` como `BulkRowError`.
2. Llama `catalog.get_locations_bulk(points)` **una sola vez** para todo el batch.
3. Itera sobre la *respuesta* (no sobre `batch`) para mergear `ResolvedPoint.location` en el wrapper por `id` — una fila sin match (`location is None`) queda en `errors` en vez de colarse sin `neighborhood_id`/`city_id`/`country_id`.
4. Devuelve `(enriched: list[dict], errors: list[BulkRowError])`.

**Sin conectar todavía** (al 2026-07-22): (a) la segunda mitad de `execute()` sigue con código muerto del diseño per-row (`asyncio.gather` sobre `sem`/`records`/`self._enrich_location`, más `row_to_item(row=result, ...)`) que no casa con el enfoque por-batch de arriba y referencia variables indefinidas; (b) `_process_users_batch` está truncado a media firma; (c) `execute()` **no cierra el `BulkJob`** — no escribe `status`/`errors`/`confirmed_at`, así que el front que lee el job siempre ve `pending` + `errors=[]`; falta un método de write-back en `BulkJobRepository` (p. ej. `mark_finished`) y decidir cuándo el status es `failed`. Falta también resolver la dirección del resolve de users (ver [[properties-service-users]]) antes de poblar `owner_id` del CSV real; hoy `build_models` usa `owner_id=principal.sub` (todo queda del admin que sube el archivo).

## Claims

- `MinioStorageAdapter.chunk_file` usa `run_in_threadpool` para `get_object` y cada `.read()`, con un `while True` que corta al recibir `b""` ([minio_storage_adapter.py](backend/properties-service/src/app/services/shared/adapters/minio_storage_adapter.py)).
- `settings.STORAGE_CHUNK_SIZE_BYTES = 10_000_000` (subido desde 1MB) ([settings.py](backend/properties-service/src/app/core/config/settings.py)).
- `chunk_file` (helper) garantiza que cada bloque yieldeado termina en un byte `\n` real, cargando el resto en `partial_chunk` para la próxima iteración, con flush final si el archivo no termina en `\n` ([chunking.py](backend/properties-service/src/app/workers/helpers/chunking.py)).
- `iter_csv_rows` solo invoca `csv.reader` cuando el conteo acumulado de `"` en el buffer es par — evita pasarle un campo entre comillas cortado, que `csv.reader` trunca en silencio sin lanzar excepción (verificado empíricamente) ([chunking.py](backend/properties-service/src/app/workers/helpers/chunking.py)).
- `iter_csv_rows` usa `pending.splitlines(keepends=True)`, no `splitlines()` — sin `keepends`, `csv.reader` reconstruye campos multilínea sin el separador de línea ([chunking.py](backend/properties-service/src/app/workers/helpers/chunking.py)).
- `iter_csv_rows` captura el header una sola vez, del primer lote de rows parseado, y lo reusa para todas las filas subsiguientes vía `dict(zip(header, row))` ([chunking.py](backend/properties-service/src/app/workers/helpers/chunking.py)).
- `BulkPropertyCsvRow` (`admin_schemas.py`) hereda `StrictBase` (`extra="forbid"`, sin `strict=True`) y mantiene los campos con valores no numéricos del CSV real como `str`, para reusar los parsers tolerantes de `seed_mapper.py` en vez de duplicarlos ([admin_schemas.py](backend/properties-service/src/app/services/admin/schemas/admin_schemas.py)).
- `execute()` valida cada fila del generador con `BulkPropertyCsvRow(**row)`; una fila que lanza `ValidationError` se convierte en `BulkRowError` y se saltea sin abortar el batch ([bulk_create_properties.py](backend/properties-service/src/app/workers/bulk_create_properties.py)).
- `BulkRowError(line, ref, issues)` reemplaza el `list[str]` de `BulkCreatePropertiesResult.errors`; `line` es un contador monotónico sobre el generador (no el índice del batch, que es windowed), `ref` sale de `row_ref(row)` e `issues` de `e.errors()` ([admin_schemas.py](backend/properties-service/src/app/services/admin/schemas/admin_schemas.py), [row_ref.py](backend/properties-service/src/app/workers/helpers/row_ref.py)).
- `BulkCreatePropertiesResult.errors` es `list[BulkRowError]`, alineado con `BulkJob.errors` (`ARRAY(JSONB)`); se serializa con `model_dump()` en el borde de persistencia ([admin_schemas.py](backend/properties-service/src/app/services/admin/schemas/admin_schemas.py), [bulk_job.py](backend/properties-service/src/app/models/bulk_job.py)).
- `execute()` acumula por fila un wrapper `{"line", "id": str(uuid.uuid4()), "value": BulkPropertyCsvRow}` y batchea en grupos de 2500 con flush final; el `id` es `str` para casar con `PointToResolve.id` / `result.id` ([bulk_create_properties.py](backend/properties-service/src/app/workers/bulk_create_properties.py)).
- `process_location_batch(batch, *, catalog)` vive en `workers/helpers/location_batch.py`, llama `catalog.get_locations_bulk` una vez por batch, correlaciona por el uuid de la fila, y separa filas con lat/lon inválido o sin ubicación resuelta a `errors` (`list[BulkRowError]`) sin abortar el resto ([location_batch.py](backend/properties-service/src/app/workers/helpers/location_batch.py)).
- La segunda mitad de `execute()` no está conectada a `row_to_item`/`build_models`/`bulk_insert` — código muerto del diseño anterior (`asyncio.gather`/`sem`/`records`/`_enrich_location`) sigue presente, referenciando variables no definidas, y `_process_users_batch` está truncado ([bulk_create_properties.py](backend/properties-service/src/app/workers/bulk_create_properties.py)).
- `execute()` no escribe de vuelta el `BulkJob` (`status`/`errors`/`confirmed_at`); `BulkJobRepository` solo expone `add` y `get_by_id`, sin método de cierre ([bulk_job_repository.py](backend/properties-service/src/app/services/admin/ports/bulk_job_repository.py), [bulk_create_properties.py](backend/properties-service/src/app/workers/bulk_create_properties.py)).
