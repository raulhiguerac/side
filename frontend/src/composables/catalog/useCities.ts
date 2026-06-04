import { ref } from "vue";
import {
  locations,
  getCitiesByCountry,
} from "@/composables/catalog/useLocation";

interface Locality {
  id: string;
  name: string;
  admin_division: {
    id: string;
    name: string;
  };
}

const countryUser = ref<string | undefined>(undefined);
export const cities = ref<Map<string, string>>(new Map());

export async function load() {
  const result = await locations();
  countryUser.value = result.countryUser;
  if (result.countryUser) {
    const data = await getCitiesByCountry(result.countryUser);
    cities.value = new Map(data.map((city: Locality) => [city.id, city.name]));
  }
}
