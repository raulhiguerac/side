import type { RouteRecordRaw } from "vue-router";

export const analyticsRoutes: RouteRecordRaw[] = [
  {
    path: "/avm",
    name: "avm",
    component: () => import("@/views/avm/AvmView.vue"),
    meta: { requiresAuth: false },
  },
];
