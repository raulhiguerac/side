import os
import uuid

import httpx

from app.integrations.catalog.error_mapper import map_response_error
from app.integrations.catalog.exceptions import CatalogClientError


class CatalogClient:
    def __init__(self) -> None:
        self.base_url = os.getenv("CATALOG_URL")
        if not self.base_url:
            raise CatalogClientError("CATALOG_URL is not set")
        self.timeout = 2.0

    async def get_neighborhood(self, *, neighborhood_id: uuid.UUID) -> dict:
        url = f"{self.base_url}/v1/neighborhoods/by-id"
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, params={"neighborhood_id": neighborhood_id})

            map_response_error(response)

            try:
                return response.json()
            except Exception as e:
                raise CatalogClientError("Catalog service returned invalid JSON") from e

        except CatalogClientError:
            raise
        except httpx.TimeoutException as e:
            raise CatalogClientError("Catalog service timed out") from e
        except httpx.RequestError as e:
            raise CatalogClientError("Could not reach catalog service") from e

    async def get_locations_bulk(self, *, points: list[dict]) -> list[dict]:
        url = f"{self.base_url}/v1/geo-resolution/by-coordinates/bulk"
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, json=points)

            map_response_error(response)

            try:
                return response.json()
            except Exception as e:
                raise CatalogClientError("Catalog service returned invalid JSON") from e

        except CatalogClientError:
            raise
        except httpx.TimeoutException as e:
            raise CatalogClientError("Catalog service timed out") from e
        except httpx.RequestError as e:
            raise CatalogClientError("Could not reach catalog service") from e
