---
title: Lint de backend en verde con ruff 0.17.1 — config compartida y decisiones por regla
captured-from: conversation
captured-on: 2026-10-16
participants: [author, claude]
---

## Context
El job `lint` del CI de backend (ruff 0.17.1, que activa por defecto muchas más reglas que 0.15) daba unos 1.100 errores entre los 4 servicios. Se dejó en verde en la rama `chore/backend-ruff`.

## Key conclusions
- `ruff==0.17.1` está fijado en el grupo `dev` de los 4 servicios, así que `uv run ruff check .` coincide con la versión del CI. analytics y properties no tenían ruff.
- Config compartida en `backend/ruff.toml`. analytics, properties y users la toman por descubrimiento jerárquico; catalog la extiende (`extend = "../ruff.toml"`) y conserva su `ignore = ["E712"]`.
- `ruff.toml` necesita `target-version = "py310"` y `[lint.isort] known-first-party = ["app"]`. Sin ellos, ruff deja de leer el `requires-python` de cada `pyproject.toml`, sugiere `datetime.UTC` (solo existe desde 3.11) y ordena `app` como si fuera una librería externa.
- `B008`: `extend-immutable-calls = ["fastapi.Depends", "fastapi.Query"]` elimina ~400 falsos positivos del patrón FastAPI.
- `BLE001` y `S110` (~140, casi todos del cache-aside fail-open de `adr-cache-optional-layer`) se ignoran en la config hasta resolver el open-item sobre la redundancia de esos wrappers.
- `SIM118` en `inspect(Model).columns.keys()` es un falso positivo: iterar `.columns` devuelve objetos `Column`, no nombres, y el arreglo de ruff rompería los upserts. Lleva `# noqa: SIM118` en los 3 repositorios.
- `RUF012` en modelos pydantic: `= []` pasa a `Field(default_factory=list)`, porque ruff no puede inferir que `StrictBase` es un `BaseModel`.
- `DTZ003`: users pasa de `datetime.utcnow()` a `datetime.now(timezone.utc)`. Las columnas son `timestamp` sin zona y el engine fija `-c timezone=utc`, así que el valor guardado no cambia. Los logs JSON ahora llevan `+00:00`.
- Bugs reales que destapó el lint:
  - **users:** `sql_onborading_completion_repository.py` usaba `func.now()` sin importar `func`, lo que daba `NameError` en ese upsert.
  - **properties:** 4 forward refs de SQLModel sin import, que ahora van bajo `TYPE_CHECKING`.
- Los arreglos "unsafe" se revisaron uno a uno antes de aplicarlos: `C408`, `RUF059`, `TRY201`, `SIM103` y `PIE794`. Este último eliminó un campo `currency` duplicado e idéntico en `listing_schemas.py`.
- Verificado en los 4 servicios con `uv run ruff check .` (verde), `pytest tests/unit` en entorno limpio (63 / 142 / 262 / 119) y `import app.main` + `configure_mappers()`.

## Open questions
- El hook `post-edit-lint.sh` y `scripts/audit.sh` siguen con `uvx ruff` sin versión.

## Next steps
- Fijar la versión de ruff en el hook y en `audit.sh`.
- Reactivar `BLE001` y `S110` cuando se resuelva la redundancia del cache-aside.
