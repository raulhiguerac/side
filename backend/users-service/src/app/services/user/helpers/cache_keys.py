import uuid

def account_cache_key(account_id: uuid.UUID) -> str:
    return f"account:{account_id}"

def profile_cache_key(account_id: uuid.UUID) -> str:
    return f"profile:{account_id}"

def reactivation_cache_key(token_hash: str) -> str:
    return f"auth:reactivation:{token_hash}"

def reset_password_cache_key(token_hash: str) -> str:
    return f"auth:reset-password:{token_hash}"