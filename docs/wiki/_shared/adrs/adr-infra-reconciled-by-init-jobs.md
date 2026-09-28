---
title: ADR-0008 — La infra se reconcilia con init jobs idempotentes, no se restaura de archivos de estado
status: stable
last-verified: 2026-09-27
owners: [_shared]
related:
  - "[[local-bootstrap]]"
  - "[[adr-dev-config-versioned-artifacts-in-r2]]"
  - "[[adr-auth-keycloak-jwt]]"
  - "[[analytics-service-mlflow]]"
  - "[[users-service-keycloak]]"
  - "[[adr-seaweedfs-dev-object-storage]]"
sources:
  - ../../../sources/_shared/2026-09-07-entorno-dev-migrable.md
  - ../../../sources/_shared/2026-09-27-minio-a-seaweedfs-y-rclone.md
---

## TL;DR

Keycloak, MinIO, las bases y MLflow se llevan a su estado esperado con one-shots
que corren en cada `up` y son idempotentes, en vez de con archivos de estado que
se importan una sola vez. El disparador fue que el mecanismo de import de
Keycloak no se re-aplica.

## Contexto

El repo tenia un `realm.template.json` montado en Keycloak con `--import-realm`.
Ese mecanismo **salta si el realm ya existe**, y lo dice en el log:

```
Realm 'core' already exists. Import skipped
```

O sea que editar el JSON no tenia ningun efecto hasta borrar el volumen de la DB
de Keycloak. Es el peor modo de falla posible para un entorno compartido: el
cambio no se aplica, no hay error, y el archivo del repo se desincroniza del
estado real sin que nadie se entere. Cuando se audito, al template le faltaban el
cliente `users-ms-auth`, el rol de realm `admin` y el client scope `api-audience`
—de donde sale el `aud: users-ms`—, todos presentes en el Keycloak real.

MinIO tenia el problema simetrico: las policies de `infra/minio/policies/` no las
aplicaba nadie, y `MINIO_DEFAULT_BUCKETS` en el compose no hacia nada porque esa
variable es de la imagen de Bitnami, no de `minio/minio`.

> **Enmienda 2026-09-27.** El storage pasó a SeaweedFS ([[adr-seaweedfs-dev-object-storage]]).
> Usuarios y permisos ya no los reconcilia `minio-init`: se declaran en `infra/seaweedfs/s3.json`.
> `seed-db` y `seed-dev-user` estan comentados en el compose mientras las apps corren en el devcontainer.

## Decision

Cada pieza de infra con estado tiene un one-shot que la lleva a su forma esperada
en cada `up`, con `depends_on: service_completed_successfully` aguas abajo:

| Job | Reconcilia |
|---|---|
| `minio-init` | Los buckets (usuarios y permisos van en `s3.json`) |
| `keycloak-init` | Los client secrets, que el export del realm enmascara |
| `seed-db` | Los dumps, saltando tablas que ya tienen filas |
| `seed-dev-user` | El usuario dev, via el endpoint de registro real |
| `mlflow-init` | El registro y los artifacts del AVM |

**Reglas del patron:**

1. **Idempotente siempre.** Corre en cada `up`, asi que una segunda corrida tiene
   que ser inofensiva.
2. **Centinela, no confianza en el exit code.** Se chequea el estado antes de
   escribir o se verifica despues. No es teorico: `mc mirror` fallaba con
   `Overwrite not allowed` sobre objetos existentes **y aun asi devolvia 0**, y
   con R2 transfiere 0 B y tambien sale en 0. Hoy `mlflow-init` confirma cada
   archivo con `rclone check`.
3. **Nunca pisar datos.** Los seeds saltan si la tabla tiene filas y `mlflow-init`
   no reemplaza un `mlflow.db` existente. Empezar de cero es explicito
   (`make reset`), no un efecto colateral de levantar el entorno.
4. **El archivo de estado sigue existiendo donde sirve.** El realm JSON aporta la
   estructura —clientes, scopes, roles, el service account con sus mappings— y el
   init solo pone lo que el export no puede llevar. No se reemplaza una cosa por
   la otra: se reparten.

## Alternativas descartadas

- **Solo archivos de import.** Es lo que habia. Vuelve a depender de borrar
  volumenes para cualquier cambio.
- **Registrar el modelo AVM por API en vez de restaurar el sqlite de MLflow.** Se
  descarto al ver que el `MLmodel` trae horneados el `artifact_path` absoluto de
  S3, el `model_id` y el `run_id`: registrar por API genera ids nuevos que no
  coinciden con los del propio artefacto.

## Consecuencias

- Arreglar el realm ya no exige borrar el volumen de Keycloak.
- El estado de infra es auditable leyendo cinco scripts cortos en `infra/dev/` e
  `infra/keycloak/`, en vez de infiriendolo de un JSON de 2.700 lineas.
- `develop` depende de que `minio-init` y `keycloak-init` terminen bien, asi que
  un init roto impide abrir el devcontainer. Es deliberado —mejor eso que una
  shell con el storage a medias— pero es un modo de falla nuevo.

## Claims

- `--import-realm` salta la importacion si el realm ya existe; el log de Keycloak lo registra como `Realm 'core' already exists. Import skipped`.
- Los one-shots son idempotentes y ninguno pisa datos existentes; `seed-db` y `seed-dev-user` estan comentados en el compose ([docker-compose.yml](docker-compose.yml), [infra/dev/](infra/dev)).
- `mlflow-init` no confia en el exit code de la copia: verifica con `rclone check --one-way` que cada artifact local este en S3 con el mismo tamaño y hash ([mlflow-init.sh](infra/dev/mlflow-init.sh)).
- `minio-init` solo crea buckets; los usuarios S3 y sus permisos se declaran en `infra/seaweedfs/s3.json` ([docker-compose.yml](docker-compose.yml)).
- `develop` declara `depends_on` con `service_completed_successfully` sobre `minio-init` y `keycloak-init` ([docker-compose.yml](docker-compose.yml)).
