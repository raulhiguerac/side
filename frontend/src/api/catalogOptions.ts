import catalogApi from "@/api/catalogApi";
import { CATALOG_ENDPOINTS } from "@/constants/catalogEndpoints";
import type { CatalogItem } from "@/types/catalog/base";
import type { AdminFilterOptions } from "@/types/admin/filters";
import { toFilterOptions } from "@/utils/adminFilters";

export async function loadCountryOptions(): Promise<AdminFilterOptions> {
  const { data } = await catalogApi.get<CatalogItem[]>(
    CATALOG_ENDPOINTS.countries
  );
  return toFilterOptions(data);
}

export async function loadLocalityOptions({
  country_id,
}: Record<string, string>): Promise<AdminFilterOptions> {
  const { data } = await catalogApi.get<CatalogItem[]>(
    CATALOG_ENDPOINTS.localitiesByCountry,
    { params: { country_id } }
  );
  return toFilterOptions(data);
}
