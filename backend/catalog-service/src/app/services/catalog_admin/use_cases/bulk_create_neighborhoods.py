import unicodedata
import uuid
from functools import partial
from fastapi.concurrency import run_in_threadpool

from app.core.logging.logger import get_logger
from app.models.location import Neighborhood
from app.services.catalog_admin.ports.unit_of_work import CatalogAdminUnitOfWork
from app.services.catalog_admin.schemas.neighborhood import BulkCreateNeighborhoodsResult
from app.services.shared.ports.cache import CachePort

logger = get_logger(__name__)


def _normalize(name: str) -> str:
    nfkd = unicodedata.normalize("NFKD", name)
    return "".join(c for c in nfkd if not unicodedata.combining(c)).lower().strip()


def _to_neighborhood(record: dict, locality_id: uuid.UUID) -> Neighborhood:
    return Neighborhood(
        locality_id=locality_id,
        code=record.get("code"),
        postal_code=record.get("postal_code"),
        name=record.get("name"),
        search_name=_normalize(record.get("name", "")),
        latitude=record.get("latitude"),
        longitude=record.get("longitude"),
        is_active=record.get("is_active", True),
    )


class BulkCreateNeighborhoodsUseCase:
    def __init__(self, *, uow: CatalogAdminUnitOfWork, cache_client: CachePort) -> None:
        self.uow = uow
        self.cache_client = cache_client

    async def execute(self, *, locality_id: uuid.UUID, records: list[dict]) -> BulkCreateNeighborhoodsResult:
        model_list = [_to_neighborhood(record=r, locality_id=locality_id) for r in records]

        try:
            await run_in_threadpool(
                partial(self.uow.neighborhoods.bulk_insert, neighborhoods=model_list)
            )
            await self.uow.commit()
            return BulkCreateNeighborhoodsResult(created=len(model_list), errors=[])
        except Exception as exc:
            await self.uow.rollback()
            logger.warning(
                "bulk_insert failed, falling back to row-by-row",
                extra={"locality_id": str(locality_id), "total": len(model_list)},
                exc_info=exc,
            )

        errors: list[str] = []
        ok_count = 0

        for neighborhood in model_list:
            try:
                await self.uow.begin_nested()
                await run_in_threadpool(
                    partial(self.uow.neighborhoods.add, neighborhood=neighborhood)
                )
                ok_count += 1
            except Exception as exc:
                await self.uow.rollback_to_savepoint()
                logger.warning(
                    "failed to insert neighborhood",
                    extra={"neighborhood_name": neighborhood.name, "locality_id": str(locality_id)},
                    exc_info=exc,
                )
                errors.append(neighborhood.name)

        if ok_count:
            await self.uow.commit()

        return BulkCreateNeighborhoodsResult(created=ok_count, errors=errors)
