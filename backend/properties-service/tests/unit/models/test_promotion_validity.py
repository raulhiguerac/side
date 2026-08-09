"""La definición de 'promoción vigente' y quiénes la aplican.

Son tests de SQL compilado, no de base de datos: lo que se verifica es que todas
las lecturas que deciden vigencia lleven la misma condición. Una que se olvide
del `ends_at` deja volver una promoción vencida por ese camino y por ninguno
otro — exactamente el drift que el predicado compartido viene a evitar.
"""

import uuid

import pytest
from sqlalchemy.orm import configure_mappers
from sqlmodel import func, select

from app.models.listing import Property
from app.models.promotion import PromotedListing, active_promotion_clause
from app.services.admin.adapters.sql_property_repository import SqlAdminPropertyRepository

PROP_ID = uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")


def _sql(stmt) -> str:
    return str(stmt).lower()


def test_clause_requires_active_and_not_expired():
    sql = _sql(select(PromotedListing).where(active_promotion_clause()))

    assert "is_active" in sql
    assert "ends_at > now()" in sql


def test_clause_uses_database_now_not_python():
    """Con `datetime.now()` el corte quedaría congelado en el import del módulo."""
    sql = _sql(select(PromotedListing).where(active_promotion_clause()))

    assert "now()" in sql
    assert "ends_at > :" not in sql  # no viaja como parámetro bindeado


def test_property_promotions_relationship_filters_expiry():
    """De esta relación sale `is_promoted` en las cards del feed."""
    configure_mappers()

    primaryjoin = str(Property.promotions.property.primaryjoin).lower()

    assert "is_active" in primaryjoin
    assert "now()" in primaryjoin


@pytest.mark.parametrize(
    "is_promoted, expected",
    [
        (True, "exists"),
        (False, "not (exists"),
    ],
)
def test_is_promoted_filter_uses_exists(is_promoted, expected):
    """`EXISTS` y no `JOIN`: con join una property con varias promociones
    duplicaría filas y el `count_all` dejaría de coincidir con las devueltas."""
    sql = _sql(
        SqlAdminPropertyRepository._apply_filters(
            select(func.count()).select_from(Property),
            status=None,
            verification_status=None,
            owner_id=None,
            is_promoted=is_promoted,
        )
    )

    assert expected in sql
    assert "ends_at > now()" in sql


def test_is_promoted_absent_adds_no_subquery():
    sql = _sql(
        SqlAdminPropertyRepository._apply_filters(
            select(func.count()).select_from(Property),
            status=None,
            verification_status=None,
            owner_id=None,
            is_promoted=None,
        )
    )

    assert "exists" not in sql
