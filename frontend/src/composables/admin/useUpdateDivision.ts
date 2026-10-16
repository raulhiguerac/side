import { ref } from "vue";
import axios from "axios";
import { updateAdminDivision } from "@/api/admin/catalog";
import type {
  DivisionAdminRow,
  DivisionUpdatePayload,
} from "@/types/admin/catalog";
import { logger } from "@/utils/logger";

function messageForError(error: unknown): string {
  if (!axios.isAxiosError(error)) return "No se pudo guardar la división";

  const code = error.response?.data?.code;
  if (code === "ADMIN_DIVISION_NOT_FOUND")
    return "La división ya no existe. Recarga la lista.";
  if (code === "ADMIN_DIVISION_CONFLICT")
    return "Ya existe otra división con esos datos en el país.";
  if (code === "CATALOG_ADMIN_DB_UNAVAILABLE")
    return "El catálogo no está disponible. Intenta de nuevo en un momento.";
  if (error.response?.status === 403)
    return "No tienes permisos para editar divisiones";
  if (error.response?.status === 422) return "Revisa los datos del formulario";

  return "No se pudo guardar la división";
}

/** PATCH de una división: lo usan los modales de editar y de estado. */
export function useUpdateDivision() {
  const saving = ref(false);
  const error = ref<string | null>(null);

  async function update(
    divisionId: string,
    payload: DivisionUpdatePayload
  ): Promise<DivisionAdminRow | null> {
    reset();
    saving.value = true;
    try {
      return await updateAdminDivision(divisionId, payload);
    } catch (e) {
      logger.error("admin division update failed", e);
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
