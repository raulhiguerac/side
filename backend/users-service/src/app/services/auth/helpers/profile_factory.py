import uuid
from app.models.account import AccountType, UserProfile, CompanyProfile
from app.services.auth.schemas.registration import RegisterRequest

class ProfileFactory:
    def from_register(self, *, req: RegisterRequest, account_id: uuid.UUID):
        match req.account_type:
            case AccountType.person:
                return UserProfile(
                    account_id=account_id,
                    first_name=req.first_name,
                    last_name=req.last_name,
                    phone=req.phone,
                    intent=getattr(req, "intent", None),
                    photo_url=getattr(req, "photo_url", None),
                    description=getattr(req, "description", None),
                    profile_score=10,
                )
            case AccountType.organization:
                return CompanyProfile(
                    account_id=account_id,
                    display_name=req.display_name,
                    phone=req.phone,
                    intent=getattr(req, "intent", None),
                    photo_url=getattr(req, "photo_url", None),
                    description=getattr(req, "description", None),
                    profile_score=10,
                )
            case _:
                return None