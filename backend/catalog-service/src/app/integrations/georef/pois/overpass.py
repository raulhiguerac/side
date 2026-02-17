import asyncio

import overpass
from requests.exceptions import ConnectionError, Timeout, HTTPError

from app.core.exceptions.geo_resolution import GeoResolutionUnavailableError
from app.core.logging.logger import get_logger

logger = get_logger(__name__)

AMENITY_TAGS = "|".join([
    "restaurant", "cafe", "fast_food",
    "school", "kindergarten", "university",
    "hospital", "clinic", "pharmacy",
    "bank", "atm",
    "bus_station", "fuel",
])

LEISURE_TAGS = "|".join([
    "park", "playground",
    "fitness_centre", "sports_centre",
])

SHOP_TAGS = "|".join([
    "supermarket", "mall", "convenience",
])

QUERY_TEMPLATE = (
    "("
    '  node["amenity"~"{amenity}"]{bbox};'
    '  node["leisure"~"{leisure}"]{bbox};'
    '  node["shop"~"{shop}"]{bbox};'
    '  way["amenity"~"{amenity}"]{bbox};'
    '  way["leisure"~"{leisure}"]{bbox};'
    '  way["shop"~"{shop}"]{bbox};'
    ");"
    "out center;"
)


class PoiClient:

    def __init__(self):
        self.api = overpass.API(timeout=30)

    async def get_pois_by_bbox(self, *, bbox: list[float]) -> dict:
        bbox_str = f"({bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]})"
        query = QUERY_TEMPLATE.format(
            amenity=AMENITY_TAGS,
            leisure=LEISURE_TAGS,
            shop=SHOP_TAGS,
            bbox=bbox_str,
        )

        try:
            response = await asyncio.to_thread(
                self.api.get, query, build=False,
            )
        except (ConnectionError, Timeout) as exc:
            logger.error(
                "overpass_unreachable",
                extra={"extra": {"bbox": bbox, "reason": exc.__class__.__name__}},
            )
            raise GeoResolutionUnavailableError(
                cause=exc,
                context={"provider": "overpass", "bbox": bbox},
            )
        except HTTPError as exc:
            logger.error(
                "overpass_http_error",
                extra={"extra": {"bbox": bbox, "status": getattr(exc.response, "status_code", None)}},
            )
            raise GeoResolutionUnavailableError(
                cause=exc,
                context={"provider": "overpass", "bbox": bbox},
            )
        except Exception as exc:
            logger.error(
                "overpass_unexpected_error",
                extra={"extra": {"bbox": bbox, "reason": str(exc)}},
            )
            raise GeoResolutionUnavailableError(
                cause=exc,
                context={"provider": "overpass", "bbox": bbox},
            )

        return response
