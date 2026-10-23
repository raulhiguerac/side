---
title: Qué le falta al front frente al back, la caché de eslint del dev server y el verde de los botones
captured-from: conversation
captured-on: 2026-10-17
participants: [author, claude]
---

## Context
Se cruzaron los endpoints que declaran los routers del backend con `constants/*Endpoints.ts` y las funciones de `api/` del front. Salieron además un falso positivo de lint en el dev server y una duda sobre el color de los botones.

## Key conclusions
- **Endpoints del back sin consumir en el front:**
  - users: `POST /v1/auth/reset-password/confirm` y `POST /v1/users/reactivation/{request,confirm}`. Faltan las vistas `/reset-password` y `/reactivate`.
  - properties: `POST /v1/admin/properties/{id}/estimated-price`. No hay UI admin, y leer el precio estimado está bloqueado porque ningún schema lo expone.
  - catalog: `GET /v1/localities/by-admin-division` y `/by-id` no hacen falta hoy. `resolve-neighborhood` está por deprecarse. `by-coordinates/bulk` y users `/users/resolve` son de servicio a servicio.
  - Ninguna función de `api/` está sin importar. `deleteAccount()` apunta a un `DELETE /v1/users/me` que no existe; su uso está comentado.
- **Huecos del front verificados en código:**
  - `useFeedMap.ts` no tiene `catch` y `useFeed.ts` solo hace `logger.error`. El feed tiene loading pero no estado de error.
  - `@vueform/multiselect` sigue sin declararse en `package.json`.
  - El detalle de propiedad no tiene forma de contactar al dueño.
  - `uploadError` de `useImageUpload` no se usa en `CreatePropertyView.vue:176`, así que un fallo al subir imágenes no se ve. Hay además un `propertyId.value!` en `:229`.
  - El comentario `<!-- Barrio detectado (mock) -->` en `AvmForm.vue:245` está desactualizado: el barrio se resuelve contra catalog.
- **Partes del wiki desactualizadas:**
  - La tabla de estado de `frontend.md` es del 2026-05-21.
  - En `open-items` siguen abiertos ítems ya hechos: las tabs de localidades, divisiones y países (ya no queda `EmptyState` en `views/admin`), el form de publicar con `/properties`, el panel de moderación y la vista de detalle.
- **Falso positivo de lint en el dev server:** `npm run serve` reportaba 230 errores `prettier/prettier` en 17 archivos, mientras `eslint --ext .ts,.vue src` y `prettier --check` daban limpio.
  - Causa: la caché de `eslint-webpack-plugin` (`node_modules/.cache/eslint/<hash>.json`) valida por mtime y tamaño, y el plugin de Vue CLI la invalida solo si cambia la versión de eslint o el `package.json`, no el resultado de prettier.
  - Se reprodujo con una copia de la caché y se arregló borrando `node_modules/.cache/eslint` y reiniciando `serve`.
- **Verde de los botones:**
  - `BaseButton` en su variante primary usa `primary-strong` (`#15803D`), por contraste.
  - El CTA del home ("Avalúa tu propiedad gratis") usa `bg-brand-primary` (`#22C55E`) con clases a mano.
  - Contraste medido: `#22C55E` con texto blanco da 2,28 y con `brand-dark` 6,34; `#16A34A` con blanco da 3,30; `#15803D` con blanco da 5,02. AA pide 4,5 para texto de 14 px semibold.

## Open questions
- **El verde de los botones, pospuesto por el autor.** Opciones:
  - `#22C55E` con texto `brand-dark` (recomendada);
  - `#22C55E` con texto blanco (no pasa AA);
  - todo en `primary-strong`, pasando el CTA del home a `BaseButton`.

## Next steps
- Archivar en el wiki la revisión de endpoints y corregir los ítems desactualizados de `open-items` y la tabla de `frontend.md`.
- Agregar la trampa de la caché de eslint al runbook del front.
- Mostrar `uploadError` en el paso de imágenes y quitar el `!` de `upload()`.
