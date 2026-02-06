import uuid
from typing import List, Protocol, Optional

from app.models.location import Locality

class LocalityRepository(Protocol):
    def get_active_by_country_id(
        self, *, country_id: uuid.UUID
    ) -> list[Locality]: ...

    def get_active_by_admin_division_id(
        self, *, admin_division_id: uuid.UUID
    ) -> list[Locality]: ...
