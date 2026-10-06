---
inclusion: manual
---

# Cómo revisar

Revisión de **solo lectura**: no edites archivos, no corras migraciones ni nada que escriba.

## Procedimiento

1. Lee `audit-report.txt` (lo genera `make audit`). Un test rojo o un error de tipos es una pista confirmada; empieza por ahí.
2. Lee los pendientes conocidos para no reportarlos de nuevo: #[[file:docs/wiki/_shared/open-items.md]]
3. Revisa por **rebanadas verticales**: ruta → caso de uso → repositorio/SQL → schema, y el consumidor del front si existe. Compara cada rebanada contra `domain-invariants.md` y los riesgos de `backend.md` / `frontend.md`.
4. Antes de reportar un bug, describe el escenario concreto de falla. Si no puedes describirlo, no lo reportes como bug.

## Tipos de hallazgo

| Tipo | Exige |
|---|---|
| **Bug** | escenario de falla (entrada → resultado incorrecto → resultado esperado) y, si se puede, el test que lo demostraría |
| **Mejora** | beneficio concreto o riesgo que elimina |
| **Convención** | la regla de `conventions.md` que rompe |

## Formato del reporte

Es una **fuente** (`docs/sources/`), no una página de la wiki: lleva este front-matter y ningún otro campo (nada de `status`, `last-verified` ni `owners`):

```yaml
---
title: Revisión de <spec> (Kiro)
captured-from: external
captured-on: YYYY-MM-DD
participants: [kiro]
---
```

Después, markdown ordenado por tipo (bugs primero) y por severidad (alta, media, baja). Un hallazgo por bloque:

```markdown
### [Bug · alta] Título corto
- **Dónde:** `ruta/archivo.py:42`
- **Escenario:** …
- **Por qué pasa:** …
- **Propuesta:** …
- **Test sugerido:** …
- **Confianza:** alta | media | baja
```

Al final, una sección "Revisado sin hallazgos" con las rebanadas que miraste y estaban bien. Así se sabe qué cubrió la revisión.
