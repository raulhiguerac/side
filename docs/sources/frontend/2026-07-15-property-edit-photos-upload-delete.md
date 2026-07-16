---
title: Property edit view — upload/delete photos feature
captured-from: conversation
captured-on: 2026-07-15
participants: [author, claude]
---

## Context

Built the "add/delete photos" flow for an already-published property inside `EditPropertyView.vue`, reusing the existing backend endpoints (presigned-urls, confirm, batch delete) originally built for the create flow.

## Key conclusions

- `PropertyImageCard` was missing an `id` field on both sides — added `id: uuid.UUID` to the backend schema (`services/shared/schemas/property_card.py`) and `id: string` to the frontend type (`types/feed.ts`). Required because the delete endpoint needs `image_ids`, and nothing identified individual images before this.
- `useImageUpload.ts` composable decoupled from `router.push` — `uploadImages()` now returns a `boolean` (success/fail) instead of navigating internally. `CreatePropertyView.vue` now does the navigation itself after awaiting the call. This made the composable reusable for the edit flow without dragging create-flow-specific behavior along.
- Added `LIMITS.MAX_IMAGES_PER_PROPERTY = 20` to `frontend/src/config/index.ts` as the single source of truth, replacing a hardcoded local `const MAX = 20` inside `StepImagenes.vue`.
- `StepImagenes.vue`'s cap became a required `max: number` prop instead of reading the config directly — each orchestrating view passes its own value: `CreatePropertyView.vue` passes the global `LIMITS.MAX_IMAGES_PER_PROPERTY` (property always starts at 0), while `UploadPropertyImagesModal.vue` passes the dynamic `imagesAllowed` (remaining slots on an existing property).
- `StepImagenes.vue` also gained a `hasExistingPhotos: boolean` prop — the "Portada" (cover) badge on the first selected file only renders when the property currently has zero existing photos. Prevents mislabeling a newly added file as cover when the property already has photos (and possibly an existing cover) elsewhere.
- Component boundary: `PropertyPhotosCard.vue` stays presentational — owns the "Fotos N/20" header and the Agregar/Eliminar buttons, computes `imagesAllowed` locally as pure derived UI, and only emits `add-photos`/`delete-photos`. `EditPropertyView.vue` owns all state (`showUploadModal`/`showDeleteModal` refs) and a `fetchProperty()` refetch function that intentionally does **not** reset `form`, to avoid clobbering in-progress edits when a photo modal closes.
- Two new modal components: `UploadPropertyImagesModal.vue` (wraps `StepImagenes` + `useImageUpload`, `BaseModal` size `3xl`) and `DeletePropertyImagesModal.vue` (5-column grid of existing images with a per-photo trash icon that toggles membership in a local `selectedIds: string[]`, plus a single "Eliminar (N)" trigger).
- Backend's delete endpoint (`DELETE /v1/properties/{id}/images`) is **batch-only** — one call with an `image_ids` array, no per-image endpoint. This is why the delete UI uses multi-select + one confirm button rather than an instant per-click delete.
- `DeletePropertyImagesModal.vue` hardening: a `loading` boolean guards `handleDelete` against double-submit races, wrapped in `try/catch/finally` with a visible error message on failure; images got `alt` text; selected photos get `opacity-40` visual feedback.
- Extracted a new `PrimaryButton.vue` (`components/shared/`) to deduplicate the green-gradient button style that had been copy-pasted inline across `PropertyPhotosCard.vue`, `UploadPropertyImagesModal.vue`, and `PropertyEditActions.vue`. It's a pure presentational wrapper (`disabled` prop + slot); callers pass their own `class` for padding/width and `@click`, both forwarded automatically via Vue's attrs fallthrough.
- Added `PROPERTIES_ENDPOINTS.images(id)` to `constants/propertiesEndpoints.ts` for the delete call. Note: presigned-urls/confirm endpoints remain inlined as string literals in `useImageUpload.ts` — this inconsistency was noted but not fixed.

## Open questions

- `CreatePropertyView.vue`'s "Publicar"/"Siguiente" buttons still duplicate the same green-gradient inline style and were **not** migrated to `PrimaryButton.vue` — only the three components explicitly in scope were touched.

## Next steps

None pending — add/delete photos in the edit flow is functionally complete end-to-end.
