import uuid
from typing import Optional

from app.core.exceptions.base import BaseError


class OnboardingCityInterestNotFoundError(BaseError):
    def __init__(self, *, account_id: uuid.UUID, locality_id: uuid.UUID):
        super().__init__(
            message="No city interest found for this locality. Complete city interest step first.",
            code="CITY_INTEREST_NOT_FOUND",
            context={"account_id": str(account_id), "locality_id": str(locality_id)},
        )


class PropertyTypeNotAllowedError(BaseError):
    def __init__(self, *, value: str):
        super().__init__(
            message=f"Property type '{value}' is not allowed.",
            code="PROPERTY_TYPE_NOT_ALLOWED",
            context={"value": value},
        )


class NeighborhoodRankOutOfRangeError(BaseError):
    def __init__(self, *, rank: int):
        super().__init__(
            message=f"Interest rank {rank} is out of range. Must be between 1 and 5.",
            code="NEIGHBORHOOD_RANK_OUT_OF_RANGE",
            context={"rank": str(rank)},
        )


class AccountDisabledError(BaseError):
    def __init__(self, *, account_id: Optional[uuid.UUID] = None, email: Optional[str] = None):
        context: dict[str, str] = {}
        if account_id:
            context = {"account_id": str(account_id)}
        if email:
            context["email"] = email

        super().__init__(
            message="Account disabled",
            code="ACCOUNT_DISABLED",
            context=context,
        )

class ProfileNotFoundError(BaseError):
    def __init__(self, *, account_id: Optional[uuid.UUID] = None):
        context: dict[str, str] = {}
        if account_id:
            context = {"account_id": str(account_id)}

        super().__init__(
            message="Account not found",
            code="ACCOUNT_NOT_FOUND",
            context=context,
        )