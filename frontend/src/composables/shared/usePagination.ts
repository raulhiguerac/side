import { ref, computed, type Ref } from "vue";

interface FetchPageResult<T> {
  items: T[];
  hasMore: boolean;
}

export function usePagination<T>(pageSize = 20) {
  const allItems = ref([]) as Ref<T[]>;
  const page = ref(1);
  const hasMore = ref(false);

  const pagedItems = computed(() =>
    allItems.value.slice((page.value - 1) * pageSize, page.value * pageSize)
  );

  const hasPrev = computed(() => page.value > 1);
  const hasNext = computed(
    () => page.value * pageSize < allItems.value.length || hasMore.value
  );
  const total = computed(() => allItems.value.length);

  function setItems(items: T[], more = false) {
    allItems.value = items;
    hasMore.value = more;
    page.value = 1;
  }

  /** Refresca la página actual y descarta las siguientes: si una fila salió, se corrieron todas. */
  function replaceCurrentPage(items: T[], more = false) {
    const start = (page.value - 1) * pageSize;
    allItems.value = [...allItems.value.slice(0, start), ...items];
    hasMore.value = more;

    // Página vacía = ya no existe; se retrocede a la anterior, que está cargada.
    if (!items.length && hasPrev.value) page.value--;
  }

  async function next(fetchMore?: () => Promise<FetchPageResult<T>>) {
    if (!hasNext.value) return;

    const isLastLoadedPage = page.value * pageSize >= allItems.value.length;
    if (isLastLoadedPage && hasMore.value && fetchMore) {
      const result = await fetchMore();
      allItems.value.push(...result.items);
      hasMore.value = result.hasMore;
    }

    page.value++;
  }

  function prev() {
    if (hasPrev.value) page.value--;
  }

  function reset() {
    allItems.value = [];
    page.value = 1;
    hasMore.value = false;
  }

  return {
    pagedItems,
    page,
    hasPrev,
    hasNext,
    hasMore,
    total,
    setItems,
    replaceCurrentPage,
    next,
    prev,
    reset,
  };
}
