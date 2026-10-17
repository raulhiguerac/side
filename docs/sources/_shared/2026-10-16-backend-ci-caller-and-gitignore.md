---
title: Caller backend-ci.yml con detección de servicios cambiados, check ci-ok y .gitignore unificado
captured-from: conversation
captured-on: 2026-10-16
participants: [author, claude]
---

## Context
El reusable `_backend-lint-unit-tests.yml` no tenía caller. Se empezó con uno solo para users (`ms-users-ci.yml`) y se cambió por un único caller para los 4 servicios, que detecta qué cambió en el PR. De paso se revisó qué rastros de ejecución podían colarse en git.

## Key conclusions
- `.github/workflows/backend-ci.yml` corre en `pull_request` (`opened`, `synchronize`, `reopened`) sin filtro `paths`. La decisión de qué correr la toma el job `changes`.
- `concurrency` agrupa por workflow + número de PR con `cancel-in-progress: true`: un push nuevo cancela la ejecución anterior del mismo PR, sin afectar a otros PRs.
- Job `changes`:
  - Usa `dorny/paths-filter` v4.0.3 (fijado por SHA, con permiso `pull-requests: read`) y un filtro por servicio (`backend/<servicio>/**`).
  - Si cambia `backend/ruff.toml` o cualquiera de los dos workflows (filtro `shared`), la salida `services` son los 4 servicios.
- Job `lint_and_test`:
  - Es una matriz sobre `services` (`fail-fast: false`) que llama al reusable con `uses: ./.github/workflows/_backend-lint-unit-tests.yml` y `path: backend/<servicio>`.
  - Con una ruta local (`./`) no lleva `@ref`: usa el reusable del mismo commit.
  - Se salta si la lista está vacía.
- Job `ci-ok`:
  - Corre con `if: always()` y falla si algún job previo terminó en `failure` o `cancelled`. Un `skipped` cuenta como éxito.
  - Es el único check que debe ser obligatorio en la protección de rama: los nombres de la matriz (`lint_and_test (<servicio>) / lint`) varían por PR, y un filtro `paths` en el `on` dejaría los checks obligatorios en "Expected".
- Los reusables deben vivir directamente en `.github/workflows/`. Las subcarpetas no funcionan, y una carpeta tipo `.github/shared/` solo sirve para composite actions.
- `.gitignore`:
  - La raíz pasa a ignorar `.venv/`, `venv/`, `.ruff_cache/`, `.pytest_cache/`, `.mypy_cache/`, `htmlcov/`, `coverage.xml`, `dist/`, `build/`, `.idea/`, `.vscode/`, `*.swp` y `.DS_Store`, en vez de depender del autoignore de cada herramienta.
  - Se borraron los `.gitignore` idénticos de analytics, catalog y properties. users-service no tenía y ahora queda cubierto por la raíz.
  - `frontend/.gitignore` se mantiene.

## Open questions
- `backend-ci.yml` solo está validado con actionlint, todavía no ha corrido en GitHub.

## Next steps
- Abrir el PR de `chore/backend-ruff`. Debería lanzar los 4 servicios porque toca `ruff.toml` y los workflows; validar que los 4 y `ci-ok` salen en verde.
- Configurar la protección de rama de `main` exigiendo `ci-ok`.
