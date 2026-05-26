---
title: Onboarding flow — full wiring & bug fixes
captured-from: conversation
captured-on: 2026-05-26
participants: [raul, claude]
---

## Context
The onboarding flow (intent → city → neighborhood → property_type) existed in both frontend and backend but was never properly wired end-to-end. Multiple integration bugs and mismatches were found and fixed in one session.

## Key conclusions

### Backend (users-service)
- `OnboardingIntent.intent` was typed as `OnboardingStep` (the step-tracker enum) instead of `AccountIntent` (buyer/seller/renter/explorer) — one-line fix in `schemas/onboarding.py`.
- `mark_completed` did a plain `flush()` on duplicate inserts, leaving the SQLAlchemy session in `PendingRollback` state. Fix: wrap the INSERT in `session.begin_nested()` (savepoint) so only that INSERT rolls back, not the whole transaction.
- All 3 interest UCs (`complete_interest_city`, `complete_interest_neighborhood`, `complete_interest_property_type`) ignored the `bool` returned by `mark_completed`. Added `first_time` guard so score and step only advance on first completion.
- `save_neighborhoods` with an empty list caused `INSERT INTO ... VALUES ()` error. Added `if neighborhoods_list:` guard.
- DB enum `onboardingstep` was missing value `"property_type"` — required `ALTER TYPE onboardingstep ADD VALUE 'property_type';` to fix.
- Catalog endpoint was `GET /v1/neighborhoods/by-locality?locality_id=` (singular). Renamed to `by-localities?locality_ids=` to match frontend convention.
- Exception handler logged only `exc.code`, not the original cause. Added `cause: repr(exc.cause)` to log for debuggability.

### Frontend
- `IntentSelector` called `PATCH /v1/users/me/profile` (requires `account_type` discriminator) instead of `POST /v1/onboarding/intent`. Fixed endpoint and import of `API.USERS_BASE_URL`.
- After saving intent, `App.vue` called `closeFlow()` instead of advancing to `LocalitySelector`. Added `advanceToCity()` to `useOnboarding` and wired `onSaved` to it.
- `UserInterests.localities` was typed as `{ id: string; name: string }[]` but backend returns `string[]` (UUIDs only). Corrected type; components do catalog lookup for names (lookup pattern).
- `getNeighborhoodsByLocalities` called `by-localities` correctly but parsed the response as a flat array. Backend returns `{ neighborhoods: { uuid: [NeighborhoodListItem] } }` dict — fixed iteration to `Object.entries(data.neighborhoods)`.
- Axios serializes arrays as `param[]=val` by default; FastAPI expects `param=val1&param=val2`. Fixed using `new URLSearchParams(ids.map(id => ['locality_ids', id]))`.
- `PropertyTypeSelector` existed with an unconnected `handleNext` (only `console.log`). Fully implemented: removed `cities` prop, added `onMounted` with catalog lookup, wired `POST /v1/onboarding/property-type` per city via `savePropertyTypes` in `useOnboarding`.
- `NeighborhoodSelector` and `PropertyTypeSelector` shared identical city-loading logic — extracted to `composables/useLocalitiesWithNames.ts` with a `load()` function.
- Added `isLoading` spinner (while fetching) and `isSaving` spinner + disabled state (while POSTing) to both selectors.

## Lookup pattern (confirmed)
Users-ms stores and returns only UUIDs for locality interests. Frontend fetches names from catalog-ms at render time using `getCitiesByCountry()` (cached in localStorage). This is intentional — no coupling between services.

## Open questions
- None for this flow. All 4 steps are now wired and working.

## Next steps
- Run `ALTER TYPE onboardingstep ADD VALUE 'property_type';` on any environment where the DB was created before this value was added.
- Consider adding the same `cause` logging improvement to other exception handlers across services.
