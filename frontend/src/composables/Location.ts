import axios from "axios";
import { API, STORAGE_KEYS } from "@/config";
import { useUserStore } from "@/stores/user";

export async function getCitiesByCountry(id: string) {
  try {
    const key = STORAGE_KEYS.CITIES_BY_COUNTRY(id);
    const raw = localStorage.getItem(key);
    if (raw) return JSON.parse(raw);
    const { data } = await axios.get(
      `${API.CATALOG_BASE_URL}/v1/localities/by-country`,
      {
        params: { country_id: id },
      }
    );
    localStorage.setItem(key, JSON.stringify(data));
    return data;
  } catch (error) {
    console.error("Error al obtener las ciudades soportadas:", error);
  }
}

export async function locations() {
  const userStore = useUserStore();
  const countryDetected = await userStore.detectLocation();

  const countries = async () => {
    try {
      const raw = localStorage.getItem(STORAGE_KEYS.COUNTRIES);
      if (raw) return JSON.parse(raw);
      const { data } = await axios.get(`${API.CATALOG_BASE_URL}/v1/countries`);
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
