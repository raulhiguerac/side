import re

from sqlalchemy.exc import IntegrityError, OperationalError

from app.core.exceptions.listing import CreatePropertyError, PropertyDbUnavailableError

# Maps PostgreSQL constraint name → conflict error factory.
# Add entries here as new unique constraints are added to the property models.
_CONSTRAINT_MAP: dict = {}


def _parse_integrity_error(exc: IntegrityError) -> tuple[str, str, str]:
    """Returns (constraint_name, field, value) parsed from the PG error string."""
    text = str(exc)

    constraint = ""
    constraint_match = re.search(r'constraint "(.+?)"', text)
    if constraint_match:
        constraint = constraint_match.group(1)

    field, value = "unknown", "unknown"
    detail_match = re.search(r'Key \((.+?)\)=\((.+?)\) already exists', text)
    if detail_match:
        field = detail_match.group(1)
        value = detail_match.group(2)

    return constraint, field, value


def translate_db_error(exc: Exception) -> Exception:
    """
    Translates SQLAlchemy low-level exceptions into domain exceptions.

    Usage in use cases:
        except Exception as exc:
            await self.uow.rollback()
            raise translate_db_error(exc) from exc
    """
    if isinstance(exc, IntegrityError):
        constraint, field, value = _parse_integrity_error(exc)
        factory = _CONSTRAINT_MAP.get(constraint)
        if factory:
            return factory(field, value)
        return CreatePropertyError(cause=exc, context={"constraint": constraint, "field": field, "value": value})

    if isinstance(exc, OperationalError):
        return PropertyDbUnavailableError(cause=exc)

    return CreatePropertyError(cause=exc, context={"reason": type(exc).__name__})
