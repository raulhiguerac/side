import uuid
from typing import Optional, Protocol

from app.models.location import AdminDivision


class AdminDivisionAdminRepository(Protocol):
    def get_by_id(self, *, admin_division_id: uuid.UUID) -> Optional[AdminDivision]: ...
    def add(self, *, admin_division: AdminDivision) -> AdminDivision: ...
