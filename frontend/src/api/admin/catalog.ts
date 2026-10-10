import catalogClient from "@/api/clients/catalog";
import { getCountries, getLocalitiesByCountry } from "@/api/catalog";
import { CATALOG_ENDPOINTS } from "@/constants/catalogEndpoints";
import type {
  NeighborhoodAdminDetail,
  NeighborhoodAdminFilters,
  NeighborhoodAdminPage,
  NeighborhoodGeometryItem,
} from "@/types/admin/catalog";
import type { AdminFilterOptions } from "@/types/admin/filters";
import type { Bbox } from "@/types/maps/base";
import type { PageParams } from "@/types/shared/pagination";
import { toFilterOptions } from "@/utils/adminFilters";

export async function getNeighborhoods(
  params: PageParams & NeighborhoodAdminFilters
): Promise<NeighborhoodAdminPage> {
  const { data } = await catalogClient.get<NeighborhoodAdminPage>(
    CATALOG_ENDPOINTS.adminNeighborhoods,
    { params }
  );
  return data;
}

export async function getNeighborhood(
  id: string
): Promise<NeighborhoodAdminDetail> {
  const { data } = await catalogClient.get<NeighborhoodAdminDetail>(
    CATALOG_ENDPOINTS.adminNeighborhood(id)
  );
  return data;
}

export async function getNeighborhoodGeometries(
  neighborhoodId: string,
  bbox: Bbox
): Promise<NeighborhoodGeometryItem[]> {
  const { data } = await catalogClient.get<NeighborhoodGeometryItem[]>(
    CATALOG_ENDPOINTS.adminNeighborhoodGeometries,
    {
      params: { neighborhood_id: neighborhoodId, bbox },
      // FastAPI espera `bbox` repetido, no el `bbox[]=` que arma axios por defecto.
      paramsSerializer: { indexes: null },
    }
  );
  return data;
}

export async function loadCountryOptions(): Promise<AdminFilterOptions> {
  return toFilterOptions(await getCountries());
}

export async function loadLocalityOptions({
  country_id,
}: Record<string, string>): Promise<AdminFilterOptions> {
  return toFilterOptions(await getLocalitiesByCountry(country_id));
}
