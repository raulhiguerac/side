---
title: Limpieza de assets, iconos de lucide en el onboarding, ilustraciones de la mascota y estado del cierre del MVP
captured-from: conversation
captured-on: 2026-10-24
participants: [author, claude]
---

## Context
Después de cablear el reset se revisó contra el código la lista "MVP — cierre antes de la infra" de open-items. Mientras se armaba el panel izquierdo de `ResetPasswordView` salieron dos temas más: qué assets se usan y cuánto pesan, y cómo se hacen las ilustraciones.

## Key conclusions
- **Estado del cierre del MVP al 2026-10-24:**
  - `@vueform/multiselect` sigue sin estar declarado en `package.json`.
  - El ítem del CSS de `App.vue` ya estaba cerrado.
  - Queda un solo `alert()` (`DeletePropertyModal.vue:82`); los de `SettingsAccount` están comentados y open-items todavía dice cuatro.
  - `FeedView` no tiene estado de error: `useFeed` loguea y traga el error.
  - No hay `vitest` ni CI del front; `.github/workflows` solo tiene la del backend.
  - En `workers/` de properties sigue solo el bulk worker, sin consumer de `price-predicted`.
- **Orden propuesto para cerrar el MVP:** multiselect → bug de change-password → reactivación → prueba en navegador de las tabs de catálogo → errores visibles (antes hay que decidir un sistema de toasts) → Vitest y CI. El worker del AVM va en paralelo, del lado del back.
- **Los assets no van a un CDN aparte.** Cloudflare Pages ya sirve `dist/` desde su red, y el build les pone hash a los nombres (`img/<nombre>.<hash>.svg`), así que se cachean sin vencimiento. R2 queda para el contenido que no viaja con el código: fotos de usuarios e imágenes de propiedades.
- **El problema de los SVG es el peso.** `reset-password.svg` pesa 620 KB (244 KB con gzip, 894 paths) y `secure-account.svg` 582 KB. Las opciones son pasarlos por SVGO o exportarlos a WebP.
- **Se borraron los 16 archivos sin uso de `src/assets/`.** Se buscó cada nombre con y sin extensión, y también rutas armadas con variables. Quedan `logo.svg`, `reset-password.svg`, `secure-account.svg` y `landing_cover.png`.
- **`house.svg` y `apartment.svg` eran iconos de lucide copiados como archivo**, y además, al ir en un `<img>`, `currentColor` no hereda el color. `PropertyTypeSelector` ahora usa `Home` y `Building2` de `@lucide/vue` con `<component :is>`, igual que `StepTipo`, con `ChoiceOption<PropertyType>[]` y `PROPERTY_TYPE_LABELS`. El icono toma el color según el estado de la tarjeta, y los dos SVG se borraron.
- **Las ilustraciones de la mascota no se pueden dibujar a mano.** La casita verde con cara y guantes son imágenes generadas y vectorizadas. Un SVG escrito a mano en la misma paleta no se parece, y se descartó. Las ilustraciones nuevas de la mascota tienen que salir de la misma herramienta.
- El panel izquierdo de `ResetPasswordView` usa `secure-account.svg`, la misma de Ajustes → Seguridad, con `alt=""` y el texto "¡Encontramos las llaves!".

## Open questions
- Si el título del panel de reset cambia a algo que vaya con el candado.
- Si hace falta una ilustración propia para reset, generada con la misma herramienta que las otras.

## Next steps
- Optimizar `reset-password.svg` y `secure-account.svg` con SVGO, o pasarlos a WebP si siguen pesados.
- Corregir en open-items el ítem de `alert()`: queda uno, no cuatro.
- Declarar `@vueform/multiselect` en `package.json`.
