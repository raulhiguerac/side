import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from fastapi import Depends, Query
from sqlmodel import Session

from app.api.deps.db import get_session
from app.api.deps.listing import get_cache_port
from app.models.listing import PropertyType
from app.services.search.adapters.sql_unit_of_work import SqlSearchUnitOfWork
from app.services.search.ports.unit_of_work import SearchUnitOfWork
from app.services.search.schemas.feed_schemas import FeedCursor, FeedFilters, FeedPreferences
from app.services.search.use_cases.get_feed import GetFeedUseCase
from app.services.search.use_cases.get_feed_map import GetFeedMapUseCase
from app.services.shared.ports.cache import CachePort


# -------------------------------------------------------------------------
# Unit of Work (request-scoped)
# -------------------------------------------------------------------------

def get_search_uow(session: Session = Depends(get_session)) -> SearchUnitOfWork:
    return SqlSearchUnitOfWork(session=session)


# -------------------------------------------------------------------------
# Query param parsers
# -------------------------------------------------------------------------

def parse_feed_preferences(
    city_ids: list[uuid.UUID] = Query(default=[]),
    neighborhood_ids: list[uuid.UUID] = Query(default=[]),
    property_types: list[PropertyType] = Query(default=[]),
) -> Optional[FeedPreferences]:
    if not city_ids and not neighborhood_ids and not property_types:
        return None
    return FeedPreferences(
        city_ids=city_ids,
        neighborhood_ids=neighborhood_ids,
        property_types=property_types,
    )


def parse_feed_filters(
    min_price: Optional[Decimal] = None,
    max_price: Optional[Decimal] = None,
    min_area_m2: Optional[Decimal] = None,
    max_area_m2: Optional[Decimal] = None,
    min_bathrooms: Optional[Decimal] = None,
    bedrooms: Optional[int] = Query(default=None, ge=1),
) -> Optional[FeedFilters]:
    filters = FeedFilters(
        min_price=min_price,
        max_price=max_price,
        min_area_m2=min_area_m2,
        max_area_m2=max_area_m2,
        min_bathrooms=min_bathrooms,
        bedrooms=bedrooms,
    )
    if all(v is None for v in filters.model_dump().values()):
        return None
    return filters

# -------------------------------------------------------------------------
# Use cases
# -------------------------------------------------------------------------

def get_feed_uc(
    uow: SearchUnitOfWork = Depends(get_search_uow),
    cache: CachePort = Depends(get_cache_port),
) -> GetFeedUseCase:
    return GetFeedUseCase(uow=uow, cache=cache)


def get_feed_map_uc(
    uow: SearchUnitOfWork = Depends(get_search_uow),
    cache: CachePort = Depends(get_cache_port),
) -> GetFeedMapUseCase:
    return GetFeedMapUseCase(uow=uow, cache=cache)
