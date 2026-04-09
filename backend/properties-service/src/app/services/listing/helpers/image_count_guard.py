import uuid
from datetime import UTC, datetime
from functools import partial

from fastapi.concurrency import run_in_threadpool

from app.core.config.settings import settings
from app.core.exceptions.listing import ImageCountExceededError, ImageNotOwnedError
from app.services.listing.ports.unit_of_work import ListingUnitOfWork
from app.services.shared.helpers.cache_keys import property_image_ids
from app.services.shared.ports.cache import CachePort


async def check_image_count(
    *,
    uow: ListingUnitOfWork,
    cache: CachePort,
    property_id: uuid.UUID,
    create_count: int,
    exclude_batch_ids: list[uuid.UUID] | None = None,
) -> int:
    """
    Resolves active image IDs (cache-aside), validates delete_image_ids ownership,
    fetches in-flight batch keys and checks the resulting count against the max.

    Returns the resolved active_ids list so callers can reuse it.
    """
    cache_key = property_image_ids(property_id)
    cached = await cache.get_json(key=cache_key)
    if cached:
        active_ids = [uuid.UUID(i) for i in cached]
    elif cached is not None:
        active_ids = []
    else:
        active_ids = await run_in_threadpool(
            partial(uow.property_images.get_active_ids, property_id=property_id)
        )
        try:
            await cache.set_json(
                key=cache_key,
                value=[str(i) for i in active_ids],
                ttl=settings.PROPERTY_IMAGE_IDS_CACHE_TTL_SECONDS,
            )
        except Exception:
            pass

    now = datetime.now(UTC)
    open_batches = await run_in_threadpool(
        partial(uow.property_images.get_open_batches, property_id=property_id, now=now, exclude_ids=exclude_batch_ids)
    )
    in_flight = sum(len(b.expected_keys) for b in open_batches)

    count = len(active_ids) + in_flight + create_count
    if count > settings.MAX_IMAGES_PER_PROPERTY:
        raise ImageCountExceededError(max=settings.MAX_IMAGES_PER_PROPERTY, requested=count)

    return create_count
