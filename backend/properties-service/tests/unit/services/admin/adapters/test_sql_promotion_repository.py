import uuid
from unittest.mock import MagicMock

import pytest

from app.services.admin.adapters.sql_promotion_repository import SqlPromotionRepository

PROP_ID = uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")


@pytest.fixture
def session():
    return MagicMock()


@pytest.fixture
def repo(session):
    return SqlPromotionRepository(session)


def _executed_sql(session) -> str:
    return str(session.exec.call_args.args[0]).lower()


def test_get_all_paginates_by_offset(repo, session):
    repo.get_all(offset=40, limit=20)

    sql = _executed_sql(session)
    assert "limit" in sql
    assert "offset" in sql


def test_get_all_orders_by_priority_then_expiry_with_tiebreak(repo, session):
    """Sin orden total, dos promociones con igual prioridad y fecha pueden
    intercambiarse entre queries y el offset repetiría o saltearía filas."""
    repo.get_all(offset=0, limit=20)

    sql = _executed_sql(session)
    order_by = sql.split("order by")[1]
    assert order_by.index("priority") < order_by.index("ends_at") < order_by.index("promoted_listings.id")
    assert "priority desc" in order_by


def test_get_all_only_returns_valid_promotions(repo, session):
    repo.get_all(offset=0, limit=20)

    sql = _executed_sql(session)
    assert "is_active" in sql
    assert "ends_at > now()" in sql


def test_count_all_filters_the_same_as_get_all(repo, session):
    """Si una filtra y la otra no, el total miente sin que nada falle."""
    repo.count_all()

    sql = _executed_sql(session)
    assert "count" in sql
    assert "is_active" in sql
    assert "ends_at > now()" in sql


def test_get_active_by_property_id_ignores_expired(repo, session):
    """Es el guard de duplicados: una promoción vencida no debe bloquear una
    nueva. La contracara es que tampoco se puede borrar por el DELETE."""
    repo.get_active_by_property_id(property_id=PROP_ID)

    sql = _executed_sql(session)
    assert "ends_at > now()" in sql


def test_repository_has_no_by_property_listing():
    """`get_all_by_property_id` se fue con el endpoint que lo usaba."""
    assert not hasattr(SqlPromotionRepository, "get_all_by_property_id")
