import uuid
from functools import partial

from fastapi.concurrency import run_in_threadpool

from app.core.exceptions.listing import InvalidStatusTransitionError, PropertyNotFoundError, SetVisibilityError
from app.models.property import VerificationStatus
from app.services.admin.ports.unit_of_work import AdminUnitOfWork
from app.services.admin.schemas.admin_schemas import VerifyPropertyRequest
from app.services.shared.helpers.cache_keys import cache_property, client_properties, map_h3_cell
from app.services.shared.ports.cache import CachePort

_ALLOWED_TRANSITIONS: dict[VerificationStatus, list[VerificationStatus]] = {
    VerificationStatus.unverified: [VerificationStatus.pending],
    VerificationStatus.pending: [VerificationStatus.verified, VerificationStatus.rejected],
    VerificationStatus.rejected: [VerificationStatus.pending],
    VerificationStatus.verified: [],
}


class VerifyPropertyUseCase:
    def __init__(self, *, uow: AdminUnitOfWork, cache: CachePort) -> None:
        self.uow = uow
        self.cache = cache

    async def execute(self, *, property_id: uuid.UUID, request: VerifyPropertyRequest) -> None:
        prop = await run_in_threadpool(
            partial(self.uow.properties.get_by_id, property_id=property_id)
        )

        if prop is None:
            raise PropertyNotFoundError(property_id=property_id)

        allowed = _ALLOWED_TRANSITIONS.get(prop.verification_status, [])
        if request.verification_status not in allowed:
            raise InvalidStatusTransitionError(
                current=prop.verification_status.value,
                target=request.verification_status.value,
            )

        prop.verification_status = request.verification_status
        prop.rejection_reason = request.rejection_reason

        try:
            await self.uow.commit()
        except Exception as exc:
            await self.uow.rollback()
            raise SetVisibilityError(cause=exc, context={"property_id": str(property_id)}) from exc

        try:
            await self.cache.delete(key=[
                cache_property(property_id=property_id),
                client_properties(user_id=prop.owner_id),
                *[map_h3_cell(i) for i in [prop.h3_r9, prop.h3_r7]],
            ])
        except Exception:
            pass
