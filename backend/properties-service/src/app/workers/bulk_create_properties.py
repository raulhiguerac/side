import uuid
import asyncio
import logging
from functools import partial

from fastapi.concurrency import run_in_threadpool

from app.schemas.principal import Principal
from app.services.admin.helpers.seed_mapper import build_models, row_to_item
from app.services.admin.ports.unit_of_work import AdminUnitOfWork
from app.services.admin.schemas.admin_schemas import BulkCreatePropertiesResult, BulkRowError, BulkPropertyCsvRow
from app.services.shared.ports.catalog_gateway import CatalogGateway
from app.services.shared.ports.users_gateway import UsersGateway
from app.services.shared.ports.storage import StoragePort
from app.services.shared.schemas.catalog_schemas import PointToResolve
from app.workers.helpers.chunking import iter_csv_rows
from app.workers.helpers.location_batch import process_location_batch
from app.workers.helpers.row_ref import row_ref
from pydantic import ValidationError

logger = logging.getLogger(__name__)


class BulkCreatePropertiesUseCase:
    def __init__(
            self, 
            *, 
            uow: AdminUnitOfWork, 
            catalog: CatalogGateway, 
            users: UsersGateway,
            storage: StoragePort
        ) -> None:
        self.uow = uow
        self.catalog = catalog
        self.users = users
        self.storage = storage

        if not settings.BUCKET_BULK_PROPERTIES:
            raise StorageMisconfiguredError(context={"missing": "BUCKET_PHOTOS_PROPERTIES"})

        self.bucket = settings.BUCKET_BULK_PROPERTIES

    async def execute(
            self, 
            principal: Principal, 
            key: str
        ) -> BulkCreatePropertiesResult:

        batch = []
        errors: list[str] = []
        lines = 1

        rows = iter_csv_rows(storage=self.storage, bucket=self.bucket, key=key)
        async for row in rows:
            lines += 1
            try:
                batch.append(
                    {
                        "line": lines,
                        "id": str(uuid.uuid4()),
                        "value": BulkPropertyCsvRow(**row)
                    }
                )
            except ValidationError as e:
                errors.append(
                    BulkRowError(
                        line = lines,
                        ref = row_ref(row),
                        issues = [f"{err['loc'][-1]}: {err['msg']}" for err in e.errors()]
                    )
                )
                continue

            if len(batch) < 2500:
                continue

            to_process, batch = batch[:2500], batch[2500:]

            enriched_geo   = await process_location_batch(to_process, catalog=self.catalog)
            owner_by_email = await self._process_users_batch(to_process)

            geo, owners = await asyncio.gather(enriched_geo, owner_by_email, return_exceptions=True)

        if batch:
            await process_location_batch(batch, catalog=self.catalog)

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

    async def _process_users_batch(self,)
