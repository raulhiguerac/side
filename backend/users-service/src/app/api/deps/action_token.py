from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

http_bearer = HTTPBearer(auto_error=True)

async def get_action_token_from_bearer(
    credentials: HTTPAuthorizationCredentials = Depends(http_bearer),
) -> str:
    return credentials.credentials