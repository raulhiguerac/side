import httpx

from app.integrations.catalog.exceptions import CatalogClientError, NeighborhoodNotFoundError


def map_response_error(response: httpx.Response) -> None:
    """Raises a typed exception based on the HTTP status code. No-op if response is ok."""
    if response.status_code == 404:
        raise NeighborhoodNotFoundError()
    if response.status_code >= 400:
        raise CatalogClientError(f"Catalog service returned {response.status_code}")
