---
title: Moderation transitions are state machines, and the imported 18.744 cannot be approved
captured-from: conversation
captured-on: 2026-07-29
participants: [raul, claude]
---

## Context
Estimating "just a couple of composables" for the admin moderation buttons meant reading the two moderation use cases, which turned out to enforce state machines that the bulk-imported data cannot enter.

## Key conclusions

### Both moderation endpoints validate transitions, they are not setters
`SetPropertyStatusUseCase` and `VerifyPropertyUseCase` each hold an `_ALLOWED_TRANSITIONS` map and raise `InvalidStatusTransitionError` on anything else:

```
verification                          status
unverified → pending                  draft    → active
pending    → verified | rejected      active   → draft | inactive | sold | rented
rejected   → pending                  inactive → active | draft
verified   → []  (terminal)           sold     → inactive
                                      rented   → inactive
```

### The blocking consequence
- `Property.verification_status` defaults to `unverified`, so **every one of the 18.744 bulk-imported properties is `unverified`**, whose only legal target is `pending`.
- **No imported property can be approved directly.** Something has to move them to `pending` first, and in the original design that was the owner requesting verification — which never happens for a bulk import.
- This is a product gap, not a bug: either the import writes `pending`, or the admin panel needs a "send to review" action (plausibly bulk), or approval accepts a direct `unverified → verified` jump.

### What this implies for the frontend
- Row actions cannot be a fixed button set; the legal targets depend on each row's current status. That transition table lives only in the backend today, so mirroring it in the front introduces drift risk.
- `verified` is **terminal** — nothing transitions out of it. An irreversible action should not be a bare click in a table row.
- Rejecting requires a reason (`rejection_reason`, max 500 chars), so it is a modal with a textarea, not a button.
- All three moderation endpoints return **204 with no body**, so after acting there is no updated row to render: the current page must be refetched or the row patched locally. Refetching is complicated by the fact that acting on a filtered list should make the row disappear.
- `InvalidStatusTransitionError` surfaces as code `INVALID_STATUS_TRANSITION` with `{current, target}` in context. Without mapping it, an admin would see a generic error for doing something the UI itself offered.

## Open questions
- Should the bulk import write `pending` instead of `unverified`, or should the panel get an explicit "send to review" action? The first makes every import a moderation queue; the second keeps the import neutral but needs a bulk action to be usable at 18.744 rows.
- Should the allowed-transitions table be exposed by the API (so the front stops duplicating it), or is duplication acceptable given how rarely it changes?
- After approving on a filtered list, should the row vanish (correct but jarring) or stay until the next refresh?

## Next steps
- Decide the `unverified` question before building the buttons — it determines whether the first action is "approve" or "send to review".
- Smallest useful slice identified: "send to review" for `unverified`, approve/reject only on `pending` rows, `reload()` in the composable, and error mapping. Explicitly excluding promotions, estimated price and the admin detail view.
