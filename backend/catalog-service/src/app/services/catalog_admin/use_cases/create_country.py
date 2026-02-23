from functools import partial
from fastapi.concurrency import run_in_threadpool

from app.services.shared.helpers.cache_keys import cache_key_country
from app.services.shared.ports.cache import CachePort

from app.models.location import Country
from app.services.catalog_admin.ports.unit_of_work import CatalogAdminUnitOfWork
from app.services.catalog_admin.schemas.country import CreateCountryRequest, CountryResponse
from app.services.catalog_admin.helpers.db_error_translator import translate_db_error


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
        except Exception as exc:
            await self.uow.rollback()
            raise translate_db_error(exc) from exc

        cache_key = cache_key_country(country_id=country.id)

        try:
            await self.cache_client.set_json(key=cache_key, value=country.model_dump(mode="json"), ttl=3600 * 24 * 30)
        except Exception:
            pass

        return CountryResponse.model_validate(country)