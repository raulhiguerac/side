from fastapi.concurrency import run_in_threadpool

from app.core.config.settings import settings
from app.services.geo_catalog.ports.unit_of_work import GeoCatalogUnitOfWork
from app.services.geo_catalog.schemas.country import CountryListItem
from app.services.shared.helpers.cache_keys import cache_key_countries
from app.services.shared.ports.cache import CachePort


class GetCountriesUseCase:
    def __init__(
        self,
        *,
        uow: GeoCatalogUnitOfWork,
        cache_client: CachePort,
    ) -> None:
        self.uow = uow
        self.cache = cache_client

    async def execute(self) -> list[CountryListItem]:
        cache_key = cache_key_countries()

        try:
            cached = await self.cache.get_json(key=cache_key)
            if cached:
                return [CountryListItem.model_validate(item) for item in cached]
        except Exception:
            pass

        countries = await run_in_threadpool(self.uow.countries.get_active_countries)

        result = [CountryListItem.model_validate(c) for c in countries]

        if result:
            try:
                await self.cache.set_json(
                    key=cache_key,
                    value=[item.model_dump(mode="json") for item in result],
                    ttl=settings.CACHE_TTL_CATALOG_SECONDS,
                )
            except Exception:
                pass

        return result
