import uuid

from sqlmodel import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.models.onboarding import OnboardingCompletions
from app.models.account import OnboardingStep
from app.services.user.ports.onboarding_completion_repository import (
    OnboardingCompletionRepository,
)
from app.services.shared.db.db_error_translator import DbErrorTranslator


class SqlOnboardingCompletionRepository(OnboardingCompletionRepository):
    def __init__(self, session: Session, db_errors: DbErrorTranslator) -> None:
        self._session = session
        self._db_errors = db_errors

    def mark_completed(self, *, account_id: uuid.UUID, key: OnboardingStep) -> bool:
        try:
            self._session.add(
                OnboardingCompletions(account_id=account_id, key=key)
            )
            self._session.flush()
            return True

        except IntegrityError as exc:
            pgcode, constraint_name, _ = self._db_errors._extract_pg_details(exc)

            if pgcode == "23505" and constraint_name in {
                "uq_user_onboarding_step",
                "onboarding_completions_pkey",
            }:
                return False

            raise self._db_errors.translate_integrity_error(exc) from exc

        except SQLAlchemyError as exc:
            raise self._db_errors.translate_sqlalchemy_error(
                exc,
                message="Database error while marking onboarding step completed",
                code="ONBOARDING_COMPLETION_DB_ERROR",
            ) from exc
