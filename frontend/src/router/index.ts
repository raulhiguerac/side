import { createRouter, createWebHashHistory, RouteRecordRaw } from "vue-router";
import HomeView from "../views/HomeView.vue";
import { useAuthStore } from "@/stores/auth";

const routes: Array<RouteRecordRaw> = [
  {
    path: "/",
    name: "home",
    component: HomeView,
    meta: {
      requiresAuth: false,
    },
  },
  {
    path: "/about",
    name: "about",
    component: () => import("../views/AboutView.vue"),
    meta: {
      requiresAuth: false,
    },
  },
  {
    path: "/login",
    name: "login",
    component: () => import("../views/LoginView.vue"),
    meta: {
      hideNavbar: true,
      isLogged: true,
    },
  },
  {
    path: "/register",
    name: "register",
    component: () => import("../views/RegisterView.vue"),
    meta: {
      hideNavbar: true,
      isLogged: true,
    },
  },
  {
    path: "/forgot-password",
    name: "forgot-password",
    component: () => import("../views/ResetPasswordView.vue"),
    meta: {
      hideNavbar: true,
    },
  },
  // Settings routes
  {
    path: "/settings",
    component: () => import("../views/settings/SettingsLayout.vue"),
    meta: {
      requiresAuth: true,
    },
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
  // Properties routes
  {
    path: "/properties",
    name: "my-properties",
    component: () => import("../views/MyPropertiesView.vue"),
    meta: {
      requiresAuth: true,
    },
  },
];

const router = createRouter({
  history: createWebHashHistory(),
  routes,
});

router.beforeEach(async (to) => {
  const authStore = useAuthStore();

  // Si aún no hemos verificado la autenticación, esperamos
  if (!authStore._authChecked) {
    await authStore.checkAuth();
  }

  // Rutas que requieren autenticación
  if (to.matched.some((record) => record.meta.requiresAuth)) {
    if (!authStore.isAuthenticated) {
      return { name: "login" };
    }
  }

  // Rutas solo para usuarios NO logueados (login, register)
  if (to.matched.some((record) => record.meta.isLogged)) {
    if (authStore.isAuthenticated) {
      return { name: "home" };
    }
  }
});

export default router;
