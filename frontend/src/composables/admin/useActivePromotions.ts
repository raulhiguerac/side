import { computed, ref } from "vue";
import axios from "axios";
import propertiesApi from "@/api/propertiesApi";
import { PROPERTIES_ENDPOINTS } from "@/constants/propertiesEndpoints";
import { PAGE_SIZE } from "@/constants/pagination";
import type {
  AdminPromotionRow,
  AdminPromotionsPage,
} from "@/types/admin/promotions";
import { pageRange } from "@/utils/pagination";
import { logger } from "@/utils/logger";

/** Promociones activas paginadas por offset, con su property anidada. */
export function useActivePromotions() {
  const promotions = ref<AdminPromotionRow[]>([]);
  const page = ref(1);
  const total = ref(0);
  const loading = ref(false);
  const error = ref<string | null>(null);
  const removing = ref(false);
  const removeError = ref<string | null>(null);

  const hasPrev = computed(() => page.value > 1);
  const hasNext = computed(
    () => page.value * PAGE_SIZE.ADMIN_PROMOTIONS < total.value
  );

  // Siempre al servidor: quitar una promoción corre las páginas siguientes.
  const range = computed(() =>
    pageRange(page.value, PAGE_SIZE.ADMIN_PROMOTIONS, promotions.value.length)
  );

  async function load(next = page.value) {
    loading.value = true;
    error.value = null;

    try {
      const { data } = await propertiesApi.get<AdminPromotionsPage>(
        PROPERTIES_ENDPOINTS.adminPromotions,
        { params: { page: next, page_size: PAGE_SIZE.ADMIN_PROMOTIONS } }
      );
      promotions.value = data.items;
      total.value = data.total;
      page.value = data.page;
    } catch (e) {
      error.value = "No se pudieron cargar las promociones activas";
      logger.error("admin active promotions load failed", e);
      promotions.value = [];
      total.value = 0;
    } finally {
      loading.value = false;
    }
  }

  // Acá y no aparte: tras el DELETE hay que releer esta misma lista.
  async function remove(propertyId: string): Promise<boolean> {
    removing.value = true;
    removeError.value = null;

    try {
      await propertiesApi.delete(
        PROPERTIES_ENDPOINTS.adminPropertyPromotions(propertyId)
      );
      return true;
    } catch (e) {
      logger.error("admin promotion removal failed", e);
      removeError.value =
        axios.isAxiosError(e) && e.response?.status === 404
          ? "Esta propiedad ya no tiene una promoción activa."
          : "No se pudo quitar la promoción";
      return false;
    } finally {
      removing.value = false;
    }
  }

  /** Vaciar la última página deja parado donde ya no hay nada. */
  async function reload() {
    const target =
      promotions.value.length === 1 && hasPrev.value
        ? page.value - 1
        : page.value;
    await load(target);
  }

  function next() {
    if (hasNext.value) load(page.value + 1);
  }

  function prev() {
    if (hasPrev.value) load(page.value - 1);
  }

  return {
    promotions,
    page,
    total,
    range,
    hasPrev,
    hasNext,
    loading,
    error,
    removing,
    removeError,
    load,
    reload,
    remove,
    next,
    prev,
  };
}
