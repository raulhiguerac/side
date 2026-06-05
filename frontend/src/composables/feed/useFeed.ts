import axios from "axios";
import { ref } from "vue";
import { useUserStore } from "@/stores/user";
import { API } from "@/config";
import type { FeedPreferences, FeedFilters, PropertyCard } from "@/types/feed";
import { buildNeighborhoodMap } from "@/composables/catalog/useNeighborhoodLookup";

async function fetchFeed(
  preferences: FeedPreferences,
  filters?: FeedFilters
): Promise<PropertyCard[]> {
  try {
    const { data } = await axios.get(
      `${API.PROPERTIES_BASE_URL}/v1/search/feed`,
      {
        params: { ...preferences, ...filters },
        paramsSerializer: { indexes: null },
      }
    );
    return data as PropertyCard[];
  } catch (error) {
    console.error("Error al obtener las ciudades soportadas:", error);
    return [];
  }
}

export function useFeed() {
  const data = ref<PropertyCard[]>([]);
  const loading = ref(false);
  const userStore = useUserStore();
  const neighborhoodLookup = ref<Record<string, string>>({});

  async function load(preferences?: FeedPreferences, filters?: FeedFilters) {
    try {
      loading.value = true;

      const resolvedPreferences =
        preferences ??
        (userStore.userInterests.localities.length > 0
          ? {
              city_ids: userStore.userInterests.localities,
              neighborhood_ids: Object.values(
                userStore.userInterests.neighborhoods
              ).flat(),
              property_types: Object.values(
                userStore.userInterests.properties
              ).flat(),
            }
          : {});

      const properties = await fetchFeed(resolvedPreferences, filters);
      const locations = new Set(
        properties.map((obj) => obj.location?.city_id).filter(Boolean)
      );
      const uniqueLocations = Array.from(locations) as string[];
      const lookup = await buildNeighborhoodMap(uniqueLocations);
      data.value = properties;
      neighborhoodLookup.value = lookup;
      console.log(data.value);
    } finally {
      loading.value = false;
    }
  }

  return { data, loading, load, neighborhoodLookup };
}
