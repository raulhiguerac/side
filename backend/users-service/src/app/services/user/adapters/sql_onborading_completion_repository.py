import uuid

from sqlalchemy import inspect
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlmodel import Session, select

from app.models.account import OnboardingStep
from app.models.interests import (
    UserInterest,
    UserNeighborhoodInterest,
    UserPropertyTypeInterest,
)
from app.models.onboarding import OnboardingCompletions
from app.services.shared.db.db_error_translator import DbErrorTranslator
from app.services.user.ports.onboarding_completion_repository import (
    OnboardingCompletionRepository,
)

_EXCLUDED_FROM_UPSERT = {"user_interest_id", "created_at", "updated_at"}
_UPSERT_FIELDS = [
    c for c in inspect(UserNeighborhoodInterest).columns.keys() if c not in _EXCLUDED_FROM_UPSERT
]

class SqlOnboardingCompletionRepository(OnboardingCompletionRepository):
    def __init__(self, session: Session, db_errors: DbErrorTranslator) -> None:
        self._session = session
        self._db_errors = db_errors
    
    def get_interest_by_account_locality(
        self,
        *,
        account_id: uuid.UUID,
        locality_id: uuid.UUID
    ) -> uuid.UUID:
        try:
            stmt = select(UserInterest.id) \
                   .where(UserInterest.account_id==account_id) \
                   .where(UserInterest.city_id==locality_id)
            
            return self._session.exec(stmt).first()
        except SQLAlchemyError as exc:
            raise self._db_errors.translate_sqlalchemy_error(
                exc,
                message="Database error while fetching city interest",
                code="ONBOARDING_COMPLETION_DB_ERROR",
            ) from exc

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
                message="Database error while marking onboarding step as completed",
                code="ONBOARDING_COMPLETION_DB_ERROR",
            ) from exc

    def save_locality(self, *, account_id: uuid.UUID, locality_id: uuid.UUID) -> None:
        try:
            stmt = (
                insert(UserInterest)
                .values(
                    id=uuid.uuid4(),
                    account_id=account_id,
                    city_id=locality_id,
                    is_active=True,
                )
                .on_conflict_do_update(
                    constraint="uq_user_interest_user_city",
                    set_={"is_active": True},
                )
            )
            self._session.execute(stmt)
            self._session.flush()
        except SQLAlchemyError as exc:
            raise self._db_errors.translate_sqlalchemy_error(
                exc,
                message="Database error while saving city interest",
                code="ONBOARDING_COMPLETION_DB_ERROR",
            ) from exc

    def save_neighborhoods(self, *, neighborhoods: list[UserNeighborhoodInterest]):
        try:
            stmt = insert(UserNeighborhoodInterest).values([
                n.model_dump(exclude={"created_at", "updated_at"}) for n in neighborhoods
            ])
            stmt = stmt.on_conflict_do_update(
                constraint="uq_user_interest_rank",
                set_={k: stmt.excluded[k] for k in _UPSERT_FIELDS},
            )
            self._session.execute(stmt)
            self._session.flush()

        except SQLAlchemyError as exc:
            raise self._db_errors.translate_sqlalchemy_error(
                exc,
                message="Database error while saving neighborhood interests",
                code="ONBOARDING_COMPLETION_DB_ERROR",
            ) from exc

    def save_property_type(self, *, properties: list[UserPropertyTypeInterest]):
        try:
            stmt = (
                insert(UserPropertyTypeInterest)
                .values([n.model_dump(exclude={"created_at", "updated_at"}) for n in properties])
                .on_conflict_do_nothing(index_elements=["user_interest_id", "property_type"])
            )
            self._session.execute(stmt)
            self._session.flush()

        except SQLAlchemyError as exc:
            raise self._db_errors.translate_sqlalchemy_error(
                exc,
                message="Database error while saving property type interests",
                code="ONBOARDING_COMPLETION_DB_ERROR",
            ) from exc