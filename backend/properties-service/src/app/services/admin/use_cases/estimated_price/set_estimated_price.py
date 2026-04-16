import uuid
from datetime import datetime, timezone
from decimal import Decimal
from functools import partial
from typing import Optional

from fastapi.concurrency import run_in_threadpool

from app.core.exceptions.listing import PropertyNotFoundError, SetEstimatedPriceError
from app.schemas.principal import Principal
from app.services.admin.ports.unit_of_work import AdminUnitOfWork


class SetEstimatedPriceUseCase:
    def __init__(self, *, uow: AdminUnitOfWork) -> None:
        self.uow = uow

    async def execute(self, principal: Optional[Principal], property_id: uuid.UUID, estimated_price: Decimal) -> None:
        prop = await run_in_threadpool(
            partial(self.uow.properties.get_by_id, property_id=property_id)
        )

        if prop is None:
            raise PropertyNotFoundError(property_id=property_id)

        if principal:
            prop.admin_estimated_price = estimated_price
            prop.admin_estimated_price_at = datetime.now(timezone.utc)
            prop.updated_by = principal.sub
        else:
            prop.ml_estimated_price = estimated_price
            prop.ml_estimated_price_at = datetime.now(timezone.utc)

        try:
            await self.uow.commit()
        except Exception as exc:
            await self.uow.rollback()
            raise SetEstimatedPriceError(cause=exc, context={"property_id": str(property_id)}) from exc
