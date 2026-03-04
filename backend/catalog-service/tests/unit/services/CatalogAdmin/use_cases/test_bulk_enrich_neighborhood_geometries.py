import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.catalog_admin.schemas.neighborhood import BulkEnrichNeighborhoodGeometriesResult
from app.services.catalog_admin.use_cases.bulk_enrich_neighborhood_geometries import BulkEnrichNeighborhoodGeometriesUseCase

LOCALITY_ID = uuid.UUID("c2eebc99-9c0b-4ef8-bb6d-6bb9bd380a33")

N1_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")
N2_ID = uuid.UUID("22222222-2222-2222-2222-222222222222")

GEOJSON = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "properties": {"name": "Chapinero"},
            "geometry": {"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 0]]]},
        },
        {
            "type": "Feature",
            "properties": {"name": "Usaquén"},
            "geometry": {"type": "Polygon", "coordinates": [[[2, 2], [3, 2], [3, 3], [2, 2]]]},
        },
    ],
}


def _make_neighborhood(neighborhood_id: uuid.UUID, search_name: str) -> MagicMock:
    n = MagicMock()
    n.id = neighborhood_id
    n.search_name = search_name
    return n


@pytest.fixture
def mock_uow():
    uow = MagicMock()
    uow.neighborhoods.get_many_by_search_names.return_value = [
        _make_neighborhood(N1_ID, "chapinero"),
        _make_neighborhood(N2_ID, "usaquen"),
    ]
    uow.neighborhoods.bulk_update.return_value = None
    uow.commit = AsyncMock()
    uow.rollback = AsyncMock()
    return uow


@pytest.fixture
def mock_cache():
    return AsyncMock()


@pytest.fixture
def uc(mock_uow, mock_cache):
    return BulkEnrichNeighborhoodGeometriesUseCase(uow=mock_uow, cache_client=mock_cache)


# ---------------------------------------------------------------------------
# Empty / no-op cases
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_returns_zero_when_no_features(uc, mock_uow):
    result = await uc.execute(locality_id=LOCALITY_ID, geojson={}, name_field="name")

    assert result == BulkEnrichNeighborhoodGeometriesResult(matched=0, unmatched=[], updated=0)
    mock_uow.neighborhoods.get_many_by_search_names.assert_not_called()


@pytest.mark.asyncio
async def test_returns_zero_when_features_lack_name_field(uc, mock_uow):
    geojson = {
        "features": [
            {"type": "Feature", "properties": {"other": "value"}, "geometry": {}},
        ]
    }

    result = await uc.execute(locality_id=LOCALITY_ID, geojson=geojson, name_field="name")

    assert result == BulkEnrichNeighborhoodGeometriesResult(matched=0, unmatched=[], updated=0)
    mock_uow.neighborhoods.get_many_by_search_names.assert_not_called()


@pytest.mark.asyncio
@patch("app.services.catalog_admin.use_cases.bulk_enrich_neighborhood_geometries.run_in_threadpool")
async def test_returns_zero_matched_when_no_db_match(mock_run, uc, mock_uow):
    mock_run.return_value = []  # DB no encontró ninguno

    result = await uc.execute(locality_id=LOCALITY_ID, geojson=GEOJSON, name_field="name")

    assert result.matched == 0
    assert result.updated == 0
    assert set(result.unmatched) == {"chapinero", "usaquen"}
    mock_uow.commit.assert_not_awaited()


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
@patch("app.services.catalog_admin.use_cases.bulk_enrich_neighborhood_geometries.geom_from_geojson")
@patch("app.services.catalog_admin.use_cases.bulk_enrich_neighborhood_geometries.run_in_threadpool")
async def test_full_match_updates_and_commits(mock_run, mock_geom, uc, mock_uow, mock_cache):
    mock_geom.return_value = MagicMock()
    neighborhoods = [
        _make_neighborhood(N1_ID, "chapinero"),
        _make_neighborhood(N2_ID, "usaquen"),
    ]
    mock_run.side_effect = [neighborhoods, None]  # get_many, bulk_update

    result = await uc.execute(locality_id=LOCALITY_ID, geojson=GEOJSON, name_field="name")

    assert result.matched == 2
    assert result.updated == 2
    assert result.unmatched == []
    mock_uow.commit.assert_awaited_once()


@pytest.mark.asyncio
@patch("app.services.catalog_admin.use_cases.bulk_enrich_neighborhood_geometries.geom_from_geojson")
@patch("app.services.catalog_admin.use_cases.bulk_enrich_neighborhood_geometries.run_in_threadpool")
async def test_partial_match_reports_unmatched(mock_run, mock_geom, uc, mock_uow, mock_cache):
    mock_geom.return_value = MagicMock()
    neighborhoods = [_make_neighborhood(N1_ID, "chapinero")]  # solo uno matcheó
    mock_run.side_effect = [neighborhoods, None]

    result = await uc.execute(locality_id=LOCALITY_ID, geojson=GEOJSON, name_field="name")

    assert result.matched == 1
    assert result.updated == 1
    assert result.unmatched == ["usaquen"]


# ---------------------------------------------------------------------------
# Cache invalidation
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
@patch("app.services.catalog_admin.use_cases.bulk_enrich_neighborhood_geometries.geom_from_geojson")
@patch("app.services.catalog_admin.use_cases.bulk_enrich_neighborhood_geometries.run_in_threadpool")
async def test_invalidates_cache_for_each_matched_neighborhood(mock_run, mock_geom, uc, mock_uow, mock_cache):
    mock_geom.return_value = MagicMock()
    neighborhoods = [
        _make_neighborhood(N1_ID, "chapinero"),
        _make_neighborhood(N2_ID, "usaquen"),
    ]
    mock_run.side_effect = [neighborhoods, None]

    await uc.execute(locality_id=LOCALITY_ID, geojson=GEOJSON, name_field="name")

    # 2 barrios + 1 lista de localidad = 3 deletes
    assert mock_cache.delete.await_count == 3


# ---------------------------------------------------------------------------
# name_field custom
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
@patch("app.services.catalog_admin.use_cases.bulk_enrich_neighborhood_geometries.geom_from_geojson")
@patch("app.services.catalog_admin.use_cases.bulk_enrich_neighborhood_geometries.run_in_threadpool")
async def test_uses_custom_name_field(mock_run, mock_geom, uc, mock_uow, mock_cache):
    """IDECA usa SCANOMBRE en vez de name."""
    mock_geom.return_value = MagicMock()
    geojson = {
        "features": [
            {
                "type": "Feature",
                "properties": {"SCANOMBRE": "Chapinero"},
                "geometry": {"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 0]]]},
            }
        ]
    }
    neighborhoods = [_make_neighborhood(N1_ID, "chapinero")]
    mock_run.side_effect = [neighborhoods, None]

    result = await uc.execute(locality_id=LOCALITY_ID, geojson=geojson, name_field="SCANOMBRE")

    assert result.matched == 1


# ---------------------------------------------------------------------------
# Normalization
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
@patch("app.services.catalog_admin.use_cases.bulk_enrich_neighborhood_geometries.geom_from_geojson")
@patch("app.services.catalog_admin.use_cases.bulk_enrich_neighborhood_geometries.run_in_threadpool")
async def test_normalizes_accents_before_lookup(mock_run, mock_geom, uc, mock_uow, mock_cache):
    """'Usaquén' y 'usaquen' deben considerarse el mismo nombre."""
    mock_geom.return_value = MagicMock()
    geojson = {
        "features": [
            {
                "type": "Feature",
                "properties": {"name": "Usaquén"},
                "geometry": {"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 0]]]},
            }
        ]
    }
    neighborhoods = [_make_neighborhood(N2_ID, "usaquen")]
    mock_run.side_effect = [neighborhoods, None]

    result = await uc.execute(locality_id=LOCALITY_ID, geojson=geojson, name_field="name")

    assert result.matched == 1
    assert result.unmatched == []


# ---------------------------------------------------------------------------
# Duplicate names
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
@patch("app.services.catalog_admin.use_cases.bulk_enrich_neighborhood_geometries.run_in_threadpool")
async def test_deduplicates_features_with_same_name(mock_run, uc, mock_uow):
    geojson = {
        "features": [
            {"type": "Feature", "properties": {"name": "Chapinero"}, "geometry": {}},
            {"type": "Feature", "properties": {"name": "Chapinero"}, "geometry": {}},
        ]
    }
    mock_run.return_value = []

    await uc.execute(locality_id=LOCALITY_ID, geojson=geojson, name_field="name")

    # Solo debe enviarse un nombre único al repo
    call_kwargs = mock_run.call_args[0][0].keywords
    assert len(call_kwargs["search_names"]) == 1
