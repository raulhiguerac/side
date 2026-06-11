import type { RouteRecordRaw } from "vue-router";

export const publicRoutes: RouteRecordRaw[] = [
  {
    path: "/",
    name: "home",
    component: () => import("@/views/public/HomeView.vue"),
    meta: { requiresAuth: false },
  },
  {
    path: "/about",
    name: "about",
    component: () => import("@/views/public/AboutView.vue"),
    meta: { requiresAuth: false },
  },
];
