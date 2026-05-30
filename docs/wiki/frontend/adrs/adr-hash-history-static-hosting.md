---
title: ADR-0002 — Hash history para deployment en bucket estático
status: stable
last-verified: 2026-05-21
owners: [frontend]
related: [[frontend]], [[frontend-architecture]], [[frontend-local-dev]]
sources: [../../../sources/frontend/2026-05-21-foundational-qa.md]
decision-date: 2026-05-21
decision-status: accepted
---

# ADR-0002 — Hash history para deployment en bucket estático

## Contexto

Vue Router 4 soporta dos modos de history:
- `createWebHistory()` — URLs limpias (`/login`, `/settings/profile`). Requiere que el servidor redirija TODAS las paths no-asset a `index.html` (rewrite rule). En S3/CloudFront/GCS/MinIO esto es configurable, en algunos buckets más rudimentarios no.
- `createWebHashHistory()` — URLs con `#` (`/#/login`, `/#/settings/profile`). El browser nunca pide la path al servidor (el `#` es client-side). Funciona en **cualquier host estático sin configuración**.

Deployment planificado del frontend `side`: **bucket público estático con build compilado**. Sin servidor de aplicaciones detrás — solo el bucket sirviendo `index.html` + assets.

SEO **no es prioridad MVP** (per autor). El roadmap menciona SEO como traffic driver, pero la calculadora pública (habímetro etc.) no se implementa por ahora; primero hay que cerrar la app.

## Decisión

Usar `createWebHashHistory()` — URLs con prefijo `#/`.

## Alternativas consideradas

- **HTML5 history + rewrite rules**: limpias estéticamente, mejores para SEO/sharing. Requiere config específica del host (CloudFront behaviors, S3 website config con `routing rules`, GCS no soporta nativo, MinIO requiere proxy). Más fricción de deployment.
- **HTML5 history + servidor (nginx/Node)**: rompe el modelo "bucket estático", agrega operación.
- **Server-Side Rendering (Nuxt)**: solución correcta para SEO pero cambio de stack mayor — fuera de scope del MVP.
- **Pre-rendering (selectivo, ej. landing page)**: posible compromiso futuro pero complejidad agregada hoy.

## Consecuencias

- ✅ Deploy en cualquier bucket estático sin config especial.
- ✅ Zero-fricción CI/CD: `npm run build && aws s3 sync dist/ s3://bucket` (o equivalente).
- ✅ Sin coupling al stack del host.
- ❌ **URLs con `#/`** — feo estéticamente, comparte mal en algunas plataformas que ofuscan fragmentos.
- ❌ **SEO**: los crawlers (Googlebot) modernos resuelven JS pero hash fragments siguen siendo señal débil — penaliza ranking de páginas profundas. Aceptado mientras SEO no sea prioridad.
- ❌ **Analytics**: muchas herramientas (Google Analytics, Mixpanel) tienen quirks con hash routes — requieren config específica para trackear cambios de hash como pageviews.
- ❌ **Cuando SEO entre en scope**: tocará migrar a HTML5 history + rewrite rules + posiblemente pre-render de páginas públicas. Cambio no-trivial.

## Re-evaluación futura

Triggers para revisar esta decisión:
- **Habímetro / calculadora pública entra en scope** (driver de tráfico SEO).
- **Compartir URLs profundas** se vuelve frecuente y el `#/` molesta a usuarios.
- **Adopción de SSR/SSG** (Nuxt) por otras razones.

## Claims

- `vue-router` se crea con `createWebHashHistory()` ([router/index.ts:1](frontend/src/router/index.ts#L1), [router/index.ts:89](frontend/src/router/index.ts#L89)).
- URLs visibles en el browser tienen el patrón `<base>/#/<path>` (ej. `http://localhost:8080/#/login`).
- Deploy planificado: bucket público estático con build compilado (per autor, 2026-05-21).
- SEO marcado como "no prioridad MVP" en este ADR; diferenciador futuro en [[project-roadmap-2026]] pero no en scope inmediato.
