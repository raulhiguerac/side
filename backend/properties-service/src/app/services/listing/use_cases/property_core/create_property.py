import uuid
from functools import partial

from fastapi.concurrency import run_in_threadpool
from geoalchemy2.shape import from_shape
from shapely.geometry import Point

from app.core.exceptions.listing import InconsistentLocationError
from app.models.property import ListingStatus, Property, PropertyLocation, VerificationStatus
from app.schemas.principal import Principal
from app.services.listing.helpers.db_error_translator import translate_db_error
from app.services.listing.ports.unit_of_work import ListingUnitOfWork
from app.services.listing.schemas.listing_schemas import CreatePropertyRequest
from app.services.shared.helpers.geometry import compute_h3
from app.services.shared.ports.catalog_gateway import CatalogGateway


class CreatePropertyUseCase:
    def __init__(self, *, uow: ListingUnitOfWork, catalog: CatalogGateway) -> None:
        self.uow = uow
        self.catalog = catalog

    async def execute(self, *, principal: Principal, property_fields: CreatePropertyRequest) -> uuid.UUID:
        loc = property_fields.location
        guard = await self.catalog.get_neighborhood(neighborhood_id=loc.neighborhood_id)

        if guard.locality_id != loc.city_id:
            raise InconsistentLocationError(
                neighborhood_id=loc.neighborhood_id,
                city_id=loc.city_id,
            )

        h3_r9, h3_r7 = compute_h3(loc.latitude, loc.longitude)
        prop, location = self.build_models(
            principal=principal,
            property_fields=property_fields,
            h3_r9=h3_r9,
            h3_r7=h3_r7,
        )

        try:
            await run_in_threadpool(partial(self.uow.properties.add, property=prop))
            await run_in_threadpool(partial(self.uow.property_locations.add, property=location))
            await self.uow.commit()
        except Exception as exc:
            await self.uow.rollback()
            raise translate_db_error(exc) from exc

        return prop.id

    @staticmethod
    def build_models(
        *,
        principal: Principal,
        property_fields: CreatePropertyRequest,
        h3_r9: str,
        h3_r7: str,
    ) -> tuple[Property, PropertyLocation]:
        property_id = uuid.uuid4()
        loc = property_fields.location

        prop = Property(
            id=property_id,
            owner_id=principal.sub,
            property_type=property_fields.property_type,
            listing_type=property_fields.listing_type,
            condition=property_fields.condition,
            currency=property_fields.currency,
            status=ListingStatus.draft,
            verification_status=VerificationStatus.unverified,
            floor_number=property_fields.floor_number,
            total_floors=property_fields.total_floors,
            area_m2=property_fields.area_m2,
            bedrooms=property_fields.bedrooms,
            bathrooms=property_fields.bathrooms,
            parking_spots=property_fields.parking_spots,
            h3_r9=h3_r9,
            h3_r7=h3_r7,
            price=property_fields.price,
            admin_fee=property_fields.admin_fee,
            description=property_fields.description,
            year_built=property_fields.year_built,
            stratum=property_fields.stratum,
            created_by=principal.sub,
            updated_by=principal.sub,
        )

        location = PropertyLocation(
            property_id=property_id,
            neighborhood_id=loc.neighborhood_id,
            city_id=loc.city_id,
            country_id=loc.country_id,
            location=from_shape(Point(loc.longitude, loc.latitude), srid=4326),
            created_by=principal.sub,
            updated_by=principal.sub,
        )

        return prop, location
