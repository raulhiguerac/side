import { ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import axios from "axios";
import * as usersApi from "@/api/users";
import { logger } from "@/utils/logger";

function isInvalidToken(error: unknown): boolean {
  return (
    axios.isAxiosError(error) &&
    error.response?.data?.code === "TOKEN_INVALID_OR_EXPIRED"
  );
}

function messageForError(error: unknown): string {
  if (!axios.isAxiosError(error))
    return "No pudimos cambiar la contraseña, intenta de nuevo";

  if (error.response?.data?.code === "PASSWORDS_DO_NOT_MATCH")
    return "Las contraseñas no coinciden";
  if (error.response?.status === 422) return "Revisa la contraseña";

  return "No pudimos cambiar la contraseña, intenta de nuevo";
}

export function useResetPassword() {
  const route = useRoute();
  const router = useRouter();

  const token = typeof route.query.token === "string" ? route.query.token : "";
  // Fuera de la URL para que no quede en el historial
  if (route.query.token !== undefined) router.replace({ query: {} });

  const sending = ref(false);
  const confirmed = ref(false);
  const invalidLink = ref(!token);
  const error = ref<string | null>(null);

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
      if (isInvalidToken(e)) invalidLink.value = true;
      else error.value = messageForError(e);
    } finally {
      sending.value = false;
    }
  }

  return { sending, confirmed, invalidLink, error, confirmReset };
}
