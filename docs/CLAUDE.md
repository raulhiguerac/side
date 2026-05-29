# Trabajando en /docs

Esta carpeta es un wiki versionado del proyecto. Está pensado para que un dev nuevo se ponga al día rápido **y** para que el LLM tenga contexto sin re-derivarlo cada vez.

## Por dónde empezar
- Índice navegable: [INDEX.md](INDEX.md)
- Convenciones completas (cómo se estructura una página, qué front-matter es obligatorio, reglas de lint): [CONVENTIONS.md](CONVENTIONS.md)

## Reglas críticas (no negociables)

1. **Todo claim debe ser rastreable** a una de tres fuentes: (a) código del repo, (b) un ADR, o (c) un archivo en `sources/`. No es obligatorio llenar `sources/` para cada página — un ADR alcanza si la decisión vive ahí. Detalle en [CONVENTIONS.md §5](CONVENTIONS.md).
2. **Front-matter siempre.** Cada página en `wiki/` lleva `title`, `status`, `last-verified`, `related`. Si actualizas el contenido, actualiza `last-verified`.
3. **Links con `[[slug]]`.** Usa el nombre del archivo sin extensión (`[[mlflow]]`, no `[mlflow](../integrations/mlflow.md)`). Permite renombrar/mover sin romper enlaces y le da al lint algo que indexar.
4. **Claims atómicos al final.** Cada página termina con una sección `## Claims` — una frase verificable por línea. Es lo que `/wiki-lint` chequea contra el código.
5. **No dupliques.** Antes de crear una página nueva, busca con grep si el concepto ya vive en `_shared/` o en otro servicio.

## Skills del wiki

Viven en `.claude/skills/`. Se invocan con `/<nombre>`.

- `/wiki-capture <tema>` — destila la conversación reciente (o texto pegado) a un archivo de `sources/`. Útil cuando una charla con el LLM llegó a una decisión y querés preservarla sin transcript literal. _User-only._
- `/wiki-ingest <ruta>` — procesa una fuente en `sources/`, propone updates a 1-5 páginas. _User-only._
- `/wiki-query <pregunta>` — responde usando el wiki, ofrece archivar Q&A valioso. _Auto-trigger habilitado_: el modelo la invoca al detectar preguntas sobre arquitectura/dominio/servicios del proyecto.
- `/wiki-lint` — chequea contradicciones, páginas stale, huérfanas. _User-only._

## Estado del piloto

El piloto arrancó sobre `wiki/analytics-service/` (2026-05-19). Tras validar el patrón, se extendió a `catalog-service`, `frontend`, `properties-service` y `users-service` (este último par el 2026-05-28). Todos los microservicios del backend + el frontend + el workload `avm` están documentados. La estructura (overview, architecture, domain/, integrations/, runbook/, adrs/) se considera estable; mantenerla para nuevas páginas.
