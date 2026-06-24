import asyncio

import overpass
from overpass.errors import (
    MultipleRequestsError,
    OverpassSyntaxError,
    ServerLoadError,
    UnknownOverpassError,
)
from requests.exceptions import ConnectionError, HTTPError, Timeout

from app.core.config.settings import settings
from app.core.exceptions.geo_resolution import GeoResolutionUnavailableError
from app.core.logging.logger import get_logger
from app.integrations.georef.pois.category_map import (
    AMENITY_TAGS,
    HEALTHCARE_TAGS,
    LEISURE_TAGS,
    PUBLIC_TRANSPORT_TAGS,
    SHOP_TAGS,
)

logger = get_logger(__name__)

QUERY_TEMPLATE = (
    "[out:json][timeout:{timeout}];"
    "("
    '  node["amenity"~"{amenity}"]{bbox};'
    '  node["shop"~"{shop}"]{bbox};'
    '  node["public_transport"~"{public_transport}"]{bbox};'
    '  node["leisure"~"{leisure}"]{bbox};'
    '  node["healthcare"~"{healthcare}"]{bbox};'
    '  way["amenity"~"{amenity}"]{bbox};'
    '  way["shop"~"{shop}"]{bbox};'
    '  way["public_transport"~"{public_transport}"]{bbox};'
    '  way["leisure"~"{leisure}"]{bbox};'
    '  way["healthcare"~"{healthcare}"]{bbox};'
    ");"
    "out center;"
)


class PoiClient:

    def __init__(self):
        self.api = overpass.API(
            timeout=settings.OVERPASS_TIMEOUT_SECONDS,
            headers={
                "User-Agent": settings.OVERPASS_USER_AGENT,
                "Accept-Charset": "utf-8;q=0.7,*;q=0.7",
            },
        )

    async def get_pois_by_bbox(self, *, bbox: list[float]) -> dict:
        bbox_str = f"({bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]})"
        query = QUERY_TEMPLATE.format(
            timeout=settings.OVERPASS_TIMEOUT_SECONDS,
            amenity=AMENITY_TAGS,
            shop=SHOP_TAGS,
            public_transport=PUBLIC_TRANSPORT_TAGS,
            leisure=LEISURE_TAGS,
            healthcare=HEALTHCARE_TAGS,
            bbox=bbox_str,
        )

        logger.info("overpass_query bbox=%s query=%s", bbox_str, query)
        try:
            response = await asyncio.to_thread(
                self.api.get, query, build=False,
            )
            logger.info("overpass_response elements=%d", len(response.get("elements", [])))
        except (ConnectionError, Timeout) as exc:
            logger.error("overpass_unreachable bbox=%s reason=%s", bbox, exc.__class__.__name__)
            raise GeoResolutionUnavailableError(
                cause=exc,
                context={"provider": "overpass", "bbox": bbox},
            )
        except HTTPError as exc:
            logger.error(
                "overpass_http_error bbox=%s status=%s",
                bbox,
                getattr(exc.response, "status_code", None),
            )
            raise GeoResolutionUnavailableError(
                cause=exc,
                context={"provider": "overpass", "bbox": bbox},
            )
        except OverpassSyntaxError as exc:
            logger.error("overpass_syntax_error bbox=%s reason=%s", bbox, exc.__class__.__name__)
            raise GeoResolutionUnavailableError(
                cause=exc,
                context={"provider": "overpass", "bbox": bbox},
            )
        except MultipleRequestsError as exc:
            logger.error("overpass_rate_limited bbox=%s reason=%s", bbox, exc.__class__.__name__)
            raise GeoResolutionUnavailableError(
                cause=exc,
                context={"provider": "overpass", "bbox": bbox},
            )
        except ServerLoadError as exc:
            logger.error("overpass_server_overloaded bbox=%s reason=%s", bbox, exc.__class__.__name__)
            raise GeoResolutionUnavailableError(
                cause=exc,
                context={"provider": "overpass", "bbox": bbox},
            )
        except UnknownOverpassError as exc:
            logger.error("overpass_unknown_error bbox=%s reason=%s", bbox, str(exc))
            raise GeoResolutionUnavailableError(
                cause=exc,
                context={"provider": "overpass", "bbox": bbox},
            )
        except Exception as exc:
            logger.error(
                "overpass_unexpected_error bbox=%s reason=%s: %s",
                bbox,
                exc.__class__.__name__,
                exc,
            )
            raise GeoResolutionUnavailableError(
                cause=exc,
                context={"provider": "overpass", "bbox": bbox},
            )

        return response
