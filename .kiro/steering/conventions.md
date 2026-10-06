---
inclusion: always
---

# Convenciones

Las reglas completas están en `.claude/CLAUDE.md` y `docs/CONVENTIONS.md`; esto es lo que se revisa en código.

- **Antes de escribir código, se discute el enfoque.** En una revisión no se edita nada: se reporta.
- **Comentarios:** como máximo 2 líneas cortas, y solo para explicar un porqué que el código no dice. Nada de comentarios que repiten el código, banners `# ====`, narración por pasos ("Paso 1…") ni docstrings tutoriales.
- **Nombres descriptivos** en APIs y schemas (`total_items`, `current_page`, `search_term`), no abreviaturas.
- **Imports explícitos** del módulo donde vive cada cosa; sin `index.ts` ni `__init__` que reexporten.
- **Organización por entidad** cuando un dominio crece (casos de uso, rutas, deps y tipos en una carpeta por entidad).
- **Validación en el borde:** los requests se validan en el schema Pydantic (rangos con `Field`, reglas entre campos con `model_validator`) para responder 422 antes del caso de uso.
- **Tests junto al código:** cada caso de uso nuevo con su test unitario (UoW falso con `MagicMock`), cubriendo el camino feliz, el borde y el error de DB.
- **Wiki:** todo claim es verificable contra código, un ADR o `docs/sources/`; los ítems de `open-items.md` se cierran con `[x]` y se mueven a "Cerrados", nunca se borran.
