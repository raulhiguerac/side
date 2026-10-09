import { computed, ref } from "vue";
import * as adminCatalogApi from "@/api/admin/catalog";
import { PAGE_SIZE } from "@/constants/pagination";
import type {
  NeighborhoodAdminFilters,
  NeighborhoodAdminPage,
} from "@/types/admin/catalog";
import { pageRange } from "@/utils/pagination";
import { logger } from "@/utils/logger";

const FILTER_KEYS: (keyof NeighborhoodAdminFilters)[] = [
  "locality_id",
  "is_active",
  "has_geometry",
  "search_term",
];

/** La URL trae también `country_id`, que solo acota el select de localidad: no se manda. */
function pickFilters(source: Record<string, string>): NeighborhoodAdminFilters {
  return Object.fromEntries(
    FILTER_KEYS.filter((key) => source[key]).map((key) => [key, source[key]])
  );
}

/** Página por página contra el servidor: la respuesta ya trae `total_pages` y la cobertura. */
export function useAdminNeighborhoods() {
  const page = ref<NeighborhoodAdminPage | null>(null);
  const loading = ref(false);
  const error = ref<string | null>(null);
  const filters = ref<NeighborhoodAdminFilters>({});

  async function fetchPage(pageNumber: number) {
    loading.value = true;
    error.value = null;
    try {
      page.value = await adminCatalogApi.getNeighborhoods({
        ...filters.value,
        page: pageNumber,
        page_size: PAGE_SIZE.ADMIN_NEIGHBORHOODS,
      });
    } catch (e) {
      error.value = "No se pudieron cargar los barrios";
      logger.error("admin neighborhoods load failed", e);
      page.value = null;
    } finally {
      loading.value = false;
    }
  }

  function load(source: Record<string, string>) {
    filters.value = pickFilters(source);
    return fetchPage(1);
  }

  const currentPage = computed(() => page.value?.current_page ?? 1);
  const hasPrev = computed(() => currentPage.value > 1);
  const hasNext = computed(
    () => currentPage.value < (page.value?.total_pages ?? 0)
  );

  /** Rango visible, 1-indexado, para el "Mostrando X-Y de Z". */
  const range = computed(() =>
    page.value
      ? pageRange(
          currentPage.value,
          page.value.items_per_page,
          page.value.items.length
        )
      : pageRange(1, 0, 0)
  );

  return {
    rows: computed(() => page.value?.items ?? []),
    totalItems: computed(() => page.value?.total_items ?? 0),
    coverage: computed(() => page.value?.coverage ?? null),
    hasPrev,
    hasNext,
    range,
    loading,
    error,
    load,
    reload: () => fetchPage(currentPage.value),
    next: () => hasNext.value && fetchPage(currentPage.value + 1),
    prev: () => hasPrev.value && fetchPage(currentPage.value - 1),
  };
}
