import json
import uuid

from fastapi import APIRouter, Depends, HTTPException, UploadFile

from app.api.deps.catalog_admin.neighborhoods import (
    bulk_create_neighborhoods_uc,
    bulk_enrich_neighborhood_geometries_uc,
    create_neighborhood_uc,
    enrich_neighborhood_geometry_uc,
    update_neighborhood_uc,
)
from app.api.deps.upload_validation import (
    validate_neighborhood_bulk_geometry_upload,
    validate_neighborhood_bulk_upload,
    validate_neighborhood_geometry_upload,
)
from app.services.catalog_admin.helpers.file_parser import NeighborhoodFileParser
from app.services.catalog_admin.schemas.neighborhood import (
    BulkCreateNeighborhoodsResult,
    BulkEnrichNeighborhoodGeometriesResult,
    CreateNeighborhoodRequest,
    NeighborhoodAdminResponse,
    UpdateNeighborhoodRequest,
)
from app.services.catalog_admin.use_cases.neighborhood.bulk_create import (
    BulkCreateNeighborhoodsUseCase,
)
from app.services.catalog_admin.use_cases.neighborhood.bulk_enrich_geometries import (
    BulkEnrichNeighborhoodGeometriesUseCase,
)
from app.services.catalog_admin.use_cases.neighborhood.create import (
    CreateNeighborhoodUseCase,
)
from app.services.catalog_admin.use_cases.neighborhood.enrich_geometry import (
    EnrichNeighborhoodGeometryUseCase,
)
from app.services.catalog_admin.use_cases.neighborhood.update import (
    UpdateNeighborhoodUseCase,
)

router = APIRouter()


@router.post("/neighborhoods", response_model=NeighborhoodAdminResponse, status_code=201)
async def create_neighborhood(
    body: CreateNeighborhoodRequest,
    uc: CreateNeighborhoodUseCase = Depends(create_neighborhood_uc),
) -> NeighborhoodAdminResponse:
    return await uc.execute(request=body)


@router.patch("/neighborhoods/{neighborhood_id}", response_model=NeighborhoodAdminResponse)
async def update_neighborhood(
    neighborhood_id: uuid.UUID,
    body: UpdateNeighborhoodRequest,
    uc: UpdateNeighborhoodUseCase = Depends(update_neighborhood_uc),
) -> NeighborhoodAdminResponse:
    return await uc.execute(neighborhood_id=neighborhood_id, request=body)


@router.post("/localities/{locality_id}/neighborhoods/bulk", response_model=BulkCreateNeighborhoodsResult, status_code=200)
async def bulk_create_neighborhoods(
    locality_id: uuid.UUID,
    file: UploadFile,
    _: None = Depends(validate_neighborhood_bulk_upload),
    uc: BulkCreateNeighborhoodsUseCase = Depends(bulk_create_neighborhoods_uc),
) -> BulkCreateNeighborhoodsResult:
    content = await file.read()
    records = NeighborhoodFileParser().parse(file=content, filename=file.filename)
    return await uc.execute(locality_id=locality_id, records=records)


@router.post("/localities/{locality_id}/neighborhoods/bulk/geometry", response_model=BulkEnrichNeighborhoodGeometriesResult)
async def bulk_enrich_neighborhood_geometries(
    locality_id: uuid.UUID,
    file: UploadFile,
    name_field: str = "name",
    _: None = Depends(validate_neighborhood_bulk_geometry_upload),
    uc: BulkEnrichNeighborhoodGeometriesUseCase = Depends(bulk_enrich_neighborhood_geometries_uc),
) -> BulkEnrichNeighborhoodGeometriesResult:
    content = await file.read()
    try:
        geojson = json.loads(content)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=422, detail="Invalid JSON file") from exc
    return await uc.execute(locality_id=locality_id, geojson=geojson, name_field=name_field)


@router.post("/neighborhoods/{neighborhood_id}/geometry", response_model=NeighborhoodAdminResponse)
async def enrich_neighborhood_geometry(
    neighborhood_id: uuid.UUID,
    file: UploadFile,
    _: None = Depends(validate_neighborhood_geometry_upload),
    uc: EnrichNeighborhoodGeometryUseCase = Depends(enrich_neighborhood_geometry_uc),
) -> NeighborhoodAdminResponse:
    content = await file.read()
    try:
        geojson = json.loads(content)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=422, detail="Invalid JSON file") from exc
    return await uc.execute(neighborhood_id=neighborhood_id, geojson=geojson)
