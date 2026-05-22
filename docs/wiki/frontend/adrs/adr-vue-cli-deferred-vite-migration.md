---
title: ADR-0001 — Vue CLI hoy, migración a Vite diferida
status: stable
last-verified: 2026-05-21
owners: [frontend]
related: [[frontend]], [[frontend-architecture]]
sources: [../../../sources/frontend/2026-05-21-foundational-qa.md]
decision-date: 2026-05-21
decision-status: accepted
---

# ADR-0001 — Vue CLI hoy, migración a Vite diferida

## Contexto

El frontend se inicializó con **Vue CLI 5** (webpack-based). Desde entonces:
- Vue CLI entró en **maintenance mode** — el equipo oficial Vue recomienda Vite para proyectos nuevos.
- El propio `vue.config.js` del repo reconoce el estado (comment: "Vue CLI is in maintenance mode, and probably won't merge my PR to fix this in their tooling").
- Vite es ~10-50× más rápido en dev (HMR), bundle más eficiente, configuración más simple.

Pero migrar de Vue CLI a Vite **no es trivial**:
- Cambia `index.html` (Vite necesita el script `<script type="module" src="/src/main.ts">` en HTML).
- Path aliases (`@/` resolution) en `vite.config.ts` en lugar de `vue.config.js`.
- ENV vars cambian de prefijo (`VUE_APP_*` → `VITE_*`).
- Plugins de Vueform/Tailwind/Vuelidate hay que re-validar.
- Webpack-specific tooling (`vue-cli-plugin-tailwind`, `vue-cli-plugin-typescript`) se elimina.

Costo estimado: 1-2 días de trabajo + testing manual de cada view.

## Decisión

**Mantener Vue CLI hasta que todos los microservicios backend estén cerrados.** Migrar a Vite como un sprint dedicado post-backend-completion.

Aceptamos la deuda técnica explícitamente — no es "olvidado", es "diferido".

## Alternativas consideradas

- **Migrar ahora**: bloquea otro trabajo de feature por 1-2 días en una etapa donde producto > infra.
- **Doble build** (Vite para dev, Vue CLI para prod): complejidad para un solo dev, riesgo de drift.
- **Nunca migrar**: Vue CLI eventualmente dejará de recibir security patches; deuda crece.

## Consecuencias

- ✅ Foco mantenido en cerrar backend antes de tocar build pipeline.
- ✅ Vite migration será un sprint claro, no un drip-by-drip.
- ✅ Cuando se migre, todo el frontend ya estará estable — menos sorpresas.
- ❌ Dev experience degradado vs Vite — HMR más lento, builds más largos.
- ❌ Algunas libs nuevas asumen Vite (ej. ciertos Vue plugins recientes); puede haber roces al instalar.
- ❌ El comment en `vue.config.js` ya menciona un PR sin merge — riesgo de quedar sin maintenance upstream antes de migrar.

## Migration outline (futuro)

Cuando se ejecute (post-backend):
1. Crear branch `feat/migrate-to-vite`.
2. Reemplazar `vue.config.js` por `vite.config.ts` con plugin Vue + path alias `@/`.
3. Renombrar env vars `VUE_APP_*` → `VITE_*` en `.env`, `.env.example`, `config/index.ts`.
4. Mover `<script>` del entry a `index.html`.
5. Reemplazar `vue-cli-plugin-tailwind` por integración directa Tailwind+PostCSS+Vite.
6. Validar Vueform, Vuelidate, leaflet, firebase (si todavía no se removió).
7. Smoke-test todas las views.
8. Borrar `vue-cli-service`, `@vue/cli-*` deps.

## Claims

- `package.json` declara `@vue/cli-service ~5.0.0` y plugins `@vue/cli-plugin-{babel,eslint,router,typescript}` ([package.json:33-37](frontend/package.json#L33-L37)).
- `vue.config.js` carga `@vue/cli-service` y aplica un `DefinePlugin` que el comment reconoce como workaround de un bug no parcheado upstream ([vue.config.js:1-22](frontend/vue.config.js#L1-L22)).
- Scripts del `package.json`: `serve`, `build`, `lint` — todos `vue-cli-service`, no Vite ([package.json:5-9](frontend/package.json#L5-L9)).
- Env vars actuales con prefijo `VUE_APP_*` ([.env.example](frontend/.env.example)).
