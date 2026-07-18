import type { RouteRecordRaw } from "vue-router";

export const adminPropertiesRoutes: RouteRecordRaw[] = [
  {
    path: "/admin/properties",
    name: "admin-properties",
    component: () =>
      import("@/views/admin/properties/AdminPropertiesView.vue"),
    meta: { requiresAuth: true, requiresAdmin: true },
  },
];
