import uuid
from typing import Optional

from geoalchemy2.shape import from_shape
from shapely.geometry import Point

from app.core.exceptions.listing import InconsistentLocationError
from app.schemas.principal import Principal
from app.services.listing.helpers.db_error_translator import translate_db_error
from app.services.listing.helpers.property_guard import get_owned_property
from app.services.listing.ports.unit_of_work import ListingUnitOfWork
from app.services.listing.schemas.listing_schemas import UpdatePropertyRequest
from app.services.shared.helpers.cache_keys import cache_property, client_properties
from app.services.shared.ports.cache import CachePort
from app.services.shared.ports.catalog_gateway import CatalogGateway


class UpdatePropertyUseCase:
    def __init__(self, *, uow: ListingUnitOfWork, cache_client: CachePort, catalog: CatalogGateway) -> None:
        self.uow = uow
        self.cache_client = cache_client
        self.catalog = catalog

    async def execute(
        self,
        *,
        principal: Principal,
        property_id: uuid.UUID,
        request: UpdatePropertyRequest,
    ) -> None:
        db_model = await get_owned_property(uow=self.uow, property_id=property_id, principal=principal)

        data = request.model_dump(exclude_unset=True)
        loc_data: Optional[dict] = data.pop("location", None)

        for field, value in data.items():
            setattr(db_model, field, value)

        db_model.updated_by = principal.sub

        if loc_data is not None:
            guard = await self.catalog.get_neighborhood(neighborhood_id=loc_data["neighborhood_id"])
            if guard.locality_id != loc_data["city_id"]:
                raise InconsistentLocationError(
                    neighborhood_id=loc_data["neighborhood_id"],
                    city_id=loc_data["city_id"],
                )
            if db_model.location:
                db_model.location.neighborhood_id = loc_data["neighborhood_id"]
                db_model.location.city_id = loc_data["city_id"]
                db_model.location.country_id = loc_data["country_id"]
                db_model.location.location = from_shape(
                    Point(loc_data["longitude"], loc_data["latitude"]), srid=4326
                )
                db_model.location.updated_by = principal.sub

        try:
            await self.uow.commit()
            await self.uow.refresh(db_model)
        except Exception as exc:
            await self.uow.rollback()
            raise translate_db_error(exc) from exc

        try:
            await self.cache_client.delete(key=cache_property(property_id=db_model.id))
            await self.cache_client.delete(key=client_properties(user_id=db_model.owner_id))
        except Exception:
            pass
