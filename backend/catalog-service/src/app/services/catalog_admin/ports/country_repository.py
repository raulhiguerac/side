import uuid
from typing import Optional, Protocol

from app.models.location import Country


class CountryAdminRepository(Protocol):
    def get_by_id(self, *, country_id: uuid.UUID) -> Optional[Country]: ...
    def add(self, *, country: Country) -> Country: ...
