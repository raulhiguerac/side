from collections import defaultdict
from functools import partial
from typing import Optional

import h3
from fastapi.concurrency import run_in_threadpool

from app.services.search.ports.unit_of_work import SearchUnitOfWork
from app.services.search.schemas.feed_schemas import BoundingBox, FeedFilters
from app.services.shared.helpers.cache_keys import map_h3_cell
from app.services.shared.ports.cache import CachePort
from app.services.shared.schemas.property_card import PropertyCardSchema

_MAP_CACHE_TTL = 300  # 5 min


class GetFeedMapUseCase:
    def __init__(self, *, uow: SearchUnitOfWork, cache: CachePort) -> None:
        self.uow = uow
        self.cache = cache

    async def execute(
        self,
        *,
        bbox: BoundingBox,
        resolution: int = 9,
    ) -> list[PropertyCardSchema]:
        polygon = bbox.to_polygon()
        h3_indexes = list(h3.h3shape_to_cells_experimental(polygon, resolution, contain="center"))

        if not h3_indexes:
            return []

        cached: list[PropertyCardSchema] = []
        missing: list[str] = []

        try:
            results = await self.cache.mget_json(keys=[map_h3_cell(index) for index in h3_indexes])
            for index, hit in zip(h3_indexes, results):
                if hit:
                    cached.extend([PropertyCardSchema.model_validate(p) for p in hit])
                else:
                    missing.append(index)
        except Exception:
            missing = list(h3_indexes)

        if not missing:
            return cached

        raw = await run_in_threadpool(
            partial(
                self.uow.properties.get_by_bbox,
                h3_indexes=missing,
                resolution=resolution,
            )
        )

        await self._cache_by_cell(raw, resolution)
        fresh = [PropertyCardSchema.model_validate(p) for p in raw]

        return cached + fresh

    async def _cache_by_cell(self, props: list, resolution: int) -> None:
        h3_field = "h3_r9" if resolution == 9 else "h3_r7"
        by_cell: dict[str, list] = defaultdict(list)

        for prop in props:
            cell = getattr(prop, h3_field, None)
            if cell:
                by_cell[cell].append(PropertyCardSchema.model_validate(prop).model_dump(mode="json"))

        try:
            await self.cache.mset_json(
                data={map_h3_cell(cell): props for cell, props in by_cell.items()},
                ttl=_MAP_CACHE_TTL,
            )
        except Exception:
            pass
