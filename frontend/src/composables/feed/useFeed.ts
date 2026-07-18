import { ref, computed } from "vue";
import { useUserStore } from "@/stores/user";
import propertiesApi from "@/api/propertiesApi";
import type {
  FeedPreferences,
  FeedFilters,
  FeedPage,
  PropertyCard,
  PageCache,
} from "@/types/feed";
import { buildNeighborhoodMap } from "@/composables/catalog/useNeighborhoodLookup";

async function fetchFeed(
  preferences: FeedPreferences,
  filters?: FeedFilters,
  cursor?: string | null
): Promise<FeedPage> {
  try {
    const { data } = await propertiesApi.get("/v1/search/feed", {
      params: { ...preferences, ...filters, ...(cursor ? { cursor } : {}) },
      paramsSerializer: { indexes: null },
    });
    return data as FeedPage;
  } catch (error) {
    console.error("Error al obtener listings:", error);
    return { items: [], next_cursor: null };
  }
}

export function useFeed() {
  const data = ref<PropertyCard[]>([]);
  const loading = ref(false);
  const userStore = useUserStore();
  const neighborhoodLookup = ref<Record<string, string>>({});

  const pageCache = ref<PageCache>({});
  const cursorStack = ref<string[]>([]);

  const nextCursor = ref<string | null>(null);
  const isFirstPage = computed(() => cursorStack.value.length === 0);

  const savedPreferences = ref<FeedPreferences | Record<string, never>>({});
  const savedFilters = ref<FeedFilters | undefined>(undefined);

  const currentPageKey = ref<string>("first");

  async function updateLookup(items: PropertyCard[]) {
    const locations = new Set(
      items.map((obj) => obj.location?.city_id).filter(Boolean)
    );
    const uniqueLocations = Array.from(locations) as string[];
    neighborhoodLookup.value = await buildNeighborhoodMap(uniqueLocations);
  }

  async function load(preferences?: FeedPreferences, filters?: FeedFilters) {
    try {
      loading.value = true;

      pageCache.value = {};
      cursorStack.value = [];
      nextCursor.value = null;
      currentPageKey.value = "first";

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

      savedPreferences.value = resolvedPreferences;
      savedFilters.value = filters;

      const properties = await fetchFeed(
        savedPreferences.value,
        savedFilters.value
      );

      pageCache.value["first"] = {
        items: properties.items,
        nextCursor: properties.next_cursor,
      };

      data.value = properties.items;
      nextCursor.value = properties.next_cursor;
      await updateLookup(properties.items);

      console.log(data.value);
    } finally {
      loading.value = false;
    }
  }

  async function loadNext(cursor: string) {
    try {
      loading.value = true;

      const already_cursor = pageCache.value[cursor];
      if (already_cursor) {
        data.value = pageCache.value[cursor].items;
        nextCursor.value = pageCache.value[cursor].nextCursor;
        cursorStack.value.push(currentPageKey.value);
        currentPageKey.value = cursor;
        return;
      }

      const properties = await fetchFeed(
        savedPreferences.value,
        savedFilters.value,
        cursor
      );
      pageCache.value[cursor] = {
        items: properties.items,
        nextCursor: properties.next_cursor,
      };
      cursorStack.value.push(currentPageKey.value);

      currentPageKey.value = cursor;

      data.value = properties.items;
      nextCursor.value = properties.next_cursor;
      await updateLookup(properties.items);
    } finally {
      loading.value = false;
    }
  }

  async function loadPrev() {
    try {
      const cursor = cursorStack.value.pop();
      if (!cursor) return;

      data.value = pageCache.value[cursor].items;
      nextCursor.value = pageCache.value[cursor].nextCursor;
      currentPageKey.value = cursor;
      await updateLookup(pageCache.value[cursor].items);
    } finally {
      loading.value = false;
    }
  }

  return {
    data,
    loading,
    load,
    neighborhoodLookup,
    nextCursor,
    isFirstPage,
    loadNext,
    loadPrev,
  };
}
