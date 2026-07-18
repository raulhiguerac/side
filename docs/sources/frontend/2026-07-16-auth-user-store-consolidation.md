---
title: Auth/user store consolidation, per-account onboarding dismissal, centralized 401 interceptor
captured-from: conversation
captured-on: 2026-07-16
participants: [raul, claude]
---

## Context
Wiring `is_admin` into the front for a planned admin panel required knowing "am I authenticated" before "what's my role," which exposed that `auth.ts` and `user.ts` both modeled overlapping "current user" concepts fetched from different, uncoordinated lifecycle triggers, plus a pre-existing UX bug where dismissing the onboarding modal didn't survive a logout/login cycle in the same browser.

## Key conclusions
- Admin panel approach: embed conditionally in the existing app (`v-if` gating, router guard later) instead of a separate subdomain — much cheaper at this project stage and reusable later if a real split is ever needed.
- `is_admin` source: enrich the existing `GET /v1/users/me/` response rather than add a new endpoint — one bootstrap call, no extra round trip.
- Root cause of "2 network calls for one user concept": `auth.ts`'s `checkAuth()` hits `/me/profile` (display data, also reused by the PUBLIC other-user-profile route) while the old `user.ts`'s `checkOnboardingStep()` hit `/me/` (account data) — genuinely different backend concerns, not a backend mistake. The front just triggered them from uncoordinated lifecycle points (`onMounted` vs. an onboarding-dismissal-gated flow), causing duplicate or sometimes-skipped fetches.
- Fixed sequencing: `checkAuth()` (does the user have a session at all) → if authenticated → `fillUserData()` (fetches `onboarding_step`/`is_admin`/`accountId`) → `checkInterests()` → `startFlow()`, all funneled through the single existing `watch(() => authStore.isAuthenticated, ...)` in `App.vue` (covers boot and post-login/register transitions uniformly). `onMounted` now only calls `checkAuth()`; removed a pre-existing duplicate `checkInterests()` call that fired both from `onMounted` and the watcher.
- Type reconciliation: two unrelated `User` interfaces shared the same name (`types/user.ts`'s account-shaped `User` vs. `auth.ts`'s local profile-shaped `User`), causing a real type bug in `fillUserData`. Renamed the local one to `AuthProfile`/`AuthUser`, moved into `types/user.ts`.
- `user.ts` slimmed down: `onboardingStep`/`isAdmin`/`accountId` ownership moved fully to `auth.ts` (now the single source of truth for identity/session/role). `user.ts` keeps only `userInterests` (feed personalization) and `detectLocation` (IP geolocation) — concerns unrelated to session identity. Rejected extracting `auth.ts`'s actions into composables (`useLogin()`, etc.) — actions fit Pinia's idiom here, and the ~9-call-site blast radius outweighs the mostly-stylistic benefit.
- Persistent-dismissal bug: onboarding "don't show again" used `sessionStorage` (correct choice — must survive logout without surviving a full browser close) but was (a) wiped on every logout and (b) not scoped per account, so a second account on the same browser inherited the first account's dismissal. Fixed: key parametrized as `STORAGE_KEYS.ONBOARDING_DISMISSED(accountId)`, no longer cleared on logout.
- `localStorage` was considered and rejected for the dismissal flag — desired semantics ("don't nag today, ask again if the browser is closed") is exactly what `sessionStorage` already gives; `localStorage` would never ask again at all.
- Coupling review: `auth.ts`/`user.ts` reading each other's state (`accountId`) or orchestrating cleanup (`resetInterests()` on logout) is normal, idiomatic Pinia — not the real problem. The real problem: both stores bypassed an already-existing centralized axios response interceptor (`api/interceptors.ts`, applied only to the `usersApi`/`propertiesApi` instances) by calling bare `axios` directly, forcing each action to hand-roll its own 401 handling. Migrated `fillUserData`, `login`, `register` (`auth.ts`) and `checkInterests` (`user.ts`) to the `usersApi` instance; removed the now-redundant manual 401→logout checks. `logout()`'s own POST deliberately stays on bare `axios` to avoid interceptor-recursion risk.
- Interceptor changes: excluded `/auth/login` and `/auth/register` from the refresh-retry path (a bad-password 401 isn't "session expired"); replaced the old hard `window.location.href` redirect-on-refresh-failure with a real `authStore.logout()` call, imported dynamically inside the interceptor (`await import("@/stores/auth")`) to avoid a static circular import (`auth.ts → usersApi.ts → interceptors.ts → auth.ts`).
- Regression caught mid-review and fixed: routing `checkAuth()` itself through `usersApi` broke anonymous browsing — a 401 there is a normal "not logged in" outcome for any anonymous page load, but through the interceptor it triggered a refresh attempt, which failed, then force-logout + `router.push("/")`, redirecting every anonymous visitor to Home on every page load. Fix: `checkAuth()` reverted to bare `axios` (the one deliberate exception); `fillUserData`/`login`/`register`/`checkInterests` correctly stay on `usersApi` since those only ever run after `checkAuth` has already confirmed a session exists.

## Open questions
- Whether to generalize "reset all session-scoped store state on logout" via a Pinia plugin if more stores accumulate session-scoped data (rejected for now as over-engineering for 2 stores).

## Next steps
- Implement the actual admin nav/route gating using `authStore.isAdmin` (data plumbing is done; UI gating is not).
- Flagged, not scheduled: `checkInterests()`'s memoization (`if already has localities, skip fetch`) leaks a previous account's interests into a different account logging in on the same tab without a full reload.
- Flagged, not scheduled: `LoginView.vue` calls `authStore.checkAuth()` redundantly right after `authStore.login()` (which already calls `checkAuth(true)` internally) — harmless (guarded by `_authChecked`) but dead code.
