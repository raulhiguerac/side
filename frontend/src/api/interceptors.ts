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

function redirectToLogin() {
  window.location.href = "/#/login";
}

export function applyAuthInterceptor(instance: AxiosInstance) {
  instance.interceptors.response.use(
    (response) => response,
    async (error) => {
      const original: InternalAxiosRequestConfig & { _retry?: boolean } =
        error.config;

      if (!error.config || error.response?.status !== 401 || original._retry) {
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
        redirectToLogin();
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }
  );
}
