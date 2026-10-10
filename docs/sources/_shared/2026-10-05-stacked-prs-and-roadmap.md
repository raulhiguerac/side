---
title: Rama de 50 commits partida en PRs apilados, evaluación del monorepo y hoja de ruta
captured-from: conversation
captured-on: 2026-10-05
participants: [author, claude]
---

## Context
`feat/front-admin-panel` llegó a 50 commits por delante de `main`, entre backend de properties, panel admin, catálogo y refactors. Se partió en PRs revisables. Al cerrar, se evaluó cuánto falta para producción y en qué orden avanzar.

## Key conclusions
- **Una rama no debe acumular 50 commits de temas distintos.** Cada tema va en su propia rama; los refactors, aparte de las features.
- **Para separar trabajo ya hecho:** cherry-pick desde la rama vieja a ramas apiladas, de modo que cada PR apunta a la rama anterior.
  - El orden lo fijan las dependencias: build verde del front → backend de moderación → panel de properties → catálogo → refactors. Kiro va independiente.
  - Los ingest de docs viajan con la rama donde ya existe el código que describen.
  - Un commit que mezcla backend y front se parte en dos:
    - en la rama de backend: `cherry-pick -n`, `git rm` de lo del front y `commit -C <sha>`;
    - en la rama del front: cherry-pick con `--ours` en los archivos de backend, que ya están.
  - La prueba de que no se perdió nada: el `git diff` entre la última rama (más la independiente) y la rama original da vacío.
- **En GitHub, estrategia *merge commit*, para conservar los commits atómicos.**
  - Al mergear un PR de la pila, GitHub reapuntó solo el siguiente a `main`, aunque el repo tiene `deleteBranchOnMerge: false`.
  - Riesgo visto: mergear un PR contra una base que ya entró a `main` lo deja fuera (pasó con #20). Se resuelve con un PR nuevo de la misma rama contra `main` (#21), sin revertir nada.
  - Resultado: PRs #15–#19 y #21 mergeados; `feat/front-admin-panel` quedó idéntica a `main`.
- **Tests de properties sin tocar el venv compartido.** En el devcontainer, `UV_PROJECT_ENVIRONMENT=/home/vscode/.venv` es de root, y `uv run` intenta sincronizarlo. Para correrlos en otro checkout, usar un venv aislado: `UV_PROJECT_ENVIRONMENT=/tmp/<x> uv sync --frozen --all-extras` y después `uv run --no-sync pytest`.
- **En `main` fallan 2 tests de properties** (`test_*_storage_misconfigured_when_bucket_missing`), y fallaban también antes del split.
- **Evaluación del monorepo:** el diseño ya está a nivel producción, la operación no. Lo que separa, en orden:
  1. La red de seguridad del front: cero tests, sin typecheck en scripts y sin CI.
  2. El loop del AVM sin cerrar: sin consumer de `price-predicted`, el worker Kafka de analytics no arranca y el precio no se expone.
  3. El bug del reimport, que pisa la moderación.
  4. Fallos invisibles: errores tragados, `alert()` y ningún reporte remoto de errores.
  5. La entrega.
- **Vitest sin migrar a Vite:** corre con su propio `vitest.config.ts` (plugin de Vue y alias `@`), aparte del build de Vue CLI. Así se testea ya sin abrir la migración que el ADR-0001 tiene diferida.
- **Hoja de ruta: unas 6,5 semanas a 2–3 h/día, 5 días por semana (~65–95 h).**
  - Estimación sin infra: 50–78 h, repartidas así:
    - Vitest + CI: 8–12 h
    - modales de barrios: 8–12 h
    - `GET` admin de catálogo: 8–12 h
    - tabs de catálogo: 12–18 h
    - loop del AVM: 12–20 h
    - bug del reimport: 2–4 h
  - Es viable si la infra son 3–5 sesiones. Si son 3–5 días completos, el catálogo de localidades, divisiones y países queda como stretch, en una versión mínima de listar y activar/desactivar.

## Open questions
- ¿Activar "Automatically delete head branches" en el repo, o seguir reapuntando y borrando a mano?
- ¿Los "3–5 días" de infra son días completos o sesiones? Define si el catálogo mínimo entra.

## Next steps
- Borrar del remoto y en local las ramas ya mergeadas: `chore/kiro-review-specs`, `chore/front-build-green`, `feat/properties-moderation`, `feat/front-admin-properties`, `feat/front-catalog-neighborhoods`, `refactor/front-abstractions` y `feat/front-admin-panel`.
- Siguiente sesión: setup de Vitest y CI, discutiendo antes la config, el orden de los tests (`useRowSelection`, `useUrlFilters`, `pageRange`, `sanitizeFilterQuery`, `useModerateProperty`, el contador de requests de `useNeighborhoodDetail`) y cómo mockear axios.
