import { computed, ref } from "vue";
import propertiesApi from "@/api/propertiesApi";
import { PROPERTIES_ENDPOINTS } from "@/constants/propertiesEndpoints";
import { PAGE_SIZE } from "@/constants/pagination";
import type {
  BulkJobRow,
  BulkJobsFilters,
  BulkJobsPage,
} from "@/types/admin/bulk";
import { pageRange } from "@/utils/pagination";
import { logger } from "@/utils/logger";

// Siempre al servidor: relanzar agrega una corrida arriba y corre las páginas.
export function useBulkJobs() {
  const jobs = ref<BulkJobRow[]>([]);
  const page = ref(1);
  const total = ref(0);
  const loading = ref(false);
  const error = ref<string | null>(null);
  const filters = ref<BulkJobsFilters>({});

  const hasPrev = computed(() => page.value > 1);
  const hasNext = computed(
    () => page.value * PAGE_SIZE.ADMIN_BULK_JOBS < total.value
  );

  const range = computed(() =>
    pageRange(page.value, PAGE_SIZE.ADMIN_BULK_JOBS, jobs.value.length)
  );

  async function load(next = page.value, nextFilters = filters.value) {
    loading.value = true;
    error.value = null;
    filters.value = nextFilters;

    try {
      const { data } = await propertiesApi.get<BulkJobsPage>(
        PROPERTIES_ENDPOINTS.adminBulkJobs,
        {
          params: {
            page: next,
            page_size: PAGE_SIZE.ADMIN_BULK_JOBS,
            ...nextFilters,
          },
        }
      );
      jobs.value = data.items;
      total.value = data.total;
      page.value = data.page;
    } catch (e) {
      error.value = "No se pudieron cargar las importaciones";
      logger.error("admin bulk jobs load failed", e);
      jobs.value = [];
      total.value = 0;
    } finally {
      loading.value = false;
    }
  }

  /** Filtrar arranca de la página 1: la que estabas viendo no existe en el nuevo conjunto. */
  function applyFilters(nextFilters: BulkJobsFilters) {
    return load(1, nextFilters);
  }

  function next() {
    if (hasNext.value) load(page.value + 1);
  }

  function prev() {
    if (hasPrev.value) load(page.value - 1);
  }

  return {
    jobs,
    page,
    total,
    range,
    hasPrev,
    hasNext,
    loading,
    error,
    filters,
    load,
    applyFilters,
    next,
    prev,
  };
}
