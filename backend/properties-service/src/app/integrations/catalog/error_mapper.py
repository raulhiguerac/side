import httpx

from app.integrations.catalog.exceptions import CatalogClientError, NeighborhoodNotFoundError

_MAX_BODY_CHARS = 500


def map_response_error(response: httpx.Response) -> None:
    """Raises a typed exception based on the HTTP status code. No-op if response is ok."""
    if response.status_code == 404:
        raise NeighborhoodNotFoundError()
    if response.status_code >= 400:
        # The body carries the actual reason — a 422 from FastAPI names the field
        # that failed validation. Dropping it turns a contract mismatch into a
        # bare status code you have to reverse-engineer.
        raise CatalogClientError(
            f"Catalog service returned {response.status_code}: {_body_excerpt(response)}"
        )


def _body_excerpt(response: httpx.Response) -> str:
    try:
        body = response.text
    except Exception:
        return "<unreadable body>"

    body = body.strip()
    if not body:
        return "<empty body>"
    return body[:_MAX_BODY_CHARS] + ("…" if len(body) > _MAX_BODY_CHARS else "")
