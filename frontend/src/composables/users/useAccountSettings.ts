import { ref } from "vue";
import * as usersApi from "@/api/users";
import { useAuthStore } from "@/stores/auth";
import { logger } from "@/utils/logger";

export function useAccountSettings() {
  const authStore = useAuthStore();
  const deactivating = ref(false);
  const error = ref<string | null>(null);

  async function deactivate() {
    deactivating.value = true;
    error.value = null;
    try {
      await usersApi.deactivateAccount();
    } catch (e) {
      logger.error("Error al desactivar la cuenta:", e);
      error.value = "No se pudo desactivar la cuenta";
      deactivating.value = false;
      return;
    }
    // El backend ya cerró la sesión; esto limpia el estado local y redirige.
    await authStore.logout();
  }

  function reset() {
    error.value = null;
  }

  return { deactivating, error, deactivate, reset };
}
