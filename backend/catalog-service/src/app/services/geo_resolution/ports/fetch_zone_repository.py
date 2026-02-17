from typing import Protocol

from app.models.location import FetchZone


class FetchZoneRepository(Protocol):
    def get_by_geohash(self, *, geohash: str) -> FetchZone | None: ...

    def add(self, *, fetch_zone: FetchZone) -> None: ...
