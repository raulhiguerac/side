import { ref } from "vue";
import {
  locations,
  getCitiesByCountry,
} from "@/composables/catalog/useLocation";

const countryUser = ref<string | undefined>(undefined);
export const cities = ref<Map<string, string>>(new Map());

export async function load() {
  const result = await locations();
  countryUser.value = result.countryUser;
  if (result.countryUser) {
    const data = await getCitiesByCountry(result.countryUser);
    cities.value = new Map((data ?? []).map((city) => [city.id, city.name]));
  }
}
