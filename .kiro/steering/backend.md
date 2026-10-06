---
inclusion: fileMatch
fileMatchPattern: "backend/**"
---

# Backend: patrones esperados y riesgos

## Patrón de caso de uso

```python
async def execute(self, *, req: Request) -> Response:
    try:
        rows = await run_in_threadpool(partial(self.uow.repo.get_all, req=req))
    except Exception as exc:
        raise translate_db_error(exc) from exc
```

- Escritura: `commit()` + `refresh()`; si falla, `rollback()` y `translate_db_error`. Después, cache best-effort en `try/except`.
- "No encontrado" se lanza como excepción de dominio (`...NotFoundError`), que el handler convierte en 404; el caso de uso no devuelve `None` a la ruta.
- Los adapters seleccionan columnas, no el modelo entero, cuando hay columnas calculadas o pesadas (`geom`, `h3_cells`).

## Dónde buscar bugs

- **Sync/async:** `await` sobre un repo síncrono; `run_in_threadpool(repo.metodo(...))` sin `partial` (ejecuta en el hilo del event loop).
- **Transacciones:** caminos de error sin `rollback()`; varios `commit()` donde un fallo deja datos a medias; compensaciones que faltan (DB + Keycloak, DB + storage).
- **Cache:** escrituras que no invalidan la lista además de la entidad; claves sin el parámetro que las distingue (página, filtro); caídas de Redis que no degradan.
- **Consultas:** listado y conteo con filtros distintos; N+1 o N llamadas HTTP donde cabe un batch; `ST_Contains` donde corresponde `ST_Intersects`; áreas o distancias en grados; falta de `ORDER BY` estable al paginar.
- **Auth:** rutas `/admin` sin `require_admin`; un usuario que puede tocar recursos de otro (dueño no verificado).
- **Validación:** reglas que solo valida el front; `Depends()` con campos `tuple`/`list` (FastAPI los trata como body: usar `Annotated[Model, Query()]`).
- **Configuración:** valores de entorno fijos en código (orígenes CORS, URLs, límites).

## Ruido conocido (no reportar)

- Ruff `B008` en `Depends(...)` como valor por defecto: es el patrón de FastAPI.
- Ruff `S110`/`BLE001` (`except Exception: pass`) alrededor de operaciones de cache: es la degradación que decide `adr-cache-optional-layer`. Sí es hallazgo si el `except` amplio envuelve algo que no es cache.
