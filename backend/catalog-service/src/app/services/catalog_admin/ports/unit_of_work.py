from typing import Protocol

from app.services.catalog_admin.ports.country_repository import CountryAdminRepository
from app.services.catalog_admin.ports.admin_division_repository import AdminDivisionAdminRepository
from app.services.catalog_admin.ports.locality_repository import LocalityAdminRepository
from app.services.catalog_admin.ports.neighborhood_repository import NeighborhoodAdminRepository


class CatalogAdminUnitOfWork(Protocol):
    countries: CountryAdminRepository
    admin_divisions: AdminDivisionAdminRepository
    localities: LocalityAdminRepository
    neighborhoods: NeighborhoodAdminRepository

    async def commit(self) -> None: ...
    async def rollback(self) -> None: ...
