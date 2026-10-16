import { ref } from "vue";
import axios from "axios";
import { createCountry } from "@/api/admin/catalog";
import type {
  CountryAdminResponse,
  CountryCreatePayload,
} from "@/types/admin/catalog";
import { logger } from "@/utils/logger";

function messageForError(error: unknown): string {
  if (!axios.isAxiosError(error)) return "No se pudo crear el país";

  const code = error.response?.data?.code;
  if (code === "COUNTRY_CONFLICT")
    return "Ya existe un país con esos códigos ISO.";
  if (code === "CATALOG_ADMIN_DB_UNAVAILABLE")
    return "El catálogo no está disponible. Intenta de nuevo en un momento.";
  if (error.response?.status === 403)
    return "No tienes permisos para crear países";
  if (error.response?.status === 422) return "Revisa los datos del formulario";

  return "No se pudo crear el país";
}

export function useCreateCountry() {
  const saving = ref(false);
  const error = ref<string | null>(null);

  async function create(
    payload: CountryCreatePayload
  ): Promise<CountryAdminResponse | null> {
    reset();
    saving.value = true;
    try {
      return await createCountry(payload);
    } catch (e) {
      logger.error("admin country create failed", e);
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
