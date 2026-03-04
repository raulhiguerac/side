from app.core.config.settings import settings
import uuid
from functools import partial
from fastapi.concurrency import run_in_threadpool

from app.services.shared.ports.cache import CachePort
from app.services.geo_resolution.ports.geocoding_gateway import GeocodingGateway
from app.services.geo_resolution.ports.unit_of_work import GeoResolutionUnitOfWork

from app.services.geo_resolution.schemas.neighborhood import NeighborhoodInfo, ResolvedNeighborhood

from app.services.geo_resolution.helpers.cache_keys import cache_key_forward_geocode

from app.core.exceptions.geo_resolution import GeoResolutionNotFoundError, NeighborhoodResolutionError


class ResolveNeighborhoodUseCase:
    def __init__(
        self,
        *,
        uow: GeoResolutionUnitOfWork,
        cache_client: CachePort,
        georef: GeocodingGateway,
    ) -> None:
        self.uow = uow
        self.cache = cache_client
        self.georef = georef

    async def execute(self, query: str, locality_id: uuid.UUID) -> ResolvedNeighborhood:
        lat, lon = await self._resolve_coordinates(query, locality_id)

        neighborhood = await run_in_threadpool(
            partial(
                self.uow.georef.get_neighborhood_by_coordinates,
                lat=lat, lon=lon, locality_id=locality_id,
            )
        )

        if not neighborhood:
            raise NeighborhoodResolutionError(
                latitude=lat,
                longitude=lon,
                locality_id=str(locality_id),
            )

        return ResolvedNeighborhood(
            neighborhood=NeighborhoodInfo.model_validate(neighborhood),
            latitude=lat,
            longitude=lon,
        )

    async def _resolve_coordinates(self, query: str, locality_id: uuid.UUID) -> tuple[float, float]:
        cache_key = cache_key_forward_geocode(query=query, locality_id=locality_id)

        try:
            cached = await self.cache.get_json(key=cache_key)
            if cached:
                return cached["lat"], cached["lon"]
        except Exception:
            pass

        country_code = await run_in_threadpool(
            partial(self.uow.georef.get_locality_country_code, locality_id=locality_id)
        )
        if not country_code:
            raise GeoResolutionNotFoundError(address=query)

        proximity = await run_in_threadpool(
            partial(self.uow.georef.get_locality_coordinates, locality_id=locality_id)
        )

        result = await self.georef.forward_geocode(query=query, country_code=country_code, proximity=proximity)

        try:
            await self.cache.set_json(
                key=cache_key,
                value={"lat": result.latitude, "lon": result.longitude},
                ttl=settings.CACHE_TTL_ENTITY_SECONDS,
            )
        except Exception:
            pass

        return result.latitude, result.longitude
