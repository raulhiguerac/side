---
title: AVM Form — neighborhood resolution, place-selected emit, and /predict wiring
captured-from: conversation
captured-on: 2026-05-29
participants: [raul, claude]
---

## Context
Wired the AVM multi-step form end-to-end: GMaps Places autocomplete → neighborhood resolution → real-time map marker → POST /predict. Session was run in learning mode (user implemented, Claude reviewed).

## Key conclusions

### AvmForm.vue
- `neighborhood = ref<string | null>(null)` holds the resolved neighborhood name reactively.
- `watch(place, async (val) => { ... })`: guard `if (!val) return`; emit `place-selected` with `val` **before** `await getNeighborhood` so the map marker paints immediately; then assign `neighborhood.value`.
- `onSubmit` guards on `payload && place.value && neighborhood.value` — won't fire if neighborhood hasn't resolved yet.
- `defineEmits` has two events: `"place-selected": [data: { place: SelectedPlace }]` and `submit: [data: { payload, place, neighborhood: string }]`. Event names with hyphens need quotes as TS object keys.

### DevPlaygroundView.vue
- `center = ref<[number, number]>([...])` and `marker = ref<MarkerData | null>(null)` — both reactive.
- `onPlaceSelected` updates both `center.value` and `marker.value` from `data.place.latitude/longitude`.
- Template: `:markers="marker ? [marker] : []"` — avoids passing `null` into the array.
- `fetchPredict(payload: AvmPredictRequest): Promise<number>` — local function (not a composable; single call, no shared state). Uses `axios.post(url, payload, { withCredentials: true })`. Returns `res.data.predicted_price`.
- `onSubmit` is `async`; wraps `price.value = await fetchPredict(avmPayload)` + `showResult.value = true` in try/catch; `barrio.value = data.neighborhood` (no longer hardcoded).
- `AvmPredictRequest` interface added to `useAvmForm.ts`, extends `AvmFormPayload` with `lat`, `lon`, `barrio_ideca`.

### Analytics service — CORS fix
- `allow_origins=["*"]` is incompatible with `withCredentials: true` (browser blocks it).
- Fixed in `src/app/main.py`: `allow_origins=["http://localhost:8080"]` + `allow_credentials=True`.

### Analytics service — year_built null bug
- MLflow schema was inferred from `_make_raw_input_example()` in `trainer.py` which has `year_built: 2012` (non-null int) → MLflow marks it `long required`.
- Model feature engineering (`_year_to_antiguedad`) handles `None` → `'sin especificar'` correctly, but schema validation rejects null before reaching it.
- Pragmatic workaround: in `avm_model_adapter.py`, replace `year_built: None` with `0` after `model_dump` (2026 years of age falls outside all bins → `'sin especificar'`).

## Open questions
- None.

## Next steps
- Re-register AVM model with `year_built: None` in `_make_raw_input_example()` so MLflow infers it as nullable — eliminates the need for the `0` workaround in the adapter.
- Implement `year_built: 0` workaround in `avm_model_adapter.py` until model is re-registered.
- Optional: add `flyTo` animation in `MapUser.vue` (watch `center` prop, call `leafletObject.flyTo`).
