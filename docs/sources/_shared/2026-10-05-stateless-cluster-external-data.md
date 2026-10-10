---
title: Cluster sin estado — datos fuera en Neon y R2, Redis efímero adentro
captured-from: conversation
captured-on: 2026-10-05
participants: [author, claude]
---

## Context
A partir del deploy de la demo en GKE con Cloudflare (ver `2026-10-05-public-demo-deploy-gke-cloudflare.md`), se propuso un cluster sin estado con la base de datos fuera, usando free tiers de Redis, Supabase o bases baratas. La meta es que el cluster sea desechable: al vencer el crédito de GCP se despliega en otro lado, apuntando a los mismos datos.

## Key conclusions
- **Topología:**
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
- **Postgres en Neon, no en Supabase:**
  - **Supabase gratis** pausa el proyecto tras una semana sin actividad (la demo quedaría caída) y solo da 2 proyectos.
  - **Neon gratis** da hasta 100 proyectos, cada uno con 0,5 GB y 100 CU-horas al mes, con PostGIS. Un proyecto por servicio más Keycloak (5) mantiene el aislamiento actual.
  - Tamaños medidos en local: catalog 54 MB, properties 38 MB, users 13 MB, Keycloak 13 MB, analytics 7,5 MB.
- **Neon suspende el cómputo gratis a los 5 minutos sin uso:** la primera request tarda más y las conexiones del pool mueren. Ningún servicio usa hoy `pool_pre_ping`; sin él, la primera request tras la suspensión falla. Elegir una región de Neon cercana a la de GKE.
- **Redis Cloud gratis se descarta:** 30 MB, 30 conexiones, 100 operaciones por segundo y 5 GB de tráfico al mes, sin réplica. Con 4 servicios, el feed, las isócronas en GeoJSON y las búsquedas de catálogo se agota rápido, y no aporta nada porque la caché es opcional por ADR. Un Redis efímero en el cluster (~50–100 MB de RAM) no rompe el "stateless": solo se pierden la caché y los tokens de reset en curso.
- **Lo que sigue teniendo estado dentro del cluster:**
  - Kafka, con un PVC chico; al mudarse solo se pierden eventos en tránsito.
  - ORS, con el grafo de Bogotá bajado de R2 en un initContainer o metido en la imagen, en vez de reconstruirlo al arrancar.
  - MLflow no hace falta en runtime para la demo: analytics puede bajar el modelo de R2 al arrancar.
- **R2 con dominio propio sirve un solo bucket.**
  - Fotos y avatares van en un bucket público detrás de `cdn.`; CSV de imports y artefactos en buckets privados sin dominio.
  - Las subidas presignadas van al endpoint S3 de R2, no a `cdn.`.
  - Choca con `build_public_url`, que hoy arma `{base}/{bucket}/{key}`.
- **Con `app.` y `api.` bajo el mismo dominio**, la cookie de auth funciona con `Domain=.<dominio>` y `SameSite=Lax`.
- **Regla para combinar proveedores:** ninguna pieza externa lleva lógica propia, solo connection strings en values y secrets. Los free tiers cambian sin aviso (Oracle recortó el suyo a la mitad en junio de 2026), así que cada pieza tiene que poder cambiarse por otra (Cloud SQL, un Postgres en VPS) editando config.

## Open questions
- ¿Kafka con PVC dentro del cluster, o un Kafka gestionado con free tier?
- ¿El modelo del AVM se baja de R2 al arrancar, o se mantiene MLflow en el cluster?

## Next steps
- Discutir y luego aplicar `pool_pre_ping` en el engine de SQLAlchemy de los 4 servicios. Es cambio de código y requiere acuerdo previo.
- Separar buckets públicos y privados en R2 y ajustar `build_public_url` (open-item ya existente de URLs públicas con R2).
- Crear los 5 proyectos de Neon en la región más cercana a GKE y cargar los seeds.
- Preparar el initContainer de ORS que baja el grafo desde R2.
