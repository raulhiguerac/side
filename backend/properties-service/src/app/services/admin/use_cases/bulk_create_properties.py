import asyncio
import logging
from functools import partial

from fastapi.concurrency import run_in_threadpool

from app.schemas.principal import Principal
from app.services.admin.helpers.seed_mapper import build_models, row_to_item
from app.services.admin.ports.unit_of_work import AdminUnitOfWork
from app.services.admin.schemas.admin_schemas import BulkCreatePropertiesResult
from app.services.shared.ports.catalog_gateway import CatalogGateway

logger = logging.getLogger(__name__)


class BulkCreatePropertiesUseCase:
    def __init__(self, *, uow: AdminUnitOfWork, catalog: CatalogGateway) -> None:
        self.uow = uow
        self.catalog = catalog

    async def execute(self, principal: Principal, records: list[dict]) -> BulkCreatePropertiesResult:
        sem = asyncio.Semaphore(50)
        tasks = [self._enrich_location(sem=sem, record=record) for record in records]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        errors: list[str] = []
        orm_objects = []

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                row_ref = f"row[{i}] lat={records[i].get('lat', '?')} lon={records[i].get('lon', '?')}"
                errors.append(f"{row_ref}: {result}")
                continue

            raw_urls = result.get("image_urls", [])
            image_urls = (
                raw_urls
                if isinstance(raw_urls, list)
                else [u.strip() for u in raw_urls.split(",") if u.strip()]
            )

            item = row_to_item(
                row=result,
                neighborhood_id=result["neighborhood_id"],
                city_id=result["city_id"],
                country_id=result["country_id"],
                image_urls=image_urls,
            )
            if item is None:
                errors.append(f"Skipped row: {result.get('id', '?')}")
                continue

            try:
                orm_objects.append(
                    build_models(item=item, owner_id=principal.sub, created_by=principal.sub)
                )
            except Exception as exc:
                errors.append(f"Build error for row {result.get('id', '?')}: {exc}")

        if not orm_objects:
            return BulkCreatePropertiesResult(inserted=0, errors=errors)

        try:
            await run_in_threadpool(
                partial(self.uow.properties.bulk_insert, properties=orm_objects)
            )
            await self.uow.commit()
            return BulkCreatePropertiesResult(inserted=len(orm_objects), errors=errors)
        except Exception as exc:
            await self.uow.rollback()
            logger.warning(
                "bulk_insert failed, falling back to row-by-row",
                extra={"total": len(orm_objects)},
                exc_info=exc,
            )

        ok_count = 0
        for item in orm_objects:
            prop, _, _ = item
            try:
                await self.uow.begin_nested()
                await run_in_threadpool(partial(self.uow.properties.add, property=item))
                ok_count += 1
            except Exception as exc:
                await self.uow.rollback_to_savepoint()
                logger.warning(
                    "failed to insert property",
                    extra={"property_id": str(prop.id)},
                    exc_info=exc,
                )
                errors.append(str(prop.id))

        if ok_count:
            await self.uow.commit()

        return BulkCreatePropertiesResult(inserted=ok_count, errors=errors)

    async def _enrich_location(self, *, sem: asyncio.Semaphore, record: dict) -> dict:
        async with sem:
            location = await self.catalog.get_location_by_point(lat=record["lat"], lon=record["lon"])
            record.update(location.model_dump())
            return record
