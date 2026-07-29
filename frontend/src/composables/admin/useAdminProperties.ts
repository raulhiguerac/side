import { ref, computed } from "vue";
import propertiesApi from "@/api/propertiesApi";
import { PROPERTIES_ENDPOINTS } from "@/constants/propertiesEndpoints";
import { PAGE_SIZE } from "@/constants/pagination";
import { usePagination } from "@/composables/shared/usePagination";
import type {
  AdminPropertiesFilters,
  AdminPropertiesPage,
  AdminPropertyRow,
} from "@/types/admin";

async function fetchAdminProperties(
  page: number,
  filters: AdminPropertiesFilters
): Promise<AdminPropertiesPage> {
  const { data } = await propertiesApi.get<AdminPropertiesPage>(
    PROPERTIES_ENDPOINTS.adminList,
    {
      params: {
        page,
        page_size: PAGE_SIZE.ADMIN_PROPERTIES,
        ...filters,
      },
    }
  );
  return data;
}

export function useAdminProperties() {
  const pagination = usePagination<AdminPropertyRow>(
    PAGE_SIZE.ADMIN_PROPERTIES
  );

  const loading = ref(false);
  const error = ref<string | null>(null);
  const filters = ref<AdminPropertiesFilters>({});

  /**
   * El total del servidor se guarda aparte a propósito: el `total` que expone
   * `usePagination` es `allItems.length`, o sea lo cargado hasta ahora. Para
   * "Mostrando 1-20 de 18.744" hace falta el conteo real, que es justamente lo
   * que el listado admin pagina por offset para poder dar (ver ADR-0009).
   */
  const serverTotal = ref(0);

  const totalPages = computed(() =>
    Math.max(1, Math.ceil(serverTotal.value / PAGE_SIZE.ADMIN_PROPERTIES))
  );

  /** Rango visible, 1-indexado, para el "Mostrando X-Y de Z". */
  const range = computed(() => {
    if (!serverTotal.value) return { from: 0, to: 0 };
    const from = (pagination.page.value - 1) * PAGE_SIZE.ADMIN_PROPERTIES + 1;
    return {
      from,
      to: Math.min(
        from + pagination.pagedItems.value.length - 1,
        serverTotal.value
      ),
    };
  });

  function hasMoreAfter(loadedCount: number): boolean {
    return loadedCount < serverTotal.value;
  }

  async function load(next: AdminPropertiesFilters = filters.value) {
    loading.value = true;
    error.value = null;
    filters.value = next;

    try {
      const data = await fetchAdminProperties(1, next);
      serverTotal.value = data.total;
      pagination.setItems(data.items, hasMoreAfter(data.items.length));
    } catch (e) {
      error.value = "No se pudieron cargar las propiedades";
      console.error("admin properties load failed", e);
      serverTotal.value = 0;
      pagination.setItems([], false);
    } finally {
      loading.value = false;
    }
  }

  /**
   * Avanzar es "cuánto nos desplazamos": `usePagination` solo pide al servidor
   * cuando la página siguiente todavía no está cargada, así que volver atrás
   * nunca dispara request — las filas ya están en memoria.
   */
  async function next() {
    if (loading.value) return;
    loading.value = true;

    try {
      await pagination.next(async () => {
        const nextPage = Math.floor(
          pagination.total.value / PAGE_SIZE.ADMIN_PROPERTIES + 1
        );
        const data = await fetchAdminProperties(nextPage, filters.value);
        serverTotal.value = data.total;
        return {
          items: data.items,
          hasMore: hasMoreAfter(pagination.total.value + data.items.length),
        };
      });
    } catch (e) {
      error.value = "No se pudo cargar la página siguiente";
      console.error("admin properties next page failed", e);
    } finally {
      loading.value = false;
    }
  }

  function prev() {
    pagination.prev();
  }

  return {
    rows: pagination.pagedItems,
    page: pagination.page,
    hasPrev: pagination.hasPrev,
    hasNext: pagination.hasNext,
    totalPages,
    serverTotal,
    range,
    filters,
    loading,
    error,
    load,
    next,
    prev,
  };
}
