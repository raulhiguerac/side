---
title: ADR-0011 — Cluster sin estado para la demo pública; datos en Neon y R2, Redis efímero adentro
status: draft
last-verified: 2026-10-14
owners: [_shared]
related:
  - "[[project-roadmap-2026]]"
  - "[[open-items]]"
  - "[[adr-cache-optional-layer]]"
  - "[[adr-seaweedfs-dev-object-storage]]"
  - "[[adr-dev-config-versioned-artifacts-in-r2]]"
  - "[[adr-hash-history-static-hosting]]"
sources:
  - ../../../sources/_shared/2026-10-05-stateless-cluster-external-data.md
  - ../../../sources/_shared/2026-10-05-public-demo-deploy-gke-cloudflare.md
  - ../../../sources/_shared/2026-10-14-mvp-close-and-demo-infra-costs.md
decision-date: 2026-10-05
decision-status: accepted
---

# ADR-0011 — Cluster sin estado para la demo pública; datos en Neon y R2, Redis efímero adentro

## TL;DR

La demo pública corre en un GKE pagado con el crédito de GCP, que dura 90 días. Para que el cluster sea desechable, los datos persistentes viven fuera: Postgres en Neon y objetos en R2. Dentro solo quedan los servicios, Keycloak y piezas que se pueden perder (Redis efímero, Kafka con PVC chico, ORS con el grafo bajado de R2). El día 91 se despliega en otro lado apuntando a los mismos datos.

## Contexto

- El crédito de GCP ($300) vence a los 90 días sin extensión; al vencer, los recursos se detienen. Mudarse no debería implicar migrar datos.
- Cloudflare va delante: DNS, CDN, WAF, DDoS y Tunnel. El cluster no expone IP pública ([[project-roadmap-2026]]).
- catalog y properties necesitan PostGIS. Hoy cada servicio tiene su propia base, y Keycloak la suya.
- Las bases locales son chicas: catalog 54 MB, properties 38 MB, users 13 MB, Keycloak 13 MB y analytics 7,5 MB (medidas el 2026-10-05).
- Por [[adr-cache-optional-layer]], Redis es una optimización: si falla, los servicios degradan a la DB.

## Decisión

El cluster de la demo no guarda estado que importe: Postgres va en Neon, con un proyecto por servicio más Keycloak; los objetos en R2, con buckets separados por visibilidad. Redis, Kafka y ORS corren dentro, como piezas reemplazables.

Topología:

```
INTERNET → CLOUDFLARE (DNS · CDN · WAF · DDoS · rate limit)
  ├─ app.<dominio> → Pages / R2   (SPA estática)
  ├─ cdn.<dominio> → R2 público   (fotos)
  └─ api.<dominio> → Tunnel → GKE (sin IP pública)
                              ├─ 4 servicios + Keycloak (stateless)
                              ├─ Redis efímero · Kafka con PVC · ORS (grafo desde R2)
                              ├─→ Neon (Postgres + PostGIS, misma región)
                              └─→ R2 privado (CSV, modelo) vía S3
```

- **Neon:** 5 proyectos gratuitos (catalog, properties, users, analytics, Keycloak), con PostGIS, en la región más cercana a GKE. Cada proyecto gratuito da 0,5 GB y 100 CU-horas al mes. Neon solo tiene regiones de AWS (las de Azure quedaron deprecadas en abril de 2026 y no hay GCP), así que "misma región" significa **misma ciudad**: `aws-sa-east-1` con `southamerica-east1` (São Paulo) o `aws-us-east-1` con `us-east4` (Virginia).
- **R2:**
  - Bucket **público** detrás de `cdn.<dominio>` para fotos y avatares.
  - Buckets **privados** sin dominio para los CSV de imports y los artefactos del modelo.
  - Las subidas presignadas van al endpoint S3 de R2, no a `cdn.`.
- **Dentro del cluster:**
  - Redis efímero (~50–100 MB de RAM).
  - Kafka con un PVC chico.
  - ORS con el grafo de Bogotá bajado de R2 en un initContainer o metido en la imagen.
  - Para la demo, analytics puede bajar el modelo de R2 al arrancar, sin MLflow corriendo.
- **Regla:** ninguna pieza externa lleva lógica propia, solo connection strings en values y secrets. Cambiar de proveedor es editar config.

## Alternativas consideradas

- **Supabase gratis para Postgres:** pausa el proyecto tras una semana sin actividad, y una demo de visitas esporádicas quedaría caída hasta reactivarla a mano. Además solo da 2 proyectos, lo que obliga a juntar servicios.
- **Redis Cloud gratis:** da 30 MB, 30 conexiones, 100 operaciones por segundo y 5 GB de tráfico al mes, sin réplica. Con 4 servicios, el feed, las isócronas y las búsquedas de catálogo se agota rápido. Y no aporta nada: la caché es opcional y perderla no pierde datos.
- **Bases dentro del cluster (CNPG con PVC):** el cluster deja de ser desechable y mudarse implica migrar datos. Sumaba además el problema del PostGIS de CNPG solo amd64 ([[open-items]]).
- **Cloud SQL:** cumple, pero consume crédito y queda atado a GCP. Es el reemplazo natural si Neon cambia sus condiciones.

## Consecuencias

- ✅ El cluster es desechable: el día 91 Argo despliega en otro destino (VPS, Oracle, local) con las mismas connection strings.
- ✅ Se conserva el aislamiento de hoy, con una base por servicio.
- ❌ **El cómputo gratis de Neon se suspende a los 5 minutos sin uso.** La primera request tarda más y las conexiones del pool mueren. Hace falta `pool_pre_ping` en el engine de SQLAlchemy de cada servicio; hoy ninguno lo usa.
- ❌ La latencia entre GKE y Neon depende de la región. Hay que elegir las dos en la misma ciudad, porque viven en nubes distintas.
- ❌ **El plan Free de Neon da 5 GB de egress por proyecto al mes y, al pasarse, suspende el cómputo** hasta el siguiente ciclo (no cobra excedente; los planes pagos dan 500 GB y cobran $0.10/GB después, según la doc de Neon de 2026). Solo cuenta lo que sale de Neon: la navegación de la demo entra con margen, pero un `pg_dump`, un reproceso o un job que recorra tablas puede tumbar la base de un servicio.
- ❌ **En el plan Free la base queda abierta a internet**, protegida solo por contraseña y TLS. IP Allow (por IP/CIDR, no por dominio) es del plan Scale según la doc actual, y para usarlo GKE necesitaría Cloud NAT con IP estática; PrivateLink solo sirve desde AWS. Mitigación en Free: un rol por servicio con mínimos privilegios, contraseñas aleatorias en Secrets de Kubernetes, `sslmode=require` y nunca el rol owner desde las apps.
- ➖ El egress de GCP lo genera sobre todo la respuesta de la API saliendo por el Tunnel; las fotos salen de R2, que no cobra egress. A volúmenes de demo son centavos (Premium Norteamérica ~$0.12/GiB, Sudamérica ~$0.19/GiB, cifras de terceros de 2026). Entre zonas de una región GCP cobra $0.01/GiB por dirección, así que un cluster zonal deja el tráfico interno en 0.
- ❌ Separar buckets por visibilidad choca con `build_public_url`, que asume `{base}/{bucket}/{key}` con un único `base`.
- ❌ Más proveedores y más cuentas. Los free tiers cambian sin aviso (Oracle recortó el suyo a la mitad en junio de 2026); la regla de "solo connection strings" es lo que hace el cambio barato.
- ➖ Kafka sigue teniendo estado. Al mudarse se pierden solo los eventos en tránsito.

## De demo a producción

La forma ya es de producción (cluster desechable, Cloudflare delante, sin IP pública, GitOps); la operación no. Lo que faltaría para llamarla production grade a escala MVP:

- **Tiers gratis fuera del camino crítico:** Neon pago o Cloud SQL, y Keycloak en una base que no se suspenda (hoy el primer login tras la inactividad tarda o falla), con `pool_pre_ping` en todos los engines.
- **CI por PR** (lint, typecheck, tests) antes de que Argo despliegue.
- **Observabilidad mínima:** chequeo de uptime y captura de errores.
- **Restore probado** al menos una vez.
- **Secrets fuera de los values de Helm.**
- **Redundancia** donde importe: Kafka de un broker y Redis efímero son aceptables solo para la demo.

El proyecto es un side para mostrar y discutir infra; esta lista es la respuesta a "¿qué cambiarías para producción?".

## Claims

- Ningún servicio del backend configura `pool_pre_ping` en su engine de SQLAlchemy ([backend/](backend)).
- `build_public_url` arma la URL pública como `{base_url}/{bucket}/{key}` ([url_builder.py:15](backend/users-service/src/app/services/shared/helpers/url_builder.py#L15)).
