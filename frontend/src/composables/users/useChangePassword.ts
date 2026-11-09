import { ref } from "vue";
import axios from "axios";
import * as usersApi from "@/api/users";
import { useAuthStore } from "@/stores/auth";
import { logger } from "@/utils/logger";

function messageForError(error: unknown): string {
  if (!axios.isAxiosError(error)) return "Error al actualizar la contraseña";

  const code = error.response?.data?.code;
  if (code === "INVALID_CREDENTIALS")
    return "La contraseña actual es incorrecta";
  if (code === "PASSWORD_SAME_AS_OLD")
    return "La nueva contraseña debe ser distinta a la actual";
  if (error.response?.status === 422) return "Revisa la contraseña";

  return "Error al actualizar la contraseña";
}

export function useChangePassword() {
  const authStore = useAuthStore();

  const sending = ref(false);
  const error = ref<string | null>(null);

  async function changePassword(oldPassword: string, newPassword: string) {
    sending.value = true;
    error.value = null;
    try {
      await usersApi.changePassword({
        old_password: oldPassword,
        new_password: newPassword,
      });
      // El back ya cerró la sesión y borró las cookies
      await authStore.logout({ name: "login" });
    } catch (e) {
      logger.error("Error al cambiar la contraseña:", e);
      error.value = messageForError(e);
    } finally {
      sending.value = false;
    }
  }

  return { sending, error, changePassword };
}
