import catalogClient from "@/api/clients/catalog";
import { CATALOG_ENDPOINTS } from "@/constants/catalogEndpoints";
import type { CatalogItem, Locality } from "@/types/catalog/base";
import type {
  CoordinatesResolution,
  NeighborhoodsByLocalitiesResponse,
} from "@/types/catalog/neighborhoods";
import type {
  ReachablePoisRequest,
  ReachablePoisResult,
} from "@/types/pois/reachable";

export async function getCountries(): Promise<CatalogItem[]> {
  const { data } = await catalogClient.get<CatalogItem[]>(
    CATALOG_ENDPOINTS.countries
  );
  return data;
}

export async function getLocalitiesByCountry(
  countryId: string
): Promise<Locality[]> {
  const { data } = await catalogClient.get<Locality[]>(
    CATALOG_ENDPOINTS.localitiesByCountry,
    { params: { country_id: countryId } }
  );
  return data;
}

export async function getNeighborhoodsByLocalities(
  localityIds: string[]
): Promise<Record<string, CatalogItem[]>> {
  const { data } = await catalogClient.get<NeighborhoodsByLocalitiesResponse>(
    CATALOG_ENDPOINTS.neighborhoodsByLocalities,
    {
      params: new URLSearchParams(
        localityIds.map((id) => ["locality_ids", id])
      ),
    }
  );
  return data.neighborhoods;
}

export async function getNeighborhoodById(id: string): Promise<CatalogItem> {
  const { data } = await catalogClient.get<CatalogItem>(
    CATALOG_ENDPOINTS.neighborhoodById,
    { params: { neighborhood_id: id } }
  );
  return data;
}

export async function resolveCoordinates(
  lat: number,
  lon: number
): Promise<CoordinatesResolution> {
  const { data } = await catalogClient.get<CoordinatesResolution>(
    CATALOG_ENDPOINTS.resolveByCoordinates,
    { params: { lat, lon } }
  );
  return data;
}

export async function getReachablePois(
  payload: ReachablePoisRequest
): Promise<ReachablePoisResult[]> {
  const { data } = await catalogClient.post<ReachablePoisResult[]>(
    CATALOG_ENDPOINTS.reachablePois,
    payload
  );
  return data;
}
