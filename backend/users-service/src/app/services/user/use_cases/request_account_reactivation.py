from app.services.user.ports.cache import CachePort
from app.services.user.ports.unit_of_work import UserUnitOfWork

class ReactivateAccountUseCase:
    def __init__(
        self,
        *,
        uow: UserUnitOfWork,
        cache_client: CachePort,
    ) -> None:
        self.uow = uow
        self.cache = cache_client