---
title: Endpoint de listado de bulk jobs y por qué el orden de la ruta importa
captured-from: conversation
captured-on: 2026-08-24
participants: [author, claude]
---

## Context

Un import era irrevisable: solo existía `GET /admin/properties/bulk/{job_id}/status`, que exige un id que el front descartaba al cerrar el modal. Se construyó el listado que faltaba, con su puerto, adapter, use case y wiring.

## Key conclusions

- **`GET /admin/properties/bulk` pagina por offset con `total`**, igual que el resto del panel (ADR-0009), y filtra por `status`, `has_errors`, `created_from` y `created_to`.
- **Guardar el `batch_id` en el front no bastaba.** El id vive en un navegador: se pierde al cambiar de máquina, no lo ve otro admin y no responde "qué importé la semana pasada". Son dos huecos distintos — el toast de confirmación y el historial.
- **Sin campo de orden.** Un historial se lee siempre del más reciente; un `sort` configurable sería una opción que nadie usa en el otro sentido. Va fijo en `ORDER BY created_at DESC`.
- **`job_id` descartado como filtro:** filtrar un listado por id es pedir un elemento, y para eso está el endpoint de status. Si hace falta seguir reintentos, el filtro útil sería `retry_of_job_id`.
- **El cliente manda `page`, no `offset`.** La respuesta ya habla de `page`, `page: int = Field(ge=1)` es validable de verdad y un offset libre acepta páginas que no existen (`offset=7` con `page_size=20`).
- **La fila lleva `error_count`, no el array de errores.** Una corrida puede tirar miles y veinte de esas en una página es un payload que nadie lee; el detalle lo sirve el endpoint de status, que así deja de ser huérfano y calza con el patrón tabla-liviana + panel-por-id del resto del panel.
- **La ruta debe declararse antes de `/properties/{property_id}`.** Registrada después, FastAPI matchea la de path param con `property_id="bulk"`, intenta parsearlo como UUID y devuelve 422 sin llegar al handler. Verificado contra el router de la app: fue exactamente el 422 que apareció al cablear el front.
- **`count_all` usa `cardinality` y no `array_length`.** Sobre un array vacío `array_length(arr, 1)` da `NULL` y no `0`, así que `has_errors=false` perdería todas las corridas limpias, que son justo las que pide.
- **`deleted_at IS NULL` en ambas queries y `order_by` explícito antes del offset**: sin orden garantizado, paginar repite o saltea filas.
- **No se cachea.** Precedente escrito en `promotions/list_all`: vista interna, pocas filas, poco frecuente. En este servicio la cache aparece en admin solo cuando el dato es compartido con el feed público — leer la misma entrada (`get_property_detail`) o invalidarla (`promotions/delete`).
- **Las dos queries van secuenciales, no con `gather`.** No es cuestión de carga: ambas comparten la `Session` del UoW y una `Session` de SQLAlchemy no es segura desde dos hilos. Si el doble round-trip molestara, la salida sería `count(*) OVER ()` en la misma query, no paralelizar.
- **El default de `limit` se alineó en 20** entre puerto y adapter: el `21` del truco "pedir uno de más" contradice un diseño que ya tiene `total` por `COUNT`.

## Open questions

- Falta `POST /admin/properties/bulk/{job_id}/retry`: `retry_of_job_id` existe en la tabla pero nada lo escribe. Ojo con `expires_at` — si el CSV venció en storage, relanzar no tiene archivo que leer.
- La tabla no guarda el nombre original del archivo (solo `storage_key`) ni un mensaje de error a nivel job.
- `bulk_jobs` no tiene `total_rows`: el total leído se deriva de `inserted + len(errors)`.

## Next steps

- Anotado en open items: el worker de import no invalida ninguna cache, y el reimport idempotente hace UPDATE sobre filas cuyo `properties:detail:{id}` vive 6 horas.
