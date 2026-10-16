import catalogClient from "@/api/clients/catalog";
import { getCountries, getLocalitiesByCountry } from "@/api/catalog";
import { CATALOG_ENDPOINTS } from "@/constants/catalogEndpoints";
import type {
  BulkGeometriesResult,
  BulkNeighborhoodsResult,
  CountryAdminFilters,
  CountryAdminPage,
  CountryAdminResponse,
  CountryCreatePayload,
  CountryUpdatePayload,
  DivisionAdminFilters,
  DivisionAdminPage,
  DivisionAdminRow,
  DivisionCreatePayload,
  DivisionUpdatePayload,
  LocalityAdminFilters,
  LocalityAdminPage,
  LocalityAdminResponse,
  LocalityCreatePayload,
  LocalityUpdatePayload,
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

export async function getLocalities(
  params: PageParams & LocalityAdminFilters
): Promise<LocalityAdminPage> {
  const { data } = await catalogClient.get<LocalityAdminPage>(
    CATALOG_ENDPOINTS.adminLocalities,
    { params }
  );
  return data;
}

export async function createLocality(
  payload: LocalityCreatePayload
): Promise<LocalityAdminResponse> {
  const { data } = await catalogClient.post<LocalityAdminResponse>(
    CATALOG_ENDPOINTS.adminLocalities,
    payload
  );
  return data;
}

export async function updateLocality(
  id: string,
  payload: LocalityUpdatePayload
): Promise<LocalityAdminResponse> {
  const { data } = await catalogClient.patch<LocalityAdminResponse>(
    CATALOG_ENDPOINTS.adminLocality(id),
    payload
  );
  return data;
}

export async function getAdminDivisions(
  params: PageParams & DivisionAdminFilters
): Promise<DivisionAdminPage> {
  const { data } = await catalogClient.get<DivisionAdminPage>(
    CATALOG_ENDPOINTS.adminAdminDivisions,
    { params }
  );
  return data;
}

export async function createAdminDivision(
  payload: DivisionCreatePayload
): Promise<DivisionAdminRow> {
  const { data } = await catalogClient.post<DivisionAdminRow>(
    CATALOG_ENDPOINTS.adminAdminDivisions,
    payload
  );
  return data;
}

export async function updateAdminDivision(
  id: string,
  payload: DivisionUpdatePayload
): Promise<DivisionAdminRow> {
  const { data } = await catalogClient.patch<DivisionAdminRow>(
    CATALOG_ENDPOINTS.adminAdminDivision(id),
    payload
  );
  return data;
}

export async function getAdminCountries(
  params: PageParams & CountryAdminFilters
): Promise<CountryAdminPage> {
  const { data } = await catalogClient.get<CountryAdminPage>(
    CATALOG_ENDPOINTS.adminCountries,
    { params }
  );
  return data;
}

export async function createCountry(
  payload: CountryCreatePayload
): Promise<CountryAdminResponse> {
  const { data } = await catalogClient.post<CountryAdminResponse>(
    CATALOG_ENDPOINTS.adminCountries,
    payload
  );
  return data;
}

export async function updateCountry(
  id: string,
  payload: CountryUpdatePayload
): Promise<CountryAdminResponse> {
  const { data } = await catalogClient.patch<CountryAdminResponse>(
    CATALOG_ENDPOINTS.adminCountry(id),
    payload
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

// Una sola página al tope del back (100): ningún país tiene más divisiones.
export async function loadDivisionOptions({
  country_id,
}: Record<string, string>): Promise<AdminFilterOptions> {
  const { items } = await getAdminDivisions({
    country_id,
    page: 1,
    page_size: 100,
  });
  return toFilterOptions(items);
}
