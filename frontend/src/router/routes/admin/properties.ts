import type { RouteRecordRaw } from "vue-router";

/**
 * El padre no lleva `name`: tiene un hijo con `path: ""`, y nombrar a los dos
 * hace ambiguo un `push({ name: "admin-properties" })`. El nombre vive en el
 * hijo por defecto, que es el destino real.
 *
 * `meta` va solo en el padre — el guard usa `to.matched.some(...)` y `matched`
 * incluye los registros padre, así que los hijos quedan protegidos igual.
 */
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
