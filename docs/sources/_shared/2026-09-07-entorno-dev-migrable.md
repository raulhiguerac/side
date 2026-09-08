---
title: Entorno de dev migrable — de "pedime el .env" a `make bootstrap && make up`
captured-from: conversation
captured-on: 2026-09-07
participants: [author, claude]
---

## Context

El repo no se podía levantar en otra máquina: el `.env` raíz estaba gitignoreado
y era la única fuente de config, el realm de Keycloak versionado estaba
desincronizado del real, nada creaba los buckets de MinIO, y los datos y binarios
no viajaban. Se auditó el gap completo y se cerró en siete fases, todas
verificadas contra entornos vírgenes y no contra la máquina de desarrollo.

## Key conclusions

### Decisiones de diseño

- **Config determinista al repo, secretos afuera.** Contraseñas de Postgres,
  secrets de Keycloak y claves de MinIO se versionan en `backend/<svc>/.env.dev`:
  son valores de `localhost` y fijarlos es lo que hace el entorno reproducible.
  Solo siete valores viajan a mano en `.env.local` (4 de Cloudflare R2 + Mapbox,
  Brevo y Google Maps). Es irreducible: la credencial que baja los artefactos no
  puede vivir dentro de los artefactos.
- **Reconciliar, no restaurar.** `--import-realm` de Keycloak salta si el realm ya
  existe, así que lo que debe poder re-aplicarse no puede vivir en un archivo de
  import. El patrón quedó en cuatro one-shots idempotentes (`minio-init`,
  `keycloak-init`, `seed-db`, `mlflow-init`) que corren en cada `up`.
- **Los seeds nunca truncan.** Cada uno chequea una tabla centinela y salta si ya
  hay filas. Empezar de cero es `make reset`, explícito y con confirmación.
- **Artefactos en R2, no en git ni en LFS.** Un solo mecanismo (`mc` en
  contenedor, ya presente en el stack por MinIO) y cero prerequisitos nuevos en
  el host más allá de Docker. Dos prefijos: `runtime/` (~85 MB, obligatorio) y
  `datasets/` (~480 MB, solo para reentrenar).
- **El usuario dev se crea por `POST /v1/auth/register`, no por INSERT.**
  `account_id` tiene que ser el `sub` que asigna Keycloak, y ese invariante vive
  en `RegisterAccountUseCase` con su compensación. Como contrapartida
  `keycloak-init` no puede pre-crearlo: la policy de email solo mira la DB local,
  así que pasaría el chequeo y reventaría al crearlo en el IdP.

### Bugs encontrados, todos preexistentes

- **PyJWT dejó de publicar el extra `cryptography`.** `pyjwt[cryptography]`
  resuelve a pyjwt pelado (uv solo emite un warning), y properties-service tiraba
  500 con `MissingCryptographyError` en todo endpoint autenticado. Lo tapaba el
  venv compartido del devcontainer (`UV_PROJECT_ENVIRONMENT`), que hace que un
  paquete declarado por un servicio quede disponible para los otros.
- **properties-service usaba las credenciales root de MinIO**: `storage.py` leía
  `AWS_ACCESS_KEY_ID`, ignorando el usuario `properties-ms` que ya existía con
  scope correcto. Las vars `ACCESS_KEY_PROPERTIES`/`SECRET_KEY_PROPERTIES` solo
  aparecían dentro de un string de error.
- **El Dockerfile de users-service estaba vacío** (0 bytes) y catalog/properties
  no seteaban `PYTHONPATH`, sin el cual `import app` falla.
- **El realm versionado estaba muy desincronizado**: le faltaban el cliente
  `users-ms-auth`, el rol de realm `admin` y el client scope `api-audience` —de
  donde sale el `aud: users-ms`—, además de los role mappings del service account.
- **Tres env vars muertas** (`ACCEPTED_IMAGE_MAX_SIZE`, `BREVO_SMTP_KEY`,
  `MINIO_PUBLIC_URL`) y los cuatro runbooks documentaban `OIDC_AUDIENCE=account`
  cuando el código valida `users-ms`.

### Hallazgos técnicos verificados

- Una **service account de MinIO creada sobre root hereda root** aunque se le
  adjunte una policy nombrada; solo se acota con policy inline. Por eso el diseño
  usa usuarios reales con `mc admin policy attach`. Verificado con 9 checks de
  allow/deny.
- **`mc mirror` no salta los objetos existentes**: falla con `Overwrite not
  allowed` y aun así devuelve exit 0. Cualquier init que lo use necesita
  centinela y verificación de conteo, no el código de salida.
- **ORS reconstruye los grafos en 145 s** para el extracto de Bogotá, y su
  `stamp.txt` guarda el tamaño en bytes del `.pbf`: un pbf cambiado dispara la
  reconstrucción solo. Los grafos (176 MB) no viajan.
- **El `MLmodel` del AVM trae horneados** el `artifact_path` absoluto de S3, el
  `model_id` y el `run_id`. Registrar por API generaría ids nuevos que no
  coinciden, así que se restaura el sqlite y los artifacts en su ruta exacta.
- **pydantic (`email-validator`) rechaza los TLD de uso especial**: un usuario
  semilla con dominio `.local` pasa el registro pero rompe la validación del
  `Principal` en runtime.
- El **partial export** de Keycloak excluye las cuentas humanas pero sí incluye
  `service-account-*` con sus `clientRoles`, que es exactamente lo que hacía falta.

## Open questions

- **`KC_HOSTNAME`/`KC_ISSUER`**: el `iss` del token cambia según el puerto por el
  que se entre a Keycloak (`:8080` interno vs `:8180` publicado). Hoy no rompe
  porque el password grant es server-side, pero cualquier flujo desde el browser
  lo pega. Pinchar `KC_HOSTNAME` a una URL absoluta toca `KC_ISSUER` en los cuatro
  `.env.dev`.
- **`users` y `analytics` reciben `cryptography` por transitividad** y no la
  declaran; el lock los protege hoy, pero cualquier regeneración los rompe.
- **Las migraciones de properties no crean la extensión PostGIS**; las de catalog
  sí. Solo funciona porque la imagen `postgis/postgis` la habilita en la DB que
  crea `POSTGRES_DB`.
- **Las 18.233 properties del seed viajan en `unverified`**, así que ese estado
  deja de ser una particularidad de una máquina y pasa a ser el arranque del
  proyecto.
- **Cómo se generó el `.pbf`** (un `osmium extract` con el bbox de Bogotá) no está
  documentado en ningún lado del repo.
- **Cómo viajan los siete secretos** entre máquinas sigue sin decidirse.

## Next steps

- Completar las claves de R2 en `.env.local` y correr `make bootstrap` real contra
  el bucket — hasta ahora solo se probaron sus guardas.
- **Ensayo de migración completo**: clone limpio, bootstrap y `up` desde cero. Es
  lo único que falta para cerrar el objetivo, y siempre encuentra cosas que
  ninguna revisión encuentra.
- Mergear `feat/front-admin-panel` cuando esté el refactor DRY: se verificó que
  el trabajo de infra es ortogonal (no toca migraciones, settings ni archivos de
  código compartidos), y el único choque es el `last-verified` de `open-items.md`.
