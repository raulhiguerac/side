import { ref } from "vue";
import axios from "axios";
import propertiesApi from "@/api/propertiesApi";
import { PROPERTIES_ENDPOINTS } from "@/constants/propertiesEndpoints";
import type { ModerationPayload } from "@/types/admin";

/** Traduce el payload del formulario a uno o dos PATCH. */

/** Verificación primero: si solo entra uno, que sea el que decide si sigue en la cola. */
const STEP_LABELS = {
  verification: "la verificación",
  status: "el estado",
} as const;

/** El 409 llega sin `{current, target}` (el handler descarta el `context`): mensaje genérico. */
function messageForError(error: unknown): string {
  if (!axios.isAxiosError(error)) return "No se pudo guardar";

  switch (error.response?.status) {
    case 409:
      return "El cambio ya no es válido — la propiedad cambió de estado. Recargá para ver el estado actual.";
    case 404:
      return "La propiedad ya no existe";
    case 403:
      return "No tenés permisos para moderar";
    case 422:
      return "El backend rechazó los datos del formulario";
    default:
      return "No se pudo guardar";
  }
}

export function useModerateProperty() {
  const saving = ref(false);
  const error = ref<string | null>(null);
  const success = ref<string | null>(null);

  /** Devuelve si algo quedó escrito, no si salió todo bien: un fallo parcial también obliga a refetchear. */
  async function moderate(
    propertyId: string,
    payload: ModerationPayload
  ): Promise<boolean> {
    saving.value = true;
    error.value = null;
    success.value = null;

    let applied: keyof typeof STEP_LABELS | null = null;

    try {
      if (payload.verificationStatus) {
        await propertiesApi.patch(
          PROPERTIES_ENDPOINTS.adminVerification(propertyId),
          {
            verification_status: payload.verificationStatus,
            // Omitido y no `null`: el backend lo prohíbe si no se está rechazando.
            ...(payload.rejectionReason
              ? { rejection_reason: payload.rejectionReason }
              : {}),
          }
        );
        applied = "verification";
      }

      if (payload.status) {
        await propertiesApi.patch(
          PROPERTIES_ENDPOINTS.adminStatus(propertyId),
          { status: payload.status }
        );
        applied = "status";
      }

      success.value = "Cambios guardados";
      return true;
    } catch (e) {
      console.error("admin moderation failed", e);

      const reason = messageForError(e);

      // Sin distinguir el fallo parcial, el reintento choca contra una transición ya aplicada.
      error.value =
        applied === "verification" && payload.status
          ? `Se guardó ${STEP_LABELS.verification}, pero ${STEP_LABELS.status} no cambió: ${reason}`
          : reason;

      return applied !== null;
    } finally {
      saving.value = false;
    }
  }

  /** Los mensajes son de una property concreta: dejan de aplicar al pasar a otra. */
  function reset() {
    error.value = null;
    success.value = null;
  }

  return {
    saving,
    error,
    success,
    moderate,
    reset,
  };
}
