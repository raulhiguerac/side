import type { RouteRecordRaw } from "vue-router";

export const devRoutes: RouteRecordRaw[] = [
  {
    path: "/dev/imagenes",
    component: () => import("@/views/dev/StepImagenesDevView.vue"),
  },
];
