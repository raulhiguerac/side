---
inclusion: fileMatch
fileMatchPattern: "frontend/**"
---

# Frontend: patrones esperados y riesgos

## Patrones

- Vistas admin: `AdminFilterBar` emite `apply` → `router.push({ query })` → `computed` sobre `route.query` → `watch(..., load, { immediate: true })`.
- Lógica con estado en composables (`composables/<área>/useX.ts`); los componentes reciben props y emiten eventos.
- Una instancia de axios por servicio en `src/api/`; los endpoints en `constants/<servicio>Endpoints.ts`.
- Tipos de respuesta espejo de los schemas del backend, en `types/`.

## Dónde buscar bugs

- **Reactividad:** `watch` sobre un getter que devuelve un array u objeto nuevo en cada render (se dispara siempre); props pasadas como literal (`:center="[a, b]"`) que provocan ciclos; leer props en la raíz de `<script setup>` cuando sí debían ser reactivas.
- **Respuestas fuera de orden:** cargas disparadas por selección o filtros sin descartar la respuesta vieja.
- **Contratos con el backend:** tipos que no coinciden con el schema (nombres, opcionales, `null`); query params mal serializados (arrays: `paramsSerializer: { indexes: null }`).
- **Auth y CORS:** instancias que necesitan la cookie sin `withCredentials`; llamadas directas a un backend en vez del proxy de dev.
- **Estados:** loading que no se apaga en el error, errores tragados sin feedback, listas vacías sin estado vacío.
- **Tailwind:** clases armadas con template strings (se purgan en el build).
