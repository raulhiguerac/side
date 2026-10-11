import { ref } from "vue";
import axios from "axios";
import * as adminCatalogApi from "@/api/admin/catalog";
import type {
  NeighborhoodAdminResponse,
  NeighborhoodCreatePayload,
} from "@/types/admin/catalog";
import { logger } from "@/utils/logger";

function messageForError(error: unknown): string {
  if (!axios.isAxiosError(error)) return "No se pudo crear el barrio";

  const code = error.response?.data?.code;
  if (code === "NEIGHBORHOOD_CONFLICT")
    return "Ya existe un barrio con ese código en la localidad.";
  if (code === "CATALOG_ADMIN_DB_UNAVAILABLE")
    return "El catálogo no está disponible. Intenta de nuevo en un momento.";
  if (error.response?.status === 403)
    return "No tienes permisos para crear barrios";
  if (error.response?.status === 422) return "Revisa los datos del formulario";

  return "No se pudo crear el barrio";
}

/** Crea un barrio sin geometría en la localidad dada. */
export function useCreateNeighborhood() {
  const saving = ref(false);
  const error = ref<string | null>(null);

  async function create(
    payload: NeighborhoodCreatePayload
  ): Promise<NeighborhoodAdminResponse | null> {
    reset();
    saving.value = true;
    try {
      return await adminCatalogApi.createNeighborhood(payload);
    } catch (e) {
      logger.error("admin neighborhood create failed", e);
      error.value = messageForError(e);
      return null;
    } finally {
      saving.value = false;
    }
  }

  function reset() {
    error.value = null;
  }

  return {
    saving,
    error,
    create,
    reset,
  };
}
