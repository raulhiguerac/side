import axios from "axios";
import { ref } from "vue";
import { useUserStore } from "@/stores/user";
import { API } from "@/config";
import type { FeedPreferences, PropertyCard } from "@/types/feed";

async function fetchFeed(
  preferences: FeedPreferences
): Promise<PropertyCard[]> {
  try {
    const { data } = await axios.get(
      `${API.PROPERTIES_BASE_URL}/v1/search/feed`,
      {
        params: { ...preferences },
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

  const preferences: FeedPreferences =
    userStore.userInterests.localities.length > 0
      ? {
          city_ids: userStore.userInterests.localities,
          neighborhood_ids: Object.values(
            userStore.userInterests.neighborhoods
          ).flat(),
          property_types: Object.values(
            userStore.userInterests.properties
          ).flat(),
        }
      : {};

  async function load() {
    try {
      loading.value = true;
      const properties = await fetchFeed(preferences);
      data.value = properties;
    } finally {
      loading.value = false;
    }
  }

  return { data, loading, load };
}
