import type { RouteRecordRaw } from "vue-router";

export const devRoutes: RouteRecordRaw[] = [
  {
    path: "/dev/create-property",
    name: "dev-create-property",
    component: () => import("@/views/dev/CreatePropertyDevView.vue"),
    meta: { requiresAuth: false },
  },
];
