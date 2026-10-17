---
title: CI reusable de backend, deps de test en dependency-groups y unit tests en verde
captured-from: conversation
captured-on: 2026-10-16
participants: [author, claude]
---

## Context
Se armó el reusable de GitHub Actions para lint + unit tests de los microservicios backend. Al probarlo en limpio, ningún servicio pasaba, así que se corrigieron los tests y se movieron las deps de test.

## Key conclusions
- El reusable vive en `.github/workflows/_backend-lint-unit-tests.yml`. GitHub solo acepta reusables en `.github/workflows/` (sin subcarpetas), por eso el prefijo `_` lo distingue de los callers. Inputs: `path` (string, un servicio por llamada) y `python-version` (por defecto `3.10`, la de los Dockerfiles).
- Job `lint`: `astral-sh/ruff-action` con ruff fijado en `0.17.1` sobre todo el servicio (incluye `tests/`).
- Job `test`: `setup-uv` con caché por `uv.lock`, `uv sync --locked` y `uv run pytest tests/unit` (sin integración). Las actions van fijadas por SHA y el checkout con `persist-credentials: false`.
- Las deps de test de los 4 servicios viven en `[dependency-groups] dev`. Antes estaban en `[project.optional-dependencies] dev` (analytics, catalog, properties) o en las dependencias principales (users; catalog tenía también pytest y ruff ahí).
- `uv sync` a secas ahora instala pytest, y ya no hace falta `--extra dev` ni `--all-extras`. Los Dockerfiles (`uv sync --frozen --no-dev`) siguen excluyendo el grupo.
- **catalog:** los tests de `GetNeighborhoodsByLocalityUseCase` se reescribieron al contrato batch (`execute(locality_ids=[...])` → `NeighborhoodsByLocalityResponse`, caché por localidad y DB solo para los misses). La garantía fail-open de caché se prueba ahora en `CacheClient` (`tests/unit/integrations/cache/`), no en `ResolveNeighborhoodUseCase`, que ya no lleva `try/except`.
- **users:** `api/deps/auth.py`, `api/deps/db.py` y `core/config/settings.py` leen `KC_JWKS_URL`, `KC_ISSUER`, `OIDC_AUDIENCE`, `DATABASE_URL` y `FRONT_BASE_URL` al importarse. `tests/unit/conftest.py` les da valores ficticios con `setdefault` para que los unit tests corran sin entorno.
- Resultado en entorno limpio (`env -i`, como CI): analytics 63, catalog 142, properties 262 y users 119 unit tests en verde.

## Open questions
- El lint sigue en rojo con ruff 0.17.1 (52–418 errores por servicio). Hace falta una limpieza o una config de reglas por servicio.
- El `uvx ruff` local y el de los hooks no fija versión, así que puede divergir del CI.

## Next steps
- Caller con `on: pull_request` que detecte qué servicios cambiaron, y protección de rama sobre `main`.
