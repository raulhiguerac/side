import axios, {
  type AxiosInstance,
  type InternalAxiosRequestConfig,
} from "axios";
import { API } from "@/config";

let isRefreshing = false;
let failedQueue: Array<{
  resolve: (value?: unknown) => void;
  reject: (reason?: unknown) => void;
}> = [];

function processQueue(error: unknown) {
  failedQueue.forEach(({ resolve, reject }) => {
    if (error) reject(error);
    else resolve();
  });
  failedQueue = [];
}

async function refreshTokens() {
  await axios.post(`${API.USERS_BASE_URL}/v1/auth/refresh`, null, {
    withCredentials: true,
    timeout: 3000,
  });
}

const AUTH_ENTRYPOINTS = ["/auth/login", "/auth/register"];

async function forceLogout() {
  const { useAuthStore } = await import("@/stores/auth");
  await useAuthStore().logout();
}

export function applyAuthInterceptor(instance: AxiosInstance) {
  instance.interceptors.response.use(
    (response) => response,
    async (error) => {
      const original: InternalAxiosRequestConfig & { _retry?: boolean } =
        error.config;

      const isAuthEntrypoint = AUTH_ENTRYPOINTS.some((path) =>
        original?.url?.includes(path)
      );

      if (
        !error.config ||
        error.response?.status !== 401 ||
        original._retry ||
        isAuthEntrypoint
      ) {
        return Promise.reject(error);
      }

      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        }).then(() => instance(original));
      }

      original._retry = true;
      isRefreshing = true;

      try {
        await refreshTokens();
        processQueue(null);
        return instance(original);
      } catch (refreshError) {
        processQueue(refreshError);
        await forceLogout();
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }
  );
}
