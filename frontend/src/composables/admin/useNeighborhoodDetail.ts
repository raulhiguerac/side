import { ref, watch, type Ref } from "vue";
import * as adminCatalogApi from "@/api/admin/catalog";
import type { NeighborhoodAdminDetail } from "@/types/admin/catalog";
import { logger } from "@/utils/logger";

/** Sigue a la fila seleccionada; si cambia antes de responder, la respuesta vieja se descarta. */
export function useNeighborhoodDetail(neighborhoodId: Ref<string | null>) {
  const detail = ref<NeighborhoodAdminDetail | null>(null);
  const loading = ref(false);
  const error = ref<string | null>(null);
  let latestRequest = 0;

  async function load(id: string | null) {
    const request = ++latestRequest;
    error.value = null;
    if (!id) {
      detail.value = null;
      return;
    }

    loading.value = true;
    try {
      const data = await adminCatalogApi.getNeighborhood(id);
      if (request === latestRequest) detail.value = data;
    } catch (e) {
      if (request !== latestRequest) return;
      error.value = "No se pudo cargar el barrio";
      detail.value = null;
      logger.error("admin neighborhood detail failed", e);
    } finally {
      if (request === latestRequest) loading.value = false;
    }
  }

  watch(neighborhoodId, load, { immediate: true });

  return { detail, loading, error, reload: () => load(neighborhoodId.value) };
}
