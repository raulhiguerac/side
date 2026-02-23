import uuid
from functools import partial
from fastapi.concurrency import run_in_threadpool

from app.services.shared.helpers.cache_keys import cache_key_country
from app.services.shared.ports.cache import CachePort

from app.services.catalog_admin.ports.unit_of_work import CatalogAdminUnitOfWork
from app.services.catalog_admin.schemas.country import UpdateCountryRequest, CountryResponse
from app.services.catalog_admin.helpers.db_error_translator import translate_db_error
from app.core.exceptions.catalog_admin import CountryNotFoundError


class UpdateCountryUseCase:
    def __init__(self, *, uow: CatalogAdminUnitOfWork, cache_client: CachePort) -> None:
        self.uow = uow
        self.cache_client = cache_client

    async def execute(self, *, country_id: uuid.UUID, request: UpdateCountryRequest) -> CountryResponse:
        db_model = await run_in_threadpool(
            partial(self.uow.countries.get_by_id, country_id=country_id)
        )

        if not db_model:
            raise CountryNotFoundError(country_id=country_id)

        for field, value in request.model_dump(exclude_unset=True).items():
            setattr(db_model, field, value)

        try:
            await self.uow.commit()
        except Exception as exc:
            await self.uow.rollback()
            raise translate_db_error(exc) from exc

        cache_key = cache_key_country(country_id=db_model.id)

        try:
            await self.cache_client.set_json(
                key=cache_key,
                value=db_model.model_dump(mode="json"),
                ttl=3600 * 24 * 30,
            )
        except Exception:
            pass

        return CountryResponse.model_validate(db_model)
