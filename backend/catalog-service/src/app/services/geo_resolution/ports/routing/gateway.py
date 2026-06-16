from typing import Protocol
from app.services.geo_resolution.schemas.isochrone import IsochroneRequest, IsochroneEntry

class RoutingGateway(Protocol):
    async def get_isochrones(self, *, req:IsochroneRequest) -> list[IsochroneEntry]: ...
