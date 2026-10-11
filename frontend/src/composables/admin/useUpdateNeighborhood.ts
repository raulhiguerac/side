import { ref } from "vue";
import axios from "axios";
import type {
  NeighborhoodAdminResponse,
  NeighborhoodUpdatePayload,
} from "@/types/admin/catalog";
import { updateNeighborhood } from "@/api/admin/catalog";
import { logger } from "@/utils/logger";

function messageForError(error: unknown): string {
  if (!axios.isAxiosError(error)) return "No se pudo guardar el barrio";

  const code = error.response?.data?.code;
  if (code === "NEIGHBORHOOD_ADMIN_NOT_FOUND")
    return "El barrio ya no existe. Recarga la lista.";
  if (code === "NEIGHBORHOOD_CONFLICT")
    return "Ya existe otro barrio con esos datos en la localidad.";
  if (code === "CATALOG_ADMIN_DB_UNAVAILABLE")
    return "El catálogo no está disponible. Intenta de nuevo en un momento.";
  if (error.response?.status === 403)
    return "No tienes permisos para editar barrios";
  if (error.response?.status === 422) return "Revisa los datos del formulario";

  return "No se pudo guardar el barrio";
}

/** PATCH de un barrio: lo usan los modales de editar y de estado. */
export function useUpdateNeighborhood() {
  const saving = ref(false);
  const error = ref<string | null>(null);

  async function update(
    neighborhoodId: string,
    payload: NeighborhoodUpdatePayload
  ): Promise<NeighborhoodAdminResponse | null> {
    let response: NeighborhoodAdminResponse | null = null;
    reset();
    saving.value = true;
    try {
      response = await updateNeighborhood(neighborhoodId, payload);
    } catch (e) {
      logger.error("admin neighborhood update failed", e);
      error.value = messageForError(e);
    } finally {
      saving.value = false;
    }
    return response;
  }

  function reset() {
    error.value = null;
  }

  return {
    saving,
    error,
    update,
    reset,
  };
}
