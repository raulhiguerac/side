from app.services.auth.services.reset_password_mailer import ResetPasswordMailer

class RequestResetPasswordUseCase:
    def __init__(
        self,
        *,
        uow: UserUnitOfWork,
        cache_client: CachePort,
        reactivation_mailer: ResetPasswordMailer,
    ) -> None:
        self.uow = uow
        self.cache = cache_client
        self.reactivation_mailer = reactivation_mailer