from app.models.account import AccountType, UserProfile, CompanyProfile
from app.services.user.schemas.current import CurrentUserPerson, CurrentUserOrganization

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
        )

    return CurrentUserOrganization(
        display_name=profile_db.display_name,
        phone=profile_db.phone,
        photo_url=profile_db.photo_url,
        description=profile_db.description,
        intent=profile_db.intent,
        account_type="organization",
    )