import uuid
from functools import partial

from fastapi.concurrency import run_in_threadpool

from app.services.listing.helpers.db_error_translator import translate_db_error
from app.services.listing.ports.unit_of_work import ListingUnitOfWork
from app.services.shared.schemas.property_card import PropertyCardSchema


class GetPublicUserPropertiesUseCase:
    def __init__(self, *, uow: ListingUnitOfWork) -> None:
        self.uow = uow

    async def execute(self, user_id: uuid.UUID) -> list[PropertyCardSchema]:
        try:
            properties = await run_in_threadpool(
                partial(self.uow.properties.get_public_user_properties, user_id=user_id)
            )
        except Exception as exc:
            raise translate_db_error(exc) from exc

        return [PropertyCardSchema.model_validate(prop) for prop in properties]
