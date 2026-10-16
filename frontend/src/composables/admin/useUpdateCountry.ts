import { ref } from "vue";
import axios from "axios";
import { updateCountry } from "@/api/admin/catalog";
import type {
  CountryAdminResponse,
  CountryUpdatePayload,
} from "@/types/admin/catalog";
import { logger } from "@/utils/logger";

function messageForError(error: unknown): string {
  if (!axios.isAxiosError(error)) return "No se pudo guardar el país";

  const code = error.response?.data?.code;
  if (code === "COUNTRY_NOT_FOUND")
    return "El país ya no existe. Recarga la lista.";
  if (code === "COUNTRY_CONFLICT") return "Ya existe otro país con esos datos.";
  if (code === "CATALOG_ADMIN_DB_UNAVAILABLE")
    return "El catálogo no está disponible. Intenta de nuevo en un momento.";
  if (error.response?.status === 403)
    return "No tienes permisos para editar países";
  if (error.response?.status === 422) return "Revisa los datos del formulario";

  return "No se pudo guardar el país";
}

/** PATCH de un país: lo usan los modales de editar y de estado. */
export function useUpdateCountry() {
  const saving = ref(false);
  const error = ref<string | null>(null);

  async function update(
    countryId: string,
    payload: CountryUpdatePayload
  ): Promise<CountryAdminResponse | null> {
    reset();
    saving.value = true;
    try {
      return await updateCountry(countryId, payload);
    } catch (e) {
      logger.error("admin country update failed", e);
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
