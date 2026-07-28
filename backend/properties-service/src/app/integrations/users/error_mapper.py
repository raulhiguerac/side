import httpx

from app.integrations.users.exceptions import UsersClientError


def map_response_error(response: httpx.Response) -> None:
    """Raises a typed exception based on the HTTP status code. No-op if response is ok."""
    if response.status_code >= 400:
        raise UsersClientError(f"Users service returned {response.status_code}")
