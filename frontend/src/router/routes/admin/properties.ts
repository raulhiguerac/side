import type { RouteRecordRaw } from "vue-router";

/** El `name` vive en el hijo por defecto; el `meta` del padre alcanza porque el guard usa `matched`. */
export const adminPropertiesRoutes: RouteRecordRaw[] = [
  {
    path: "/admin/properties",
    component: () =>
      import("@/views/admin/properties/AdminPropertiesLayout.vue"),
    meta: { requiresAuth: true, requiresAdmin: true },
    children: [
      {
        path: "",
        name: "admin-properties",
        component: () =>
          import("@/views/admin/properties/AdminPropertiesModerationView.vue"),
      },
      {
        path: "promotions",
        name: "admin-properties-promotions",
        component: () =>
          import("@/views/admin/properties/AdminPropertiesPromotionsView.vue"),
      },
      {
        path: "imports",
        name: "admin-properties-imports",
        component: () =>
          import("@/views/admin/properties/AdminPropertiesImportsView.vue"),
      },
    ],
  },
];
