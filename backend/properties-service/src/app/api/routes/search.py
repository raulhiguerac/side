from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Query, status

from app.api.deps.search import (
    get_feed_map_uc,
    get_feed_uc,
    parse_feed_cursor,
    parse_feed_filters,
    parse_feed_preferences,
)
from app.services.search.schemas.feed_schemas import BoundingBox, FeedCursor, FeedFilters, FeedPreferences
from app.services.search.use_cases.get_feed import GetFeedUseCase
from app.services.search.use_cases.get_feed_map import GetFeedMapUseCase
from app.services.shared.schemas.property_card import PropertyCardSchema

router = APIRouter(prefix="/search", tags=["search"])


@router.get(
    "/feed",
    response_model=list[PropertyCardSchema],
    status_code=status.HTTP_200_OK,
)
async def get_feed(
    preferences: Annotated[Optional[FeedPreferences], Depends(parse_feed_preferences)],
    filters: Annotated[Optional[FeedFilters], Depends(parse_feed_filters)],
    cursor: Annotated[Optional[FeedCursor], Depends(parse_feed_cursor)],
    uc: Annotated[GetFeedUseCase, Depends(get_feed_uc)],
) -> list[PropertyCardSchema]:
    return await uc.execute(preferences=preferences, filters=filters, cursor=cursor)


@router.get(
    "/feed/map",
    response_model=list[PropertyCardSchema],
    status_code=status.HTTP_200_OK,
)
async def get_feed_map(
    uc: Annotated[GetFeedMapUseCase, Depends(get_feed_map_uc)],
    min_lat: float = Query(ge=-90, le=90),
    max_lat: float = Query(ge=-90, le=90),
    min_lon: float = Query(ge=-180, le=180),
    max_lon: float = Query(ge=-180, le=180),
    resolution: int = Query(default=9, ge=7, le=9),
) -> list[PropertyCardSchema]:
    bbox = BoundingBox(min_lat=min_lat, max_lat=max_lat, min_lon=min_lon, max_lon=max_lon)
    return await uc.execute(bbox=bbox, resolution=resolution)
