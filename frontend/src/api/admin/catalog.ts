import catalogClient from "@/api/clients/catalog";
import { getCountries, getLocalitiesByCountry } from "@/api/catalog";
import { CATALOG_ENDPOINTS } from "@/constants/catalogEndpoints";
import type {
  BulkGeometriesResult,
  BulkNeighborhoodsResult,
  NeighborhoodAdminDetail,
  NeighborhoodAdminFilters,
  NeighborhoodAdminPage,
  NeighborhoodAdminResponse,
  NeighborhoodCreatePayload,
  NeighborhoodGeometryItem,
  NeighborhoodUpdatePayload,
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

export async function createNeighborhood(
  payload: NeighborhoodCreatePayload
): Promise<NeighborhoodAdminResponse> {
  const { data } = await catalogClient.post<NeighborhoodAdminResponse>(
    CATALOG_ENDPOINTS.adminNeighborhoods,
    payload
  );
  return data;
}

export async function updateNeighborhood(
  id: string,
  payload: NeighborhoodUpdatePayload
): Promise<NeighborhoodAdminResponse> {
  const { data } = await catalogClient.patch<NeighborhoodAdminResponse>(
    CATALOG_ENDPOINTS.adminNeighborhood(id),
    payload
  );
  return data;
}

export async function replaceNeighborhoodGeometry(
  id: string,
  file: File
): Promise<NeighborhoodAdminResponse> {
  const body = new FormData();
  body.append("file", file);
  const { data } = await catalogClient.post<NeighborhoodAdminResponse>(
    CATALOG_ENDPOINTS.adminNeighborhoodGeometry(id),
    body
  );
  return data;
}

// Los bulk procesan todo antes de responder: los 8 s del cliente no alcanzan.
const BULK_TIMEOUT_MS = 120_000;

export async function bulkCreateNeighborhoods(
  localityId: string,
  file: File
): Promise<BulkNeighborhoodsResult> {
  const body = new FormData();
  body.append("file", file);
  const { data } = await catalogClient.post<BulkNeighborhoodsResult>(
    CATALOG_ENDPOINTS.adminBulkNeighborhoods(localityId),
    body,
    { timeout: BULK_TIMEOUT_MS }
  );
  return data;
}

export async function bulkEnrichNeighborhoodGeometries(
  localityId: string,
  file: File,
  nameField: string
): Promise<BulkGeometriesResult> {
  const body = new FormData();
  body.append("file", file);
  const { data } = await catalogClient.post<BulkGeometriesResult>(
    CATALOG_ENDPOINTS.adminBulkNeighborhoodGeometries(localityId),
    body,
    { params: { name_field: nameField }, timeout: BULK_TIMEOUT_MS }
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
