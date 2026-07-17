import { createRouter, createWebHashHistory } from "vue-router";
import { useAuthStore } from "@/stores/auth";
import { publicRoutes } from "./routes/public";
import { authRoutes } from "./routes/auth";
import { settingsRoutes } from "./routes/settings";
import { propertiesRoutes } from "./routes/properties";
import { analyticsRoutes } from "./routes/analytics";
import { devRoutes } from "./routes/dev";
import { adminRoutes } from "./routes/admin";

const router = createRouter({
  history: createWebHashHistory(),
  routes: [
    ...publicRoutes,
    ...authRoutes,
    ...settingsRoutes,
    ...propertiesRoutes,
    ...analyticsRoutes,
    ...devRoutes,
    ...adminRoutes,
  ],
});

router.beforeEach(async (to) => {
  const authStore = useAuthStore();

  const requiresAuth = to.matched.some((record) => record.meta.requiresAuth);
  const requiresAdmin = to.matched.some((record) => record.meta.requiresAdmin);
  const isGuestRoute = to.matched.some((record) => record.meta.isLogged);

  if (isGuestRoute) {
    if (authStore.isAuthenticated) return { name: "home" };
    return;
  }

  if (requiresAuth && !authStore._authChecked) {
    try {
      await authStore.checkAuth();
    } catch (e) {
      console.error("🚫 Error verificando identidad en navegación protegida");
    }
  }

  if (requiresAuth && !authStore.isAuthenticated) {
    return { name: "login" };
  }

  if (requiresAdmin) {
    if (!authStore.accountId) {
      try {
        await authStore.fillUserData();
      } catch (e) {
        console.error("🚫 Error verificando rol de administrador");
      }
    }

    if (!authStore.isAdmin) {
      return { name: "home" };
    }
  }
});

export default router;
