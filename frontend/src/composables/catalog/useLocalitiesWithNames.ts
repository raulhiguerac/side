import { useUserStore } from "@/stores/user";
import type { CatalogItem } from "@/types/catalog/base";
import {
  locations,
  getCitiesByCountry,
} from "@/composables/catalog/useLocation";

export function useLocalitiesWithNames() {
  const userStore = useUserStore();

  const load = async (): Promise<CatalogItem[]> => {
    let localityIds: string[] = userStore.userInterests.localities;

    if (localityIds.length === 0) {
      const interests = await userStore.checkInterests();
      localityIds = interests.localities;
    }

    const { countryUser } = await locations();
    const allCities = countryUser
      ? (await getCitiesByCountry(countryUser)) ?? []
      : [];
    const cityMap = new Map<string, string>(
      allCities.map((c) => [c.id, c.name])
    );

    return localityIds.map((id) => ({ id, name: cityMap.get(id) ?? id }));
  };

  return { load };
}
