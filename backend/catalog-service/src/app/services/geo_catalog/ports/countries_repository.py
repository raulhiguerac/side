from typing import Protocol

from app.models.location import Country


class CountryRepository(Protocol):
    def get_active_countries(self) -> list[Country]: ...