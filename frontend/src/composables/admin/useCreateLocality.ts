import { ref } from "vue";
import axios from "axios";
import { createLocality } from "@/api/admin/catalog";
import type {
  LocalityAdminResponse,
  LocalityCreatePayload,
} from "@/types/admin/catalog";
import { logger } from "@/utils/logger";

function messageForError(error: unknown): string {
  if (!axios.isAxiosError(error)) return "No se pudo crear la localidad";

  const code = error.response?.data?.code;
  if (code === "LOCALITY_CONFLICT")
    return "Ya existe una localidad con ese código en el país.";
  if (code === "CATALOG_ADMIN_DB_UNAVAILABLE")
    return "El catálogo no está disponible. Intenta de nuevo en un momento.";
  if (error.response?.status === 403)
    return "No tienes permisos para crear localidades";
  if (error.response?.status === 422) return "Revisa los datos del formulario";

  return "No se pudo crear la localidad";
}

export function useCreateLocality() {
  const saving = ref(false);
  const error = ref<string | null>(null);

  async function create(
    payload: LocalityCreatePayload
  ): Promise<LocalityAdminResponse | null> {
    reset();
    saving.value = true;
    try {
      return await createLocality(payload);
    } catch (e) {
      logger.error("admin locality create failed", e);
      error.value = messageForError(e);
      return null;
    } finally {
      saving.value = false;
    }
  }

  function reset() {
    error.value = null;
  }

  return { saving, error, create, reset };
}
