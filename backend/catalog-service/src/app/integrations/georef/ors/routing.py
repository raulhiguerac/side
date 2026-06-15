import asyncio
import os

import httpx

from app.core.exceptions.geo_resolution import GeoResolutionUnavailableError
from app.core.logging.logger import get_logger
from app.services.geo_resolution.schemas.isochrone import IsochroneProfileResult, IsochroneRequest

logger = get_logger(__name__)


class OrsRoutingClient:
    def __init__(self):
        base_url = os.getenv("ORS_URL")
        if not base_url:
            raise ValueError("ORS_URL is not set")

        self.base_url = base_url
        self.timeout = 5.0

    async def _fetch_profile(self, client: httpx.AsyncClient, url: str, body: dict, profile: str) -> tuple:
        logger.info("ors_isochrone_request profile=%s", profile)
        response = await client.post(url, json=body)
        logger.info("ors_isochrone_response profile=%s status=%d", profile, response.status_code)
        return response.status_code, response.json(), profile

    async def get_isochrone(self, req: IsochroneRequest) -> list[IsochroneProfileResult]:
        profiles = req.profile
        body = {
            "locations": [[req.lon, req.lat]],
            "range": req.range_seconds,
        }
        urls = [f"{self.base_url}/v2/isochrones/{profile}" for profile in profiles]

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                tasks = [
                    self._fetch_profile(client, url, body, profile)
                    for url, profile in zip(urls, profiles)
                ]
                results = await asyncio.gather(*tasks)

            geo_responses = []

            for status, response, profile in results:
                if status != 200:
                    logger.warning(
                        "ors_isochrone_non_200 profile=%s status=%d body=%s",
                        profile, status, response,
                    )
                    geo_responses.append(
                        IsochroneProfileResult(
                            profile=profile,
                            error=str(status),
                        )
                    )
                    continue

                geo_responses.append(
                    IsochroneProfileResult(
                        profile=profile,
                        features=response.get("features"),
                    )
                )

            return geo_responses

        except httpx.TimeoutException as exc:
            logger.error(
                "ors_timeout",
                extra={"extra": {"profiles": profiles, "reason": str(exc)}},
            )
            raise GeoResolutionUnavailableError(
                cause=exc,
                context={"provider": "ors", "profiles": profiles},
            )

        except httpx.ConnectError as exc:
            logger.error(
                "ors_unreachable",
                extra={"extra": {"profiles": profiles, "reason": str(exc)}},
            )
            raise GeoResolutionUnavailableError(
                cause=exc,
                context={"provider": "ors", "profiles": profiles},
            )

        except Exception as exc:
            logger.error(
                "ors_unexpected_error",
                extra={"extra": {"profiles": profiles, "reason": str(exc)}},
            )
            raise GeoResolutionUnavailableError(
                cause=exc,
                context={"provider": "ors", "profiles": profiles},
            )
