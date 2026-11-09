import { onBeforeUnmount, onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import axios from "axios";
import * as usersApi from "@/api/users";
import { logger } from "@/utils/logger";

const REDIRECT_DELAY_MS = 2000;

export function useReactivateAccount() {
  const route = useRoute();
  const router = useRouter();

  const token = typeof route.query.token === "string" ? route.query.token : "";
  // Fuera de la URL para que no quede en el historial
  if (route.query.token !== undefined) router.replace({ query: {} });

  const confirming = ref(!!token);
  const confirmed = ref(false);
  const invalidLink = ref(false);

  const sending = ref(false);
  const sent = ref(false);
  const error = ref<string | null>(null);

  let redirectTimer: ReturnType<typeof setTimeout> | undefined;

  async function confirmReactivation() {
    try {
      await usersApi.confirmReactivation(token);
      confirmed.value = true;
      redirectTimer = setTimeout(
        () => router.replace({ name: "login" }),
        REDIRECT_DELAY_MS
      );
    } catch (e) {
      logger.error("Error al confirmar la reactivación:", e);
      invalidLink.value = true;
    } finally {
      confirming.value = false;
    }
  }

  async function requestReactivation(email: string) {
    sending.value = true;
    error.value = null;
    invalidLink.value = false;
    try {
      await usersApi.requestReactivation(email);
      sent.value = true;
    } catch (e) {
      logger.error("Error al pedir la reactivación:", e);
      error.value =
        axios.isAxiosError(e) && e.response?.status === 422
          ? "Revisa el correo"
          : "No pudimos enviar el enlace, intenta de nuevo";
    } finally {
      sending.value = false;
    }
  }

  onMounted(() => {
    if (token) void confirmReactivation();
  });
  onBeforeUnmount(() => clearTimeout(redirectTimer));

  return {
    confirming,
    confirmed,
    invalidLink,
    sending,
    sent,
    error,
    requestReactivation,
  };
}
