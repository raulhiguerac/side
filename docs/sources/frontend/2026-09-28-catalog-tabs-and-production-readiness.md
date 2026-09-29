---
title: Tabs de catálogo montadas y camino del frontend a production grade
captured-from: conversation
captured-on: 2026-09-28
participants: [author, claude]
---

## Context
Se montó el esqueleto de la sección de catálogo del panel admin y, a partir de ahí, se evaluó qué le falta al frontend para ser production grade, dado que no tiene tests.

## Key conclusions
- La sección de catálogo sigue el patrón de propiedades: tabs como rutas hijas.
  - `/admin/catalog` es padre sin `name` y lleva el `meta` de admin; `admin-catalog` pasa al hijo por defecto (Barrios), así que los links existentes siguen funcionando.
  - Hijos: `""` (Barrios), `localities`, `admin-divisions` y `countries`, con los mismos nombres de recurso que el backend.
  - Cada tab es un placeholder con `EmptyState` hasta que exista el read path admin de catalog-service.
- `AdminCatalogView.vue` quedó como layout (título, `AdminTabsNav`, `RouterView`) sin renombrarse. Alinearlo a `AdminCatalogLayout.vue` es opcional.
- Importar el ícono `Map` de lucide tapa el `Map` nativo de JS en el módulo: se usa el alias `MapIcon`.
- Lo que ya es de nivel producción en el frontend es el diseño:
  - la lógica en composables y los componentes tontos;
  - las transiciones decididas por el servidor;
  - el estado en la URL;
  - las races resueltas (`requestToken`, guard admin);
  - los ADRs y el wiki verificados contra el código.
- Lo que falta es la red de seguridad y la entrega:
  - no hay tooling de tests ni `vue-tsc`, ni CI;
  - el build está roto por lint;
  - `.gitignore` no cubre `.env.local`;
  - el único Dockerfile (en la rama chore) corre el dev server en vez de servir `dist/`;
  - el contrato con el backend se tipa a mano.
- La migración a Vite va antes que los tests: con Vue CLI el camino sería Jest, que habría que tirar; con Vite, Vitest reusa la config.
- Los tests unitarios van donde vive la lógica (composables como `usePagination`, `useModerateProperty`, `useRowSelection`, y utils como `sanitizeFilterQuery`), no en las vistas, que todavía cambian mucho.

## Next steps
Orden propuesto para llevar el frontend a production grade:
1. Build verde: los 2 errores de lint manuales (`StepImagenes.vue`, bloque vacío) y `.env.local` en `.gitignore`.
2. Migrar a Vite, con `vue-tsc` dentro del script de build.
3. Vitest sobre composables y utils.
4. CI mínimo por PR: lint + `vue-tsc` + Vitest + build.
5. Tipos generados desde el OpenAPI del backend (`openapi-typescript`).
6. Dockerfile de producción multi-stage que sirva `dist/` estático, con `/api/*` ruteado en el Gateway del clúster en lugar del proxy de dev.
7. Smoke tests con Playwright (login, feed, moderar) cuando el panel admin se estabilice.
