import os
import uuid

import httpx

from app.integrations.users.error_mapper import map_response_error
from app.integrations.users.exceptions import UsersClientError


class UsersClient:
    def __init__(self) -> None:
        self.base_url = os.getenv("USERS_URL")
        if not self.base_url:
            raise UsersClientError("USERS_URL is not set")
        self.timeout = 30.0

    async def resolve_by_emails(self, *, emails: list[str]) -> list[tuple[uuid.UUID, str]]:
        """Returns (account_id, email) pairs for the active accounts among `emails`.
        Unknown or inactive emails are simply absent from the response."""
        url = f"{self.base_url}/v1/users/resolve"
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=emails)

            map_response_error(response)

            try:
                return response.json()
            except Exception as e:
                raise UsersClientError("Users service returned invalid JSON") from e

        except UsersClientError:
            raise
        except httpx.TimeoutException as e:
            raise UsersClientError("Users service timed out") from e
        except httpx.RequestError as e:
            raise UsersClientError("Could not reach users service") from e
