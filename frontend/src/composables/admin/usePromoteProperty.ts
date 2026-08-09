import { ref } from "vue";
import axios from "axios";
import propertiesApi from "@/api/propertiesApi";
import { PROPERTIES_ENDPOINTS } from "@/constants/propertiesEndpoints";
import type { PromotionPayload } from "@/types/admin";

/** Crea la promoción de una property; un solo POST, a diferencia de moderar. */

/**
 * Los dos 409 posibles llegan distinguidos por `code` —a diferencia de las
 * transiciones, donde el handler descarta el contexto— así que el mensaje puede
 * decir qué pasó.
 */
function messageForError(error: unknown): string {
  if (!axios.isAxiosError(error)) return "No se pudo promocionar";

  const code = error.response?.data?.code;
  if (code === "DUPLICATE_ACTIVE_PROMOTION")
    return "Esta propiedad ya tiene una promoción activa.";
  if (code === "PROPERTY_NOT_READY_FOR_PROMOTION")
    return "Solo se pueden promocionar propiedades activas.";
  if (error.response?.status === 404) return "La propiedad ya no existe";
  if (error.response?.status === 403)
    return "No tenés permisos para promocionar";

  return "No se pudo promocionar";
}

export function usePromoteProperty() {
  const saving = ref(false);
  const error = ref<string | null>(null);
  const success = ref<string | null>(null);

  async function promote(
    propertyId: string,
    payload: PromotionPayload
  ): Promise<boolean> {
    saving.value = true;
    error.value = null;
    success.value = null;

    try {
      await propertiesApi.post(PROPERTIES_ENDPOINTS.adminPromotions, {
        property_id: propertyId,
        promoted_days: payload.promotedDays,
        priority: payload.priority,
      });
      success.value = "Promoción creada";
      return true;
    } catch (e) {
      console.error("admin promotion failed", e);
      error.value = messageForError(e);
      return false;
    } finally {
      saving.value = false;
    }
  }

  /** Los mensajes son de la property promocionada: dejan de aplicar al pasar a otra. */
  function reset() {
    error.value = null;
    success.value = null;
  }

  return {
    saving,
    error,
    success,
    promote,
    reset,
  };
}
