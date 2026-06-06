import uuid
from  datetime import datetime
from functools import partial
from typing import Optional

from fastapi.concurrency import run_in_threadpool

from app.services.search.ports.unit_of_work import SearchUnitOfWork
from app.services.search.schemas.feed_schemas import FeedCursor, FeedFilters, FeedPreferences
from app.services.shared.schemas.property_card import PropertyCardSchema


async def get_organic(
    *,
    uow: SearchUnitOfWork,
    preferences: Optional[FeedPreferences],
    filters: FeedFilters,
    cursor: Optional[FeedCursor],
    count: int,
) -> tuple[list[PropertyCardSchema], tuple[datetime, uuid.UUID] | None]:
    base_kwargs: dict = dict(
        min_price=filters.min_price,
        max_price=filters.max_price,
        min_area_m2=filters.min_area_m2,
        max_area_m2=filters.max_area_m2,
        min_bathrooms=filters.min_bathrooms,
        bedrooms=filters.bedrooms,
        promoted_only=False,
        cursor_created_at=cursor.created_at if cursor else None,
        cursor_id=cursor.id if cursor else None,
        limit=count,
    )

    phases = _build_phases(preferences)

    for phase in phases:
        raw = await run_in_threadpool(
            partial(uow.properties.get_properties, **base_kwargs, **phase)
        )
        if raw:
            cards = [PropertyCardSchema.model_validate(p) for p in raw]
            last_created, last_id = raw[-1].created_at, raw[-1].id
            return (cards,(last_created,last_id))

    return ([], None)

def _build_phases(preferences: Optional[FeedPreferences]) -> list[dict]:
    if preferences is None:
        return [dict(city_ids=None, neighborhood_ids=None, property_types=None)]

    return [
        dict(
            city_ids=preferences.city_ids,
            neighborhood_ids=preferences.neighborhood_ids,
            property_types=preferences.property_types,
        ),
        dict(
            city_ids=preferences.city_ids,
            neighborhood_ids=None,
            property_types=preferences.property_types,
        ),
        dict(city_ids=None, neighborhood_ids=None, property_types=None),
    ]
