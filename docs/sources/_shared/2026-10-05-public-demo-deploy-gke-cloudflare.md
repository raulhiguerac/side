---
title: Deploy de la demo pública — GKE con crédito, Cloudflare Tunnel, R2 y CDN
captured-from: conversation
captured-on: 2026-10-05
participants: [author, claude]
---

## Context
Se buscó dónde publicar el monorepo para que cualquiera pueda entrar a ver la demo, gastando lo mínimo y sin exponerlo a abuso. El autor ya tiene Helm y planea Argo CD con ApplicationSet. La infra es su área: estima 3–5 días para tenerla, netpols incluidas.

## Key conclusions
- **El dimensionamiento lo manda la RAM:** el stack completo pide unos 12–16 GB.
  - Corren 4 Postgres con PostGIS, Redis, Keycloak, Kafka, MLflow, SeaweedFS y los 4 servicios.
  - ORS con `-Xmx6g` es el que más pesa. Bajarle el heap o servir isócronas ya calculadas desde la caché reduce el tamaño necesario.
- **Opciones evaluadas (precios de octubre de 2026):**
  - **Oracle Always Free (ARM):** desde el 2026-06-15 da 2 OCPU / 12 GB en cuentas gratuitas. Según reportes de usuarios, las cuentas pay-as-you-go siguen con 4 OCPU / 24 GB sin costo, pero Oracle no lo confirma públicamente. Hay poca capacidad ARM y exige imágenes arm64.
  - **Hetzner CAX31 / CAX41 (ARM):** 16 GB / 32 GB por €20,99 / €40,99 al mes, tras la subida de junio de 2026. Es la opción paga más fiable.
  - **Crédito de GCP:** $300 por 90 días que no se extienden; al vencer, los recursos se detienen. No aplica si ya se fue cliente de pago de Google Maps Platform, y el proyecto usa Places.
- **Dirección elegida: GKE pagado con el crédito y Cloudflare para todo lo que da la cara.**
  - **Control plane gratis:** GKE da $74,40 de crédito al mes por billing account, que cubren la tarifa de un cluster zonal Standard o de uno Autopilot. Los $300 se van en nodos y discos.
  - **Nodos:** uno de 16 GB on-demand ronda los $100 al mes (cifra a confirmar en la calculadora); con spot alcanza de sobra para los 90 días.
  - **Cloudflare Tunnel:** `cloudflared` corre como Deployment en el cluster y apunta al Gateway como `ClusterIP`. No hay Load Balancer de GCP ni IP pública, y el cluster no expone puertos.
  - **R2 como object storage en cloud:** compatible con S3 y sin costo de egress. Gratis hasta 10 GB, 1M de operaciones de clase A y 10M de clase B al mes. Las URLs presignadas de fotos y CSV funcionan igual; solo cambia el endpoint en los values (SeaweedFS en local, R2 en cloud). Sirve también para los artefactos de MLflow.
  - **El CDN viene incluido al proxiar el dominio:**
    - el front, estático con hash history (ADR-0002), va en Cloudflare Pages o R2, fuera del cluster;
    - las fotos se sirven desde un dominio propio sobre el bucket y quedan cacheadas en el edge;
    - la API no se cachea, salvo quizás los `GET` públicos de catálogo con un TTL corto.
- **Seguridad por capas:**
  - **En Cloudflare:** DDoS, WAF y rate limit en el edge.
  - **En el Gateway (Cilium/Envoy):** rate limit por IP como segunda capa en los endpoints caros, que son `predict` del AVM, `reachable-pois` (dispara ORS y Overpass), registro y login.
  - **En Keycloak:** detección de fuerza bruta activada.
  - **Contenido:** registro cerrado o cuentas demo de solo lectura.
- **El riesgo de plata real es la API key de Google Maps, no el cluster:** restringirla por referrer, poner una cuota diaria con tope en Places y una alerta de facturación.

## Open questions
- Cookies y CORS: ¿front en `app.` y API en `api.` (cookie `Domain=.<dominio>`, `SameSite=Lax`, CORS con origen exacto), o todo en un dominio con `/api/*` enrutado al tunnel por path, sin CORS?
- ¿El trial de GCP es elegible, habiendo pagado Google Maps Platform?
- ¿Cuánto se puede recortar ORS (heap, o precalcular isócronas) para entrar en 12–16 GB?
- ¿Los "3–5 días" de infra son días completos o sesiones de 2–3 horas? Cambia el plan de abajo.

## Next steps
- Armar el presupuesto de RAM por servicio con los `requests`/`limits` reales del Helm.
- Values por entorno (local, GKE, VPS) y Argo ApplicationSet que apunte al destino, para mudarse sin fricción cuando venza el crédito (día 91).
- Configurar CORS del bucket de R2 para permitir `PUT` desde el origen del front, porque el navegador sube directo con la URL presignada.
- Antes de usar el crédito: alerta de presupuesto en GCP. El egress de GKE hacia Cloudflare se cobra como tráfico a internet, poco para una demo.
- Plan tentativo de 6 semanas a 2–3 h/día, 5 días por semana (~65–95 h):
  1. Vitest + CI (lint, typecheck, tests de composables) y el bug del reimport.
  2. Modales reales del panel de barrios.
  3. Loop del AVM: consumer de `price-predicted`, arranque del worker y precio expuesto y visible.
  4. Infra: Argo + Helm + ApplicationSet y primer deploy.
  5. Netpols y deploy estable; empezar el catálogo mínimo (listar y activar/desactivar).
  6. Terminar el catálogo mínimo, margen y demo de punta a punta.

  Si la infra lleva 3–5 días completos, no entra todo: el catálogo mínimo queda como stretch.
