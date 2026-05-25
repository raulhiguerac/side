# Convenciones del Wiki

Este documento es el **schema** del wiki: define cómo está estructurado, qué metadata lleva cada página y qué reglas siguen los comandos `/wiki-*`. Tanto humanos como el LLM deben respetar lo que está aquí.

Inspirado en el patrón "LLM Wiki" de Karpathy ([gist](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)) — tres capas: fuentes inmutables, wiki curado, schema.

---

## 1. Layout

```
docs/
├── CLAUDE.md           # entry point para el LLM
├── CONVENTIONS.md      # este archivo
├── INDEX.md            # índice navegable para humanos
├── sources/            # capa 1 — material crudo, inmutable
│   └── <service>/      # PRDs, transcripts, notas de reunión, decisiones originales
└── wiki/               # capa 2 — síntesis curada
    ├── _templates/     # plantillas para nuevas páginas
    ├── _shared/        # contenido transversal a todo el monorepo
    │   ├── glossary.md
    │   ├── architecture.md
    │   └── adrs/       # ADRs cross-service
    └── <service>/      # un subdirectorio por microservicio
        ├── 00-overview.md
        ├── architecture.md
        ├── domain/
        ├── flows/
        ├── integrations/
        ├── runbook/
        └── adrs/       # ADRs específicos del servicio
```

**Reglas del layout:**
- Archivos en `kebab-case.md`. El slug del archivo es el identificador estable.
- `00-` como prefijo solo para el overview de cada servicio (sale primero al listar).
- Los subdirectorios bajo un servicio son una taxonomía sugerida, no obligatoria. Si una página no encaja, crearla en la raíz del servicio.
- `_` (underscore) como prefijo indica meta-directorios (`_templates`, `_shared`) — no son contenido propio.

---

## 2. Anatomía de una página

Todo archivo bajo `wiki/` (excluyendo `_templates/` y `_shared/glossary.md`) tiene **tres secciones obligatorias** y en este orden:

### 2.1 Front-matter

```yaml
---
title: Online prediction use case
status: stable
last-verified: 2026-05-19
owners: [analytics-service]
related: [[mlflow]], [[prediction-domain]], [[training-pipeline]]
sources: [sources/analytics-service/2026-05-prediction-rfc.md]
---
```

Campos:

| Campo           | Obligatorio | Valores                                              |
|-----------------|-------------|------------------------------------------------------|
| `title`         | sí          | Título legible (no kebab-case)                       |
| `status`        | sí          | `draft` \| `stable` \| `stale`                       |
| `last-verified` | sí          | `YYYY-MM-DD` — última vez que se cotejó con el código |
| `owners`        | sí          | Lista de servicios o equipos responsables             |
| `related`       | recomendado | Lista de slugs `[[name]]` de páginas relacionadas    |
| `sources`       | recomendado | Lista de rutas relativas a `sources/`                 |

### 2.2 Cuerpo

1. **TL;DR (3 líneas).** Para que un dev sepa en 10 segundos si esta página le sirve.
2. **Contenido explicativo.** Prosa para humanos. Referencias a código con links estilo `[archivo.py:42](ruta/relativa/archivo.py#L42)`.
3. **Diagramas, tablas, snippets** según hagan falta. Mermaid preferido si se necesita diagrama.

### 2.3 Claims atómicos

Sección final, exactamente con este formato:

```markdown
## Claims

- El UC online carga el modelo desde el MLflow registry, no desde MinIO directo.
- El endpoint `/predict` rechaza requests sin `property_id` con HTTP 422.
- Las features se validan contra el schema en `schemas/prediction_input.py` antes de la inferencia.
```

**Reglas para claims:**
- Una frase verificable por línea, en presente indicativo.
- Cada claim debe poder validarse leyendo código (o tests), no otras páginas del wiki.
- Si un claim deja de ser cierto, se borra o se actualiza junto al `last-verified`. Nunca se deja "histórico" en esta sección — para eso existen los ADRs.

---

## 3. Ciclo de vida de una página

```
status: draft   → recién creada, contenido en construcción, no usar como referencia
status: stable  → verificada contra código, segura para citar
status: stale   → marcada por /wiki-lint, requiere revisión
```

**Transiciones:**
- `draft → stable` cuando el autor confirma que los claims pasan contra el código actual y setea `last-verified` a hoy.
- `stable → stale` automáticamente vía `/wiki-lint` si: `last-verified` > 30 días **y** ha habido commits que tocaron archivos referenciados.
- `stale → stable` requiere refrescar el contenido y actualizar `last-verified`.

---

## 4. Linking

- **Dentro del wiki:** siempre `[[slug]]` (el nombre de archivo sin `.md`). Ejemplos válidos: `[[mlflow]]`, `[[online-prediction]]`, `[[glossary]]`.
- **Al código del proyecto:** ruta relativa estilo IDE — `[online.py:42](backend/analytics-service/src/app/services/prediction/use_cases/online.py#L42)`.
- **A fuentes externas:** URL normal con texto descriptivo.
- **A `sources/`:** ruta relativa estándar — `[RFC original](../../sources/analytics-service/2026-05-prediction-rfc.md)`.

---

## 5. Fuentes de verdad

Todo claim del wiki debe poder rastrearse a **una** de estas tres fuentes:

- **(a) Código del repo** — el claim se verifica leyendo `backend/` o `frontend/`. Citar con `[archivo.py:42](ruta#L42)`.
- **(b) Un ADR** — la decisión vive en `wiki/<service>/adrs/` o `_shared/adrs/`. El ADR es autosuficiente, no requiere registro separado en `sources/`.
- **(c) Un archivo en `sources/`** — material externo o destilado del autor que no se ve en código.

### Reglas de `sources/`
- **Inmutable.** Nunca editar un archivo dentro; solo agregar nuevos.
- Convención de nombres: `YYYY-MM-DD-<descriptor>.md` (ej: `2026-05-19-mlflow-decision.md`).
- No es un registro de todo lo que pasó — solo de material que respalda claims del wiki.

### Cuándo NO hace falta un archivo en `sources/`
- El claim deriva de código → basta la referencia al archivo.
- El claim deriva de una decisión del autor → registrarla como ADR es suficiente.
- La directriz es trivial (preferencia de naming, elección obvia) → no requiere ni source ni ADR.

### Cuándo SÍ archivar en `sources/`
- Material externo (RFCs, PRDs, papers, docs largos de proveedor).
- Conversaciones con LLM que llegaron a una conclusión no trivial — usar `/wiki-capture` para destilarlas a un resumen accionable, **nunca guardar transcripts crudos**.
- Brain-dumps extensos del autor que no encajan como ADR (ej. estrategia de pricing, exploración de alternativas).

### Vínculo con front-matter
En `sources:` de cada página podés listar:
- Rutas relativas a `sources/` (ej: `[../../sources/analytics-service/2026-05-19-mlflow.md]`)
- Slugs de ADRs como `[[adr-0001-mlflow-tracking]]`
- Ambos si aplica. Vacío si la página se sostiene solo contra código.

---

## 6. Reglas de `/wiki-lint`

El comando reporta (no edita automáticamente) cuatro tipos de hallazgos:

1. **Stale:** `last-verified` > 30 días con commits recientes en archivos referenciados.
2. **Huérfanas:** páginas sin ningún inbound `[[link]]` desde otra página del wiki.
3. **Links rotos:** `[[slugs]]` que no existen como archivo.
4. **Contradicciones:** claims que se contradicen entre páginas (heurística textual, requiere revisión humana).

---

## 7. Convenciones de naming

- Archivos: `kebab-case.md`
- Slugs en `[[links]]`: deben coincidir exactamente con el nombre de archivo sin extensión
- Títulos en front-matter (`title:`): legibles, en mayúscula inicial, sin guiones
- Servicios: el nombre tal cual aparece en el directorio del repo (`analytics-service`, no `analytics`)

---

## 8. Qué NO va en el wiki

- Documentación de API auto-generable (OpenAPI/Swagger lo hace mejor desde el código).
- Comentarios sobre código específico que ya vive bien en el código fuente (docstrings).
- Logs, métricas, dashboards — apuntar a la herramienta, no replicar.
- Información sensible (credenciales, datos personales). Si una fuente la tiene, sanitizar antes de meterla a `sources/`.
