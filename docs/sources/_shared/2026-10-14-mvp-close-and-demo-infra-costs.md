---
title: Cierre del MVP antes de la infra, rate limiting y costos/red de la demo (GKE + Neon)
captured-from: conversation
captured-on: 2026-10-14
participants: [raul, claude]
---

## Context
Con el back del admin de catálogo cerrado (#28), se revisó qué falta en el front para dar el MVP por terminado antes de la infra, y se discutió rate limiting y los costos/seguridad de red del despliegue de la demo (GKE + Cloudflare Tunnel + Neon + R2, ADR-0011). El proyecto es un side para mostrar y discutir infra, no para usuarios reales.

## Key conclusions
- **Flujos de cuenta incompletos:** el front solo pide el correo de reset (`/forgot-password`); faltan las vistas de confirmar reset (`POST /v1/auth/reset-password/confirm`) y de reactivar cuenta (`/v1/users/reactivation/{request,confirm}`). El link del correo (`build_redirect_url` → `FRONT_BASE_URL + /reset-password?token=…` y `/reactivate?token=…`) no llega a ninguna vista porque el router usa `createWebHashHistory` (`/#/…`); además `FRONT_BASE_URL` no tiene esquema. No existe verificación de email (solo se lee el claim `email_verified`): fuera del MVP salvo decisión contraria.
- **Orden del cierre del MVP:** triviales (multiselect no declarado, CSS de `App.vue`) → flujos de cuenta y tabs de catálogo → errores visibles y toasts → Vitest + CI → precio del AVM visible. Registrado como sección "MVP — cierre antes de la infra" en open-items. La fila de moderación del roadmap figura ⏳ pero funciona de punta a punta desde 2026-08.
- **Rate limiting:** Redis guarda contadores compartidos entre réplicas; el middleware/gateway decide (rate limit = rechazar con 429 + `Retry-After`; throttling = demorar/encolar). Dos capas: Cloudflare para el límite grueso por IP y middleware con Redis (`slowapi`/`fastapi-limiter`) solo en endpoints sensibles: login, `reset-password/request`, `/users/resolve`, `/search/feed`, `/predict`, `reachable-pois`. Redis efímero sirve (perder contadores es tolerable); decidir fail-open vs fail-closed por endpoint.
- **Red en GCP:** tráfico entre nodos en la misma zona es gratis; entre zonas de la misma región, $0.01/GiB por dirección → para la demo, cluster **zonal**. El principal egress es la respuesta de la API saliendo por el Tunnel; las fotos salen de R2 (sin egress). Nodos privados exigen Cloud NAT (cobro por hora y por GB).
- **Precios de egress (aprox., fuentes de terceros 2026; verificar en la página oficial):** Premium Norteamérica ~$0.12/GiB (1 GiB gratis/mes); Standard Norteamérica ~$0.085/GiB (200 GiB gratis/mes); Premium Sudamérica ~$0.19/GiB. A volúmenes de demo, centavos.
- **Neon:** solo tiene regiones AWS (Azure deprecado desde 2026-04; sin GCP). "Misma región" del ADR significa misma ciudad: `aws-sa-east-1` ↔ `southamerica-east1` (São Paulo) o `aws-us-east-1` ↔ `us-east4` (Virginia). Plan Free: 5 GB de egress por proyecto al mes y, al pasarse, **suspende el cómputo** (no cobra); pagos: 500 GB/proyecto y $0.10/GB después. Solo cuenta lo que sale de Neon; riesgo real son lecturas masivas (`pg_dump`, reprocesos, jobs que recorren tablas).
- **Neon IP Allow:** filtra por IP/CIDR (no dominios), plan Scale según la doc actual; PrivateLink solo desde AWS. En Free la base queda abierta a internet protegida por contraseña + TLS. Con IP Allow, GKE necesitaría Cloud NAT con IP estática.
- **Veredicto de la arquitectura:** la forma es de producción (cluster sin estado, Cloudflare delante, sin IP pública, GitOps); la operación no (tiers gratis en el camino crítico, sin CI, sin observabilidad, restore sin probar). Para un MVP real sería sobreingeniería; como side para mostrar infra, es el contenido.

## Open questions
- Región final: São Paulo (latencia a Colombia) o Virginia (egress más barato).
- ¿Nodos públicos o privados con Cloud NAT?
- ¿Mover Keycloak a una base que no se suspenda?

## Next steps
- Sección "De demo a producción" en ADR-0011: Neon solo AWS y misma ciudad, cupo de egress Free con suspensión, IP Allow/NAT, y lo que falta para production grade (CI, uptime + captura de errores, `pool_pre_ping` y Keycloak sin cold start, restore probado, secrets fuera de los values de Helm).
- Hardening en plan Free: rol por servicio con mínimos privilegios, contraseñas aleatorias en Secrets de k8s, `sslmode=require`, nunca el rol owner desde las apps.

## References
- https://neon.com/docs/introduction/regions
- https://neon.com/docs/import/azure-regions-deprecation
- https://neon.com/docs/introduction/plans
- https://neon.com/docs/introduction/network-transfer
- https://neon.com/faqs/free-plan-limits-and-quotas
- https://neon.com/docs/security/security-overview
- https://cloud.google.com/vpc/network-pricing
- https://cloud.google.com/vpc/pricing-announce
- https://egresscost.com/gcp/calculator/
- https://www.nops.io/blog/gcp-egress-cost/
