import type { RouteRecordRaw } from "vue-router";

export const adminCatalogRoutes: RouteRecordRaw[] = [
  {
    path: "/admin/catalog",
    name: "admin-catalog",
    component: () => import("@/views/admin/catalog/AdminCatalogView.vue"),
    meta: { requiresAuth: true, requiresAdmin: true },
  },
];
