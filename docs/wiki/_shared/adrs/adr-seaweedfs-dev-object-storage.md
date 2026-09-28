---
title: ADR-0009 — SeaweedFS como S3 de dev y rclone como cliente, en lugar de MinIO y mc
status: stable
last-verified: 2026-09-27
owners: [_shared]
related:
  - "[[local-bootstrap]]"
  - "[[adr-infra-reconciled-by-init-jobs]]"
  - "[[adr-dev-config-versioned-artifacts-in-r2]]"
  - "[[adr-mlflow-minio-stack]]"
  - "[[analytics-service-mlflow]]"
  - "[[adr-image-upload-presigned-batch]]"
sources:
  - ../../../sources/_shared/2026-09-27-minio-a-seaweedfs-y-rclone.md
decision-date: 2026-09-27
decision-status: accepted
---

# ADR-0009 — SeaweedFS como S3 de dev y rclone como cliente

## TL;DR

MinIO dejó de distribuir imágenes y `mc` no funciona contra R2. El S3 local pasa
a SeaweedFS, con usuarios y permisos declarados en un JSON versionado, y todo
cliente S3 del repo (Makefile y one-shots) pasa a rclone.

## Contexto

Dos problemas llegaron juntos:

- **`mc` contra R2 transfiere 0 B y termina en éxito.** `mc mirror` pide el listado
  con `metadata=true`, extensión de MinIO que R2 responde con
  `ListObjectsV2 search parameter metadata not implemented`. `make bootstrap` no
  bajaba nada.
- **MinIO retiró su distribución libre.** El 2026-09-11 borró `minio/minio` y
  `minio/mc` de Docker Hub; los tags fijos en quay.io tampoco existen y el repo
  está archivado. Sin esas imágenes no arrancaban `minio`, `minio-init` ni
  `mlflow-init`, y casi todo el stack depende de `minio-init`.

Lo que el repo necesita del S3 local: boto3 con `endpoint_url`, URLs prefirmadas
de PUT y GET (firmadas con un endpoint público distinto del interno), CORS para
que el navegador suba directo, un usuario por servicio limitado a sus buckets,
lectura anónima para las URLs públicas `{base}/{bucket}/{key}`, y multipart para
MLflow.

## Decisión

- El servicio de storage del compose corre `chrislusf/seaweedfs:4.47` (`weed
  server -s3`). Conserva el nombre `minio` y el puerto `9000`, así que ningún
  `.env.dev` cambia.
- Usuarios y permisos se declaran en
  [infra/seaweedfs/s3.json](infra/seaweedfs/s3.json), con las mismas keys que ya
  estaban en `.env.dev`. Reemplaza a las policies JSON y a `mc admin user add`.
- `minio-init` solo crea los buckets (`rclone mkdir`, que en S3 es `CreateBucket`).
- rclone (`rclone/rclone:1.75.1`, configurado por env) es el único cliente S3:
  `make bootstrap`, `make data-pull`, `minio-init` y `mlflow-init`.

## Alternativas consideradas

- **Garage.** Liviano, pero las keys tienen formato `GK…` (habría que cambiar
  `.env.dev`), no da lectura anónima por la API S3, el CORS es por bucket y
  manual, y la imagen no trae shell para el init.
- **RustFS.** Promete compatibilidad con `mc`, pero está en alfa y `mc admin
  user/policy` —justo lo que usaba `minio-init`— devuelve 500 o "Volume not found".
- **Chainguard MinIO.** Gratis solo con `latest`, sin versión fija, y compilado
  de un repo archivado. Sirve de parche, no de solución.
- **Ceph (RGW).** La mejor compatibilidad S3, pero la imagen demo es solo amd64
  y no se publica desde 2024-11; la imagen oficial está pensada para `cephadm`
  (systemd, discos) y un nodo pide 4 GB o más además de ORS.
- **aws-cli en vez de rclone.** Funciona con R2, pero la imagen pesa ~400 MB
  para bajar ~85 MB.

## Consecuencias

- Los permisos son un archivo versionado, igual que el realm: ya no los
  reconcilia un init.
- La identidad `anonymous` lee `profile-photos` y `property-images`, así que las
  URLs públicas que arman users y properties funcionan. Con MinIO daban 403: nunca
  se configuró acceso anónimo.
- CORS viene abierto por defecto, como en MinIO.
- `mlflow-init` valida con `rclone check --one-way` (tamaño y hash por archivo)
  en vez de contar objetos, y deja de necesitar un centinela previo porque
  `rclone copy` salta lo que ya está igual.
- La consola de MinIO (`:9001`) no tiene equivalente directo; la UI del filer en
  `:8888` permite navegar archivos.
- `infra/minio/policies/` queda sin uso; se conserva hasta decidir borrarlo.
- El nombre `minio` del servicio y de `MINIO_URL` ya no describe lo que corre.
  Renombrarlo toca todos los `.env.dev` y se dejó para después.

## Claims

- El servicio `minio` del compose usa la imagen `chrislusf/seaweedfs:4.47` y expone S3 en el puerto 9000 y la UI del filer en el 8888 ([docker-compose.yml](docker-compose.yml)).
- Los usuarios S3 y sus permisos por bucket están declarados en `infra/seaweedfs/s3.json`, montado en `/etc/seaweedfs/s3.json` ([s3.json](infra/seaweedfs/s3.json)).
- La identidad `anonymous` de `s3.json` tiene lectura sobre `profile-photos` y `property-images`, y sobre ningún otro bucket.
- `minio-init` usa `rclone/rclone:1.75.1` y solo crea los cuatro buckets con `rclone mkdir` ([docker-compose.yml](docker-compose.yml)).
- `mlflow-init` sube los artifacts con `rclone copy` y los valida con `rclone check --one-way` ([mlflow-init.sh](infra/dev/mlflow-init.sh)).
- `make bootstrap` y `make data-pull` bajan de R2 con rclone en contenedor ([Makefile](Makefile)).
- El healthcheck del storage consulta `http://127.0.0.1:9000/healthz` con `wget` ([docker-compose.yml](docker-compose.yml)).
