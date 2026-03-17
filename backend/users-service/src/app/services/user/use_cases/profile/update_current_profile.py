import os

from app.schemas.common import Principal
from app.services.shared.ports.cache import CachePort
from app.services.user.helpers.cache_keys import profile_cache_key
from app.services.user.helpers.current_account_reader import CurrentAccountReader
from app.services.user.helpers.current_profile_reader import CurrentProfileReader
from app.services.user.helpers.mapper import map_profile_db_to_schema
from app.services.user.ports.unit_of_work import UserUnitOfWork
from app.services.user.schemas.current import CurrentUserProfileOut
from app.services.user.schemas.update import UpdateRequest

PROFILE_CACHE_TTL_SECONDS = int(os.getenv("PROFILE_CACHE_TTL_SECONDS", "600"))

class UpdateCurrentProfileUseCase:
    def __init__(
            self, 
            *,
            uow: UserUnitOfWork,
            cache_client: CachePort,
            account_reader: CurrentAccountReader,
            profile_reader: CurrentProfileReader,
        ):
        self.uow = uow
        self.cache_client = cache_client
        self.account_reader = account_reader
        self.profile_reader = profile_reader
    
    async def execute(self, *, principal: Principal, req: UpdateRequest) -> CurrentUserProfileOut:
        account_id = principal.sub

        account = await self.account_reader.get_active(account_id=account_id)
        profile_db = await self.profile_reader.get_model(
            account_id=account_id, 
            account_type=account.account_type
        )

        data = req.model_dump(exclude_unset=True, exclude={"account_type"})
        for field, value in data.items():
            setattr(profile_db, field, value)
        
        try:
            await self.uow.commit()
        except:
            await self.uow.rollback()
            raise

        cache_key = profile_cache_key(account_id=account_id)

        out = CurrentUserProfileOut(
                profile=map_profile_db_to_schema(account.account_type, profile_db)
            )

        await self.cache_client.delete(key=cache_key)
        await self.cache_client.set(key=cache_key, value=out.model_dump_json(), ttl=PROFILE_CACHE_TTL_SECONDS)


        return out