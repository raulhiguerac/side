import { computed, shallowRef, ref } from "vue";
import type { AdminPage, PageParams } from "@/types/shared/pagination";
import { pageRange } from "@/utils/pagination";
import { logger } from "@/utils/logger";

interface AdminPageOptions<TPage> {
  fetch: (page: PageParams, filters: Record<string, string>) => Promise<TPage>;
  pageSize: number;
  errorMessage: string;
}

/** Listado admin paginado contra el servidor: la respuesta ya trae `total_pages`. */
export function useAdminPage<TPage extends AdminPage<unknown>>({
  fetch,
  pageSize,
  errorMessage,
}: AdminPageOptions<TPage>) {
  const page = shallowRef<TPage | null>(null);
  const loading = ref(false);
  const error = ref<string | null>(null);
  let filters: Record<string, string> = {};

  async function fetchPage(pageNumber: number) {
    loading.value = true;
    error.value = null;
    try {
      page.value = await fetch(
        { page: pageNumber, page_size: pageSize },
        filters
      );
    } catch (e) {
      error.value = errorMessage;
      logger.error(errorMessage, e);
      page.value = null;
    } finally {
      loading.value = false;
    }
  }

  function load(source: Record<string, string>) {
    filters = source;
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
    page,
    rows: computed<TPage["items"]>(() => page.value?.items ?? []),
    totalItems: computed(() => page.value?.total_items ?? 0),
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
