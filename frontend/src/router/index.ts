import { createRouter, createWebHashHistory, RouteRecordRaw } from "vue-router";
import HomeView from "../views/public/HomeView.vue";
import { useAuthStore } from "@/stores/auth";

const routes: Array<RouteRecordRaw> = [
  {
    path: "/",
    name: "home",
    component: HomeView,
    meta: { requiresAuth: false },
  },
  {
    path: "/about",
    name: "about",
    component: () => import("../views/public/AboutView.vue"),
    meta: { requiresAuth: false },
  },

  {
    path: "/login",
    name: "login",
    component: () => import("../views/auth/LoginView.vue"),
    meta: {
      hideNavbar: true,
      isLogged: true,
      requiresAuth: false,
    },
  },
  {
    path: "/register",
    name: "register",
    component: () => import("../views/auth/RegisterView.vue"),
    meta: {
      hideNavbar: true,
      isLogged: true,
      requiresAuth: false,
    },
  },
  {
    path: "/forgot-password",
    name: "forgot-password",
    component: () => import("../views/auth/ResetPasswordView.vue"),
    meta: { hideNavbar: true },
  },

  {
    path: "/settings",
    component: () => import("../views/settings/SettingsLayout.vue"),
    meta: { requiresAuth: true },
    children: [
      {
        path: "",
        redirect: "/settings/profile",
      },
      {
        path: "profile",
        name: "settings-profile",
        component: () => import("../views/settings/SettingsProfile.vue"),
      },
      {
        path: "security",
        name: "settings-security",
        component: () => import("../views/settings/SettingsSecurity.vue"),
      },
      {
        path: "account",
        name: "settings-account",
        component: () => import("../views/settings/SettingsAccount.vue"),
      },
    ],
  },

  {
    path: "/dev",
    name: "dev-playground",
    component: () => import("../views/dev/DevPlaygroundView.vue"),
    meta: { requiresAuth: false },
  },

  {
    path: "/properties",
    name: "my-properties",
    component: () => import("../views/properties/MyPropertiesView.vue"),
    meta: { requiresAuth: true },
  },
];

const router = createRouter({
  history: createWebHashHistory(),
  routes,
});

router.beforeEach(async (to) => {
  const authStore = useAuthStore();

  const requiresAuth = to.matched.some((record) => record.meta.requiresAuth);
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
});

export default router;
