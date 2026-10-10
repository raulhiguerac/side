import type { CatalogItem } from "@/types/catalog/base";

export interface CityWithNeighborhoods extends CatalogItem {
  neighborhoods: CatalogItem[];
}

export interface ResolvedNeighborhood {
  name: string;
  neighborhood_id: string;
  city_id: string;
  country_id: string;
}

export interface NeighborhoodsByLocalitiesResponse {
  neighborhoods: Record<string, CatalogItem[]>;
}

export interface CoordinatesResolution {
  neighborhood_id: string;
  locality_id: string;
  country_id: string;
}
