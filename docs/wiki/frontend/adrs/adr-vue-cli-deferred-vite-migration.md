---
title: ADR-0001 — Vue CLI hoy, migración a Vite diferida
status: stable
last-verified: 2026-07-28
owners: [frontend]
related:
  - "[[frontend]]"
  - "[[frontend-architecture]]"
  - "[[adr-no-component-library]]"
sources: [../../../sources/frontend/2026-05-21-foundational-qa.md, ../../../sources/frontend/2026-07-28-admin-panel-groundwork.md]
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

### Update 2026-07-28 — el costo ahora está medido, no estimado

Evaluar Nuxt UI (ver [[adr-no-component-library]]) obligó a mirar de verdad qué tan atado a webpack está el proyecto. El resultado es **menos que lo que asumía este ADR**:

| Superficie | Estimado en 2026-05 | Medido en 2026-07 |
|---|---|---|
| Archivos del `src/` | — | 116 |
| Usos de `process.env` | "cambian de prefijo" | **5**, todos en `config/index.ts` |
| APIs específicas de webpack | "webpack-specific tooling" | **1** (`require("leaflet.markercluster")` en `MapUser.vue`) |
| `require.context` | — | ninguno |
| Proxy de dev | — | 4 entradas, traducen directo a `server.proxy` |

La lista de "plugins a re-validar" también encogió: **Vuelidate ya no existe** (removido 2026-07-28, tenía cero imports) y ningún template usa componentes de Vueform.

Lo que sí apareció es un riesgo que este ADR no contemplaba, y que **no está bajo nuestro control**: subir a **Tailwind v4** depende de Vueform. `tailwind.config.js` carga `@vueform/vueform/tailwind` como plugin y Vueform 1.13 apunta a v3; además dos hojas (`main.css` y `assets/tailwind.css`) llevan directivas `@tailwind`, la segunda con ~40 líneas de `@layer` que tematizan el web component de autocomplete de Google, cuya semántica cambió en v4.

**La decisión no cambia** — sigue diferida — pero cambian dos cosas al ejecutarla: Vite es más barato de lo que decía el ADR y se puede hacer solo; Tailwind v4 es un proyecto aparte, más riesgoso, y conviene no meterlos en la misma rama.

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
5. Reemplazar `vue-cli-plugin-tailwind` por integración directa Tailwind+PostCSS+Vite — **manteniendo Tailwind v3**; subir a v4 es un proyecto aparte (ver update de 2026-07-28).
6. Validar leaflet (`require("leaflet.markercluster")` pasa a `import`), `@vueform/multiselect` y firebase (si todavía no se removió). Vuelidate ya no aplica — removido.
7. Smoke-test todas las views.
8. Borrar `vue-cli-service`, `@vue/cli-*` deps.

**Prerequisito nuevo**: `npm run build` hoy falla por 9 errores de lint pre-existentes (`vue-cli-service build` corre ESLint y aborta). Conviene dejarlo verde **antes** de migrar, para que cualquier build roto durante la migración sea atribuible a la migración. Ver [[open-items]].

## Claims

- `package.json` declara `@vue/cli-service ~5.0.0` y plugins `@vue/cli-plugin-{babel,eslint,router,typescript}` ([package.json:41-45](frontend/package.json#L41-L45)).
- `vue.config.js` carga `@vue/cli-service` y aplica un `DefinePlugin` que el comment reconoce como workaround de un bug no parcheado upstream ([vue.config.js:34-41](frontend/vue.config.js#L34-L41)) — un bloque `devServer.proxy` se agregó antes de este código (2026-06-15), moviendo las líneas.
- Scripts del `package.json`: `serve`, `build`, `lint` — todos `vue-cli-service`, no Vite ([package.json:5-9](frontend/package.json#L5-L9)).
- Env vars actuales con prefijo `VUE_APP_*` ([.env.example](frontend/.env.example)).
- `process.env` aparece 5 veces en `src/`, todas en `config/index.ts` ([config/index.ts](frontend/src/config/index.ts)).
- El único uso de una API de módulos de webpack en `src/` es `require("leaflet.markercluster")`; no hay `require.context` ([components/map/MapUser.vue](frontend/src/components/map/MapUser.vue)).
- `tailwind.config.js` declara `plugins: [require("@vueform/vueform/tailwind")]`, atando la major de Tailwind a la que soporte Vueform ([tailwind.config.js:30](frontend/tailwind.config.js#L30)).
- Las directivas `@tailwind` viven en dos hojas, `src/main.css` y `src/assets/tailwind.css`; la segunda tiene bloques `@layer` que estilan el web component de autocomplete de Google ([assets/tailwind.css](frontend/src/assets/tailwind.css)).
- Ya no hay dependencias de `vuelidate` en `package.json` ni imports en `src/` ([package.json](frontend/package.json)).
