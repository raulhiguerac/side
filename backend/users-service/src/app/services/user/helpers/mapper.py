from app.models.account import AccountType, CompanyProfile, UserProfile
from app.services.user.schemas.current import CurrentUserOrganization, CurrentUserPerson


def map_profile_db_to_schema(
    account_type: AccountType,
    profile_db: UserProfile | CompanyProfile,
) -> CurrentUserPerson | CurrentUserOrganization:

    if account_type == AccountType.person:
        return CurrentUserPerson(
            first_name=profile_db.first_name,
            last_name=profile_db.last_name,
            phone=profile_db.phone,
            photo_url=profile_db.photo_url,
            description=profile_db.description,
            intent=profile_db.intent,
            account_type="person",
            created_at=profile_db.created_at,
        )

    return CurrentUserOrganization(
        display_name=profile_db.display_name,
        phone=profile_db.phone,
        photo_url=profile_db.photo_url,
        description=profile_db.description,
        intent=profile_db.intent,
        account_type="organization",
        created_at=profile_db.created_at,
    )