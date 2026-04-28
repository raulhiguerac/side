from pydantic import BaseModel, ConfigDict


class StrictBase(BaseModel):
    """Base schema with strict validation."""

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )
