---
title: Moderation moves into the preview panel as a staged form, not action buttons on the table
captured-from: conversation
captured-on: 2026-08-02
participants: [raul, claude]
---

## Context

With the moderation endpoints ready, the question was where the actions live. The first design — an actions column in the table, then an action bar with buttons — was built and then discarded on UX grounds before being wired to anything.

## Key conclusions

### Actions live in the preview panel, not in the table

The deciding argument: **moderating requires looking.** Approving from a table row means approving without seeing the photos, which is exactly what verification is supposed to prevent — and the table's columns (type, price, date) are not enough to decide anything. Acting should cost the same as looking.

Consequence: the table stays an index. It never passes `#actions`, so `AdminPropertiesTable` never appends the actions column (`slots.actions` check) — no change needed there at all. Clicking a row still only selects it.

Rejected along the way: one column per action. Which actions are legal varies per row, so most cells would be empty, and between both machines a single row can have up to 6 legal actions against 6 data columns.

### A staged form with a save button, not instant action buttons

The button design was built (`AdminModerationActionBar.vue`) and deleted. Three problems killed it:

1. One visible button plus a hidden `⋯` overflow menu is not discoverable.
2. Moderating both axes meant two requests and two refetches.
3. Worst: with the table filtered by `verification_status=pending`, changing verification removes the row from the list **before** the second change can be made. The two-axis case was not slow — it was impossible.

`AdminModerationForm.vue` replaces it: two selects prefilled with the current state, changes staged locally, one "Guardar". The row leaves the filter once, after the work is done.

Accepted costs, both known upfront:

- **The dominant action gets slower.** In a queue filtered by `pending`, most rows only need "approve" — one click before, two now. Judged acceptable because the two-change case was previously impossible, and because the moderator has to look anyway. A highlighted "Aprobar" shortcut on top of the form was considered and deferred: it complicates the form state before there is evidence the extra click hurts.
- **One save can be two non-atomic requests.** They are separate endpoints; if the second fails with a 409 the first already applied. The form must report per-axis success/failure and reload rather than pretend it's atomic.

### The selects make the state machine visible

Options are "current state (actual)" plus only the legal targets from it. Reaching `verified` from `unverified` is two saves by construction, because `verified` simply isn't in the list — the two-hop rule is communicated instead of exploding as a 409.

`constants/moderationTransitions.ts` mirrors both backend tables (`verify.py` and `set_status.py`) with the source of truth named in a comment.

### The rejection reason is inline, not a modal

It appears under the select only when "Rechazada" is picked, with a 500-char counter matching the backend limit, and "Guardar" stays disabled while it's empty. Being part of choosing a state reads better than a separate window, and it's what the schema validator now enforces server-side.

### The form is dumb; the composable will live in the view

Props are `status`, `verificationStatus`, `saving`, `successMessage`, `errorMessage`; it emits `save` with **only what changed**. The panel forwards it upward with the `propertyId` it is already showing.

The panel feeds the form from its own fetched detail (`PropertyDetailSchema` carries both `status` and `verification_status`), so the controls and the property being looked at come from the same response. Behind `v-if="property"`, so nothing is moderatable while the photo is still loading.

The execution composable belongs to `AdminPropertiesModerationView`, the only place holding the list, the selection and the refetch. Keeping the API call out of the form and out of the panel avoids tying either to this screen.

### Estimated price is not moderation

Left out of the panel on two grounds: it's a pricing signal feeding the AVM training label, not a review decision — and it is currently **write-only from the front**. `admin_estimated_price` and `ml_estimated_price` appear in no response schema, so the input would overwrite a value the moderator never saw. It needs the admin detail schema split from the public one first.

## Open questions

- **After saving: auto-advance to the next row, or stay?** With instant buttons auto-advance was the plan; with a form, staying and showing the applied result may read better — auto-advance after a form feels like the page was pulled away.
- **The sticky footer isn't sticky yet.** The panel root has `overflow-hidden` and doesn't scroll, so `sticky bottom-0` is currently a no-op. Making it real needs a `max-h` + `overflow-y-auto` on the content block; the height is a design call.
- **A "leaves this filter" warning** in the form would need the active filter passed down as a prop.
- `tone` and `label` in `moderationTransitions.ts` are now unused — they were for the deleted buttons. Only `target` is consumed; state names come from `propertyStatus.ts`.

## Next steps

- Build the execution composable in the moderation view: call one or both endpoints, handle partial failure, refetch the list.
- `ModerationPayload` lives in `types/admin.ts`, not exported from the SFC: the `*.vue` shim only declares a default export, so a named type import from a component would break under `vue-tsc`.
