import uuid
from typing import Protocol

from app.models.location import AdminDivision
from app.services.catalog_admin.schemas.admin_division import (
    GetAllAdminDivisionsRequest,
)


class AdminDivisionAdminRepository(Protocol):
    def get_all(self, *, filters: GetAllAdminDivisionsRequest) -> list[AdminDivision]: ...
    def count_all(self, *, filters: GetAllAdminDivisionsRequest) -> int: ...
    def get_by_id(self, *, admin_division_id: uuid.UUID) -> AdminDivision | None: ...
    def add(self, *, admin_division: AdminDivision) -> AdminDivision: ...
