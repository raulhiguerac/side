import { ref, computed } from "vue";
import { getNeighborhoodsByLocalities } from "@/composables/catalog/useLocation";
import type { CityWithNeighborhoods } from "@/types/catalog/neighborhoods";

export function useCityMultiselect() {
  const selected = ref<string[]>([]);
  function removeCity(id: string) {
    selected.value = selected.value.filter((c) => c !== id);
  }
  return { selected, removeCity };
}

export function useNeighborhoodMultiselect() {
  const cities = ref<CityWithNeighborhoods[]>([]);
  const selectedByCity = ref<Record<string, string[]>>({});

  const allSelected = computed(() =>
    cities.value.flatMap((city) =>
      (selectedByCity.value[city.id] ?? []).map((neighborhoodId) => ({
        cityId: city.id,
        cityName: city.name,
        neighborhoodId,
        neighborhoodName:
          city.neighborhoods.find((n) => n.id === neighborhoodId)?.name ?? "",
      }))
    )
  );

  const allNeighborhoodOptions = computed(() =>
    cities.value.flatMap((city) =>
      city.neighborhoods.map((n) => ({ value: n.id, label: n.name }))
    )
  );

  function removeNeighborhood(cityId: string, neighborhoodId: string) {
    selectedByCity.value[cityId] = (selectedByCity.value[cityId] ?? []).filter(
      (id) => id !== neighborhoodId
    );
  }

  async function load(localities: { id: string; name: string }[]) {
    const ids = localities.map((l) => l.id);
    const result = await getNeighborhoodsByLocalities(ids);
    cities.value = localities.map((loc) => ({
      ...loc,
      neighborhoods: (result[loc.id] ?? []).map((n) => ({
        id: n.id,
        name: n.name,
      })),
    }));
    for (const id of ids) {
      if (!selectedByCity.value[id]) selectedByCity.value[id] = [];
    }
  }

  return {
    cities,
    selectedByCity,
    allSelected,
    allNeighborhoodOptions,
    removeNeighborhood,
    load,
  };
}
