import os
import asyncio

import mapbox
from mapbox.errors import ValidationError
from requests.exceptions import ConnectionError, Timeout, HTTPError

from app.core.exceptions.geo_resolution import (
    GeoResolutionBadRequestError,
    GeoResolutionMisconfiguredError,
    GeoResolutionNotFoundError,
    GeoResolutionUnavailableError,
)
from app.core.logging.logger import get_logger

logger = get_logger(__name__)


class GeoreferentiationClient:
    def __init__(self):
        self.mapbox_token = os.getenv("MAPBOX_API_KEY")
        if not self.mapbox_token:
            raise GeoResolutionMisconfiguredError(context={"missing": "MAPBOX_API_KEY"})

    async def forward_geocoding(self, *, address: str, country_code: str) -> dict:
        geocoder = mapbox.Geocoder(access_token=self.mapbox_token)
        try:
            response = await asyncio.to_thread(geocoder.forward, address, country=[country_code])
            response.raise_for_status()
        except ValidationError as exc:
            raise GeoResolutionBadRequestError(
                cause=exc,
                context={"address": address},
            )
        except (ConnectionError, Timeout) as exc:
            logger.error(
                "mapbox_unreachable",
                extra={"extra": {"address": address, "reason": exc.__class__.__name__}},
            )
            raise GeoResolutionUnavailableError(
                cause=exc,
                context={"address": address},
            )
        except HTTPError as exc:
            logger.error(
                "mapbox_http_error",
                extra={"extra": {"address": address, "status": exc.response.status_code}},
            )
            raise GeoResolutionUnavailableError(
                cause=exc,
                context={"address": address, "status": exc.response.status_code},
            )

        geojson = response.geojson()
        if not geojson.get("features"):
            raise GeoResolutionNotFoundError(address=address)

        return geojson
