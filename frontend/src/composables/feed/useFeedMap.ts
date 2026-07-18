import { ref, computed } from "vue";
import propertiesApi from "@/api/propertiesApi";
import type { PropertyCard, BboxPayload } from "@/types/feed";

export function useFeedMap() {
  const loading = ref(false);

  const zoom = ref<number>(15);
  const page = ref<number>(0);
  const _allItems = ref<PropertyCard[]>([]);

  const PAGE_SIZE = computed(() => (zoom.value >= 15 ? 20 : 40));

  const hasNext = computed(
    () => (page.value + 1) * PAGE_SIZE.value < _allItems.value.length
  );
  const hasPrev = computed(() => page.value > 0);
  const items = computed(() =>
    _allItems.value.slice(
      page.value * PAGE_SIZE.value,
      (page.value + 1) * PAGE_SIZE.value
    )
  );

  async function fetchByBbox(payload: BboxPayload): Promise<void> {
    try {
      loading.value = true;
      zoom.value = payload.zoom;
      page.value = 0;
      const h3_resolution = zoom.value >= 15 ? 9 : 7;
      const { data } = await propertiesApi.get("/v1/search/feed/map", {
        params: {
          min_lat: payload.min_lat,
          max_lat: payload.max_lat,
          min_lon: payload.min_lon,
          max_lon: payload.max_lon,
          resolution: h3_resolution,
        },
      });
      _allItems.value = data.sort(() => Math.random() - 0.5);
    } finally {
      loading.value = false;
    }
  }

  function next() {
    if (hasNext.value) page.value++;
  }

  function prev() {
    if (hasPrev.value) page.value--;
  }

  return { hasPrev, hasNext, items, loading, fetchByBbox, next, prev };
}
