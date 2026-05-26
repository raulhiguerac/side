import { useUserStore } from "@/stores/user";
import { locations, getCitiesByCountry } from "@/composables/Location";

export interface LocalityWithName {
  id: string;
  name: string;
}

export function useLocalitiesWithNames() {
  const userStore = useUserStore();

  const load = async (): Promise<LocalityWithName[]> => {
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
      allCities.map((c: any) => [c.id, c.name])
    );

    return localityIds.map((id) => ({ id, name: cityMap.get(id) ?? id }));
  };

  return { load };
}
