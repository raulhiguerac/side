import { ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import axios from "axios";
import * as usersApi from "@/api/users";
import { logger } from "@/utils/logger";

const INVALID_LINK_MESSAGE = "El enlace no es válido o venció";

export function useResetPassword() {
  const route = useRoute();
  const router = useRouter();

  const token = typeof route.query.token === "string" ? route.query.token : "";
  // Fuera de la URL para que no quede en el historial
  if (route.query.token !== undefined) router.replace({ query: {} });

  const sending = ref(false);
  const confirmed = ref(false);
  const invalidLink = ref(!token);
  const error = ref<string | null>(token ? null : INVALID_LINK_MESSAGE);

  async function confirmReset(newPassword: string, confirmPassword: string) {
    sending.value = true;
    error.value = null;
    try {
      await usersApi.confirmPasswordReset(token, {
        new_password: newPassword,
        confirm_password: confirmPassword,
      });
      confirmed.value = true;
    } catch (e) {
      logger.error("Error al confirmar el reset de contraseña:", e);
      const status = axios.isAxiosError(e) ? e.response?.status : undefined;
      if (status === 401) {
        invalidLink.value = true;
        error.value = INVALID_LINK_MESSAGE;
      } else if (status === 400) {
        error.value = "Las contraseñas no coinciden";
      } else {
        error.value = "No pudimos cambiar la contraseña, intenta de nuevo";
      }
    } finally {
      sending.value = false;
    }
  }

  return { sending, confirmed, invalidLink, error, confirmReset };
}
