from functools import partial

from fastapi.concurrency import run_in_threadpool

from app.core.config.settings import settings
from app.models.location import Country
from app.services.catalog_admin.helpers.db_error_translator import translate_db_error
from app.services.catalog_admin.ports.unit_of_work import CatalogAdminUnitOfWork
from app.services.catalog_admin.schemas.country import (
    CountryResponse,
    CreateCountryRequest,
)
from app.services.shared.helpers.cache_keys import (
    cache_key_countries,
    cache_key_country,
)
from app.services.shared.ports.cache import CachePort


class CreateCountryUseCase:
    def __init__(
            self, 
            *, 
            uow: CatalogAdminUnitOfWork,
            cache_client: CachePort, 
        ) -> None:
        self.uow = uow
        self.cache_client = cache_client

    async def execute(self, *, request: CreateCountryRequest) -> CountryResponse:
        country = await run_in_threadpool(                                                                         
            partial(self.uow.countries.add, country=Country(**request.model_dump()))
        )

        try:
            await self.uow.commit()
            await self.uow.refresh(country)
        except Exception as exc:
            await self.uow.rollback()
            raise translate_db_error(exc) from exc

        try:
            await self.cache_client.set_json(
                key=cache_key_country(country_id=country.id),
                value=country.model_dump(mode="json"),
                ttl=settings.CACHE_TTL_ENTITY_SECONDS,
            )
            await self.cache_client.delete(key=cache_key_countries())
        except Exception:
            pass

        return CountryResponse.model_validate(country)