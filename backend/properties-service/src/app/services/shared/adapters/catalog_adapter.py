import uuid

from app.core.exceptions.listing import CatalogServiceUnavailableError, InvalidLocationError, LocationNotResolvedError
from app.integrations.catalog.catalog_client import CatalogClient
from app.integrations.catalog.exceptions import NeighborhoodNotFoundError
from app.services.shared.ports.catalog_gateway import CatalogGateway
from app.services.shared.schemas.catalog_schemas import LocationInfo, NeighborhoodInfo


class CatalogAdapter(CatalogGateway):
    def __init__(self, client: CatalogClient) -> None:
        self._client = client

    async def get_neighborhood(self, *, neighborhood_id: uuid.UUID) -> NeighborhoodInfo:
        try:
            neighborhood = await self._client.get_neighborhood(neighborhood_id=neighborhood_id)
            return NeighborhoodInfo.model_validate(neighborhood)
        except NeighborhoodNotFoundError as e:
            raise InvalidLocationError(neighborhood_id=neighborhood_id, cause=e) from e
        except Exception as e:
            raise CatalogServiceUnavailableError(cause=e) from e

    async def get_location_by_point(self, *, lat: float, lon: float) -> LocationInfo:
        try:
            data = await self._client.get_location_info(lat=lat, lon=lon)
            return LocationInfo.model_validate(data)
        except NeighborhoodNotFoundError as e:
            raise LocationNotResolvedError(lat=lat, lon=lon) from e
        except Exception as e:
            raise CatalogServiceUnavailableError(cause=e) from e