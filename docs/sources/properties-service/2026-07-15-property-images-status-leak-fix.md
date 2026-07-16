---
title: Fix — pending_delete images leaking into API responses
captured-from: conversation
captured-on: 2026-07-15
participants: [author, claude]
---

## Context

While planning an "edit photos" feature for properties (add/delete photos on an existing property), investigation of the image delete flow surfaced a real, reproducible bug in how `Property.images` is loaded.

## Key conclusions

- `Property.images` (`models/property.py`) had no status filter on its ORM relationship, unlike the sibling `promotions` relationship on the same model, which filters `PromotedListing.is_active == True` via `primaryjoin` + `viewonly=True`.
- `DeletePropertyImagesUseCase` only soft-deletes (`PropertyImage.status = pending_delete`) and never removes the row — so any code path reading `property.images` directly (not via the filtered repo methods) pulled back images in every status, including `pending_delete`.
- Confirmed leaking endpoints (all populate `images` from the raw ORM relationship via `PropertyDetailSchema`/`PropertyCardSchema.model_validate(prop)`): property detail, admin detail, `GET /properties/mine`, public profile properties, admin list, feed, and map.
- The bug is **deterministically reproducible immediately after a delete**, not just theoretical: `delete_property_images.py` invalidates the property detail and `/me` caches right after marking `pending_delete`, guaranteeing the next read is a cache miss that re-triggers the unfiltered relationship query.
- Fix: mirrored the `promotions` pattern on `Property.images` — added `primaryjoin="and_(Property.id == foreign(PropertyImage.property_id), PropertyImage.status == 'active')"`, `viewonly=True`, `overlaps="property"`. Removed `PropertyImage.property`'s `back_populates="images"` (now just `overlaps="images"`), since nothing writes images via `property.images.append(...)` — `confirm_image_uploads.py` always creates rows through `uow.property_images.add(image=...)` directly.
- Verified safe: `sqlalchemy.orm.configure_mappers()` succeeds, and `uv run pytest` shows the exact same 4 pre-existing failures before and after (confirmed via `git stash` comparison on `test_get_feed.py`, unrelated mock issue), with 67 tests passing unaffected.

## Open questions

None — fix is closed and verified.

## Next steps

None pending for this specific fix.
