import h3
from functools import partial

from fastapi.concurrency import run_in_threadpool

from app.core.config.settings import settings
from app.core.exceptions.geo_resolution import CoordinatesResolutionNotFoundError
from app.services.geo_resolution.ports.unit_of_work import GeoResolutionUnitOfWork
from app.services.geo_resolution.schemas.neighborhood import LocationByCoordinates


class ResolveLocationByCoordinatesUseCase:
    def __init__(self, *, uow: GeoResolutionUnitOfWork) -> None:
        self.uow = uow

    async def execute(self, *, lat: float, lon: float) -> LocationByCoordinates:
        h3_cell = h3.latlng_to_cell(lat, lon, settings.H3_RESOLUTION)
        result = await run_in_threadpool(
            partial(
                self.uow.georef.get_location_by_point, 
                lat=lat, 
                lon=lon,
                cell = h3_cell
            )
        )

        if result is None:
            raise CoordinatesResolutionNotFoundError(latitude=lat, longitude=lon)

        return result
