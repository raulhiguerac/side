import re

from sqlalchemy.exc import IntegrityError, OperationalError

from app.core.exceptions.catalog_admin import (
    CatalogAdminDbUnavailableError,
    CountryConflictError,
    AdminDivisionConflictError,
    LocalityConflictError,
    NeighborhoodConflictError,
)

# Maps PostgreSQL constraint name → conflict error factory.
# Constraint names come from UniqueConstraint/unique=True definitions in models.
_CONSTRAINT_MAP = {
    "countries_iso_alpha2_key": lambda f, v: CountryConflictError(field=f, value=v),
    "countries_iso_alpha3_key": lambda f, v: CountryConflictError(field=f, value=v),
    "countries_iso_numeric_key": lambda f, v: CountryConflictError(field=f, value=v),
    "uq_admin_div_country_code": lambda f, v: AdminDivisionConflictError(field=f, value=v),
    "uq_locality_country_code": lambda f, v: LocalityConflictError(field=f, value=v),
    "uq_neighborhood_locality_code": lambda f, v: NeighborhoodConflictError(field=f, value=v),
}


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
        return exc

    if isinstance(exc, OperationalError):
        return CatalogAdminDbUnavailableError(cause=exc)

    return exc
