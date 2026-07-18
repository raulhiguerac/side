---
title: Componentización del form AVM + diseño del componente de mapa dumb
captured-from: conversation
captured-on: 2026-05-28
participants: [raul, claude]
---

## Context

Se refactorizó el form del AVM del dev playground en componentes reusables y se diseñó el componente de mapa (Leaflet) como pieza dumb/reusable. Sesión en "modo aprendizaje": el user escribió la lógica/composables; Claude guió, hizo Tailwind/scaffolding de tipos y señaló errores.

## Key conclusions

- **Form AVM partido en `components/avm/`**: `AvmForm` (stepper de 3 pasos, consume `composables/useAvmForm.ts`), `AvmResult` (recibe `price`/`barrio`/`estrato` por props, dueño del tween GSAP, emite `reset`), `AvmMap` (pendiente). `DevPlaygroundView` orquesta vía `<Transition name="panel">`.
- **`AvmForm` emite `{ payload: AvmFormPayload, place: SelectedPlace }`** — `payload` son los atributos del inmueble (sin lat/lon/barrio); `place` (lat/lon/address) viene del autocomplete de Google Maps. El barrio lo agrega el orquestador con el chain catalog by-coords (pendiente). En el playground hoy: `estrato` real desde el payload, `barrio` placeholder.
- **`useAvmForm` patrón**: `step`/`form`/`stepLabels`/`stepperFields` adentro; `canAdvance` valida los 3 pasos (paso 3 exige `place`); `toPayload()` narrowea `AvmFormState` (con nulls) → `AvmFormPayload` (estricto) con guard, sin `as`. El DOM ref del autocomplete lo **posee el componente** y se pasa al composable por parámetro (no lo crea ni retorna el composable) — evita el falso "unused" de Volar en template refs por string.
- **Mapa reusable `MapUser.vue` = dumb/controlado, patrón híbrido**: props in (`center: [number,number]`, `markers: MarkerData[]`), `v-model:zoom` con `defineModel`, **+ un `<slot>`** como escape hatch para capas extra. El padre posee los datos/decisiones; el componente posee la instancia Leaflet. Los hijos del slot se compilan en el scope del **padre** → `MapUser` no importa todos los `L*`, queda mínimo.
- **Stack mapa**: usar `@vue-leaflet/vue-leaflet` (declarativo: `<l-map>/<l-tile-layer>/<l-marker>/<l-icon>`) en vez de Leaflet crudo imperativo. Ambos ya son deps. El CSS de Leaflet ya carga vía `<link>` en `public/index.html` (no hace falta el import).
- **Iconos de marker data-driven**: `MarkerImageType` en `types/maps.ts` (`subject | house | apartment | food | education`, evoluciona). SVGs en `public/icons/<imageType>.svg` con **filename === valor del union**. El `:src` por template literal **solo funciona para assets en `public/`**, no `src/assets/` (ahí el bundler no resuelve strings dinámicos).
- **`subject`** = el inmueble que se está avaluando — marker propio, diferenciado de comparables (house/apartment) y POIs, para verlo contra los demás.
- **Upgrade a Vue 3.5 decidido** (habilita `defineModel` y `useTemplateRef`) — independiente de la migración a Vite, que sigue diferida (ver adr-vue-cli-deferred-vite-migration). Planeado para 2026-05-29.
- **D3 sobre el mapa = capa plug-and-play**: vive en un componente/composable dedicado que consume la instancia del mapa (expuesta por `MapUser` vía `@ready`/`defineExpose`), **no en la view**. La data baja desde la view por props; la mecánica D3↔Leaflet (proyección, redibujo en zoom/move) va pegada a la instancia.
- **`defineModel`/`defineProps`/`defineEmits` son macros del compilador** — no se importan.

## Open questions

- Set final de `MarkerImageType` (evoluciona; faltan categorías de POI: health, transport, recreation...).
- ¿`markers` opcional (`?`) para permitir uso slot-only del mapa?
- Naming de `subject` (vs `own`/`target`).

## Next steps

- 2026-05-29: upgrade Vue 3.5, luego verificar que `MapUser` monta, que `v-model:zoom` sincroniza con el padre y que cargan los íconos.
- Crear los SVG en `public/icons/`.
- Cablear el padre (`DevPlaygroundView`) para usar `MapUser` + el chain autocomplete → coords → marker `subject` (relacionado con el pendiente del handler `gmp-placeselect` → catalog by-coords → /predict).
