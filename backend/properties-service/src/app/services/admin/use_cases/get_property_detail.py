import uuid
from functools import partial

from fastapi.concurrency import run_in_threadpool

from app.core.config.settings import settings
from app.core.exceptions.listing import PropertyNotFoundError
from app.models.listing import ListingStatus
from app.services.admin.ports.unit_of_work import AdminUnitOfWork
from app.services.admin.schemas.admin_schemas import AdminPropertyDetailSchema
from app.services.listing.helpers.db_error_translator import translate_db_error
from app.services.shared.helpers.cache_keys import cache_property
from app.services.shared.helpers.status_transitions import (
    LISTING_STATUS_TRANSITIONS,
    VERIFICATION_TRANSITIONS,
)
from app.services.shared.ports.cache import CachePort
from app.services.shared.schemas.property_detail import PropertyDetailSchema


def _with_transitions(detail: PropertyDetailSchema) -> AdminPropertyDetailSchema:
    """Los destinos legales se calculan a la salida, no se guardan ni se cachean:
    la cache sigue siendo la misma entrada que sirve al detalle público."""
    return AdminPropertyDetailSchema(
        **detail.model_dump(),
        allowed_verification_targets = VERIFICATION_TRANSITIONS.get(detail.verification_status, []),
        allowed_status_targets = LISTING_STATUS_TRANSITIONS.get(detail.status, []),
    )


class GetPropertyDetailAdminUseCase:
    def __init__(self, *, cache: CachePort, uow: AdminUnitOfWork) -> None:
        self.uow = uow
        self.cache = cache

    async def execute(
        self,
        property_id: uuid.UUID
    ) -> AdminPropertyDetailSchema:
        cache_key = cache_property(property_id=property_id)

        try:
            cached = await self.cache.get_json(key=cache_key)
            if cached:
                return _with_transitions(PropertyDetailSchema.model_validate(cached))
        except Exception:
            pass

        try:
            prop = await run_in_threadpool(
                partial(self.uow.properties.get_by_id, property_id=property_id)
            )
        except Exception as exc:
            raise translate_db_error(exc) from exc

        if prop is None:
            raise PropertyNotFoundError(property_id=property_id)

        result = PropertyDetailSchema.model_validate(prop)

        if prop.status == ListingStatus.active:
            try:
                await self.cache.set_json(
                    key=cache_key,
                    value=result.model_dump(mode="json"),
                    ttl=settings.CACHE_TTL_PROPERTY_SECONDS,
                )
            except Exception:
                pass

        return _with_transitions(result)