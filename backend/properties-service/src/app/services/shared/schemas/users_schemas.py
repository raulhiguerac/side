import uuid

from pydantic import BaseModel, ConfigDict


class _ExternalSchema(BaseModel):
    model_config = ConfigDict(extra="ignore")


class ResolvedAccount(_ExternalSchema):
    account_id: uuid.UUID
    email: str
