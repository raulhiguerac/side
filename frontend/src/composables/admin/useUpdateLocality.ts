import { ref } from "vue";
import axios from "axios";
import { updateLocality } from "@/api/admin/catalog";
import type {
  LocalityAdminResponse,
  LocalityUpdatePayload,
} from "@/types/admin/catalog";
import { logger } from "@/utils/logger";

function messageForError(error: unknown): string {
  if (!axios.isAxiosError(error)) return "No se pudo guardar la localidad";

  const code = error.response?.data?.code;
  if (code === "LOCALITY_ADMIN_NOT_FOUND")
    return "La localidad ya no existe. Recarga la lista.";
  if (code === "LOCALITY_CONFLICT")
    return "Ya existe otra localidad con esos datos en el país.";
  if (code === "CATALOG_ADMIN_DB_UNAVAILABLE")
    return "El catálogo no está disponible. Intenta de nuevo en un momento.";
  if (error.response?.status === 403)
    return "No tienes permisos para editar localidades";
  if (error.response?.status === 422) return "Revisa los datos del formulario";

  return "No se pudo guardar la localidad";
}

/** PATCH de una localidad: lo usan los modales de editar y de estado. */
export function useUpdateLocality() {
  const saving = ref(false);
  const error = ref<string | null>(null);

  async function update(
    localityId: string,
    payload: LocalityUpdatePayload
  ): Promise<LocalityAdminResponse | null> {
    reset();
    saving.value = true;
    try {
      return await updateLocality(localityId, payload);
    } catch (e) {
      logger.error("admin locality update failed", e);
      error.value = messageForError(e);
      return null;
    } finally {
      saving.value = false;
    }
  }

  function reset() {
    error.value = null;
  }

  return { saving, error, update, reset };
}
