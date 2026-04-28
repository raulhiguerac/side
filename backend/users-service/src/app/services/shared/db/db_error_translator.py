import uuid
from typing import Optional

from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.core.exceptions.auth import EmailAlreadyRegisteredError
from app.core.exceptions.base import BaseError
from app.core.logging.utils import email_hash


class DbErrorTranslator:
    """
    Traduce errores técnicos de SQLAlchemy/Postgres a errores de dominio (BaseError).
    Este módulo NO hace I/O, NO toca session, NO hace rollback.
    """

    def translate_integrity_error(
        self,
        exc: IntegrityError,
        *,
        email: Optional[str] = None,
        kc_user_id: Optional[uuid.UUID] = None,
    ) -> BaseError:
        pgcode, constraint_name, column_name = self._extract_pg_details(exc)

        ctx = {
            "constraint_name": constraint_name,
            "kc_user_id": kc_user_id
        }
        if email:
            ctx["email_hash"] = email_hash(email)

        if pgcode == "23505":
            if constraint_name in {"accounts_email_key", "uq_accounts_email"}:
                return EmailAlreadyRegisteredError(email=email)

            return BaseError(
                message="Unique constraint violated",
                code="UNIQUE_CONSTRAINT_VIOLATION",
                context={
                    "constraint_name": constraint_name,
                    "email_hash": email_hash(email),
                    "kc_user_id": str(kc_user_id) if kc_user_id else None,
                },
                cause=exc,
            )

        if pgcode == "23502":
            return BaseError(
                message=f"Missing required field: {column_name or 'unknown'}",
                code="MISSING_REQUIRED_FIELD",
                context={
                    "field": column_name,
                    "email_hash": email_hash(email),
                    "kc_user_id": str(kc_user_id) if kc_user_id else None,
                },
                cause=exc,
            )

        if pgcode == "23503":
            return BaseError(
                message="Foreign key constraint violated",
                code="FOREIGN_KEY_VIOLATION",
                status_code=409,
                context={
                    "constraint_name": constraint_name,
                    "email_hash": email_hash(email),
                    "kc_user_id": str(kc_user_id) if kc_user_id else None,
                },
                cause=exc,
            )

        return BaseError(
            message="Database integrity error while processing request",
            code="DATABASE_INTEGRITY_ERROR",
            context={
                "pgcode": pgcode,
                "constraint_name": constraint_name,
                "email_hash": email_hash(email),
                "kc_user_id": str(kc_user_id) if kc_user_id else None,
            },
            cause=exc,
        )

    def translate_sqlalchemy_error(
        self,
        exc: SQLAlchemyError,
        *,
        email: Optional[str] = None,
        kc_user_id: Optional[uuid.UUID] = None,
        message: str = "Database error",
        code: str = "DATABASE_ERROR",
    ) -> BaseError:
        ctx = {
            "kc_user_id": str(kc_user_id) if kc_user_id else None,
        }
        if email:
            ctx["email_hash"] = email_hash(email)

        return BaseError(
            message=message,
            code=code,
            context=ctx,
            cause=exc,
        )

    def _extract_pg_details(self, exc: IntegrityError) -> tuple[Optional[str], Optional[str], Optional[str]]:
        orig = getattr(exc, "orig", None)
        pgcode = getattr(orig, "pgcode", None)

        diag = getattr(orig, "diag", None)
        constraint_name = getattr(diag, "constraint_name", None) if diag else None
        column_name = getattr(diag, "column_name", None) if diag else None

        return pgcode, constraint_name, column_name
