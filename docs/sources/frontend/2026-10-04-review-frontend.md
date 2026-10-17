---
title: Revisión de frontend (Kiro)
captured-from: external
captured-on: 2026-10-04
participants: [kiro]
---

# Revisión staff del frontend

## Resumen

Revisión de solo lectura de `frontend/src` con la lente de la skill `frontend-staff-review`: recorrido por rebanadas verticales (vista → componente → composable → `api/` → `types/` → endpoint en `constants/`), pasando el catálogo de smells Vue3+TS y las reglas de capas del proyecto por cada archivo.

El núcleo del panel admin (moderación, promociones, catálogo de barrios) sigue sólido y confirma lo que ya reportó la revisión del 2026-10-04: URL como fuente de verdad, descarte de respuestas fuera de orden con `requestToken`/`latestRequest`, transiciones servidas por el backend, paginación por offset con `total`. **Los tres bugs del feed/mapa de esa revisión están corregidos**: `useFeedMap` ya descarta respuestas viejas (`latestRequest`), `sortForMap` reemplazó el shuffle sesgado, y `MapView` tiene spinner y `EmptyState`.

Los hallazgos nuevos de esta pasada están todos en **la rebanada de escritura del dueño** (crear/editar propiedad y sus modales), que la revisión anterior no recorrió a fondo: modales que se cierran mientras guardan, un guardado sin estado de envío ni `:disabled`, una carga inicial sin manejo de error (spinner infinito), un fallo parcial de subida que navega como si todo hubiera salido bien, y un toggle de visibilidad que miente el estado y falla en silencio para `inactive`/`sold`/`rented`. A eso se suma duplicación de la cáscara de los modales de confirmación.

Total: **5 bugs media, 2 mejoras, 1 convención.** No se encontraron bugs de severidad alta nuevos; el único alta conocido (mapa del feed) ya está resuelto.

> Nota sobre contratos (rebanada 7): revisé `types/properties/*`, `types/feed/*` y `types/admin/*` contra su uso. Las dos desalineaciones de contrato que se ven a ojo (`AdminPropertyRow.currency` con 5 de 7 monedas; `PropertyCardUI` sin `currency`) ya están en `open-items.md`, así que no las reporto. No encontré una tercera divergencia que oculte un `null` o un nombre de campo distinto del schema Pydantic.

---

## Bugs

### [Bug · media] Los modales de subir y borrar fotos se cierran a mitad de la escritura

- **Dónde:** `frontend/src/components/properties/edit/UploadPropertyImagesModal.vue:5` y `:67` (`close`), `frontend/src/components/properties/edit/DeletePropertyImagesModal.vue:3` (`@update:model-value="close"`), vía `frontend/src/components/shared/BaseModal.vue:5` (`@click.self="$emit('update:modelValue', false)"`).
- **Escenario:** El dueño abre "Agregar fotos", selecciona 10 imágenes, pulsa "Subir fotos" y mientras los PUT a storage están en vuelo hace click en el backdrop del modal. `BaseModal` emite `update:modelValue=false` sin mirar `loading`, el `watch` de `modelValue` resetea `selectedFiles` y `error`, y el modal se desmonta. La subida sigue corriendo contra un componente ya cerrado: si termina OK el `@success` no refresca nada visible y el usuario no sabe que subió; si falla, el `error` se setea en un modal que ya nadie ve. Debería quedar bloqueado el cierre (backdrop incluido) mientras `loading` es `true`.
- **Por qué pasa:** La regla del proyecto dice que "los modales no se cierran mientras `saving` es `true`", pero ni `close()` ni el `@update:model-value` del `BaseModal` consultan `loading`. El botón de acción sí está `:disabled` mientras sube; la vía de escape por backdrop no.
- **Propuesta:** En `close()` de ambos modales, `if (loading.value) return;` (y en `DeletePropertyImagesModal`, idéntico con `loading`). Alternativa de raíz: que `BaseModal` acepte una prop `:dismissable` y no emita el cierre por backdrop cuando sea `false`.
- **Test sugerido:** Montar `UploadPropertyImagesModal` con `useImageUpload` mockeado en `loading=true`, disparar el `@click.self` del backdrop y afirmar que no se emitió `update:modelValue=false`.
- **Confianza:** alta

### [Bug · media] Guardar la edición de una propiedad no bloquea el botón ni muestra que está guardando

- **Dónde:** `frontend/src/components/properties/edit/PropertyEditActions.vue:11` (`<PrimaryButton @click="emit('save')">` sin `:disabled`/`:loading`) y `frontend/src/views/properties/edit/EditPropertyView.vue:131` (`handleSave`, sin `ref` de envío).
- **Escenario:** El dueño cambia el precio y pulsa "Guardar cambios". El PATCH tarda (conexión lenta). El botón sigue habilitado y sin feedback, así que vuelve a pulsarlo: se disparan dos `PATCH /v1/properties/{id}` concurrentes. En el mejor caso es trabajo repetido; si el segundo llega después de una navegación, es una escritura huérfana. Además, durante el guardado la UI no indica nada: parece colgada.
- **Por qué pasa:** `handleSave` no tiene un `saving = ref(false)` que envuelva el `try/finally`, y `PropertyEditActions` no recibe ni consume ese estado. El patrón de composable de escritura del proyecto (`saving` + `:disabled`) no se aplicó acá — a diferencia de `DeletePropertyImagesModal`, que sí lo hace.
- **Propuesta:** Agregar `const saving = ref(false)` en `EditPropertyView`, envolver el PATCH (`saving.value = true` … `finally { saving.value = false }`), pasar `:saving="saving"` a `PropertyEditActions` y en su `PrimaryButton` poner `:disabled="saving"` `:loading="saving"`. Guardar también `if (saving.value) return` al entrar a `handleSave`.
- **Test sugerido:** Montar `EditPropertyView` con `updateProperty` mockeado a una promesa pendiente; afirmar que tras el primer click el botón queda deshabilitado y que un segundo click no llama de nuevo a `updateProperty`.
- **Confianza:** alta

### [Bug · media] La vista de editar propiedad se queda en spinner infinito si la carga inicial falla

- **Dónde:** `frontend/src/views/properties/edit/EditPropertyView.vue:119-137` (`onMounted` → `fetchProperty()` sin `try/catch`; `isLoading` solo se apaga al final del happy path).
- **Escenario:** El dueño entra a `/properties/:id/edit` y el `GET /v1/properties/{id}` falla (id inexistente, 404, red caída, backend 8002 abajo). `fetchProperty` lanza, el `onMounted` no lo atrapa, y como `isLoading.value = false` está en la última línea del `onMounted` (después del `await`), nunca se ejecuta: la pantalla queda con el spinner centrado para siempre, sin mensaje ni salida.
- **Por qué pasa:** `fetchProperty()` (la función reutilizable) no maneja error y el `onMounted` tampoco. Es el smell "loading que no se apaga si el await lanza: falta `finally`".
- **Propuesta:** Envolver el cuerpo del `onMounted` en `try/catch/finally`: en `catch` setear un `loadError` que el template muestre (banner + botón "Volver a mis propiedades"), y en `finally` apagar `isLoading`. Igual criterio que `AdminPropertyPreviewPanel`, que sí traduce el fallo a un `error` visible.
- **Test sugerido:** Montar `EditPropertyView` con `getProperty` mockeado para rechazar; afirmar que el spinner desaparece y aparece el mensaje de error.
- **Confianza:** alta

### [Bug · media] Una subida de fotos parcial o fallida al publicar no se distingue del éxito

- **Dónde:** `frontend/src/composables/properties/useImageUpload.ts:16-47` (`uploadImages`) y `frontend/src/views/properties/create/CreatePropertyView.vue:191-205` (`upload`, `uploadError` desestructurado y nunca renderizado).
- **Escenario (dos caras del mismo hueco):**
  1. *Fallo total:* el usuario publica, llega al paso de imágenes y pulsa "Publicar". Si todos los PUT fallan (`confirmed_keys.length === 0`) o `requestImageUploadUrls` da 500, `uploadImages` setea `error` y devuelve `false`; en la vista `upload()` solo navega si `success`, así que ante `false` **no pasa nada visible**: el spinner se apaga, el `uploadError` no se muestra en ningún lado, y la propiedad quedó publicada sin fotos sin que el usuario lo sepa. (Confirmo el Bug media de la revisión del 2026-10-04; sigue vigente.)
  2. *Fallo parcial:* de 10 fotos suben 6 y 4 fallan. `confirmed_keys` lleva 6, `uploadImages` confirma esas y devuelve `true`, y `upload()` navega a `/properties` como si todo hubiera ido bien. El usuario cree que publicó 10 fotos; subió 6 y nunca se le avisó.
- **Por qué pasa:** `useImageUpload` sí expone `error`, pero `CreatePropertyView` nunca lo renderiza (de ahí el warning `no-unused-vars` sobre `uploadError`), y `uploadImages` colapsa "todo bien" y "subieron algunas" en el mismo `return true`.
- **Propuesta:** (a) Renderizar `uploadError` como banner junto al botón "Publicar". (b) Que `uploadImages` devuelva el conteo (`{ confirmed, total }`) en vez de un booleano, y que la vista avise cuando `confirmed < total` ("Se publicó con N de M fotos; reintenta las faltantes") en lugar de navegar en silencio. (c) No vaciar `selectedFiles` cuando la subida no fue completa, para permitir reintento.
- **Test sugerido:** Mock de `requestImageUploadUrls` con 3 items y `fetch` que resuelve 2 OK y 1 fallo; afirmar que `uploadImages` reporta `confirmed=2,total=3` y que `CreatePropertyView` no navega y muestra el aviso.
- **Confianza:** alta

### [Bug · media] El toggle de visibilidad miente el estado y falla en silencio para `inactive`/`sold`/`rented`

- **Dónde:** `frontend/src/components/properties/cards/PropertyCard.vue:163` (`property.status === "active" ? "Activa" : "Borrador"`) y `:170` (`@click.stop="$emit('toggle-visibility', ...)"` sin gatear por estado); consumido en `frontend/src/views/properties/dashboard/MyPropertiesView.vue:77` (`:show-visibility-toggle="true"` para todas las filas) y resuelto por `frontend/src/composables/properties/usePropertyVisibility.ts:6-13` (traga el error).
- **Escenario:** En "Mis Propiedades", el dueño abre la pestaña "Vendidas" (o "Inactivas"/"Arrendadas"). Cada card muestra el toggle de visibilidad con la etiqueta **"Borrador"** y el switch apagado, aunque la propiedad esté `sold`. Si pulsa el switch, se llama `POST /v1/properties/{id}/visibility`; el backend solo define transiciones de dueño `draft↔active` (`OWNER_VISIBILITY_TRANSITIONS` en `backend/.../status_transitions.py`), así que desde `sold`/`rented`/`inactive` devuelve 409 `InvalidStatusTransitionError`. `usePropertyVisibility.toggleVisibility` atrapa, loguea y devuelve `false`; `onToggleVisibility` corta sin tocar nada. El usuario pulsa un control que parece activo y no ocurre nada, sin explicación.
- **Por qué pasa:** La card trata `status` como binario (`active` vs "todo lo demás = Borrador") en la etiqueta y muestra el toggle de forma incondicional, pero el estado del listado tiene 5 valores y solo `draft`/`active` son conmutables por el dueño. El label `? "Activa" : "Borrador"` es incorrecto para los otros tres estados; el click sobre ellos es un no-op silencioso.
- **Propuesta:** Mínimo: renderizar el toggle solo cuando `status === 'active' || status === 'draft'` (y para el resto mostrar el badge de estado, no el switch). La etiqueta debería salir de `LISTING_STATUS_LABELS[status]`, no del ternario binario. Así el dueño no ve "Borrador" sobre una vendida ni un control que el backend va a rechazar.
- **Test sugerido:** Montar `PropertyCard` con `status: "sold"` y `show-visibility-toggle`; afirmar que el switch no se renderiza (o está deshabilitado) y que la etiqueta dice "Vendida", no "Borrador".
- **Confianza:** alta

---

## Mejoras

### [Mejora · media] El feed en lista sigue sin descartar respuestas fuera de orden al filtrar

- **Dónde:** `frontend/src/composables/feed/useFeed.ts:60-91` (`load`), disparado desde `frontend/src/views/properties/feed/FeedView.vue:80` (`onSubmit`).
- **Beneficio / riesgo que elimina:** `load()` resetea cursores y `pageCache` y luego hace `data.value = properties.items` sin token de request. Si el usuario aplica un filtro (respuesta lenta), cambia de opinión y aplica otro antes de que vuelva el primero, la respuesta vieja puede pisar a la nueva — el mismo invariante que ya se cerró en `useFeedMap`, pero acá sin resolver. Menor severidad que el del mapa porque el disparo es un click deliberado en "Aplicar filtros", no un drag continuo, y porque `fetchFeed` traga sus errores devolviendo `{ items: [], next_cursor: null }`, así que el peor caso es ver resultados de un filtro anterior, no un crash. (Re-cito el hallazgo del 2026-10-04; sigue vigente y ahora es la única carga por selección sin el patrón que el resto del código ya adoptó.)
- **Propuesta:** Mismo `let latestRequest = 0; const request = ++latestRequest` que `useFeedMap`, chequeado antes de asignar `data`/`nextCursor` en `load` y `loadNext` (la rama no cacheada).
- **Confianza:** media

### [Mejora · baja] La cáscara de los modales de confirmación está copiada en cuatro archivos

- **Dónde:** `frontend/src/components/properties/dashboard/DeletePropertyModal.vue`, `frontend/src/components/properties/edit/DeletePropertyImagesModal.vue`, `frontend/src/components/properties/edit/UploadPropertyImagesModal.vue` y `frontend/src/components/admin/properties/promotions/RemovePromotionModal.vue`.
- **Qué varía:** el ícono y el título de la cabecera, el texto del cuerpo, el label del botón de acción y su variante de color (rojo peligro vs primario). Lo repetido es la estructura: `BaseModal` + cabecera (ícono en círculo + título) + pie con "Cancelar" y un botón de acción `:disabled` mientras `loading`, los dos ocupando `flex-1`.
- **API propuesta (2-4 líneas):** un `ConfirmModal` dumb: props `modelValue`, `title`, `icon`, `confirmLabel`, `variant: 'primary'|'danger'`, `loading`, `confirmDisabled`; slot default para el cuerpo; emite `confirm` y `update:modelValue`. Internamente bloquea el cierre por backdrop mientras `loading` (lo que de paso cierra el Bug media de los modales de fotos de arriba para todos a la vez).
- **Riesgo de no hacerlo:** el fix del cierre-mientras-guarda hay que aplicarlo hoy en cuatro archivos, y cada modal nuevo (editar/geometría/desactivar barrio, que `open-items` marca pendientes) nace copiando la misma cáscara y arrastrando el mismo bug.
- **Confianza:** alta

---

## Convención

### [Convención · baja] `watch(selected)` en `FeedFilters` carga barrios sin descartar la respuesta vieja

- **Dónde:** `frontend/src/components/properties/feed/FeedFilters.vue:270-277` (`watch(selected, async (cityIds) => { … await loadNeighborhoods(localities) })`) y `frontend/src/composables/shared/useMultiselect.ts:40-52` (`load` reconstruye `cities` desde las localidades que recibe).
- **Regla / análisis:** `domain-invariants.md` (§frontend) exige que "una respuesta vieja nunca pisa a una nueva: toda carga que dependa de una selección descarta las respuestas fuera de orden". El `watch` dispara `loadNeighborhoods` en cada cambio de ciudades seleccionadas; `useNeighborhoodMultiselect.load` no lleva token, así que si una selección lenta (ciudad A) resuelve después de una rápida (ciudad B), `cities.value` queda con los barrios de A mientras el multiselect ya muestra B — el usuario ve barrios de una ciudad que ya no tiene seleccionada. Probabilidad baja (son clicks deliberados y el catálogo cachea por localidad en `sessionStorage`, lo que acorta la ventana), de ahí la severidad; pero es el mismo patrón que el resto del front ya resuelve con `latestRequest`.
- **Propuesta:** Agregar un token a `useNeighborhoodMultiselect.load` (o al `watch`): capturar `const request = ++latestRequest` al entrar y descartar la asignación de `cities.value` si al volver `request !== latestRequest`.
- **Confianza:** media

---

## Revisado sin hallazgos

Rebanadas recorridas que cumplen los invariantes y las reglas de capas:

- **Auth (store, interceptor, guard).** `stores/auth.ts`, `api/clients/interceptors.ts` y `router/index.ts`: refresh silencioso con cola module-level (`isRefreshing`/`failedQueue`), `AUTH_ENTRYPOINTS` excluye login/register/logout del retry, `forceLogout` solo desloguea si había sesión, guard con `requiresAuth`/`requiresAdmin` y el paso extra de `fillUserData` para la race del admin por link directo. `withCredentials: true` en los clientes de users/catalog/properties; `avm` sin cookie, correcto. Las baseURLs caen al proxy `/api/*` por defecto (`config/index.ts`). (El `.env.development` que saltea el proxy ya está en `open-items`.)
- **Panel admin de moderación.** `AdminModerationView.vue` + `useUrlFilters` + `useModerateProperty` + `AdminModerationForm.vue`: URL como fuente de verdad, borrador acumulado, dos PATCH con reporte de fallo parcial, el formulario se resetea al cambiar de property (`watch` sobre `[status, verificationStatus]`), botón `:disabled` por `canSave`/`saving`, transiciones del backend sin recalcular en el front.
- **Preview panel admin.** `AdminPropertyPreviewPanel.vue`: descarta respuestas fuera de orden con `requestToken` en los dos `await`, estados `loading`/`error`/vacío, y `refresh()` para releer tras moderar (el id no cambia). Sin `NearbyPlaces` a propósito.
- **Catálogo de barrios admin.** `AdminNeighborhoodPanel.vue`, `useNeighborhoodDetail`, `useNeighborhoodNeighbors`: `latestRequest` en la carga de vecinos y `clear()` que invalida el token al cambiar de barrio; los vecinos degradan a vacío si el bbox excede el tope del backend. (Las acciones editar/geometría/desactivar sin UI real ya están en `open-items`.)
- **Paginación admin por offset.** `useAdminProperties`: `serverTotal` del backend, `reload()` que refetchea la página actual sin resetear a la 1, `next()` que solo pide si la página no está cacheada, guardas `if (loading.value) return`.
- **Feed / mapa (los tres bugs del 2026-10-04 están corregidos).** `useFeedMap` descarta respuestas viejas (`latestRequest`), `utils/feedMap.ts#sortForMap` reemplazó el `data.sort(() => Math.random())` sesgado y ya no muta la respuesta de axios, y `MapView.vue` tiene spinner de primera carga y `EmptyState`. (Que `MapView`/`FeedView` sigan sin estado de error de red ya está en `open-items`.)
- **Capas HTTP.** No hay rutas `/v1/...` literales fuera de `constants/*Endpoints.ts` (grep sin resultados), ni clientes axios importados fuera de `api/`: los `import axios from "axios"` en composables/vistas son todos para `axios.isAxiosError` (narrowing de error), salvo el `axios.get` a ipapi en `stores/user.ts` (third-party documentado) y el `axios.post` del refresh en el interceptor (deliberadamente fuera de la instancia para no reentrar).
- **Tailwind.** No se encontraron clases armadas por template string; las condicionales usan strings completos en `:class`.
