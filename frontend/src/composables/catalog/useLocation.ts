import { STORAGE_KEYS } from "@/config";
import catalogApi from "@/api/catalogApi";
import { useUserStore } from "@/stores/user";

export async function getCitiesByCountry(id: string) {
  try {
    const key = STORAGE_KEYS.CITIES_BY_COUNTRY(id);
    const raw = sessionStorage.getItem(key);
    if (raw) return JSON.parse(raw);
    const { data } = await catalogApi.get(
      `/v1/localities/by-country`,
      {
        params: { country_id: id },
      }
    );
    sessionStorage.setItem(key, JSON.stringify(data));
    return data;
  } catch (error) {
    console.error("Error al obtener las ciudades soportadas:", error);
  }
}

export async function getNeighborhoodsByLocalities(localityIds: string[]) {
  const cached: Record<string, any[]> = {};
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
    const { data } = await catalogApi.get(
      `/v1/neighborhoods/by-localities`,
      { params: new URLSearchParams(missing.map((id) => ["locality_ids", id])) }
    );

    for (const [lid, neighborhoods] of Object.entries(
      data.neighborhoods as Record<string, any[]>
    )) {
      cached[lid] = neighborhoods;
      sessionStorage.setItem(
        STORAGE_KEYS.NEIGHBORHOODS_BY_LOCALITY(lid),
        JSON.stringify(neighborhoods)
      );
    }
  } catch (error) {
    console.error("Error al obtener los barrios:", error);
  }

  return cached;
}

export async function locations() {
  const userStore = useUserStore();
  const countryDetected = await userStore.detectLocation();

  const countries = async () => {
    try {
      const raw = localStorage.getItem(STORAGE_KEYS.COUNTRIES);
      if (raw) return JSON.parse(raw);
      const { data } = await catalogApi.get(`/v1/countries`);
      localStorage.setItem(STORAGE_KEYS.COUNTRIES, JSON.stringify(data));
      return data;
    } catch (error) {
      console.error("Error al obtener los paises soportados:", error);
    }
  };

  const data = await countries();
  const match = data?.find(
    (country: any) => country.name === countryDetected.country_name
  );
  const countryUser: string | undefined = match?.id;

  return { countryDetected, countryUser };
}

export interface ResolvedNeighborhood {
  name: string;
  neighborhood_id: string;
  city_id: string;
  country_id: string;
}

export async function getNeighborhood(
  lat: number,
  lon: number
): Promise<ResolvedNeighborhood | undefined> {
  try {
    const { data: coords } = await catalogApi.get(
      `/v1/geo-resolution/by-coordinates`,
      { params: { lat, lon } }
    );
    const { data: nbh } = await catalogApi.get(
      `/v1/neighborhoods/by-id`,
      { params: { neighborhood_id: coords.neighborhood_id } }
    );

    return {
      name: nbh.name,
      neighborhood_id: coords.neighborhood_id,
      city_id: coords.locality_id,
      country_id: coords.country_id,
    };
  } catch (error) {
    console.error("Error al obtener los barrios:", error);
  }
}
