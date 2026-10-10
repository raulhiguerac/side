import { ref, computed } from "vue";
import * as propertiesApi from "@/api/properties";
import { PAGE_SIZE } from "@/constants/pagination";
import type { PropertyCard } from "@/types/feed/cards";
import type { BboxPayload } from "@/types/feed/search";
import { sortForMap } from "@/utils/feedMap";

// El backend devuelve todo el bbox; la lista lo pinta por tandas al hacer scroll.
export function useFeedMap() {
  const loading = ref(false);
  const _allItems = ref<PropertyCard[]>([]);
  const visibleCount = ref<number>(PAGE_SIZE.FEED_MAP_CHUNK);
  let latestRequest = 0;

  const items = computed(() => _allItems.value.slice(0, visibleCount.value));
  const hasMore = computed(() => visibleCount.value < _allItems.value.length);

  async function fetchByBbox(payload: BboxPayload): Promise<void> {
    const request = ++latestRequest;
    try {
      loading.value = true;
      const data = await propertiesApi.getFeedMap({
        min_lat: payload.min_lat,
        max_lat: payload.max_lat,
        min_lon: payload.min_lon,
        max_lon: payload.max_lon,
        resolution: payload.zoom >= 15 ? 9 : 7,
      });
      // Si el mapa se movió mientras tanto, esta respuesta ya es de otra área.
      if (request !== latestRequest) return;
      _allItems.value = sortForMap(data, payload);
      visibleCount.value = PAGE_SIZE.FEED_MAP_CHUNK;
    } finally {
      if (request === latestRequest) loading.value = false;
    }
  }

  // Devuelve si cargó algo, para que el scroll sepa si volver a mirar.
  function loadMore(): boolean {
    if (!hasMore.value) return false;
    visibleCount.value += PAGE_SIZE.FEED_MAP_CHUNK;
    return true;
  }

  return {
    allItems: computed(() => _allItems.value),
    items,
    hasMore,
    loading,
    fetchByBbox,
    loadMore,
  };
}
