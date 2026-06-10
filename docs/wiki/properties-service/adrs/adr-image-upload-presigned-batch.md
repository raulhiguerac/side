---
title: ADR-0001 — Upload de imágenes vía presigned URLs + batch
status: stable
last-verified: 2026-05-28
owners: [properties-service]
related:
  - "[[properties-service-listing]]"
  - "[[properties-service-architecture]]"
sources: [../../../sources/properties-service/2026-05-28-foundational-exploration.md]
decision-date: 2026-05-28
decision-status: accepted
---

# ADR-0001 — Upload de imágenes vía presigned URLs + batch

## Contexto

Cada propiedad lleva hasta `MAX_IMAGES_PER_PROPERTY` (20) fotos. Dos preguntas de diseño:

1. ¿Los bytes de las imágenes pasan por el backend (multipart al servicio → servicio sube a storage) o el cliente sube directo al object storage?
2. ¿Cómo se mantiene consistencia entre "el cliente subió N archivos" y "la DB registra esas N imágenes", si la subida ocurre fuera del request del backend?

## Decisión

- **El cliente sube directo a MinIO/S3** usando URLs presignadas PUT — los bytes nunca pasan por properties-service.
- **Protocolo de batch en tres pasos**:
  1. **Request** (`POST /properties/images/presigned-urls`): el servicio verifica ownership + cuenta, genera keys `{property_id}/{uuid}`, crea un `PropertyImageUploadBatch` con `expected_keys` y `expires_at`, pide las URLs al storage, y marca el batch `ready`.
  2. **Upload**: el cliente hace PUT directo a cada `upload_url`.
  3. **Confirm** (`POST /properties/{id}/images/confirm`): el servicio valida el batch (existe, consistente con la property, no expirado, en estado `ready`, `confirmed_keys ⊆ expected_keys`) y materializa los `PropertyImage`.
- **State machine del batch**: `pending → ready → confirmed`, con ramas `expired` (TTL vencido) y `failed` (error de storage al generar URLs, o confirm sobre un batch `pending`).
- TTLs cortos (`IMAGE_UPLOAD_BATCH_TTL_SECONDS` = 5 min) para que batches abandonados expiren solos.

## Alternativas consideradas

- **Multipart al backend** — simple de razonar, pero el servicio se vuelve un proxy de bytes: consumo de memoria/CPU, timeouts en uploads grandes, y acopla el throughput del API al ancho de banda de subida.
- **Presigned sin batch** (solo devolver URLs, registrar al vuelo) — sin forma de saber cuáles subidas tuvieron éxito; la DB se desincroniza del storage.
- **Webhook de S3/MinIO → backend** — elimina el confirm explícito, pero agrega infra (notificaciones del bucket) y un path async difícil de testear localmente.

## Consecuencias

- ✅ El backend nunca maneja bytes de imágenes — escala independiente del tamaño/numero de fotos.
- ✅ El confirm explícito mantiene DB y storage consistentes: solo se registran las keys que el cliente confirma y que estaban en el batch.
- ✅ Batches abandonados expiran por TTL — sin basura colgada indefinidamente.
- ✅ Ownership y límite de cuenta se chequean antes de emitir URLs.
- ❌ **Tres round-trips** para subir fotos (request, upload, confirm) — más chatty que un multipart.
- ❌ **Objetos huérfanos en storage posibles**: si el cliente sube pero nunca confirma, el archivo queda en MinIO sin fila en DB. No hay GC de objetos no confirmados hoy.
- ❌ La consistencia depende de que el cliente llame confirm con las keys correctas; un cliente buggeado puede confirmar menos de las que subió.

## Claims

- El flujo crea un `PropertyImageUploadBatch` con `expected_keys` y `expires_at` antes de devolver las URLs ([request_presigned_urls.py:51-59](backend/properties-service/src/app/services/listing/use_cases/images/request_presigned_urls.py#L51-L59)).
- El batch pasa por `pending → ready` antes de retornar; un error de storage lo marca `failed` ([request_presigned_urls.py:74-87](backend/properties-service/src/app/services/listing/use_cases/images/request_presigned_urls.py#L74-L87)).
- Confirm exige estado `ready` y que `confirmed_keys` sea subconjunto de `expected_keys` ([confirm_image_uploads.py:65-81](backend/properties-service/src/app/services/listing/use_cases/images/confirm_image_uploads.py#L65-L81)).
- El TTL del batch es `IMAGE_UPLOAD_BATCH_TTL_SECONDS` = 300s ([settings.py:31](backend/properties-service/src/app/core/config/settings.py#L31)).
- No hay GC de objetos subidos pero no confirmados al 2026-05-28.
