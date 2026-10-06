import uuid
from functools import partial

from fastapi.concurrency import run_in_threadpool

from app.core.exceptions.listing import InvalidStatusTransitionError, PropertyNotFoundError, SetVisibilityError
from app.models.listing import VerificationStatus
from app.schemas.principal import Principal
from app.services.admin.ports.unit_of_work import AdminUnitOfWork
from app.services.admin.schemas.admin_schemas import VerifyPropertyRequest
from app.services.shared.helpers.cache_keys import cache_property, client_properties, map_h3_cell
from app.services.shared.helpers.status_transitions import VERIFICATION_TRANSITIONS
from app.services.shared.ports.cache import CachePort

# Estados en los que la verificación quedó resuelta por un admin concreto.
_RESOLVED_STATES = (VerificationStatus.verified, VerificationStatus.rejected)


class VerifyPropertyUseCase:
    def __init__(self, *, uow: AdminUnitOfWork, cache: CachePort) -> None:
        self.uow = uow
        self.cache = cache

    async def execute(
        self,
        *,
        principal: Principal,
        property_id: uuid.UUID,
        request: VerifyPropertyRequest,
    ) -> None:
        prop = await run_in_threadpool(
            partial(self.uow.properties.get_by_id, property_id=property_id)
        )

        if prop is None:
            raise PropertyNotFoundError(property_id=property_id)

        allowed = VERIFICATION_TRANSITIONS.get(prop.verification_status, [])
        if request.verification_status not in allowed:
            raise InvalidStatusTransitionError(
                current=prop.verification_status.value,
                target=request.verification_status.value,
            )

        prop.verification_status = request.verification_status
        prop.rejection_reason = request.rejection_reason
        prop.updated_by = principal.sub

        # `verified_by` es "quién resolvió la verificación", así que lo firma
        # tanto aprobar como rechazar. `updated_by` no sirve para esto: lo pisa
        # la siguiente escritura de cualquiera, incluida la del dueño.
        # Reencolar borra la firma junto con el motivo — la resolución anterior
        # dejó de valer.
        prop.verified_by = (
            principal.sub
            if request.verification_status in _RESOLVED_STATES
            else None
        )

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
