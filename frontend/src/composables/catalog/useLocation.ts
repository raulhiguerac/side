import { STORAGE_KEYS } from "@/config";
import * as catalogApi from "@/api/catalog";
import { useUserStore } from "@/stores/user";
import type { CatalogItem, Locality } from "@/types/catalog/base";
import type { ResolvedNeighborhood } from "@/types/catalog/neighborhoods";
import { logger } from "@/utils/logger";

export async function getCitiesByCountry(
  id: string
): Promise<Locality[] | undefined> {
  try {
    const key = STORAGE_KEYS.CITIES_BY_COUNTRY(id);
    const raw = sessionStorage.getItem(key);
    if (raw) return JSON.parse(raw);
    const data = await catalogApi.getLocalitiesByCountry(id);
    sessionStorage.setItem(key, JSON.stringify(data));
    return data;
  } catch (error) {
    logger.error("Error al obtener las ciudades soportadas:", error);
  }
}

export async function getNeighborhoodsByLocalities(
  localityIds: string[]
): Promise<Record<string, CatalogItem[]>> {
  const cached: Record<string, CatalogItem[]> = {};
  const missing: string[] = [];

  for (const id of localityIds) {
    const raw = sessionStorage.getItem(
      STORAGE_KEYS.NEIGHBORHOODS_BY_LOCALITY(id)
    );
    if (raw) {
      cached[id] = JSON.parse(raw);
    } else {
      missing.push(id);
    }
  }

  if (missing.length === 0) return cached;

  try {
    const byLocality = await catalogApi.getNeighborhoodsByLocalities(missing);

    for (const [lid, neighborhoods] of Object.entries(byLocality)) {
      cached[lid] = neighborhoods;
      sessionStorage.setItem(
        STORAGE_KEYS.NEIGHBORHOODS_BY_LOCALITY(lid),
        JSON.stringify(neighborhoods)
      );
    }
  } catch (error) {
    logger.error("Error al obtener los barrios:", error);
  }

  return cached;
}

export async function locations() {
  const userStore = useUserStore();
  const countryDetected = await userStore.detectLocation();

  const countries = async (): Promise<CatalogItem[] | undefined> => {
    try {
      const raw = localStorage.getItem(STORAGE_KEYS.COUNTRIES);
      if (raw) return JSON.parse(raw);
      const data = await catalogApi.getCountries();
      localStorage.setItem(STORAGE_KEYS.COUNTRIES, JSON.stringify(data));
      return data;
    } catch (error) {
      logger.error("Error al obtener los paises soportados:", error);
    }
  };

  const data = await countries();
  const match = data?.find(
    (country) => country.name === countryDetected.country_name
  );
  const countryUser: string | undefined = match?.id;

  return { countryDetected, countryUser };
}

export async function getNeighborhood(
  lat: number,
  lon: number
): Promise<ResolvedNeighborhood | undefined> {
  try {
    const coords = await catalogApi.resolveCoordinates(lat, lon);
    const nbh = await catalogApi.getNeighborhoodById(coords.neighborhood_id);

    return {
      name: nbh.name,
      neighborhood_id: coords.neighborhood_id,
      city_id: coords.locality_id,
      country_id: coords.country_id,
    };
  } catch (error) {
    logger.error("Error al obtener los barrios:", error);
  }
}
