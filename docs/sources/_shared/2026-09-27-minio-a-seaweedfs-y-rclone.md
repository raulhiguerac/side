---
title: MinIO fuera del stack — SeaweedFS como S3 de dev y rclone como cliente
captured-from: conversation
captured-on: 2026-09-27
participants: [author, claude]
---

## Context

`make bootstrap` bajaba 0 B de R2 y, en paralelo, MinIO borró `minio/minio` y
`minio/mc` de Docker Hub (2026-09-11); los tags fijos de quay.io tampoco
existen ya. El compose quedaba sin arrancar: `minio`, `minio-init` y
`mlflow-init` dependían de esas imágenes.

## Key conclusions

### Cliente S3: rclone reemplaza a `mc` en todo el repo

- `mc mirror` lista con `metadata=true`, extensión de MinIO que R2 no implementa
  (`ListObjectsV2 search parameter metadata not implemented`): transfiere 0 B y
  termina en éxito. El token de R2 no tenía nada que ver.
- `make bootstrap` y `make data-pull` usan `rclone/rclone:1.75.1` con el remote
  armado por env (`RCLONE_CONFIG_R2_*`, `RCLONE_CONFIG=/dev/null` para no buscar
  archivo de config). `rclone copy` es idempotente: la segunda corrida no transfiere nada.
- `minio-init` solo crea los 4 buckets con `rclone mkdir s3:<bucket>`: en un
  remote S3 eso hace `CreateBucket`, y no falla si el bucket ya existe.
- `mlflow-init` sube los artifacts con `rclone copy` y los valida con
  `rclone check --one-way` (tamaño y hash por archivo), que es más estricto que el
  conteo de objetos de antes. Ya no hace falta el chequeo previo por el
  "Overwrite not allowed" de `mc`.
- Makefile: `$$(PWD)` corría el comando `PWD`, que solo funcionaba por el
  filesystem case-insensitive de macOS; ahora es `$(CURDIR)`.

### Almacenamiento S3 de dev: SeaweedFS (`chrislusf/seaweedfs:4.47`)

- Alternativas evaluadas y descartadas:
  - **Garage:** keys con formato `GK…`, sin lectura anónima por S3 y CORS configurado a mano.
  - **RustFS:** alfa, y `mc admin user/policy` roto.
  - **Chainguard MinIO:** solo `latest`, congelado.
  - **Ceph:** la imagen demo es solo amd64, sin builds desde 2024-11, pide 4 GB o más, y cephadm no encaja en compose.
- Usuarios y permisos van **declarados** en `infra/seaweedfs/s3.json` (reemplaza
  policies + `mc admin user add`). Conserva las keys de `.env.dev`.
- Identidad `anonymous` con lectura de `profile-photos` y `property-images`:
  arregla las URLs públicas `{base}/{bucket}/{key}` que con MinIO daban 403
  (nunca se configuró acceso anónimo).
- Verificado con boto3:
  - el alcance por servicio (AccessDenied cruzado);
  - las URLs prefirmadas de PUT y GET, incluido firmar con `localhost` y hacer el PUT desde el host;
  - CORS abierto por defecto (preflight desde `:8080`);
  - multipart.
- Verificado de punta a punta: `models:/bogota-avm@production` baja completo desde SeaweedFS.
- El servicio sigue llamándose `minio` y escucha en `:9000`: ningún `.env.dev`
  cambió. La consola de `:9001` pasa a la UI del filer en `:8888`. El volumen `minio_data` pasa a `seaweedfs_data`.

### Puertos del host

- MLflow se publica en `5050:5000`: macOS ocupa el 5000 con AirPlay Receiver.
  Adentro de la red sigue siendo `mlflow:5000`.
- Makefile, README y `forwardPorts` del devcontainer quedan con 8888 y 5050.

### R2 frente a boto3 (para prod)

- Compatible con todo lo que usa el código (put/get, `upload_file(obj)`, URLs
  prefirmadas de PUT y GET, multipart). `us-east-1` equivale a `auto`.
- Sin bucket policies ni ACLs: el acceso se limita con un token por servicio y por bucket.
- Lo público se sirve por dominio propio o `r2.dev`, sin el bucket en la ruta:
  `{base}/{bucket}/{key}` (`confirm_image_uploads.py`, `build_public_url`) saldría mal.
- CORS hay que configurarlo en el bucket.

## Open questions

- En prod, cómo se arman las URLs públicas: sacar el bucket de la ruta o usar un dominio por bucket.
- Qué puertos tiene sentido listar en `forwardPorts`: el contenedor `develop` no corre los servicios.
- `WORKER_PRINCIPAL` sigue siendo un UUID de una DB vieja, y el worker de Kafka no está en el compose.

## Next steps

- Borrar `infra/minio/policies/`: ya nada lo monta, se conserva a pedido.
- Correr `make up` completo en limpio; hasta ahora solo se probaron `minio`,
  `minio-init`, `mlflow-init` y `mlflow` por separado.
- Rotar o restringir la key de Google Maps que quedó en el historial de git
  (commits `66629bc`..`faf5cdb`) antes de abrir el repo.
- Arreglar `FRONT_BASE_URL` en users: le falta el esquema y el TLD.
