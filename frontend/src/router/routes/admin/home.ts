import type { RouteRecordRaw } from "vue-router";

export const adminHomeRoutes: RouteRecordRaw[] = [
  {
    path: "/admin",
    name: "admin-home",
    component: () => import("@/views/admin/AdminHomeView.vue"),
    meta: { requiresAuth: true, requiresAdmin: true },
  },
];
