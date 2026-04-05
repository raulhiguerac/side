import uuid
from functools import partial

from fastapi.concurrency import run_in_threadpool

from app.core.exceptions.listing import PropertyForbiddenError, PropertyNotFoundError
from app.models.property import Property
from app.schemas.principal import Principal
from app.services.listing.helpers.db_error_translator import translate_db_error
from app.services.listing.ports.unit_of_work import ListingUnitOfWork


async def get_owned_property(
    *,
    uow: ListingUnitOfWork,
    property_id: uuid.UUID,
    principal: Principal,
) -> Property:
    try:
        prop = await run_in_threadpool(
            partial(uow.properties.get_by_id, property_id=property_id)
        )
    except Exception as exc:
        raise translate_db_error(exc) from exc

    if prop is None:
        raise PropertyNotFoundError(property_id=property_id)

    if prop.owner_id != principal.sub:
        raise PropertyForbiddenError(property_id=property_id)

    return prop
