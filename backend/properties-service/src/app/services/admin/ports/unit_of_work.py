from typing import Protocol

from app.services.admin.ports.property_repository import AdminPropertyRepository
from app.services.admin.ports.promotion_repository import PromotionRepository


class AdminUnitOfWork(Protocol):
    properties: AdminPropertyRepository
    promotions: PromotionRepository

    async def commit(self) -> None: ...
    async def rollback(self) -> None: ...
    async def refresh(self, instance: object) -> None: ...