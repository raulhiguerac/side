---
title: "ADR-0010 — La verificación es reversible y el takedown es un cambio de status, no un estado nuevo"
status: stable
last-verified: 2026-08-02
owners: [properties-service]
related:
  - "[[properties-service-admin]]"
  - "[[properties-service-listing]]"
  - "[[adr-property-edit-fixed-fields]]"
  - "[[frontend-admin-panel]]"
  - "[[open-items]]"
sources: [../../../sources/properties-service/2026-08-02-moderation-lifecycle-verified-not-terminal.md]
decision-date: 2026-08-02
decision-status: accepted
---

# ADR-0010 — La verificación es reversible y el takedown es un cambio de status, no un estado nuevo

## Contexto

`VerificationStatus.verified` era **terminal**: no tenía ninguna transición de salida. Eso deja dos casos sin respuesta:

1. Una property aprobada que **después** viola las normas. No había forma de quitarle el sello sin tocar la DB.
2. Una property aprobada cuyo **contenido cambia** después. El dueño puede reemplazar el juego de fotos completo sobre algo ya verificado, así que lo aprobado deja de ser lo publicado.

La pregunta de producto que lo destapó fue si hacía falta un estado tipo "eliminada" para el caso de la violación.

## Decisión

**1. `verified` deja de ser terminal.** Sale a `pending` (volver a la cola) y a `rejected` (perder el sello). La única transición prohibida desde ahí es volver a `unverified`, que existe solo como estado inicial y al que nada apunta.

**2. Bajar una publicación no es un estado de verificación: es `ListingStatus: active → inactive`.** No se agrega ningún estado nuevo. Publicación y verificación son ejes independientes y los dos ya existen; mezclarlos habría metido una preocupación de visibilidad dentro de la máquina de moderación.

El detalle que lo hace funcionar sin código extra: la máquina del dueño (`SetPropertyVisibilityUseCase`) solo hace `draft ↔ active`, así que desde `inactive` **solo un admin puede republicar**. `inactive` ya era un takedown de facto.

**3. `rejected` se reusa para la revocación post-aprobación.** No se introduce un `revoked` aparte.

**4. La degradación (`verified → pending`) la disparan solo los cambios de imágenes.** Vive en `degrade_verification` ([verification_guard.py](backend/properties-service/src/app/services/listing/helpers/verification_guard.py)), llamado por `ConfirmImageUploadsUseCase` y `DeletePropertyImagesUseCase` antes de su `commit`, dentro de la misma transacción: el cambio de fotos y la pérdida del sello entran o fallan juntos.

## Alternativas consideradas

- **Un estado nuevo (`removed` / `revoked`) para la violación post-aprobación.** Descartado: duplica en el eje de verificación algo que el eje de status ya resuelve, y separar "rechazada en la primera revisión" de "revocada después" solo paga si hay métricas de rechazo o un flujo de apelaciones que necesiten distinguirlas. Hoy no existen.
- **Degradar también al editar la `description`.** Descartado por ahora: mandaría properties a una cola que todavía no se trabaja, y el spam de texto se ataca mejor con reportes que con re-verificación preventiva. De los cinco campos que quedaron editables ([[adr-property-edit-fixed-fields]]), ninguno de los otros cuatro —precio, moneda, admin fee, condición— cambia lo que se verificó del inmueble.
- **Que la degradación pase por `_ALLOWED_TRANSITIONS`.** Descartado: la tabla valida transiciones que **alguien pide**, y acá origen y destino están fijos en el código. El `if` sobre `verified` además da la idempotencia gratis; la versión con tabla necesitaría ese mismo `if` igual.
- **Enganchar la degradación en `request_presigned_urls`.** Descartado: ahí no aterriza ninguna foto, así que castigaría a alguien que abrió el formulario y se arrepintió.

## Consecuencias

- ✅ Aprobar deja de ser irreversible. Un error de moderación se corrige por la API en vez de por SQL.
- ✅ Reemplazar las fotos de una property verificada la devuelve a la cola automáticamente, sin que nadie tenga que notarlo.
- ✅ No se agregó ningún estado ni ninguna columna: la máquina de status y la de verificación siguen siendo las mismas dos.
- ❌ Una property se puede resolver varias veces y **solo la última sobrevive** en `verified_by` / `rejection_reason`. No hay historial de moderación; eso necesitaría una tabla de eventos (ver [[open-items]]).
- ❌ El worker de import no pasa por esto: construye las filas en `pending` directamente, así que nacer en un estado sigue sin ser una transición.

## Claims

- `VerifyPropertyUseCase._ALLOWED_TRANSITIONS` mapea `verified → [pending, rejected]` ([verify.py:13-18](backend/properties-service/src/app/services/admin/use_cases/moderation/verify.py#L13-L18)).
- `unverified` no es destino de ninguna transición declarada en `VerifyPropertyUseCase._ALLOWED_TRANSITIONS` ([verify.py:13-18](backend/properties-service/src/app/services/admin/use_cases/moderation/verify.py#L13-L18)).
- No existe ningún `VerificationStatus` ni `ListingStatus` llamado `removed` o `revoked` ([listing.py:34-56](backend/properties-service/src/app/models/listing.py#L34-L56)).
- `SetPropertyVisibilityUseCase._ALLOWED_TRANSITIONS` solo declara `draft → active` y `active → draft`, así que el dueño no puede salir de `inactive` ([set_property_visibility.py:15-18](backend/properties-service/src/app/services/listing/use_cases/property_core/set_property_visibility.py#L15-L18)).
- `degrade_verification` solo escribe cuando `verification_status == verified`, y en ese caso lo pasa a `pending` ([verification_guard.py](backend/properties-service/src/app/services/listing/helpers/verification_guard.py)).
- `degrade_verification` no commitea: muta el modelo y deja la transacción al caller ([verification_guard.py](backend/properties-service/src/app/services/listing/helpers/verification_guard.py)).
- `ConfirmImageUploadsUseCase` y `DeletePropertyImagesUseCase` llaman `degrade_verification` antes de su `commit` ([confirm_image_uploads.py](backend/properties-service/src/app/services/listing/use_cases/images/confirm_image_uploads.py), [delete_property_images.py](backend/properties-service/src/app/services/listing/use_cases/images/delete_property_images.py)).
- `RequestPresignedUrlsUseCase` y `UpdatePropertyUseCase` no llaman `degrade_verification` ([request_presigned_urls.py](backend/properties-service/src/app/services/listing/use_cases/images/request_presigned_urls.py), [update_property.py](backend/properties-service/src/app/services/listing/use_cases/property_core/update_property.py)).
