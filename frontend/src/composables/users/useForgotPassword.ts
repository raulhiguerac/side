import { ref } from "vue";
import axios from "axios";
import * as usersApi from "@/api/users";
import { logger } from "@/utils/logger";

export function useForgotPassword() {
  const sending = ref(false);
  const sent = ref(false);
  const error = ref<string | null>(null);

  async function requestReset(email: string) {
    sending.value = true;
    error.value = null;
    try {
      await usersApi.requestPasswordReset(email);
      sent.value = true;
    } catch (e) {
      logger.error("Error al pedir el reset de contraseña:", e);
      error.value =
        axios.isAxiosError(e) && e.response?.status === 422
          ? "Revisa el correo"
          : "No pudimos enviar el enlace, intenta de nuevo";
    } finally {
      sending.value = false;
    }
  }

  return { sending, sent, error, requestReset };
}
