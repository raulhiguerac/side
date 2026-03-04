from typing import Protocol

from app.models.location import FetchZone


class FetchZoneRepository(Protocol):
    def get_by_h3_index(self, *, h3_index: str) -> FetchZone | None: ...

    def add_or_update(self, *, fetch_zone: FetchZone) -> None: ...
