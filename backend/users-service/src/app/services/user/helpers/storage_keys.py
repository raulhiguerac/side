import uuid

def profile_photo_storage_key(account_id: uuid.UUID) -> str:
    return f"accounts/{account_id}/profile/photo"