---
title: Refactor de components/properties + nueva PublicProfileView (mock)
captured-from: conversation
captured-on: 2026-06-21
participants: [author, claude]
---

## Context

Antes de construir la vista de perfil público de un usuario/publicante, se reorganizaron los componentes de `components/properties/` (estaban todos sueltos en un solo folder) y se maquetó `PublicProfileView.vue` con datos 100% mock, siguiendo el patrón de paginación local ya usado en `MapView`/`useFeedMap`.

## Key conclusions

- `components/properties/` se reorganizó en subcarpetas por dominio: `cards/` (`PropertyCard.vue`, `HouseCard.vue` — este último sin uso actual), `photos/` (`PropertyPhotoGrid.vue`, `PhotoGalleryPopup.vue`), `detail/` (`PropertyOverview.vue`, `NearbyPlaces.vue`), `feed/` (`FeedFilters.vue`). Imports actualizados en `FeedView.vue`, `MapView.vue`, `MyPropertiesView.vue`, `PropertyDetailView.vue` (todos usan alias `@/`, sin rutas relativas).
- Nueva ruta pública `/users/:userId` → `views/public/PublicProfileView.vue`, registrada en `router/routes/public.ts`, `requiresAuth: false`.
- Backend ya tiene el endpoint necesario para esta vista: `GET /v1/properties/users/{user_id}` (público, sin auth) → `GetPublicUserPropertiesUseCase` → devuelve `list[PropertyCardSchema]`. No expone datos del usuario (nombre, avatar, fecha de registro) — eso se mockea en frontend hasta que exista un endpoint público en `users-service`.
- Se acordó separar en dos composables cuando se conecte la data real: `useUserPublicProfile(userId)` (perfil/avatar/bio, mock por ahora) y `usePublicUserProperties(userId)` (listings reales).
- Diseño del header: se descartó el layout original (foto grande, mucho espacio vacío) por una tarjeta compacta — foto `w-28 h-28` (se probó `w-16 h-16` más chica pero se revirtió), nombre + badge "verificado" (`BadgeCheck` de `@lucide/vue`), rating con ícono `Star`, stats en una sola línea separadas por `·`, y 3 CTAs mock (WhatsApp/Mensaje/Llamar) con iconos `MessageCircle`/`MessageSquare`/`Phone`. Se evitaron emoji en favor de SVG/lucide por compatibilidad cross-browser.
- Diseño de `PropertyCard.vue` (componente compartido, afecta también Feed/Map/MyProperties): precio subido a `text-2xl` y reordenado antes del título (que ahora es `text-brand-muted`, sin negrita); separadores `divide-x` entre hab/baños/m²; toda la card ahora tiene `cursor-pointer` + `hover:-translate-y-1` además del shadow/zoom que ya tenía.
- Se probó un overlay con gradiente sobre la foto (ubicación + m² encima de la imagen) y se revirtió — no se leía bien incluso subiendo opacidad/altura del gradiente. Ubicación volvió a su lugar original debajo del título.
- Paginación: el endpoint público de propiedades no pagina (devuelve todo). Con datasets grandes (ej. owner con 450 listings vía bulk admin, no representativo de un agente real) esto no escala. Se decidió agregar paginación server-side **offset/limit** (no cursor-based como el feed) porque `owner_id` ya está indexado, `Property.created_at` (vía `AuditMixin`) sirve para ordenar estable, y el offset es invertible — no hace falta el patrón de cursor-stack que usa `useFeed.ts`. Detalle de la sub-tarea ya documentado en `docs/wiki/_shared/open-items.md` bajo el ítem "Página pública de perfil del publicante".

## Open questions

- Alcance final del perfil público real (avatar, bio, rating, contacto) — requiere nuevos campos/UCs en `users-service` expuestos a terceros. No decidido todavía.

## Next steps

- El dev va a implementar la paginación offset/limit manualmente (router → use case → port → repo en `properties-service`, luego el composable real en frontend) para practicar — no lo implementó Claude.
- Mejoras visuales de `PropertyCard.vue` quedaron acotadas a precio/título/separadores/hover; overlay sobre foto, badges con ícono, y layout en grid quedaron fuera de alcance por ahora.
